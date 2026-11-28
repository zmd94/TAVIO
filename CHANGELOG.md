# Changelog

All notable code changes to TAVIO are documented in this file.

This project uses version numbers in the format `vMAJOR.MINOR.PATCH`.

## [Unreleased]

The entries below summarize code changes present in the repository's `main` branch. The navigation milestone has passed local automated tests and manual application verification. These are not a published or tagged release. No release version is assigned yet.

### Verified

- **Navigation structure milestone:** Completed the main collapsible sidebar hierarchy for Dashboard, File, School Setup, Master Data, Timetable, Manual Editor, Absences & Relief, Reports, and Settings.
- **School Setup navigation:** Added and ordered the six submenu destinations as Academic Year, Bell & Break Times, School Sessions, School Profile, School Administrators, and Schedule Signatories. Academic Year, Bell & Break Times, and School Sessions are navigation placeholders only; their page workflows remain to be designed and implemented.
- **Sidebar interaction and presentation:** Added expanded/collapsed navigation behaviour, custom icons for key menu items, Dashboard positioning, and removal of sidebar tooltips. Save As shares the Save icon.
- **Navigation verification:** Updated startup/navigation tests to assert the School Setup submenu order, route keys, icons, collapsed startup state, sidebar layout, and removal of tooltips. The complete local test suite passed (114/114 tests), Ruff passed, and manual application testing confirmed that the menus and navigation work correctly.

### Documentation

- **Workspace lifecycle architecture specification:** Documented the recommended three-file model (portable `.tavio`, computer-local working database, and computer-local recovery snapshot), File command lifecycle flows, atomic workspace-context activation, failure/cancellation invariants, and proposed dirty-state tracking. This is a design specification only; no application code or database schema was changed.

### Documentation

- **Dirty-state write-path audit:** Reviewed current database transaction management, repository/service write paths, app settings, logo file operations, and MainWindow dependency construction. Recorded the existing transaction boundary as a candidate for post-commit change tracking and documented read-only connection, settings ownership, and workspace-asset gaps. No application code or database schema was changed.

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
- **Navigation test coverage:** Updated School Profile, School Administrators, Schedule Signatories, and startup database tests to match the `QTreeWidget` sidebar hierarchy, verify stable route keys, and assert stacked-page counts.
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

- Navigation milestone verification: the complete local test suite passed **114/114 tests**, Ruff checks passed, and manual application testing confirmed menu/navigation behaviour.
- Class Teacher Migration v3 verification: **111/111 automated tests passed**, including **29/29 database tests**; Ruff checks passed.
- Migration v4 verification: **32/32 database tests passed**; the complete test suite passed **114/114 tests**; `python -m ruff check src tests` reported **All checks passed**.
- Navigation test alignment verification: the complete test suite passed **114/114 tests** in **82.42 seconds** after the four navigation/startup test updates.
- The two warnings reported by the latest full test-suite run are `DeprecationWarning` messages from Google Protobuf (`MessageMapContainer` and `ScalarMapContainer`) concerning Python 3.14 compatibility. They are dependency warnings, not test failures.
- Migration tests cover schema version progression, preservation of unrelated data, removal of the legacy autosave table/triggers/setting, foreign-key checks, SQLite integrity checks, rollback on migration failure, and repeat initialization.
- No GitHub Actions workflow runs were found for this repository at the time this changelog was reviewed; the verification above reflects the recorded local test results.

---

## Versioning

- **MAJOR**: Incompatible changes or major milestones that require breaking compatibility.
- **MINOR**: New functionality that remains compatible with the existing system.
- **PATCH**: Bug fixes and small, backward-compatible corrections.

Only code changes that have been successfully implemented and verified through the relevant tests are recorded as verified entries. Implemented changes awaiting a fresh test run are explicitly labelled as pending verification. Discussions and proposals must not be presented as completed changes.

Each versioned entry should include its release date and relevant change categories. Move verified entries from `[Unreleased]` into a versioned section (for example, `v0.1.0`) only when that version is formally released or tagged.
