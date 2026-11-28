# Workspace Architecture Reconciliation — Technical Review

**Project:** TAVIO — Timetable Administration & Validation Intelligent Organizer  
**Repository:** `zmd94/TAVIO`  
**Branch:** `main`  
**Status:** Agreed architecture direction; detailed design and implementation still require review and explicit authorization  
**Related specification:** [Workspace and Data Management Decisions](data_management.md)

## 1. Purpose

This document records the technical review that reconciles TAVIO's existing SQLite application with the agreed portable `.tavio` workspace-file workflow.

It separates:
- user-facing product decisions already agreed;
- findings observed in the current repository;
- the agreed technical direction; and
- technical details that still need design and testing.

This document is not authorization to change application code, database schema, migrations, or stable modules.

## 2. Agreed architecture direction

The agreed direction is:

1. A `.tavio` workspace will be a **single native SQLite database file** with the `.tavio` extension. It will not use a ZIP layer or another packaging format and should remain inspectable with standard SQLite software.
2. The `.tavio` file is portable: it can be moved and opened on another Windows computer with TAVIO installed, without depending on the original computer or an internet connection.
3. The school logo and other workspace-owned assets must be stored inside that workspace database, so moving or opening a workspace on another computer does not depend on a shared machine-local asset path.
4. Each workspace has a unique, persistent internal workspace ID stored in the database. The ID remains unchanged when the file is moved or renamed. A newly created workspace receives a new ID, even when selected school information is copied from another workspace.
5. TAVIO will introduce a `WorkspaceManager` and active `WorkspaceContext` lifecycle/context layer. The manager owns workspace creation, opening, switching, and safe activation; the context binds the active database manager, repositories, services, file path, and workspace-owned assets together. Repositories and services are rebuilt for the new context when switching. If opening a candidate workspace fails, the current context remains active and intact.
6. TAVIO follows an **offline-first, independent-computer model**. It does not detect whether the same workspace or another copy is open on another computer, does not use cross-computer file locks, and does not provide cross-computer synchronization, conflict detection, or merge. Users manage file transfer and decide which workspace copy is authoritative/latest.
7. Recovery data is computer-local and separate from the portable workspace file. Each computer maintains its own recovery state for a workspace, matched using the persistent workspace ID. A missing local recovery file must never prevent opening a valid `.tavio` file.
8. Existing SQLite repositories and services should be retained where practical. The project should evolve from its current SQLite foundation; a wholesale database or application rewrite is not the goal.
9. Workspace data must remain isolated. A failed OPEN AS or workspace switch must leave the currently active workspace usable and unchanged.
10. These decisions define the architecture direction only. They do not approve a specific migration, new table definition, code change, or implementation task.

## 3. Findings in the current repository

The technical review inspected the current database manager, connection setup, application startup, main window/service wiring, schema and migrations, school-profile service, configuration paths, and the workspace data-file decision record.

### 3.1 SQLite uses WAL mode

The current database connection configures SQLite with WAL journal mode and `synchronous=NORMAL`.

WAL mode can create companion `-wal` and `-shm` files. That behavior needs explicit lifecycle handling if the user-facing workspace is intended to be one portable file. A simple file copy of an active WAL database is not a safe packaging or backup strategy.

**Design implication:** the workspace implementation must define a safe SQLite checkpoint/close/backup lifecycle. A rollback-journal configuration such as `journal_mode=DELETE` may be more suitable for a single-file workspace, but the final journal-mode choice must be tested and approved as part of detailed design. Do not change the current connection mode casually or as an isolated patch.

### 3.2 Database path is currently application-managed

The current `DatabaseManager` obtains its database path from application paths. It is not currently designed around an injected, user-selected active `.tavio` file.

The main window constructs repositories and services around that manager at startup. The current arrangement does not provide a complete, safe mechanism for switching the database underneath all existing repositories and services.

**Design implication:** introduce a workspace context/lifecycle boundary that owns the active database manager and the services/repositories bound to it. Avoid scattered path changes or partial rebinding.

### 3.3 Startup currently initializes a local database

Application startup currently initializes the local SQLite database and applies migrations before the user-facing workspace-selection/reopen workflow.

**Design implication:** startup must be redesigned so it can resolve the last-used workspace, create the initial empty workspace when appropriate, validate a selected workspace, and only then establish the active workspace context. It must not silently create an unrelated blank workspace when reopening the last one fails.

### 3.4 School logo is currently outside the database

