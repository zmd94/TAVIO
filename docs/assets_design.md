# Workspace Asset Design

**Project:** TAVIO — Timetable Administration & Validation Intelligent Organizer  
**Repository:** `zmd94/TAVIO`  
**Status:** Design decisions recorded; detailed technical choices remain open; implementation not authorized  
**Scope:** Embedded workspace assets, School Logo lifecycle, shared asset access, integrity, caching, and use by application views and document output.

## 1. Purpose and scope

This document records the decisions and design discussion for storing and using assets inside a TAVIO workspace. The immediate use case is the school's logo, which is used throughout the application and in timetable previews, printing, and PDF generation.

This is a design record only. It does not authorize application-code changes, database schema changes, migrations, or implementation. Those require a separately reviewed technical design and explicit implementation approval.

This document supplements:

- [Workspace and Data Management Decisions](data_management.md)
- [Architecture Reconciliation](architecture_reconciliation.md)

If a detail in this document is still described as a proposal or open question, it must not be treated as an approved implementation requirement.

## 2. Core principles

1. The portable `.tavio` workspace is a native SQLite database file.
2. Workspace-owned assets, including the School Logo, are embedded in that workspace database as binary data (SQLite BLOB), not kept as authoritative machine-local files.
3. Each workspace has one official School Logo at a time.
4. The official School Logo is a workspace-level shared asset. All TAVIO modules that need the school's logo use the same authoritative asset.
5. Pending edits are not authoritative workspace data until the relevant Save operation succeeds.
6. Asset changes must be transactional and must not leave a profile referring to a missing or partially written asset.
7. Integrity checks must be conservative. TAVIO must not silently delete suspicious or orphaned assets.
8. Asset storage, preview caches, and temporary render files must not bypass workspace dirty tracking.

## 3. School Logo processing rules to preserve

The current School Logo processing behavior was inspected and the user decided to preserve it while changing authoritative storage from a filesystem path to SQLite BLOB storage.

The existing rules are:

- Accepted input formats: PNG and JPEG/JPG.
- Maximum input file size: 5 MiB (5,242,880 bytes).
- Minimum dimensions: 128 × 128 pixels.
- Maximum dimension: 3,000 pixels on either side; oversized dimensions are resized proportionally so the longest side is at most 3,000 pixels.
- No cropping and no upscaling.
- EXIF orientation is applied.
- Corrupt or truncated image data is rejected.
- Decompression-bomb protections remain in place.
- Transparency is preserved.
- The processed output format is PNG.
- Resizing uses LANCZOS resampling.
- The existing input-size limit applies to the original selected file. The current behavior does not impose a separate 5 MiB limit on the processed PNG output.
- An input file larger than 5 MiB is rejected; it is not automatically compressed to fit.

The implementation should preserve these behaviors unless a separate user decision explicitly changes them. Processing should be decoupled from persistence so that image validation/transformation can produce processed PNG bytes and metadata without writing the authoritative asset to a local file.

## 4. Embedded asset storage

### 4.1 Agreed direction

The School Logo is stored inside the workspace SQLite database as a BLOB. The logo must travel with its `.tavio` workspace and must not depend on a path under the computer's application-local assets directory.

### 4.2 Generic asset table

**Agreed direction:** use a generic table named `workspace_assets`, rather than creating a table dedicated only to the School Logo.

The table is intended to support the School Logo now and other workspace-owned assets if required later.

A possible set of fields discussed is:

| Field concept | Purpose |
|---|---|
| `asset_id` | Unique identifier for an asset record |
| `asset_type` | Asset classification, e.g. `school_logo` |
| `media_type` | Content type, e.g. `image/png` |
| `content` | Binary asset content stored as BLOB |
| `sha256` | Content-integrity digest |
| `file_size_bytes` | Actual BLOB size |
| `width` | Image width in pixels, where applicable |
| `height` | Image height in pixels, where applicable |

These are field concepts, not an approved SQL schema. Exact names, types, constraints, indexes, uniqueness rules, and relationships remain subject to detailed schema design.

