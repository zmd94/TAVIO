"""Database schema migration v4."""

from __future__ import annotations

MIGRATION_V4_SQL = """
DROP TRIGGER trg_twa_base_version_ins;
DROP TRIGGER trg_twa_base_version_upd;

DROP TABLE timetable_workspace_autosaves;

DELETE FROM app_settings
WHERE setting_key = 'autosave_interval_minutes';
"""