The school logo is currently stored under the application-local assets directory (for example, `%LOCALAPPDATA%\\TAVIO\\assets\\school_logo.png`). The school profile stores a path, and the school-profile service resolves and writes the image through application paths.

This creates a workspace-isolation problem: separate workspaces can point to or overwrite the same machine-local logo file.

**Design implication:** move workspace-owned logo bytes into the corresponding `.tavio` database. The application may extract an image to a temporary location when a UI or PDF library requires a filesystem path, but that temporary copy must not become the authoritative asset. Any cache must be workspace-scoped and safely cleaned up.

### 3.5 Existing migrations and schema version

The current migration chain contains schema migrations v1 through v4. Migration v3 adds the nullable `classes.class_teacher_id` foreign key to `teachers(id)` with `ON DELETE RESTRICT`. Migration v4 removes the unused legacy timetable-autosave table and its scope-validation triggers, and deletes the obsolete `autosave_interval_minutes` setting.

The migration system uses SQLite `PRAGMA user_version` to track the database schema version. The current supported schema version is 4.

**Design implication:** keep schema versioning distinct from the TAVIO application/package compatibility version. A newer TAVIO application version and a newer SQLite schema are related but are not interchangeable concepts. Validate package/application compatibility before attempting migration.

### 3.6 Legacy timetable autosave schema is superseded by whole-workspace recovery

The v1 schema created `timetable_workspace_autosaves`, two associated scope-validation triggers (`trg_twa_base_version_ins` and `trg_twa_base_version_upd`), and an `app_settings` value named `autosave_interval_minutes` seeded to 10 minutes. Repository inspection found no current runtime reads or writes for these objects. The timetable-construction workflow that might have used the draft table has not yet been implemented.

**Agreed decision:** do not retain a separate timetable-draft autosave mechanism. The single autosave mechanism will be whole-workspace computer-local recovery every 5 minutes, keyed by the persistent workspace ID. It writes recovery data outside the portable `.tavio` database and never updates the main workspace file.

**Migration v4 status: implemented.** The forward-only migration leaves historical migrations v1-v3 unchanged, drops both legacy scope triggers and the `timetable_workspace_autosaves` table, deletes the `autosave_interval_minutes` setting, and advances `PRAGMA user_version` to 4 atomically. Automated migration tests cover the v3-to-v4 upgrade, fresh initialization, preservation of unrelated data, integrity, repeat initialization, and rollback on failure.

The 5-minute interval belongs in application-local configuration, not in `app_settings` or the portable `.tavio` file. Migration v4 is schema cleanup only; it does not implement the new whole-workspace recovery engine.

## 4. Proposed logical architecture

The following is the recommended separation of responsibilities. Exact class names and module boundaries remain subject to detailed design.

```text
TAVIO Application
|
+-- Application Services
|   +-- Main Window / UI
|   +-- Application-local settings and logging
|   +-- Recent / last-opened workspace reference
|
+-- Workspace Lifecycle Layer
|   +-- WorkspaceManager
|   +-- Active WorkspaceContext
|   +-- NEW TIMETABLE / OPEN AS / SAVE / SAVE AS
|   +-- Compatibility and integrity validation
|   +-- Autosave / backup / recovery coordination
|
+-- Active WorkspaceContext
|   +-- Workspace file path (.tavio)
|   +-- SQLite DatabaseManager / connection
|   +-- Repositories and services for this workspace
|   +-- Workspace-owned assets (including school logo)
|
+-- Native SQLite .tavio file
    +-- Existing TAVIO relational data
    +-- Workspace settings and report settings
    +-- Timetable data and versions
    +-- Embedded workspace assets
```

### 4.1 Application-local data versus workspace data

Keep application-local operational data separate from school workspace data.

Potential application-local items include logs, application preferences, last-opened workspace reference, lock/coordination files, recovery metadata, local working databases, and temporary staging files. These must not contain authoritative school data that should travel with the `.tavio` package.

School profile, master data, assignments, timetables, report configuration, school-owned assets, and settings that describe or configure the school workspace belong to the active workspace.

#### Current `app_settings` inventory and ownership

The current source tree has one live application-level repository usage of `app_settings`:

| Setting key | Current purpose | Ownership decision |
|---|---|---|
| `signatory_label_language` | EN/MS display language for the Prepared By / Verified By labels on the Schedule Signatories page | **Workspace-owned** |

