# TAVIO — Workspace Recovery Design

**File:** `docs/recovery_design.md`  
**Status:** Technical Design — Decisions Agreed  
**Scope:** Workspace Autosave, Recovery and Temporary File Management

---

## 1. Purpose

This document defines the technical design for TAVIO workspace autosave and recovery.

The objectives are to:

1. Reduce data-loss risk when the application or computer stops unexpectedly.
2. Protect the main `.tavio` file from unintended autosave changes.
3. Provide a reliable recovery mechanism.
4. Ensure a failed autosave cannot destroy the last valid recovery state.
5. Keep recovery computer-local and fully usable offline.

This document records agreed design decisions. It does not mean that the features have been implemented or that implementation has been authorized.

## 2. Core Principles

### 2.1 Portable workspace

- A `.tavio` file is a native SQLite database file.
- Workspace data and related assets are stored in that file.
- Each workspace has a unique, persistent `workspace_id`.
- The `workspace_id` is not displayed to the user.
- A `.tavio` file can be moved to another Windows computer with TAVIO installed.
- Recovery is stored separately on each computer.

### 2.2 Computer-local recovery

Recovery directory:

`%LOCALAPPDATA%\TAVIO\recovery\`

- Each workspace has one local recovery state per computer.
- Recovery is identified by `workspace_id`, not by file name or file location.
- Recovery does not travel with the portable `.tavio` file.
- Opening a `.tavio` file on another computer does not require recovery from the original computer.
- The absence of a recovery file must not prevent opening a valid `.tavio` file.
- TAVIO does not provide cross-computer file locking, synchronization, conflict detection or merging.

## 3. Autosave

### 3.1 Interval and behavior

- Autosave runs every **5 minutes**.
- Autosave runs silently in the background.
- No notification is shown when autosave succeeds.
- No persistent autosave status is shown in the status bar.
- No immediate notification is shown when autosave fails.

### 3.2 Location and content

- Autosave writes the latest workspace state to the computer-local recovery file.
- Autosave does not write directly to the main `.tavio` file.
- One recovery state is maintained per workspace per computer.
- The five-minute interval is stored in local application configuration, not in `app_settings` or in the `.tavio` workspace.

### 3.3 Autosave failure

When autosave fails:

- Record the failure internally.
- Preserve the last valid recovery state.
- Do not replace an existing valid recovery with an incomplete or invalid file.
- Do not show an immediate notification or persistent status-bar message.
- If the user chooses EXIT or NEW TIMETABLE without first using SAVE or SAVE AS after an autosave failure, warn that the recovery file could not be updated and the latest changes may not be protected.

A subsequent successful autosave clears the current failure status.

## 4. Building a Recovery Snapshot

### 4.1 Temporary candidate

Each autosave creates a separate temporary candidate in the recovery directory.

Proposed process:

1. Create a consistent database snapshot using the SQLite Backup API.
2. Write the snapshot to a temporary candidate file.
3. Close relevant connections as appropriate.
4. Validate the candidate.
5. If all checks pass, promote the candidate to the active recovery file.
6. If validation or replacement fails, reject the candidate and preserve the previous recovery file.

The SQLite Backup API is recommended because the application uses SQLite WAL mode. A raw copy of only the main database file may omit changes that are still in the WAL file.

### 4.2 Candidate validation

Minimum checks:

- `PRAGMA integrity_check`
- `PRAGMA foreign_key_check`
- Candidate `workspace_id` matches the target workspace.
- `PRAGMA user_version` can be read and is supported.
- Required schema and workspace metadata exist.
- The candidate can be reopened as a SQLite database.

A candidate that fails any required check must not be accepted as the active recovery.

### 4.3 Recovery replacement

- Build the new candidate separately from the existing recovery file.
- Validate the candidate before replacement.
- Use a safe file-replacement procedure.
- Preserve the previous valid recovery if snapshot creation, validation or replacement fails.
- Never delete the previous recovery merely because creation of a new candidate has started.

## 5. Generation Number

Each recovery snapshot has:

- Snapshot time.
- `workspace_id`.
- `generation_number`.

The generation number identifies snapshot order.

Rules:

1. Increment the generation number for each newly accepted snapshot.
2. If two valid candidates have the same snapshot time, the higher generation number is newer.
3. Select the valid candidate with the latest snapshot time; use generation number to break ties.
4. Older candidates may be deleted after the newer candidate has successfully become the active recovery.
5. If replacement fails, preserve the previous valid recovery.

Generation number is recovery metadata and does not change the main workspace database schema.

## 6. Startup Recovery

At startup, TAVIO checks:

- Existing recovery files.
- Leftover temporary candidates.
- File validity and `workspace_id` matching.
- Snapshot times and generation numbers.

If a valid recovery is available, present three choices to the user.

### 6.1 RESTORE

Agreed behavior:

- Open the recovery contents as the active workspace.
- Do not overwrite or modify the main `.tavio` file.
- Let the user continue working in the recovered workspace.
- Continue five-minute autosave to the same recovery state.
- Replace the previous recovery only after a new snapshot has been created and validated successfully.
- Update the main `.tavio` file only when the user explicitly chooses SAVE or SAVE AS.

If opening the recovery fails, the main `.tavio` file must remain unchanged.

### 6.2 KEEP CURRENT

Agreed behavior:

- Open the main `.tavio` file as the active workspace.
- Preserve the existing recovery file.
- Do not delete recovery merely because the user selected KEEP CURRENT.
- Continue autosave at the five-minute interval.
- Replace the old recovery only after a new autosave has been created, validated and accepted successfully.

If the new autosave fails, preserve the old recovery.

### 6.3 CANCEL

Agreed behavior:

- Defer the recovery process.
- Do not restore the recovery file.
- Do not modify the main `.tavio` file.
- Do not delete or modify recovery files.
- Allow the user to make the recovery decision again at the next application launch.

## 7. Temporary Files After an Unexpected Shutdown

If TAVIO or the computer stops unexpectedly:

1. Inspect leftover temporary files at the next startup.
2. Validate each candidate's SQLite integrity and `workspace_id`.
3. Do not use invalid candidates.
4. Allow valid candidates to be considered for recovery.
5. If multiple valid candidates exist, select the most recent one.
6. If snapshot times are equal, use the higher generation number.
7. Protect the previous valid recovery until the new candidate has been accepted as the active recovery.

### 7.1 Cleanup rules

- Older candidates that are no longer needed may be deleted after the newer candidate has successfully become the active recovery.
- Unneeded temporary files may be cleaned up after the recovery process is complete.
- The active recovery must not be deleted by cleanup.
- The main `.tavio` file must not be deleted by recovery cleanup.
- If a new candidate fails validation, do not delete any previous valid recovery.

**Mandatory principle:** Never sacrifice the last valid recovery in order to accept a candidate that has not been proven valid.

## 8. SAVE and SAVE AS

### 8.1 SAVE

Proposed process:

1. Ensure the latest workspace state can be safely represented in recovery.
2. Build a temporary candidate for the main file.
3. Validate SQLite integrity and workspace metadata.
4. Replace the main file using a safe replacement procedure.
5. Reopen or otherwise verify the replacement.
6. Delete the related recovery only after SAVE has succeeded.

If SAVE fails:

- Preserve the original main file.
- Preserve valid recovery.
- Notify the user of the failure.
- Allow the user to retry or choose SAVE AS.

### 8.2 SAVE AS

- Save the workspace as a new `.tavio` file.
- Do not modify the source file.
- Preserve the same `workspace_id` for the same workspace.
- Manage recovery by `workspace_id`, not by file name or location.
- Never silently treat an existing recovery for a different workspace as belonging to the new workspace.

### 8.3 Important rule

A successful autosave does not update the main `.tavio` file. An explicit SAVE or SAVE AS is required to persist changes to the main file.

## 9. Workspace Identity and Recovery Isolation

- Each workspace has a unique `workspace_id`.
- The ID remains unchanged when the file is saved, renamed, moved or copied.
- NEW TIMETABLE creates a new `workspace_id`.
- Recovery must have the same ID as the target workspace.
- An ID mismatch blocks use of that recovery for the target workspace.
- Recovery belonging to another workspace must never be used or overwritten.

If a valid `.tavio` file is opened on a computer that has no recovery for its ID, TAVIO may establish a new local recovery context after the file has been validated and opened.

## 10. Proposed Technical Components

The following components are proposed for implementation:

| Component | Responsibility |
|---|---|
| `WorkspaceManager` | Manage workspace opening, switching and lifecycle |
| `WorkspaceContext` | Provide the active workspace context |
| `WorkspaceRecoveryManager` | Manage recovery state and identity |
| `WorkspaceRecoveryService` | Handle snapshots, validation and replacement |
| `RecoveryWorker` | Execute recovery work outside the UI thread |
| `RecoveryMetadata` | Store snapshot metadata and generation number |

These are proposed architectural boundaries. Names and class responsibilities may be refined during technical implementation review.

## 11. Relationship With the Existing Architecture

Current application characteristics:

- DatabaseManager uses a fixed database path.
- SQLite uses WAL mode.
- Database connections are opened independently for operations.
- WorkspaceManager and the portable `.tavio` lifecycle are not yet complete.
- Whole-workspace recovery has not yet been implemented.

Therefore:

- Do not add whole-workspace autosave hastily to `main.py`.
- Integrate recovery after the workspace lifecycle and WorkspaceContext are available.
- Preserve the existing SQLite and repository/service architecture where practical.
- Do not change the main database schema without a separate technical design and approval.

## 12. Out of Scope and Not Yet Authorized

This design does not automatically authorize:

- Implementation of WorkspaceManager.
- Implementation of portable `.tavio` workspace support.
- Implementation of five-minute autosave.
- Database schema changes.
- UI changes.
- Adding or changing recovery tables in SQLite.
- Cross-computer locking or synchronization.
- Conflict detection or merging.
- Cloud backup or cloud recovery.

Each implementation step requires technical review and separate approval.

## 13. Required Tests

Before recovery is considered complete, test at least:

1. Successful autosave every five minutes.
2. Autosave failure preserves the previous recovery.
3. Crash while a snapshot is being created.
4. Computer shutdown before a candidate is complete.
5. Crash after candidate validation but before replacement.
6. Crash during replacement.
7. Invalid temporary candidate.
8. Recovery with a mismatched `workspace_id`.
9. Two valid candidates with different snapshot times.
10. Two valid candidates with the same time but different generation numbers.
11. RESTORE opens recovery without modifying the main file.
12. Autosave after RESTORE updates the same recovery state.
13. KEEP CURRENT preserves recovery until a new autosave succeeds.
14. CANCEL preserves all recovery files.
15. Successful SAVE before recovery deletion.
16. Failed SAVE preserves the main file and recovery.
17. SAVE AS does not affect the source file.
18. Insufficient disk space.
19. Insufficient folder permissions.
20. Recovery on another computer is rejected when the ID does not match.

## 14. Agreed Decisions

| # | Topic | Decision |
|---:|---|---|
| 1 | Autosave interval | Every 5 minutes |
| 2 | Recovery location | `%LOCALAPPDATA%\TAVIO\recovery\` |
| 3 | Successful autosave | Silent; no notification |
| 4 | Failed autosave | Record internally |
| 5 | Previous recovery | Preserve if new candidate fails |
| 6 | RESTORE | Open recovery as active workspace |
| 7 | SAVE after RESTORE | Only then update the main file |
| 8 | Autosave after RESTORE | Continue to the same recovery state |
| 9 | KEEP CURRENT | Preserve recovery until a new autosave succeeds |
| 10 | CANCEL | Defer recovery without modifying files |
| 11 | Temporary candidate | May be considered after validation |
| 12 | Multiple valid candidates | Select the most recent |
| 13 | Equal snapshot times | Use generation number |
| 14 | Older candidates | Delete after new candidate is accepted |
| 15 | New candidate fails | Do not delete previous valid recovery |
| 16 | Recovery identity | Match using `workspace_id` |
| 17 | Snapshot method | SQLite Backup API recommended |
| 18 | Validation | SQLite integrity, foreign keys and metadata |
| 19 | Cross-computer recovery | Local recovery on each computer |
| 20 | Implementation | Requires technical review and separate approval |

---

**This document records the agreed TAVIO Workspace Recovery design.** Any change to the decisions above must be documented as a design revision before implementation.
