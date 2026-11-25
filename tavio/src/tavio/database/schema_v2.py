"""Incremental SQLite schema and seed SQL for Migration v2 (TAVIO v1.3.4)."""

from __future__ import annotations

SCHEMA_V2_SQL = """
-- 1. Add nullable relative logo path to school_profile (preserve all existing columns & data)
ALTER TABLE school_profile ADD COLUMN logo_path TEXT;

-- 2. Create school_administrators table
CREATE TABLE school_administrators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_title TEXT NOT NULL CHECK (LENGTH(TRIM(position_title)) > 0),
    administrator_name TEXT NOT NULL CHECK (LENGTH(TRIM(administrator_name)) > 0),
    sort_order INTEGER NOT NULL DEFAULT 1 CHECK (sort_order >= 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- 3. Create schedule_signatory_settings table
CREATE TABLE schedule_signatory_settings (
    schedule_type TEXT PRIMARY KEY CHECK (schedule_type IN ('TEACHER', 'CLASS', 'SPECIAL_ROOM')),
    prepared_by_administrator_id INTEGER,
    verified_by_administrator_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (prepared_by_administrator_id)
        REFERENCES school_administrators(id) ON DELETE RESTRICT,
    FOREIGN KEY (verified_by_administrator_id)
        REFERENCES school_administrators(id) ON DELETE RESTRICT
);
"""

SEED_V2_SQL = """
-- 4. Backfill non-empty school_profile.principal_name as 'Guru Besar' without creating duplicates
INSERT INTO school_administrators (
    position_title,
    administrator_name,
    sort_order,
    is_active
)
SELECT
    'Guru Besar',
    TRIM(sp.principal_name),
    1,
    1
FROM school_profile sp
WHERE sp.principal_name IS NOT NULL
  AND LENGTH(TRIM(sp.principal_name)) > 0
  AND NOT EXISTS (
      SELECT 1
      FROM school_administrators sa
      WHERE TRIM(sa.position_title) = 'Guru Besar' COLLATE NOCASE
        AND TRIM(sa.administrator_name) = TRIM(sp.principal_name) COLLATE NOCASE
  );

-- 5. Seed exact three signatory configuration records starting with NULL administrator references
INSERT OR IGNORE INTO schedule_signatory_settings (
    schedule_type,
    prepared_by_administrator_id,
    verified_by_administrator_id
) VALUES
    ('TEACHER', NULL, NULL),
    ('CLASS', NULL, NULL),
    ('SPECIAL_ROOM', NULL, NULL);
"""

MIGRATION_V2_SQL = f"{SCHEMA_V2_SQL}\n{SEED_V2_SQL}"