Rationale: the setting is currently persisted in the same SQLite database as the workspace's schedule-signatory configuration, is edited within that workspace feature, and determines how that workspace's signatory roles are presented. It should travel with the `.tavio` file and its successful change should count as a workspace mutation for dirty-state and SAVE purposes.

The schema v1 seed also introduced `autosave_interval_minutes` (10 minutes). Migration v4 removes that obsolete key together with the legacy timetable autosave table. It is not a live setting and must not be restored or repurposed. The agreed whole-workspace recovery cadence is five minutes and belongs to application-local operational policy/configuration, not to an individual workspace.

No current implementation was found using `app_settings` for general application preferences. Keep future installation/computer-specific preferences outside the workspace database, including (when implemented) theme, sidebar/window presentation state, last-opened workspace reference, recent-file history, application-wide UI preferences, logging configuration, and recovery scheduling/metadata.

**Ownership rule for future settings:** a value belongs in the workspace only when it describes, configures, or affects the school/workspace data or its workspace-specific presentation and must follow that workspace to another computer. A value that configures this TAVIO installation, this Windows user, or local operational behavior belongs in application-local configuration. Do not decide ownership solely from a generic setting name or from the fact that a value is convenient to store in SQLite.

New settings must be classified explicitly before adding a key or persistence path. Workspace-owned settings must use the active workspace context and participate in workspace dirty tracking; application-local settings must not alter workspace dirty state or be copied by NEW TIMETABLE unless a separate product decision explicitly requires it.

### 4.2 Workspace context and switching

The workspace lifecycle layer should own creation and activation of the workspace context.

For OPEN AS, the recommended sequence is:
1. Resolve unsaved-change and recovery decisions for the current workspace using the already agreed user workflow.
2. Validate the candidate `.tavio` file without changing the active context.
3. Open and initialize a candidate database manager and its dependent services/repositories.
4. Complete required integrity and compatibility checks.
5. Activate the new context only after all prior steps succeed.
6. Release the previous context safely after successful activation.

If any candidate step fails, retain the existing active workspace and its services. Never mix repositories or services from two workspaces.

### 4.3 Database manager injection

The current fixed-path database manager should be adapted through a deliberate design so it can receive the active workspace database path (or a workspace-owned connection provider).

Repositories and services must be constructed against the correct active context. Avoid mutating a global path while existing repositories still hold connections to the previous database.

### 4.4 File menu command dispatch

The File menu is not a page-navigation module. Its submenu entries must be connected to application/workspace command handlers and must never be inserted into the main page stack or display placeholder pages.

The existing visible commands map to the agreed workspace operations as follows:
- **New** → NEW TIMETABLE: create a new workspace and apply the agreed data-retention rules.
- **Open** → OPEN AS: select, validate, and activate a `.tavio` workspace without damaging the currently active workspace if opening fails.
- **Save** → SAVE: commit the active workspace to its current `.tavio` file using the safe candidate-and-verify sequence.
- **Save As** → SAVE AS: write the active workspace to a separately selected destination without modifying its source; handle an existing destination and its recovery identity safely.
- **Exit** → run the application shutdown workflow, including unsaved-change decisions and the agreed autosave-failure warning conditions.

The UI layer should dispatch these commands to a dedicated application/workspace service (or a clearly bounded command-handler layer). The handlers own validation, prompts, persistence and failure handling; the navigation tree only initiates the command. Do not put database lifecycle logic directly into navigation-item callbacks.

The command flow must respect the agreed SAVE / DON'T SAVE / CANCEL decisions before NEW TIMETABLE and OPEN AS, and the corresponding safe-exit decisions before EXIT. A cancelled or failed command must leave the active workspace and its displayed pages usable and unchanged. SAVE and SAVE AS are operations, not navigation destinations.

### 4.5 Active working database versus the portable source file

A key persistence issue must be resolved before implementation.

The existing repositories commit changes directly to the SQLite database during normal operations. If TAVIO opens a user's .tavio file as the live DatabaseManager target, ordinary form saves and repository transactions would modify that file before the user chooses the File → Save command. That would contradict the agreed rule that opening a workspace must not silently modify its source and that only explicit SAVE or SAVE AS commits changes to the portable package.

**Recommended architecture for review:** use a computer-local active working database for each open workspace.

