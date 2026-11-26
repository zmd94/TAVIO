"""Incremental SQLite schema SQL for Migration v3 (Guru Kelas)."""

from __future__ import annotations

SCHEMA_V3_SQL = """
-- Add nullable class_teacher_id column referencing teachers(id) with ON DELETE RESTRICT
ALTER TABLE classes
ADD COLUMN class_teacher_id INTEGER
REFERENCES teachers(id) ON DELETE RESTRICT;
"""

MIGRATION_V3_SQL = SCHEMA_V3_SQL
