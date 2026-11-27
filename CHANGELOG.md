# Changelog

All notable code changes to TAVIO are documented in this file.

This project uses version numbers in the format `vMAJOR.MINOR.PATCH`.

## [Unreleased]

The entries below summarize code changes present in the repository's `main` branch that have been implemented and verified. They are not a published or tagged release. No release version is assigned yet.

### Added

- **SQLite database foundation:** Introduced database connection configuration, connection and transaction management, database error handling, and a versioned migration runner using `PRAGMA user_version`.
- **Database schema migrations:** Added the initial core schema (Migration v1), school profile/administrator/schedule-signatory schema updates (Migration v2), Class Teacher database support (Migration v3), and legacy autosave schema cleanup (Migration v4).
- **School Profile management:** Added domain, repository, service, and UI support for school profile details and school logo upload/management.
- **School Administrator management:** Added domain, repository, service, validation, and UI support for managing school administrators.
- **Schedule Signatories management:** Added domain, repository, service, validation, and UI configuration for Teacher, Class, and Special Room schedule signatories, including Prepared By/Verified By assignments and label-language preference.
- **Class Teacher database groundwork:** Added nullable `classes.class_teacher_id` referencing `teachers(id)` with `ON DELETE RESTRICT`. Existing classes remain unassigned after migration. This is database support only; Class Teacher assignment UI and application-level validation are not yet implemented.
- **Application branding:** Integrated TAVIO branding assets into the desktop application, including application/window icons and sidebar branding.

### Changed

- **Application startup:** Integrated database initialization and startup error handling into the desktop application lifecycle.
- **Windows packaging:** Improved PyInstaller configuration, resource and asset discovery, dependency bundling, and Windows build verification.
- **Single-instance protection:** Adopted Qt `QLockFile` for application instance locking and clean lock release.
- **Resource handling:** Improved resolution of bundled resources in source and PyInstaller execution environments.
- **Legacy autosave configuration:** Removed the unused 10-minute `autosave_interval_minutes` workspace setting. The planned five-minute whole-workspace recovery interval is computer-local application configuration and is not stored in the workspace database; the recovery mechanism itself is not implemented by Migration v4.

### Fixed

- **School logo upload safety:** Added protection against oversized/decompression-bomb images and strengthened file/database consistency with backup and restoration handling.
- **Single-instance lock handling:** Disabled stale-lock expiry for a valid long-running application instance so it is not incorrectly treated as stale.
- **Packaging paths:** Corrected project-root and branding-asset paths used by the Windows packaging configuration.

### Removed

- **Legacy timetable draft autosave schema:** Removed the unused `timetable_workspace_autosaves` table and its `trg_twa_base_version_ins` and `trg_twa_base_version_upd` triggers in Migration v4. The timetable draft autosave feature was not implemented; this cleanup does not remove user-created timetable drafts.
- **Legacy autosave interval setting:** Removed the `autosave_interval_minutes` row from `app_settings`. No replacement workspace setting was added because the planned whole-workspace recovery interval belongs in computer-local application configuration.

### Security

- **Image-processing safeguards:** Added decompression-bomb warning protection during school logo processing.

### Verification

- Class Teacher Migration v3 verification: **111/111 automated tests passed**, including **29/29 database tests**; Ruff checks passed.
- Migration v4 verification: **32/32 database tests passed**; the complete test suite passed **114/114 tests**; `python -m ruff check src tests` reported **All checks passed**.
- The two warnings reported by the full test suite are `DeprecationWarning` messages from Google Protobuf (`MessageMapContainer` and `ScalarMapContainer`) concerning Python 3.14 compatibility. They are dependency warnings, not test failures.
- Migration tests cover schema version progression, preservation of unrelated data, removal of the legacy autosave table/triggers/setting, foreign-key checks, SQLite integrity checks, rollback on migration failure, and repeat initialization.
- No GitHub Actions workflow runs were found for this repository at the time this changelog was reviewed; the verification above reflects the recorded local test results.

---

## Versioning

- **MAJOR**: Incompatible changes or major milestones that require breaking compatibility.
- **MINOR**: New functionality that remains compatible with the existing system.
- **PATCH**: Bug fixes and small, backward-compatible corrections.

Only code changes that have been successfully implemented and verified through the relevant tests are recorded as completed entries. Discussions, proposals, planned work, and unverified changes must not be presented as completed changes.

Each versioned entry should include its release date and relevant change categories. Move verified entries from `[Unreleased]` into a versioned section (for example, `v0.1.0`) only when that version is formally released or tagged.