- **Portable workspace path:** the user's .tavio file. It remains the last explicitly saved version.
- **Active working path:** a private local SQLite working copy associated with the workspace ID. Existing repositories and services operate on this database, so normal form operations can continue using SQLite transactions without modifying the portable source file.
- **Recovery path:** the computer-local .bak recovery snapshot, produced from the active working database according to the agreed five-minute recovery policy. It is distinct from both the portable source and the active working copy.
- **SAVE:** create and validate a candidate from the active working database, then safely replace the portable workspace file. Do not discard the working database until the save has been verified.
- **SAVE AS:** create a validated portable destination from the active working database. Keep the original source unchanged. The active workspace identity remains the same because SAVE AS is a copy of the same workspace, not creation of a new workspace.
- **OPEN AS:** validate the selected portable file, create/open its local working copy, and build a candidate context. Activate that context only after all checks succeed.
- **NEW TIMETABLE:** create a new local working database with a new workspace ID, copying only the three agreed school-information sections from the current context.

This working-copy approach is a technical recommendation derived from the existing repository's immediate SQLite transaction model and the agreed explicit-save behaviour. It is **not yet an approved implementation decision**. Review its storage footprint, cleanup, startup recovery, file permissions, and behavior when the portable file is on removable storage before implementation.

### 4.6 WorkspaceContext and WorkspaceManager responsibilities

The following responsibilities are proposed; exact module names and public method signatures remain subject to detailed design.

**WorkspaceContext** represents one fully prepared active workspace and owns:
- workspace ID and display/file metadata;
- portable source path, when one exists;
- local active working-database path;
- the DatabaseManager bound to that working database;
- repositories and application services constructed from that manager;
- workspace-owned asset access;
- dirty/last-explicit-save state needed by command workflows.

A context must not be partially rebound to another database. Its repositories and services all belong to the same workspace ID and working database.

**WorkspaceManager** coordinates lifecycle operations and owns:
- creating a new empty workspace;
- opening and validating a portable .tavio file;
- preparing a candidate working copy and candidate context;
- activating a candidate context only after successful preparation;
- creating NEW TIMETABLE from the permitted retained sections;
- saving and saving-as through validated candidate files;
- coordinating recovery checks and safe context shutdown;
- preserving the previous active context if a candidate operation fails.

The manager should not contain UI widgets or show dialogs directly. It should return typed outcomes/errors for a UI command controller to present to the user.

