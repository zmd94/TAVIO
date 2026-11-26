# Changelog

All notable code changes to TAVIO are documented in this file.

This project uses version numbers in the format `vMAJOR.MINOR.PATCH`.

## [Unreleased]

The entries below summarize code changes present in the repository's `main` branch that have been implemented and verified. They are not a published or tagged release. No release version is assigned yet.

### Added

- **SQLite database foundation:** Introduced database connection configuration, connection and transaction management, database error handling, and a versioned migration runner using `PRAGMA user_version`.
- **Database schema migrations:** Added the initial core schema (Migration v1), school profile/administrator/schedule-signatory schema updates (Migration v2), and Class Teacher database support (Migration v3).
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

### Fixed

- **School logo upload safety:** Added protection against oversized/decompression-bomb images and strengthened file/database consistency with backup and restoration handling.
- **Single-instance lock handling:** Disabled stale-lock expiry for a valid long-running application instance so it is not incorrectly treated as stale.
- **Packaging paths:** Corrected project-root and branding-asset paths used by the Windows packaging configuration.

### Removed

### Security

- **Image-processing safeguards:** Added decompression-bomb warning protection during school logo processing.

### Verification

- Class Teacher Migration v3 verification: **111/111 automated tests passed**, including **29/29 database tests**; Ruff checks passed.
- The migration tests cover schema version progression to v3, preservation of existing class and timetable data, nullable Class Teacher references, foreign-key enforcement, `ON DELETE RESTRICT`, SQLite integrity checks, and repeat initialization.
- No GitHub Actions workflow runs were found for this repository at the time this changelog was reviewed; the verification above reflects the recorded local test results.

---

## Versioning

- **MAJOR**: Incompatible changes or major milestones that require breaking compatibility.
- **MINOR**: New functionality that remains compatible with the existing system.
- **PATCH**: Bug fixes and small, backward-compatible corrections.

Only code changes that have been successfully implemented and verified through the relevant tests are recorded as completed entries. Discussions, proposals, planned work, and unverified changes must not be presented as completed changes.

Each versioned entry should include its release date and relevant change categories. Move verified entries from `[Unreleased]` into a versioned section (for example, `v0.1.0`) only when that version is formally released or tagged.