### 4.3 School Profile reference

The School Profile is expected to hold a reference such as `logo_asset_id` to the official logo asset record.

A valid reference must resolve to an existing asset. Foreign-key enforcement is expected to protect referential integrity. The exact delete action and whether other asset references may be shared need to be specified in the schema design.

## 5. School Logo lifecycle and unsaved edits

### 5.1 New School Profile — pending logo

**Agreed decision:** if no School Profile exists yet, selecting a logo creates a pending logo in memory. It is not inserted into the workspace database until the user selects **Save School Profile**.

The intended behavior is:

1. The user selects an image.
2. TAVIO validates and processes it using the preserved rules in Section 3.
3. If processing succeeds, the processed image becomes the pending logo and is shown in the form preview.
4. If the user selects another image and it processes successfully, it replaces the previous pending logo.
5. If processing the replacement fails, the previous valid pending logo remains available and the preview does not change.
6. **Remove Logo** clears the pending logo and returns the preview to the no-logo state.
7. On **Save School Profile**, the profile record and logo asset are persisted together in one database transaction.
8. If Save fails, all form input and the pending logo remain available for another attempt.
9. If the user discards the form or the application stops unexpectedly before Save succeeds, the pending logo is discarded. It is not part of workspace autosave or recovery.

This avoids leaving an orphaned asset when a new profile is never saved.

### 5.2 Existing School Profile — staged changes

**Agreed decision:** when a School Profile already exists, logo edits are staged and do not alter the authoritative asset before Save succeeds.

- The currently saved logo remains intact in the workspace while the user edits the form.
- A successfully processed replacement is shown as a pending replacement.
- A failed replacement does not change the preview or the saved logo.
- **Remove Logo** marks a pending removal and updates the form preview, but does not delete the saved asset yet.
- On successful Save, profile changes and the logo replacement/removal are committed together in one transaction.
- If Save fails, the saved logo remains intact and the staged changes remain available for retry.
- Discarding changes restores the form to the last successfully saved profile and logo state.

### 5.3 Unsaved-change confirmation

**Agreed decision:** when the user attempts to cancel or leave School Profile while it contains unsaved changes, TAVIO asks:

> You have unsaved changes. Do you want to discard them?

The confirmation must account for all unsaved School Profile changes, not only the logo.

The intended actions are:

- **Keep Editing** — return to the form and retain all staged changes.
- **Discard Changes** — discard all unsaved form changes, including a pending logo, pending replacement, or pending removal, and restore the last saved state.
- **Cancel** — cancel the attempt to leave and retain the current form state.

If there are no unsaved changes, the user may leave without this confirmation. Final UI wording and button naming can be refined during UI design to avoid ambiguity with a page-level Cancel button.

## 6. Workspace-level shared School Logo

**Agreed decision:** there is one official School Logo per workspace, shared by all TAVIO modules that need it.

The logo is not a page-level or feature-level asset, and TAVIO must not create separate authoritative copies for each module.

Expected consumers include:

- School Profile display;
- Dashboard or other application identity views where the logo is shown;
- timetable views and tables;
- timetable preview;
- print output;
- PDF generation;
- other modules that require the official school identity.

All consumers must resolve the same official workspace logo. They may create temporary in-memory or file-based render representations when required by Qt, printing, or PDF libraries, but those representations are derived artifacts, not separate authoritative assets.

The School Profile is expected to own the official logo reference. The precise service/API boundary for consumers remains to be designed.

## 7. Asset replacement, references, and deletion

The discussion identified two possible identity strategies when replacing an asset:

- update the existing asset record's content while retaining its identifier; or
- create a new asset record with a new identifier and update the relevant reference.

Creating a new identifier for each replacement was recommended, but the user has not yet confirmed that choice. Therefore, **asset-ID behavior on replacement remains an open design decision**.

The following safety principles were discussed:

1. Replacing the School Logo must not mutate the saved logo before the Save transaction succeeds.
2. A normal School Logo replacement changes the official School Profile reference; it must not silently change unrelated references elsewhere in the workspace.
3. If an asset is referenced by more than one record, it must not be deleted while any valid reference remains.
4. An asset may be deleted as part of a known, successful replacement/removal transaction only after the transaction's reference checks establish that it is no longer referenced.
5. A global operation that intentionally redirects every reference from one asset to another is distinct from replacing the School Logo. No such global replacement workflow has been approved.
6. The product currently requires one official shared School Logo per workspace; it does not require a historical logo-version library.

The detailed model for shared references, asset ownership, replacement, and deletion must be resolved before schema implementation.

## 8. Integrity checks and orphaned assets

**Agreed decision:** use a conservative policy for orphaned assets and integrity anomalies.

TAVIO should be designed to detect and report conditions such as:

- an asset not referenced by any workspace record;
- a School Profile logo reference that does not resolve to an asset;
- a BLOB whose actual size differs from `file_size_bytes`;
- a SHA-256 digest that does not match the BLOB content;
- image format or dimensions that disagree with stored metadata;
- SQLite integrity-check failures;
- foreign-key violations.

When an orphan or inconsistency is detected:

1. Report it as an integrity warning or error with enough context for diagnosis.
2. Do not silently delete or rewrite the suspicious asset.
3. Preserve the asset and related workspace data until the cause is understood.
4. Any repair requires further inspection and user confirmation.
5. Before a repair operation, ensure a valid recovery copy is available.
6. Do not claim a repair succeeded until the repaired workspace has been validated.

This conservative integrity-repair policy does not prohibit a deliberate, transactional deletion of a known superseded asset during a normal user-requested replacement/removal, provided no references remain and the final deletion policy is approved in the detailed design.

## 9. Workspace Asset Service and consumers

A centralized **Workspace Asset Service** was proposed as the single application access point for authoritative workspace assets.

The proposed responsibilities include:

- retrieving the official School Logo for the active workspace;
- validating asset metadata and content when appropriate;
- coordinating asset insertion, replacement, and removal through workspace transactions;
- exposing processed bytes or suitable image representations to UI, preview, print, and PDF consumers;
- keeping asset persistence separate from temporary rendering/extraction;
- notifying or invalidating dependent caches only after a successful database commit.

The user has not yet explicitly approved the service's exact API, ownership, or transaction boundary. Those remain technical design items.

Application modules should not independently construct ad hoc SQL queries for the logo. A shared access abstraction is the proposed direction, subject to detailed architecture review.

## 10. In-memory caching

Caching was discussed to avoid repeatedly reading the logo BLOB from SQLite whenever the logo is rendered.

The proposed principles are:

- SQLite remains the authoritative source.
- Cache is temporary, in-memory, and never included in the `.tavio` file, autosave, or recovery.
- Cache reads must not mark the workspace dirty.
- A missing or invalid cache entry should be discarded and reloaded from SQLite.
- If SQLite cannot provide the official logo, TAVIO should report the read failure rather than inventing a replacement.
- If no official logo exists, consumers show the agreed no-logo state.
- Pending form images are kept separate from the cache of the currently saved official logo.
- A cache update or invalidation for a saved logo occurs only after the database transaction commits successfully.
- A failed transaction must leave the currently saved logo/cache state intact.
- Cache entries must be isolated by workspace identity so one workspace's logo is never displayed in another workspace.

A cache identity using `workspace_id`, `asset_id`, and/or `sha256` was discussed as a possible strategy. The exact cache key and invalidation mechanism remain open.

A **single active official-logo cache per workspace**, with pending form content managed separately and cache cleanup on workspace disposal, was proposed. The user has not yet confirmed this cache policy. It remains an open decision.

## 11. Workspace switching, temporary files, and rendering

The workspace lifecycle design requires repositories and services to be bound to the active workspace context. Asset access must follow the same isolation boundary.

Expected behavior:

- On workspace activation, logo retrieval is scoped to that workspace.
- Switching workspaces must not allow a stale cache entry from the previous workspace to appear in the new workspace.
- On workspace disposal, its cache and temporary derived resources are released safely.
- If a rendering library requires a filesystem path, TAVIO may materialize a temporary derived file from the authoritative BLOB.
- A derived file is not authoritative, is rebuildable, and must be scoped and cleaned up safely.
- Temporary render files and cache activity must not mark the workspace dirty or alter its saved/recovery state.

The exact temporary-file location, lifecycle, Qt image ownership, PDF library interface, and cleanup strategy remain technical design questions.

## 12. Relationship to SAVE, autosave, recovery, and portability

The asset lifecycle must follow the workspace data-management decisions:

1. A successfully saved official logo is part of the workspace SQLite database and therefore travels with the `.tavio` file.
2. SAVE and SAVE AS include the official logo because it is stored in the workspace database.
3. The logo is included when NEW TIMETABLE copies the allowed SCHOOL PROFILE data from the source workspace.
4. Pending School Profile logo edits are not authoritative workspace data and are not included in workspace autosave/recovery.
5. Once an asset change is committed to the active working database, it participates in the same workspace dirty tracking as other workspace data.
6. Autosave/recovery snapshots must include committed workspace asset changes.
7. Cache and temporary rendering files are not workspace data and are not included in dirty tracking or recovery.
8. The asset implementation must use the safe SQLite backup/candidate validation strategy selected for workspace SAVE and recovery. A raw copy of only the main database file must not be assumed safe while WAL is enabled.

## 13. Migration from the current filesystem-based logo

The current application stores the logo as a machine-local file and keeps a relative logo path in School Profile. The target design embeds the processed logo in the workspace database.

A migration/import design is still required. It must address:

- locating and validating an existing logo file;
- preserving the existing image-processing rules;
- embedding the processed bytes in the correct workspace;
- updating the School Profile reference safely;
- behavior when the old file is missing, unreadable, or invalid;
- preserving the original workspace and recoverable data if migration fails;
- removal of the old authoritative path dependency only after the embedded asset has been validated.

No migration behavior or schema version has been approved by this document.

## 14. Open decisions before implementation

The following items remain unresolved and must be reviewed before schema or code changes:

1. Exact `workspace_assets` SQL schema, field types, constraints, indexes, and uniqueness rules.
2. Whether a new `asset_id` is created on every replacement or the existing identifier is retained.
3. The precise reference/ownership model and whether generic assets may be shared by multiple records.
4. The deletion strategy for superseded assets and the exact foreign-key behavior.
5. Whether the proposed Workspace Asset Service is the sole public access boundary, and its exact API/transaction ownership.
6. Cache policy: single active logo cache or another bounded strategy; exact cache key and invalidation.
7. Temporary image/file strategy for Qt, printing, and PDF generation.
8. Detailed handling of missing/corrupt assets and user-facing integrity diagnostics/repair.
9. Migration/import of existing filesystem-based logos.
10. Test plan for transaction rollback, failed Save, workspace switching, cache invalidation, PDF/print rendering, integrity checks, and migration failure.

Do not silently resolve these items in implementation. Bring the trade-offs back for review.

## 15. Implementation boundary

- This document does not authorize code, schema, or migration changes.
- Preserve the existing School Logo validation and processing behavior unless separately approved.
- Do not leave the authoritative logo in a shared application-local folder after workspace embedding is implemented.
- Do not create per-module authoritative logo copies.
- Do not silently delete assets discovered by integrity checks.
- Do not include pending logo form state or render caches in workspace dirty tracking.
- Do not begin implementation until the open technical decisions and test plan have been reviewed and implementation is explicitly authorized.

---

**Summary:** TAVIO will embed the official School Logo in each workspace as a SQLite BLOB, use one workspace-level shared logo across application views and document output, stage edits until Save succeeds, and apply conservative asset-integrity handling. The generic `workspace_assets` table is the agreed direction. Detailed schema, asset identity, service API, caching policy, migration, and implementation remain open for review.