**File command controller** (provisional name) connects File menu actions to WorkspaceManager and application shutdown services. It owns user interaction sequencing (SAVE / DON'T SAVE / CANCEL, file pickers, confirmations) but delegates database and file safety to the lifecycle services. It must not implement persistence logic inside QTreeWidget callbacks.


### 4.9 Repository write-path audit and dirty-state implications

An initial read-only audit of the current `main` branch inspected `DatabaseManager`, SQLite connection configuration, the three current repositories, their services, the school-logo workflow, application startup, and MainWindow dependency construction.

**Observed write paths**

- `SchoolProfileRepository.upsert_profile()` and `update_logo_path()` perform writes through `DatabaseManager.transaction(immediate=True)`.
- `SchoolAdministratorRepository` add, edit, active-state, reorder, and delete operations use `DatabaseManager.transaction(immediate=True)`.
- `ScheduleSignatoryRepository.update_setting()` and `set_label_language()` use `DatabaseManager.transaction(immediate=True)`. The live `signatory_label_language` key is classified as workspace-owned because it configures the signatory-role presentation for the active workspace.
- The corresponding services delegate persistence to these repositories; the inspected service methods do not issue direct SQL writes themselves.
- The inspected repository uses of `DatabaseManager.connection()` are SELECT/read paths.
- Schema migrations are applied through `DatabaseManager.initialize()` and the migration runner using a connection-level, explicit migration transaction. Migration writes must not be confused with user edits or advance the active workspace's dirty generation.
- `SchoolProfileService.upload_logo()` and `remove_logo()` perform filesystem mutations in the application-local assets directory and then update `school_profile.logo_path` through the repository. This is a multi-resource operation; SQLite transaction tracking alone cannot represent its full consistency or failure state.

**Central transaction boundary**

The existing `DatabaseManager.transaction()` context manager owns BEGIN, COMMIT, ROLLBACK, and connection closure. This is a promising instrumentation point: a future change-generation notification can be emitted only after a successful commit. A transaction that raises or fails to commit must not advance the generation.

However, the current manager does not yet expose a dirty-state/change-generation callback or classify transactions by purpose. The audit therefore supports the central-boundary approach as a candidate, not as an implemented feature.

**Important gaps and design constraints**

1. `DatabaseManager.connection()` yields a normal writable SQLite connection in autocommit mode. The inspected repository call sites use it for reads, but the API itself does not enforce read-only use. A future write could bypass transaction-based tracking. Before implementation, decide whether to make ordinary connection access query-only/read-only and provide a separate explicit write unit-of-work, while preserving a dedicated migration path.
2. The current live `app_settings` usage is classified: `signatory_label_language` is workspace-owned and must count as a workspace mutation. The old `autosave_interval_minutes` key was removed by migration v4 and must not return; the agreed five-minute recovery cadence is application-local. General installation/user preferences belong outside the workspace database.
3. The school-logo workflow writes a machine-local file outside SQLite. It must be redesigned as a workspace-asset operation with coordinated staging/commit semantics when assets are embedded in the workspace. Do not treat the existing logo upload as covered merely because its final `logo_path` update uses a repository transaction.
4. The current `DatabaseManager.transaction()` API does not distinguish user-data writes, application maintenance, migrations, or recovery bookkeeping. The future tracking boundary needs an explicit policy so only committed workspace-data changes advance the workspace generation.
5. A successful transaction may contain no effective data change. The implementation should decide whether generation changes are based on actual SQLite change counts or an explicit mutation signal, and test no-op updates, trigger effects, rollback, and commit failure. Do not use widget dirty flags as the authoritative source.
6. The inspected MainWindow constructs repositories and services once from the startup DatabaseManager and passes them into pages. This confirms that a workspace switch must rebuild or replace the complete dependency graph, not merely change a path on an existing manager.

**Recommended next design step**

Before implementing dirty-state, complete a write-path inventory whenever new repositories or modules are added, define a read-only contract for non-transactional connections, preserve the setting-ownership rule in Section 4.1 for every new setting, and design an explicit post-commit mutation notification at the DatabaseManager/unit-of-work boundary. Add focused tests for successful commit, rollback, failed commit, no-op write, read-only enforcement, migrations, and workspace-asset changes.

This audit is based on the current source files inspected on `main`; it is not proof that future modules cannot add new write paths. No application code, schema, or migration was changed as part of this audit.


## 5. Embedded workspace assets

The approved direction is that the logo is stored within the `.tavio` workspace database.

A possible implementation is a dedicated table such as `workspace_assets` containing an asset key, media type, binary content, and any required metadata. This is an example of a design option, **not an approved schema definition**.

Before adding a table or migration, decide:
- supported asset types and size limits;
- whether there can be multiple logos or historical assets;
- how asset replacement and deletion work;
- how UI and PDF code access asset bytes;
- whether temporary extracted files are needed and how they are scoped/cleaned;
- how existing school-logo files are imported during migration;
- how failed migration or SAVE preserves the original asset and workspace.

Do not leave the authoritative logo in a shared application-local folder after workspace embedding is implemented.

## 5.1 Portable workspace identity and computer-local recovery

Every workspace must contain a unique internal workspace ID. The ID is generated when the workspace is created and remains stable through SAVE, SAVE AS, file movement, and file renaming. A genuinely new workspace receives a new ID.

The recovery mechanism is local to each computer:
- The portable `.tavio` file contains the authoritative workspace data and workspace ID.
- Each computer keeps its own recovery data in an application-local recovery area, keyed by workspace ID. Recovery data is not required to travel with the `.tavio` file.
- The local recovery record also carries the workspace ID. TAVIO must verify the ID before offering or applying recovery; a mismatch blocks recovery.
- When a `.tavio` file is opened on a computer that has no local recovery record for that workspace ID, TAVIO creates a new local recovery context after successfully validating/opening the workspace. The source `.tavio` is not modified merely by opening it.
- The absence of a local recovery file must not block OPEN AS.

The exact local recovery file layout and naming remain implementation details, but the design must not put the only recovery copy beside a portable file on removable or shared storage in a way that makes recovery depend on that location.

## 5.2 Offline-first and multiple computers

TAVIO does not coordinate workspace access between computers. It does not check whether a file or another copy is open elsewhere, does not create cross-computer locks, and does not synchronize or merge data.

Users may independently open a `.tavio` file on different computers. Each computer works with its own local state and recovery data. When users transfer workspace files by USB, network storage, or cloud storage, they are responsible for choosing and managing the latest authoritative copy. TAVIO does not resolve differences between copies.

This is not a collaborative editing or cloud-sync model. Avoid introducing network services, mandatory internet access, or cross-computer coordination into the workspace lifecycle.

## 6. Safe SQLite persistence and recovery

The existing workspace data-file decisions remain authoritative for user-facing behavior:
- one `.tavio` file per workspace;
- SAVE and SAVE AS are explicit operations;
- autosave every 5 minutes writes the associated `.bak`, not the main file;
- a failed autosave must not replace the last valid `.bak`;
- SAVE must not delete the recovery file until the new main file has been fully written and validated;
- recovery choices are RESTORE, KEEP CURRENT, and CANCEL;
- newer-version workspace files are rejected without modifying the source;
- older supported files are migrated only after preserving the original and validating the result.

### 6.1 Do not copy a live WAL database as a normal file

If WAL remains enabled, a valid database state may depend on the WAL file. Do not use a raw filesystem copy of only the main database file as the backup or SAVE candidate.

The detailed design must choose and test a safe mechanism, such as SQLite's Backup API or a properly coordinated checkpoint and connection shutdown. A candidate file should be validated before it replaces the destination.

### 6.2 Candidate validation

At minimum, the design should evaluate:
- SQLite `PRAGMA integrity_check`;
- SQLite `PRAGMA foreign_key_check`;
- required TAVIO schema objects and migration state;
- TAVIO application/package compatibility metadata;
- required workspace contents and asset integrity.

Validation must happen before replacing a valid main or recovery file. Exact validation rules and performance impact need testing with realistic school workspaces.

### 6.3 Journal mode decision

A single-file portable workspace may be easier to manage with SQLite rollback-journal mode (`DELETE`) than WAL, provided the application's local database access and performance requirements are satisfied. Cross-computer simultaneous editing and coordination are not product requirements.

This is a candidate decision for detailed design, not an instruction to change the current database connection immediately. Compare:
- sidecar-file behavior;
- local read/write needs;
- checkpoint and shutdown behavior;
- save/backup reliability;
- performance on typical and large school workspaces;
- behavior on USB and network-backed storage, while keeping the offline-first/no-sync product boundary clear.

## 7. Migration and compatibility boundaries

1. Validate that a candidate file is a TAVIO workspace before treating it as one.
2. Read both TAVIO application/package compatibility metadata and SQLite schema version.
3. Reject files from a newer TAVIO application version without modifying them.
4. For an older supported schema, preserve the original package before migration.
5. Migrate a safe candidate rather than risking the only original file.
6. Validate the migrated candidate before activation.
7. On failure, retain the original package and recovery material, and keep the currently active workspace unchanged.

Do not conflate `PRAGMA user_version` with the application version. The exact metadata location and compatibility policy need a separate technical specification.

## 8. Required follow-up technical design

Before implementation, prepare and review designs for:

1. Workspace file format metadata and application/schema compatibility.
2. WorkspaceManager and WorkspaceContext lifecycle and ownership.
3. DatabaseManager path/connection injection and repository/service construction.
4. SQLite journal mode, checkpoint, connection close, and backup strategy.
5. Embedded asset schema and logo import/access lifecycle.
6. Startup and last-opened workspace behavior.
7. NEW TIMETABLE creation and copying only SCHOOL PROFILE, SCHOOL ADMINISTRATORS, and SCHEDULE SIGNATORIES.
8. Computer-local recovery for a workspace that has not yet been saved to a user-selected path, and creation of a fresh local recovery context when a portable workspace is opened on another computer.
9. Removal of the legacy timetable-draft autosave schema and separation of the single whole-workspace recovery mechanism from portable workspace data.
10. SAVE, SAVE AS, computer-local recovery, migration, and interrupted replacement failure handling.
11. Test plan for crash, power loss, disk full, permission errors, USB/network/removable storage, invalid files, local recovery identity checks, and multiple workspace switching. Do not add cross-computer locking or synchronization tests as product requirements.
12. File-menu command dispatch tests: New, Open, Save, Save As, and Exit invoke their respective workflows and never create or display page-stack destinations; cancelled/failed operations preserve the active workspace.



### 8.1 Migration v4 — legacy autosave schema cleanup

The migration v4 decision is recorded in [Workspace and Data Management Decisions](data_management.md#17-existing-timetable-autosave-schema-cleanup--planned-migration-v4).

The migration is limited to removing the unused legacy timetable autosave table, its two validation triggers, and the old 10-minute `app_settings` entry. The whole-workspace recovery interval is 5 minutes and is held in application-local configuration, not in the workspace database. Historical migrations remain immutable.

This is an approved design direction, not permission to edit application code or execute the migration. Implementation must be separately authorized after the migration and recovery designs are reviewed.

## 9. Explicit implementation boundaries

- No code, database schema, or migration changes are authorized by this document.
- Do not begin implementation solely because the architecture direction is agreed.
- Do not repurpose existing timetable autosave tables/settings without tracing their usage and reviewing the impact.
- Do not change unrelated stable modules or perform a broad refactor.
- Preserve the existing SQLite foundation and existing data wherever possible.
- Bring unresolved technical choices back for review before implementation.


### 4.7 Workspace lifecycle state machine and File command flows

The three-file model is the recommended basis for the lifecycle design:

| Artifact | Role | May ordinary page edits modify it? |
|---|---|---|
| Portable `.tavio` | Last explicitly saved, transferable workspace | No |
| Local working database | Active editable state for this computer | Yes |
| Local recovery `.bak` | Latest successfully written recovery snapshot | Only the recovery process replaces it, atomically |

The local working database and recovery snapshot are application-managed files. Their locations must be derived from application-local paths and workspace identity, not from the portable file's folder. A workspace that has never been saved still has a workspace ID and a local working database; it therefore can be recovered before the user chooses a `.tavio` destination.

**Startup / reopen last workspace**

1. Read the last-opened portable path from application-local settings.
2. If no workspace has ever been created, create a new empty local working workspace with a new workspace ID. Do not invent a portable `.tavio` file until the user saves.
3. If a last-opened path exists, verify that it still exists and is accessible. If it is missing, moved, invalid, or incompatible, ask the user to locate/open a valid workspace or cancel. Do not silently substitute a new empty workspace.
4. Validate the portable source without modifying it. Prepare a local working database from the source using a safe SQLite backup mechanism.
5. Check for local recovery data keyed by workspace ID and verify its identity/metadata before offering recovery. If a valid recovery snapshot is newer than the working copy's saved baseline, offer the agreed RESTORE / KEEP CURRENT / CANCEL choices. RESTORE prepares a candidate working database from the recovery snapshot; KEEP CURRENT uses the freshly prepared working copy and follows the agreed recovery-retention policy; CANCEL aborts startup or workspace activation without activating the candidate.
6. Build all repositories/services against the candidate working database and activate the complete context only after preparation succeeds.
7. If any preparation step fails, retain the existing context (if one exists), source file, and valid recovery material.

The implementation must distinguish a genuinely first launch (no last-workspace reference has ever been recorded) from a stale or broken last-workspace reference. A missing path is not evidence that the user wants a blank workspace.

**NEW TIMETABLE**

1. Run the current-workspace unsaved-change decision: SAVE, DON'T SAVE, or CANCEL. SAVE must complete successfully before continuing; a failed SAVE aborts the command. DON'T SAVE discards the current unsaved working state only after the new workspace is successfully prepared; CANCEL changes nothing.
2. Prepare a new local working database with a newly generated workspace ID.
3. Copy only SCHOOL PROFILE, SCHOOL ADMINISTRATORS, and SCHEDULE SIGNATORIES from the current workspace, using an explicit allowlist. Do not copy timetable, master data, or other workspace data.
4. Validate the new working database and build its complete candidate context.
5. Activate it atomically at the application level, update the last-opened workspace state to represent an unsaved/new workspace, then retire the old context safely.
6. If preparation fails, keep the old context active. Do not leave a half-created workspace as active.

**OPEN AS**

1. Run the same SAVE / DON'T SAVE / CANCEL decision for the current workspace. A failed SAVE aborts; DON'T SAVE does not destroy the current context until the candidate is ready; CANCEL leaves everything unchanged.
2. Select and validate the candidate `.tavio` file, including format, compatibility, SQLite integrity, foreign keys, schema, and workspace ID.
3. Prepare a local working database and check recovery for that workspace ID.
4. Resolve any recovery prompt before activation. A recovery mismatch must never be applied to the candidate.
5. Build candidate repositories/services, then activate the candidate context only after all preparation succeeds.
6. Record the selected portable path as the last-opened workspace and retire the previous context safely.
7. Any cancel or failure leaves the current workspace, its pages, and its unsaved working data unchanged.

**SAVE**

1. If the active workspace has no portable source path yet, ask for a destination and follow SAVE AS creation semantics.
2. Ensure the active working database is in a consistent state and obtain a transactionally consistent SQLite backup into a temporary candidate in the destination folder.
3. Validate the candidate (integrity, foreign keys, schema/package compatibility, workspace ID, and required assets).
4. Replace the portable destination using a same-volume atomic replacement strategy where supported. Preserve the previous valid destination if candidate creation, validation, or replacement fails.
5. Verify the resulting destination. Only after successful verification update the saved baseline/dirty state and last-explicit-save metadata.
6. Do not delete the recovery snapshot before the new portable file has been fully verified. Recovery cleanup follows the agreed recovery policy and must itself be safe.
7. A failed SAVE leaves the active working database and last valid recovery snapshot intact and reports failure; it must not claim the workspace is saved.

**SAVE AS**

1. Ask for a destination. If it already exists, require explicit replace confirmation before touching it.
2. Create and validate a candidate from the active working database, then safely replace/create the destination.
3. Never modify the previous portable source as part of SAVE AS. On success, the destination becomes the active workspace's new portable source path and last-opened path; the workspace ID remains unchanged.
4. The local working database remains active; do not reopen or rebind repositories just because the portable path changed.
5. Keep recovery associated with the unchanged workspace ID. Do not treat SAVE AS as NEW TIMETABLE or create a new recovery identity.
6. On failure or cancellation, retain the previous source path, active context, working data, and recovery data.

**EXIT**

1. Apply the agreed unsaved-change decision: SAVE, DON'T SAVE, or CANCEL. A failed SAVE prevents a clean exit unless the user explicitly chooses a supported discard path.
2. If autosave has failed since the last successful explicit SAVE, show the agreed warning at EXIT. Do not imply recovery is current when the latest autosave failed.
3. Stop and await recovery/background work; checkpoint/close SQLite connections according to the selected journal-mode strategy.
4. Persist the last-opened workspace reference and close the active context safely.
5. A clean exit must not delete the only valid recovery snapshot for a workspace with unsaved changes.

**Atomic activation and disposal invariant**

Prepare a complete candidate context before swapping the active-context reference. The UI must not observe a partially initialized context or a mixture of old and new repositories. On candidate failure/cancellation, dispose only candidate resources and retain the old active context. After successful activation, stop workers and close connections belonging to the previous context before deleting or replacing its local working files.

### 4.8 Dirty-state and saved-baseline tracking

The File command workflow needs a reliable answer to whether the active working database contains changes not yet explicitly saved to its portable source. A page being visited, a form being opened, or a local recovery snapshot being written must not by itself mark the workspace as explicitly saved.

The current application commits repository/service writes directly to SQLite. Therefore, dirty tracking must be designed around successful data mutations, not merely around widget state.

**Recommended design direction for review:**
- Establish a saved baseline when a portable workspace is loaded into a new working database, and after a successful SAVE or SAVE AS.
- Route or instrument every successful workspace-data write transaction through a central DatabaseManager/unit-of-work boundary that can advance a workspace change generation. A rolled-back or failed transaction must not advance it.
- Record the generation associated with the last successful explicit save. The workspace is dirty when the current successful-write generation differs from that saved generation.
- Recovery snapshots preserve the generation metadata but do not reset the saved generation or mark the workspace clean.
- A new unsaved workspace begins with a defined initial baseline; its creation alone should not force a misleading SAVE prompt if it contains no user-entered changes. User edits make it dirty.
- Before implementation, inventory every write path (repositories, services, direct SQL, migrations, settings, and asset operations) and ensure workspace-data writes cannot bypass the tracking boundary. Application-local settings and recovery bookkeeping must not mark the workspace dirty.
- If the current code cannot provide one reliable transaction boundary without invasive changes, return with alternatives and trade-offs rather than adding incomplete dirty flags.

A plain SQLite `PRAGMA data_version` check is not sufficient by itself for this purpose because its semantics do not provide a reliable count of writes made by the same connection. File timestamps or raw database-file hashes are also not accepted as the sole dirty-state mechanism.

The exact implementation mechanism, transaction API, and treatment of schema migrations remain open until the write-path inventory and tests are reviewed.


---

**Summary:** TAVIO will move toward a native SQLite `.tavio` workspace with workspace-owned assets embedded in the database and a dedicated workspace lifecycle/context layer. This is the agreed direction; detailed technical design and implementation approval remain separate steps.
