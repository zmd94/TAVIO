"""Tests for TAVIO foundational SQLite database infrastructure."""

from __future__ import annotations

import ast
import sqlite3
from pathlib import Path

import pytest

from tavio.config import build_app_paths, ensure_app_directories
from tavio.database import (
    DEFAULT_MIGRATIONS,
    ConnectionConfig,
    DatabaseConnectionError,
    DatabaseManager,
    DatabaseMigrationError,
    DatabaseTransactionError,
    Migration,
    UnsupportedDatabaseVersionError,
    get_connection_pragmas,
    get_schema_version,
    split_sql_statements,
)


def test_initialize_with_empty_migrations_starts_at_version_zero(tmp_path: Path) -> None:
    db_path = tmp_path / "tavio_empty.db"
    manager = DatabaseManager(db_path, migrations=())

    result = manager.initialize()

    assert db_path.is_file()
    assert result.initial_version == 0
    assert result.final_version == 0
    assert result.applied_versions == ()
    assert manager.supported_version == 0
    assert manager.get_schema_version() == 0

    with manager.connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    assert tables == []


def test_initialize_applies_v1_schema_and_seeds(tmp_path: Path) -> None:
    db_path = tmp_path / "tavio_v1.db"
    manager = DatabaseManager(db_path, migrations=(DEFAULT_MIGRATIONS[0],))

    result = manager.initialize()

    assert db_path.is_file()
    assert result.initial_version == 0
    assert result.final_version == 1
    assert result.applied_versions == (1,)
    assert manager.supported_version == 1
    assert manager.get_schema_version() == 1

    with manager.connection() as conn:
        tables = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        custom_indexes = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        triggers = [
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'").fetchall()
        ]
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        autosave_row = conn.execute(
            "SELECT setting_value, value_type FROM app_settings WHERE setting_key = 'autosave_interval_minutes'"
        ).fetchone()
        absence_reasons = conn.execute(
            "SELECT name, is_active FROM absence_reasons ORDER BY id"
        ).fetchall()

    assert len(tables) == 42
    assert len(custom_indexes) == 45
    assert sum(1 for name in custom_indexes if name.startswith("uq_")) == 23
    assert sum(1 for name in custom_indexes if name.startswith("idx_")) == 22
    assert len(triggers) == 64
    assert fk_violations == []
    assert autosave_row is not None
    assert (autosave_row["setting_value"], autosave_row["value_type"]) == ("10", "INTEGER")
    assert len(absence_reasons) >= 5
    assert all(row["is_active"] == 1 for row in absence_reasons)

    second_result = manager.initialize()
    assert second_result.initial_version == 1
    assert second_result.final_version == 1
    assert second_result.applied_versions == ()


def test_initialize_applies_default_migrations_from_zero_to_v4(tmp_path: Path) -> None:
    db_path = tmp_path / "tavio.db"
    manager = DatabaseManager(db_path)

    assert [m.version for m in DEFAULT_MIGRATIONS] == [1, 2, 3, 4]

    result = manager.initialize()

    assert db_path.is_file()
    assert result.initial_version == 0
    assert result.final_version == 4
    assert result.applied_versions == (1, 2, 3, 4)
    assert manager.supported_version == 4
    assert manager.get_schema_version() == 4

    with manager.connection() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        custom_indexes = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        triggers = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'").fetchall()
        }
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        integrity_rows = conn.execute("PRAGMA integrity_check").fetchall()
        school_profile_cols = {
            row["name"]: row for row in conn.execute("PRAGMA table_info(school_profile)").fetchall()
        }
        classes_cols = {
            row["name"]: row for row in conn.execute("PRAGMA table_info(classes)").fetchall()
        }
        classes_fks = conn.execute("PRAGMA foreign_key_list(classes)").fetchall()
        admin_rows = conn.execute("SELECT * FROM school_administrators").fetchall()
        signatory_rows = conn.execute(
            "SELECT schedule_type, prepared_by_administrator_id, verified_by_administrator_id "
            "FROM schedule_signatory_settings ORDER BY schedule_type"
        ).fetchall()
        legacy_setting = conn.execute(
            "SELECT setting_key FROM app_settings WHERE setting_key = 'autosave_interval_minutes'"
        ).fetchone()

    assert len(tables) == 43
    assert {"school_administrators", "schedule_signatory_settings"}.issubset(tables)
    assert "timetable_workspace_autosaves" not in tables
    assert len(custom_indexes) == 45
    assert sum(1 for name in custom_indexes if name.startswith("uq_")) == 23
    assert sum(1 for name in custom_indexes if name.startswith("idx_")) == 22
    assert len(triggers) == 62
    assert "trg_twa_base_version_ins" not in triggers
    assert "trg_twa_base_version_upd" not in triggers
    assert legacy_setting is None
    assert fk_violations == []
    assert [tuple(row) for row in integrity_rows] == [("ok",)]
    assert "logo_path" in school_profile_cols
    assert school_profile_cols["logo_path"]["notnull"] == 0
    assert school_profile_cols["logo_path"]["type"] == "TEXT"
    assert "principal_name" in school_profile_cols
    assert "class_teacher_id" in classes_cols
    assert classes_cols["class_teacher_id"]["type"] == "INTEGER"
    assert classes_cols["class_teacher_id"]["notnull"] == 0
    assert classes_cols["class_teacher_id"]["dflt_value"] is None
    assert any(
        fk["table"] == "teachers"
        and fk["from"] == "class_teacher_id"
        and fk["to"] == "id"
        and fk["on_delete"] == "RESTRICT"
        for fk in classes_fks
    )
    assert admin_rows == []
    assert [(r["schedule_type"], r["prepared_by_administrator_id"], r["verified_by_administrator_id"]) for r in signatory_rows] == [
        ("CLASS", None, None),
        ("SPECIAL_ROOM", None, None),
        ("TEACHER", None, None),
    ]

    second_result = manager.initialize()
    assert second_result.initial_version == 4
    assert second_result.final_version == 4
    assert second_result.applied_versions == ()

    with manager.connection() as conn:
        count_after = conn.execute("SELECT COUNT(*) FROM schedule_signatory_settings").fetchone()[0]
    assert count_after == 3


def test_initialize_integrates_with_app_paths(isolated_tavio_dir: Path) -> None:
    paths = ensure_app_directories(build_app_paths())
    manager = DatabaseManager.from_app_paths(paths)

    result = manager.initialize()

    assert manager.db_path == paths.db_path.resolve()
    assert paths.db_path.is_file()
    assert result.final_version == 4
    assert result.applied_versions == (1, 2, 3, 4)


def test_parent_directories_are_created_automatically(tmp_path: Path) -> None:
    nested_db_path = tmp_path / "nested" / "level1" / "level2" / "tavio.db"
    assert not nested_db_path.parent.exists()

    manager = DatabaseManager(nested_db_path)
    manager.initialize()

    assert nested_db_path.parent.is_dir()
    assert nested_db_path.is_file()


def test_connection_pragmas_configured_on_every_connection(tmp_path: Path) -> None:
    db_path = tmp_path / "pragmas.db"
    manager = DatabaseManager(
        db_path,
        config=ConnectionConfig(
            timeout_seconds=12.0,
            busy_timeout_ms=4500,
            journal_mode="WAL",
            synchronous="NORMAL",
            foreign_keys=True,
        ),
    )
    manager.initialize()

    for _ in range(2):
        with manager.connection() as conn:
            pragmas = get_connection_pragmas(conn)
            assert pragmas["foreign_keys"] == 1
            assert pragmas["busy_timeout"] == 4500
            assert pragmas["journal_mode"] == "wal"
            assert pragmas["synchronous"] == 1

    with manager.transaction() as tx_conn:
        tx_pragmas = get_connection_pragmas(tx_conn)
        assert tx_pragmas["foreign_keys"] == 1
        assert tx_pragmas["busy_timeout"] == 4500
        assert tx_pragmas["journal_mode"] == "wal"
        assert tx_pragmas["synchronous"] == 1


def test_foreign_keys_are_enforced(tmp_path: Path) -> None:
    migrations = (
        Migration(
            version=1,
            description="Create test parent and child tables",
            sql="""
                CREATE TABLE test_parents (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                );
                CREATE TABLE test_children (
                    id INTEGER PRIMARY KEY,
                    parent_id INTEGER NOT NULL REFERENCES test_parents(id) ON DELETE RESTRICT
                );
            """,
        ),
    )
    manager = DatabaseManager(tmp_path / "fk.db", migrations=migrations)
    manager.initialize()

    with pytest.raises(sqlite3.IntegrityError), manager.transaction() as conn:
        conn.execute("INSERT INTO test_children (id, parent_id) VALUES (1, 999)")

    with manager.transaction() as conn:
        conn.execute("INSERT INTO test_parents (id, name) VALUES (10, 'Alpha')")
        conn.execute("INSERT INTO test_children (id, parent_id) VALUES (1, 10)")

    with pytest.raises(sqlite3.IntegrityError), manager.transaction() as conn:
        conn.execute("DELETE FROM test_parents WHERE id = 10")


def test_wal_mode_persists_and_supports_concurrent_reader(tmp_path: Path) -> None:
    db_path = tmp_path / "wal.db"
    migrations = (
        Migration(
            version=1,
            description="Create WAL test table",
            sql="CREATE TABLE items (id INTEGER PRIMARY KEY, label TEXT NOT NULL);",
        ),
    )
    manager = DatabaseManager(db_path, migrations=migrations)
    manager.initialize()

    with manager.transaction() as writer_conn:
        writer_conn.execute("INSERT INTO items (id, label) VALUES (1, 'uncommitted')")
        wal_sidecar = Path(f"{db_path}-wal")
        assert wal_sidecar.exists()

        # Separate reader connection sees committed snapshot without blocking.
        with manager.connection() as reader_conn:
            assert reader_conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
            rows = reader_conn.execute("SELECT id, label FROM items").fetchall()
            assert rows == []

    with manager.connection() as reader_conn:
        rows = reader_conn.execute("SELECT id, label FROM items").fetchall()
        assert [(row["id"], row["label"]) for row in rows] == [(1, "uncommitted")]


def test_transaction_commit_persists_changes(tmp_path: Path) -> None:
    migrations = (
        Migration(
            version=1,
            description="Create notes table",
            sql="CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT NOT NULL);",
        ),
    )
    manager = DatabaseManager(tmp_path / "commit.db", migrations=migrations)
    manager.initialize()

    with manager.transaction(immediate=True) as conn:
        conn.execute("INSERT INTO notes (id, body) VALUES (1, 'saved')")

    with manager.connection() as conn:
        row = conn.execute("SELECT body FROM notes WHERE id = 1").fetchone()
        assert row is not None
        assert row["body"] == "saved"


def test_transaction_rolls_back_on_exception_and_rejects_nesting(tmp_path: Path) -> None:
    migrations = (
        Migration(
            version=1,
            description="Create notes table",
            sql="CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT NOT NULL);",
        ),
    )
    manager = DatabaseManager(tmp_path / "rollback.db", migrations=migrations)
    manager.initialize()

    with manager.transaction() as conn:
        conn.execute("INSERT INTO notes (id, body) VALUES (1, 'initial')")

    with pytest.raises(RuntimeError, match="abort"), manager.transaction() as conn:
        conn.execute("INSERT INTO notes (id, body) VALUES (2, 'should-rollback')")
        raise RuntimeError("abort")

    with manager.connection() as conn:
        rows = conn.execute("SELECT id, body FROM notes ORDER BY id").fetchall()
        assert [(r["id"], r["body"]) for r in rows] == [(1, "initial")]

    with manager.transaction(), pytest.raises(
        DatabaseTransactionError, match="Nested transactions are not supported"
    ), manager.transaction():
        pass


def test_migrations_apply_incrementally_and_track_user_version(tmp_path: Path) -> None:
    db_path = tmp_path / "migrations.db"
    v1_migrations = (
        Migration(
            version=1,
            description="Create audit_items table",
            sql="""
                -- Initial test table
                CREATE TABLE audit_items (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                );
                CREATE TABLE audit_events (
                    id INTEGER PRIMARY KEY,
                    item_id INTEGER NOT NULL
                );
                CREATE TRIGGER trg_audit_insert AFTER INSERT ON audit_items
                BEGIN
                    INSERT INTO audit_events (item_id) VALUES (NEW.id);
                END;
                -- Trailing comment
            """,
        ),
    )
    manager_v1 = DatabaseManager(db_path, migrations=v1_migrations)
    res_v1 = manager_v1.initialize()

    assert res_v1.initial_version == 0
    assert res_v1.final_version == 1
    assert res_v1.applied_versions == (1,)
    assert manager_v1.get_schema_version() == 1

    def add_column_and_seed(conn: sqlite3.Connection) -> None:
        conn.execute("ALTER TABLE audit_items ADD COLUMN note TEXT NOT NULL DEFAULT ''")
        conn.execute("INSERT INTO audit_items (id, name, note) VALUES (1, 'Seed', 'v2')")

    v3_migrations = (
        *v1_migrations,
        Migration(
            version=2,
            description="Add note column and seed record",
            up=add_column_and_seed,
        ),
        Migration(
            version=3,
            description="Add index on audit_items name",
            sql="CREATE INDEX idx_audit_items_name ON audit_items(name)",
        ),
    )
    manager_v3 = DatabaseManager(db_path, migrations=v3_migrations)
    res_v3 = manager_v3.initialize()

    assert res_v3.initial_version == 1
    assert res_v3.final_version == 3
    assert res_v3.applied_versions == (2, 3)
    assert manager_v3.get_schema_version() == 3

    with manager_v3.connection() as conn:
        item = conn.execute("SELECT name, note FROM audit_items WHERE id = 1").fetchone()
        events = conn.execute("SELECT item_id FROM audit_events").fetchall()
        assert item is not None
        assert (item["name"], item["note"]) == ("Seed", "v2")
        assert [e["item_id"] for e in events] == [1]


def test_repeated_initialization_is_idempotent(tmp_path: Path) -> None:
    migrations = (
        Migration(
            version=1,
            description="Create settings table",
            sql="CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT NOT NULL);",
        ),
    )
    manager = DatabaseManager(tmp_path / "idempotent.db", migrations=migrations)

    first = manager.initialize()
    with manager.transaction() as conn:
        conn.execute("INSERT INTO kv (k, v) VALUES ('mode', 'desktop')")

    second = manager.initialize()
    third = manager.initialize()

    assert first.applied_versions == (1,)
    assert second.initial_version == 1
    assert second.final_version == 1
    assert second.applied_versions == ()
    assert third.applied_versions == ()

    with manager.connection() as conn:
        row = conn.execute("SELECT v FROM kv WHERE k = 'mode'").fetchone()
        assert row is not None
        assert row["v"] == "desktop"


def test_unsupported_future_version_raises_without_downgrade(tmp_path: Path) -> None:
    db_path = tmp_path / "future.db"
    manager = DatabaseManager(db_path)
    manager.initialize()

    with manager.connection() as conn:
        conn.execute("PRAGMA user_version = 999")

    with pytest.raises(UnsupportedDatabaseVersionError, match="999"):
        manager.initialize()

    assert manager.get_schema_version() == 999

    with manager.connection() as conn:
        conn.execute("PRAGMA user_version = -1")

    with pytest.raises(UnsupportedDatabaseVersionError, match="-1"):
        manager.initialize()


def test_connections_are_closed_after_normal_and_error_exits(tmp_path: Path) -> None:
    manager = DatabaseManager(tmp_path / "cleanup.db")
    manager.initialize()

    with manager.connection() as conn:
        assert get_schema_version(conn) == 4

    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        conn.execute("SELECT 1")

    with pytest.raises(ValueError, match="trigger"), manager.connection() as err_conn:
        assert get_schema_version(err_conn) == 4
        raise ValueError("trigger")

    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        err_conn.execute("SELECT 1")

    with manager.transaction() as tx_conn:
        assert tx_conn.in_transaction

    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        tx_conn.execute("SELECT 1")

    with pytest.raises(RuntimeError, match="tx-fail"), manager.transaction() as err_tx_conn:
        assert err_tx_conn.in_transaction
        raise RuntimeError("tx-fail")

    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        err_tx_conn.execute("SELECT 1")


def test_error_handling_for_invalid_paths_configs_and_failed_migrations(tmp_path: Path) -> None:
    directory_path = tmp_path / "is_a_directory"
    directory_path.mkdir()

    with pytest.raises(DatabaseConnectionError):
        DatabaseManager(directory_path).initialize()

    with pytest.raises(DatabaseConnectionError):
        DatabaseManager(":memory:").initialize()

    with pytest.raises(DatabaseConnectionError):
        DatabaseManager("   ").initialize()

    blocking_file = tmp_path / "file_not_dir"
    blocking_file.write_text("occupied", encoding="utf-8")
    with pytest.raises(DatabaseConnectionError):
        DatabaseManager(blocking_file / "tavio.db").initialize()

    with pytest.raises(ValueError):
        ConnectionConfig(timeout_seconds=0)

    with pytest.raises(ValueError):
        ConnectionConfig(journal_mode="INVALID_MODE")

    with pytest.raises(DatabaseMigrationError, match="contiguous"):
        DatabaseManager(
            tmp_path / "gap.db",
            migrations=(
                Migration(version=1, description="v1", sql="CREATE TABLE a (id INT);"),
                Migration(version=3, description="v3", sql="CREATE TABLE b (id INT);"),
            ),
        )

    failing_migrations = (
        Migration(version=1, description="valid v1", sql="CREATE TABLE ok_table (id INT);"),
        Migration(
            version=2,
            description="broken v2",
            sql="""
                CREATE TABLE partial_table (id INT);
                INSERT INTO nonexistent_table (id) VALUES (1);
            """,
        ),
    )
    failing_db = tmp_path / "failed_migration.db"
    failing_manager = DatabaseManager(failing_db, migrations=failing_migrations)

    with pytest.raises(DatabaseMigrationError, match="v2"):
        failing_manager.initialize()

    assert failing_manager.get_schema_version() == 1
    with failing_manager.connection() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert "ok_table" in tables
    assert "partial_table" not in tables


def test_split_sql_statements_handles_same_line_triggers_comments_and_literals() -> None:
    script = """
        -- Leading comment with semicolon; ignored
        CREATE TABLE sample_a (id INTEGER PRIMARY KEY, label TEXT DEFAULT 'x;y''z;w'); CREATE TABLE sample_b ("col;1" INTEGER, [col;2] TEXT);
        /* Block comment with ; and CREATE TABLE fake; */
        CREATE TRIGGER trg_one AFTER INSERT ON sample_a
        BEGIN
            INSERT INTO sample_b ("col;1", [col;2])
            VALUES (NEW.id, CASE WHEN NEW.id > 0 THEN 'ok;done' ELSE 'zero;end' END);
        END;CREATE TRIGGER trg_two AFTER DELETE ON sample_a
        BEGIN
            DELETE FROM sample_b WHERE "col;1" = OLD.id;
        END;
        -- Trailing comment without semicolon;
    """
    statements = split_sql_statements(script)
    assert len(statements) == 4
    assert statements[0].startswith("CREATE TABLE sample_a")
    assert statements[1].startswith("CREATE TABLE sample_b")
    assert statements[2].startswith("CREATE TRIGGER trg_one")
    assert statements[2].endswith("END;")
    assert statements[3].startswith("CREATE TRIGGER trg_two")
    assert statements[3].endswith("END;")

    conn = sqlite3.connect(":memory:")
    try:
        for stmt in statements:
            conn.execute(stmt)
        conn.execute("INSERT INTO sample_a (id) VALUES (1)")
        row = conn.execute('SELECT "col;1", [col;2] FROM sample_b').fetchone()
        assert row == (1, "ok;done")
    finally:
        conn.close()

    with pytest.raises(DatabaseMigrationError, match="Unterminated"):
        split_sql_statements("SELECT 'unterminated;")
    with pytest.raises(DatabaseMigrationError, match="Unterminated"):
        split_sql_statements("/* unterminated block comment")
    with pytest.raises(DatabaseMigrationError, match="Unterminated"):
        split_sql_statements("SELECT [unterminated")
    with pytest.raises(DatabaseMigrationError, match="Incomplete"):
        split_sql_statements("CREATE TRIGGER broken BEFORE INSERT ON t BEGIN SELECT 1;")


def test_failed_v1_migration_rolls_back_completely(tmp_path: Path) -> None:
    broken_v1 = (
        Migration(
            version=1,
            description="Partially broken v1",
            sql="""
                CREATE TABLE partial_one (id INTEGER PRIMARY KEY);
                INSERT INTO missing_table (id) VALUES (1);
            """,
        ),
    )
    manager = DatabaseManager(tmp_path / "broken_v1.db", migrations=broken_v1)

    with pytest.raises(DatabaseMigrationError, match="v1"):
        manager.initialize()

    assert manager.get_schema_version() == 0
    with manager.connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    assert tables == []


def test_relief_teacher_id_composite_fk_enforces_same_year_and_session(tmp_path: Path) -> None:
    manager = DatabaseManager(tmp_path / "relief_fk.db")
    manager.initialize()

    with manager.transaction() as conn:
        conn.execute(
            "INSERT INTO academic_years (id, year_code, name, start_date, end_date) "
            "VALUES (1, '2026', 'Tahun 2026', '2026-01-01', '2026-12-31')"
        )
        conn.execute(
            "INSERT INTO school_sessions (id, academic_year_id, session_code, name, sort_order) "
            "VALUES (1, 1, 'PAGI', 'Sesi Pagi', 1), (2, 1, 'PETANG', 'Sesi Petang', 2)"
        )
        conn.execute(
            "INSERT INTO education_levels (id, academic_year_id, session_id, level_code, name, sort_order) "
            "VALUES (1, 1, 1, 'T1', 'Tingkatan 1', 1)"
        )
        conn.execute(
            "INSERT INTO classes (id, academic_year_id, session_id, education_level_id, short_name, name) "
            "VALUES (1, 1, 1, 1, '1A', '1 Amanah')"
        )
        conn.execute(
            "INSERT INTO subjects (id, short_name, name) VALUES (1, 'BM', 'Bahasa Melayu')"
        )
        conn.execute(
            "INSERT INTO teachers (id, short_name, full_name) VALUES "
            "(1, 'Cikgu A', 'Ali bin Abu'), "
            "(2, 'Cikgu B', 'Bakar bin Omar'), "
            "(3, 'Cikgu C', 'Chong Wei'), "
            "(4, 'Cikgu D', 'Daud bin Idris')"
        )
        # Teacher 1 & 2 in session 1 (PAGI); Teacher 3 in session 2 (PETANG); Teacher 4 unregistered.
        conn.execute(
            "INSERT INTO teacher_sessions (academic_year_id, teacher_id, session_id) VALUES "
            "(1, 1, 1), (1, 2, 1), (1, 3, 2)"
        )
        conn.execute(
            "INSERT INTO absence_reasons (id, name) VALUES (100, 'Ujian Khas')"
        )
        conn.execute(
            "INSERT INTO teacher_absences (id, academic_year_id, session_id, teacher_id, absence_reason_id, absence_date) "
            "VALUES (1, 1, 1, 1, 100, '2026-03-09')"
        )
        conn.execute(
            "INSERT INTO timetable_versions (id, academic_year_id, session_id, version_number, version_name) "
            "VALUES (1, 1, 1, 1, 'V1')"
        )
        conn.execute(
            "INSERT INTO timetable_lessons (id, timetable_version_id, academic_year_id, session_id, subject_id, assignment_type, lessons_per_week, periods_per_lesson) "
            "VALUES (1, 1, 1, 1, 1, 'SINGLE', 1, 1), "
            "(2, 1, 1, 1, 1, 'SINGLE', 1, 1), "
            "(3, 1, 1, 1, 1, 'SINGLE', 1, 1)"
        )
        conn.execute(
            "INSERT INTO timetable_entries (id, timetable_version_id, timetable_lesson_id, day_of_week, start_minute, end_minute) "
            "VALUES (1, 1, 1, 1, 480, 510), "
            "(2, 1, 2, 1, 510, 540), "
            "(3, 1, 3, 1, 540, 570)"
        )
        conn.execute(
            "INSERT INTO relief_batches (id, academic_year_id, session_id, timetable_version_id, relief_date) "
            "VALUES (1, 1, 1, 1, '2026-03-09')"
        )
        # Valid relief teacher in same academic year & session (including conflict override).
        conn.execute(
            """
            INSERT INTO relief_assignments (
                relief_batch_id, academic_year_id, session_id, timetable_version_id,
                teacher_absence_id, relief_date, absent_teacher_id, relief_teacher_id,
                timetable_lesson_id, timetable_entry_id, subject_id, day_of_week,
                start_minute, end_minute, status, is_conflict_overridden, override_conflicts_json,
                absent_teacher_short_name_snapshot, absent_teacher_name_snapshot,
                relief_teacher_short_name_snapshot, relief_teacher_name_snapshot,
                subject_short_name_snapshot, subject_name_snapshot, target_classes_snapshot_json
            ) VALUES (
                1, 1, 1, 1, 1, '2026-03-09', 1, 2, 1, 1, 1, 1, 480, 510,
                'ASSIGNED', 1, '["TEACHER_BUSY"]',
                'Cikgu A', 'Ali bin Abu', 'Cikgu B', 'Bakar bin Omar',
                'BM', 'Bahasa Melayu', '["1A"]'
            )
            """
        )
        # NULL relief_teacher_id is allowed for UNRESOLVED records.
        conn.execute(
            """
            INSERT INTO relief_assignments (
                relief_batch_id, academic_year_id, session_id, timetable_version_id,
                teacher_absence_id, relief_date, absent_teacher_id, relief_teacher_id,
                timetable_lesson_id, timetable_entry_id, subject_id, day_of_week,
                start_minute, end_minute, status, is_conflict_overridden, override_conflicts_json,
                absent_teacher_short_name_snapshot, absent_teacher_name_snapshot,
                relief_teacher_short_name_snapshot, relief_teacher_name_snapshot,
                subject_short_name_snapshot, subject_name_snapshot, target_classes_snapshot_json
            ) VALUES (
                1, 1, 1, 1, 1, '2026-03-09', 1, NULL, 2, 2, 1, 1, 510, 540,
                'UNRESOLVED', 0, NULL,
                'Cikgu A', 'Ali bin Abu', NULL, NULL,
                'BM', 'Bahasa Melayu', '["1A"]'
            )
            """
        )

    # Teacher 3 registered in session 2 (different session) must be rejected.
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"), manager.transaction() as conn:
        conn.execute(
            """
            INSERT INTO relief_assignments (
                relief_batch_id, academic_year_id, session_id, timetable_version_id,
                teacher_absence_id, relief_date, absent_teacher_id, relief_teacher_id,
                timetable_lesson_id, timetable_entry_id, subject_id, day_of_week,
                start_minute, end_minute, status, is_conflict_overridden, override_conflicts_json,
                absent_teacher_short_name_snapshot, absent_teacher_name_snapshot,
                relief_teacher_short_name_snapshot, relief_teacher_name_snapshot,
                subject_short_name_snapshot, subject_name_snapshot, target_classes_snapshot_json
            ) VALUES (
                1, 1, 1, 1, 1, '2026-03-09', 1, 3, 3, 3, 1, 1, 540, 570,
                'ASSIGNED', 0, NULL,
                'Cikgu A', 'Ali bin Abu', 'Cikgu C', 'Chong Wei',
                'BM', 'Bahasa Melayu', '["1A"]'
            )
            """
        )

    # Teacher 4 unregistered in teacher_sessions for academic_year 1 must be rejected.
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"), manager.transaction() as conn:
        conn.execute(
            """
            INSERT INTO relief_assignments (
                relief_batch_id, academic_year_id, session_id, timetable_version_id,
                teacher_absence_id, relief_date, absent_teacher_id, relief_teacher_id,
                timetable_lesson_id, timetable_entry_id, subject_id, day_of_week,
                start_minute, end_minute, status, is_conflict_overridden, override_conflicts_json,
                absent_teacher_short_name_snapshot, absent_teacher_name_snapshot,
                relief_teacher_short_name_snapshot, relief_teacher_name_snapshot,
                subject_short_name_snapshot, subject_name_snapshot, target_classes_snapshot_json
            ) VALUES (
                1, 1, 1, 1, 1, '2026-03-09', 1, 4, 3, 3, 1, 1, 540, 570,
                'ASSIGNED', 0, NULL,
                'Cikgu A', 'Ali bin Abu', 'Cikgu D', 'Daud bin Idris',
                'BM', 'Bahasa Melayu', '["1A"]'
            )
            """
        )

    # ON DELETE RESTRICT prevents removing teacher_sessions referenced by relief_teacher_id.
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"), manager.transaction() as conn:
        conn.execute(
            "DELETE FROM teacher_sessions WHERE academic_year_id = 1 AND teacher_id = 2 AND session_id = 1"
        )


def test_v1_to_v2_upgrade_preserves_data_and_backfills_principal_name(tmp_path: Path) -> None:
    db_path = tmp_path / "upgrade_v1_to_v2.db"
    v1_manager = DatabaseManager(db_path, migrations=(DEFAULT_MIGRATIONS[0],))
    v1_manager.initialize()

    with v1_manager.transaction() as conn:
        conn.execute(
            """
            INSERT INTO school_profile (
                id, school_name, school_code, school_week_group,
                address, phone, email, principal_name
            ) VALUES (
                1, 'SK Seri Melati', 'BBA1001', 'B',
                'Jalan Melati 1', '03-12345678', 'bba1001@moe.edu.my', 'Puan Aminah binti Ahmad'
            )
            """
        )
        conn.execute(
            "INSERT INTO academic_years (id, year_code, name, start_date, end_date) "
            "VALUES (1, '2026', 'Tahun 2026', '2026-01-01', '2026-12-31')"
        )
        conn.execute(
            "INSERT INTO school_sessions (id, academic_year_id, session_code, name, sort_order) "
            "VALUES (1, 1, 'PAGI', 'Sesi Pagi', 1)"
        )
        conn.execute(
            "INSERT INTO teachers (id, short_name, full_name) VALUES (1, 'CIKGU A', 'Ahmad bin Ali')"
        )

    v2_manager = DatabaseManager(db_path, migrations=DEFAULT_MIGRATIONS[:2])
    upgrade_result = v2_manager.initialize()

    assert upgrade_result.initial_version == 1
    assert upgrade_result.final_version == 2
    assert upgrade_result.applied_versions == (2,)
    assert v2_manager.get_schema_version() == 2

    with v2_manager.connection() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        custom_indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        triggers = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger'"
        ).fetchall()
        assert len(tables) == 44
        assert len(custom_indexes) == 45
        assert len(triggers) == 64
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

        profile = conn.execute("SELECT * FROM school_profile WHERE id = 1").fetchone()
        assert profile is not None
        assert profile["school_name"] == "SK Seri Melati"
        assert profile["school_code"] == "BBA1001"
        assert profile["school_week_group"] == "B"
        assert profile["address"] == "Jalan Melati 1"
        assert profile["phone"] == "03-12345678"
        assert profile["email"] == "bba1001@moe.edu.my"
        assert profile["principal_name"] == "Puan Aminah binti Ahmad"
        assert profile["logo_path"] is None

        year_row = conn.execute("SELECT year_code, name FROM academic_years WHERE id = 1").fetchone()
        teacher_row = conn.execute("SELECT short_name, full_name FROM teachers WHERE id = 1").fetchone()
        assert (year_row["year_code"], year_row["name"]) == ("2026", "Tahun 2026")
        assert (teacher_row["short_name"], teacher_row["full_name"]) == ("CIKGU A", "Ahmad bin Ali")

        admins = conn.execute(
            "SELECT position_title, administrator_name, sort_order, is_active FROM school_administrators"
        ).fetchall()
        assert len(admins) == 1
        assert (
            admins[0]["position_title"],
            admins[0]["administrator_name"],
            admins[0]["sort_order"],
            admins[0]["is_active"],
        ) == ("Guru Besar", "Puan Aminah binti Ahmad", 1, 1)

        signatories = conn.execute(
            "SELECT schedule_type, prepared_by_administrator_id, verified_by_administrator_id "
            "FROM schedule_signatory_settings ORDER BY schedule_type"
        ).fetchall()
        assert [
            (r["schedule_type"], r["prepared_by_administrator_id"], r["verified_by_administrator_id"])
            for r in signatories
        ] == [
            ("CLASS", None, None),
            ("SPECIAL_ROOM", None, None),
            ("TEACHER", None, None),
        ]

    # Repeated initialization must remain idempotent with zero duplicate backfill or seed records.
    repeat_result = v2_manager.initialize()
    assert repeat_result.applied_versions == ()
    with v2_manager.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM school_administrators").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM schedule_signatory_settings").fetchone()[0] == 3

        # Verify logo_path can hold a relative path and revert back to NULL cleanly.
        conn.execute("UPDATE school_profile SET logo_path = 'assets/school_logo.png' WHERE id = 1")
        assert (
            conn.execute("SELECT logo_path FROM school_profile WHERE id = 1").fetchone()["logo_path"]
            == "assets/school_logo.png"
        )
        conn.execute("UPDATE school_profile SET logo_path = NULL WHERE id = 1")
        assert conn.execute("SELECT logo_path FROM school_profile WHERE id = 1").fetchone()["logo_path"] is None


@pytest.mark.parametrize("blank_principal", [None, "", "   "])
def test_v2_migration_skips_backfill_when_principal_name_empty_or_null(
    tmp_path: Path,
    blank_principal: str | None,
) -> None:
    db_path = tmp_path / "blank_principal.db"
    v1_manager = DatabaseManager(db_path, migrations=(DEFAULT_MIGRATIONS[0],))
    v1_manager.initialize()

    with v1_manager.transaction() as conn:
        conn.execute(
            "INSERT INTO school_profile (id, school_name, school_code, principal_name) "
            "VALUES (1, 'SK Kosong', 'BBA0001', ?)",
            (blank_principal,),
        )

    v2_manager = DatabaseManager(db_path, migrations=DEFAULT_MIGRATIONS[:2])
    result = v2_manager.initialize()
    assert result.applied_versions == (2,)

    with v2_manager.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM school_administrators").fetchone()[0] == 0
        assert (
            conn.execute("SELECT principal_name FROM school_profile WHERE id = 1").fetchone()[
                "principal_name"
            ]
            == blank_principal
        )
        assert conn.execute("SELECT COUNT(*) FROM schedule_signatory_settings").fetchone()[0] == 3


def test_v2_backfill_seed_sql_does_not_create_duplicate_administrators(tmp_path: Path) -> None:
    from tavio.database.schema_v2 import SEED_V2_SQL

    db_path = tmp_path / "no_dup_backfill.db"
    manager = DatabaseManager(db_path)
    manager.initialize()

    with manager.transaction() as conn:
        conn.execute(
            "INSERT INTO school_profile (id, school_name, school_code, principal_name) "
            "VALUES (1, 'SK Uji', 'BBA2002', 'Encik Razak bin Hassan')"
        )
        for statement in split_sql_statements(SEED_V2_SQL):
            conn.execute(statement)
        # Running SEED_V2_SQL a second time must not duplicate either administrators or signatory rows.
        for statement in split_sql_statements(SEED_V2_SQL):
            conn.execute(statement)

        admins = conn.execute(
            "SELECT position_title, administrator_name FROM school_administrators"
        ).fetchall()
        signatories_count = conn.execute(
            "SELECT COUNT(*) FROM schedule_signatory_settings"
        ).fetchone()[0]

    assert len(admins) == 1
    assert (admins[0]["position_title"], admins[0]["administrator_name"]) == (
        "Guru Besar",
        "Encik Razak bin Hassan",
    )
    assert signatories_count == 3


def test_v2_signatory_foreign_keys_and_on_delete_restrict(tmp_path: Path) -> None:
    db_path = tmp_path / "signatory_fk.db"
    manager = DatabaseManager(db_path)
    manager.initialize()

    with manager.transaction() as conn:
        conn.execute(
            "INSERT INTO school_administrators (id, position_title, administrator_name, sort_order) "
            "VALUES (1, 'Guru Besar', 'Encik Ahmad', 1), "
            "(2, 'GPK Pentadbiran', 'Puan Salmah', 2), "
            "(3, 'GPK HEM', 'Encik Lim', 3)"
        )
        # Same administrator allowed as both prepared_by and verified_by.
        conn.execute(
            "UPDATE schedule_signatory_settings "
            "SET prepared_by_administrator_id = 1, verified_by_administrator_id = 1 "
            "WHERE schedule_type = 'TEACHER'"
        )
        # Distinct administrators allowed for prepared_by and verified_by.
        conn.execute(
            "UPDATE schedule_signatory_settings "
            "SET prepared_by_administrator_id = 2, verified_by_administrator_id = 3 "
            "WHERE schedule_type = 'CLASS'"
        )
        # SPECIAL_ROOM uses administrator 3 as prepared_by only.
        conn.execute(
            "UPDATE schedule_signatory_settings "
            "SET prepared_by_administrator_id = 3, verified_by_administrator_id = NULL "
            "WHERE schedule_type = 'SPECIAL_ROOM'"
        )

    # Invalid administrator references must be rejected for both columns.
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"), manager.transaction() as conn:
        conn.execute(
            "UPDATE schedule_signatory_settings SET prepared_by_administrator_id = 999 "
            "WHERE schedule_type = 'TEACHER'"
        )

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"), manager.transaction() as conn:
        conn.execute(
            "UPDATE schedule_signatory_settings SET verified_by_administrator_id = 999 "
            "WHERE schedule_type = 'TEACHER'"
        )

    # Invalid schedule_type and empty administrator fields must be rejected by CHECK constraints.
    with pytest.raises(sqlite3.IntegrityError), manager.transaction() as conn:
        conn.execute(
            "INSERT INTO schedule_signatory_settings (schedule_type) VALUES ('INVALID')"
        )
    with pytest.raises(sqlite3.IntegrityError), manager.transaction() as conn:
        conn.execute(
            "INSERT INTO school_administrators (position_title, administrator_name) VALUES ('   ', 'Nama')"
        )
    with pytest.raises(sqlite3.IntegrityError), manager.transaction() as conn:
        conn.execute(
            "INSERT INTO school_administrators (position_title, administrator_name) VALUES ('PK', '   ')"
        )

    # ON DELETE RESTRICT blocks deleting administrator referenced by prepared_by_administrator_id (id=2).
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"), manager.transaction() as conn:
        conn.execute("DELETE FROM school_administrators WHERE id = 2")

    # ON DELETE RESTRICT blocks deleting administrator referenced by verified_by_administrator_id (id=3 via CLASS).
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"), manager.transaction() as conn:
        conn.execute("DELETE FROM school_administrators WHERE id = 3")

    # Clearing references from schedule_signatory_settings allows deletion; FK integrity holds.
    with manager.transaction() as conn:
        conn.execute(
            "UPDATE schedule_signatory_settings "
            "SET prepared_by_administrator_id = NULL, verified_by_administrator_id = NULL "
            "WHERE schedule_type = 'CLASS'"
        )
        conn.execute("DELETE FROM school_administrators WHERE id = 2")
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_failed_v2_migration_rolls_back_all_v2_changes_and_preserves_v1(tmp_path: Path) -> None:
    from tavio.database.schema_v2 import MIGRATION_V2_SQL

    db_path = tmp_path / "failed_v2.db"
    v1_manager = DatabaseManager(db_path, migrations=(DEFAULT_MIGRATIONS[0],))
    v1_manager.initialize()

    with v1_manager.transaction() as conn:
        conn.execute(
            "INSERT INTO school_profile (id, school_name, school_code, principal_name) "
            "VALUES (1, 'SK Kekal', 'BBA3003', 'Puan Rosnah')"
        )

    broken_v2_migrations = (
        DEFAULT_MIGRATIONS[0],
        Migration(
            version=2,
            description="Broken v2 after DDL and backfill",
            sql=f"{MIGRATION_V2_SQL}\nINSERT INTO non_existent_v2_table (id) VALUES (1);",
        ),
    )
    failing_v2_manager = DatabaseManager(db_path, migrations=broken_v2_migrations)

    with pytest.raises(DatabaseMigrationError, match="v2"):
        failing_v2_manager.initialize()

    assert failing_v2_manager.get_schema_version() == 1
    with failing_v2_manager.connection() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        profile_cols = {row["name"] for row in conn.execute("PRAGMA table_info(school_profile)").fetchall()}
        profile = conn.execute("SELECT school_name, principal_name FROM school_profile WHERE id = 1").fetchone()
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()

    assert len(tables) == 42
    assert "school_administrators" not in tables
    assert "schedule_signatory_settings" not in tables
    assert "logo_path" not in profile_cols
    assert profile is not None
    assert (profile["school_name"], profile["principal_name"]) == ("SK Kekal", "Puan Rosnah")
    assert fk_violations == []


def test_v2_to_v3_upgrade_preserves_data_and_leaves_class_teacher_id_null(tmp_path: Path) -> None:
    db_path = tmp_path / "upgrade_v2_to_v3.db"
    v2_manager = DatabaseManager(db_path, migrations=DEFAULT_MIGRATIONS[:2])
    v2_init = v2_manager.initialize()
    assert v2_init.final_version == 2

    with v2_manager.transaction() as conn:
        conn.execute(
            "INSERT INTO academic_years (id, year_code, name, start_date, end_date) "
            "VALUES (1, '2026', 'Tahun 2026', '2026-01-01', '2026-12-31')"
        )
        conn.execute(
            "INSERT INTO school_sessions (id, academic_year_id, session_code, name, sort_order) "
            "VALUES (1, 1, 'PAGI', 'Sesi Pagi', 1)"
        )
        conn.execute(
            "INSERT INTO education_levels (id, academic_year_id, session_id, level_code, name, sort_order) "
            "VALUES (1, 1, 1, 'T1', 'Tingkatan 1', 1)"
        )
        conn.execute(
            "INSERT INTO rooms (id, short_name, name, room_type, capacity) "
            "VALUES (1, 'B101', 'Bilik 101', 'REGULAR', 35)"
        )
        conn.execute(
            "INSERT INTO classes ("
            "    id, academic_year_id, session_id, education_level_id, short_name, name, "
            "    student_count, home_room_id, is_active"
            ") VALUES "
            "(1, 1, 1, 1, '1A', '1 Amanah', 32, 1, 1), "
            "(2, 1, 1, 1, '1B', '1 Bestari', 28, NULL, 0)"
        )
        conn.execute(
            "INSERT INTO teachers (id, short_name, full_name) VALUES "
            "(1, 'CG A', 'Ahmad bin Ali'), "
            "(2, 'CG B', 'Siti binti Hassan')"
        )
        conn.execute(
            "INSERT INTO subjects (id, short_name, name) VALUES (1, 'BM', 'Bahasa Melayu')"
        )
        conn.execute(
            "INSERT INTO timetable_versions (id, academic_year_id, session_id, version_number, version_name) "
            "VALUES (1, 1, 1, 1, 'Jadual Induk 2026')"
        )
        conn.execute(
            "INSERT INTO timetable_lessons ("
            "    id, timetable_version_id, academic_year_id, session_id, subject_id, "
            "    assignment_type, lessons_per_week, periods_per_lesson"
            ") VALUES (1, 1, 1, 1, 1, 'SINGLE', 1, 1)"
        )
        conn.execute(
            "INSERT INTO timetable_lesson_targets ("
            "    id, timetable_version_id, timetable_lesson_id, academic_year_id, session_id, class_id"
            ") VALUES (1, 1, 1, 1, 1, 1)"
        )
        conn.execute(
            "INSERT INTO timetable_lesson_teachers ("
            "    id, timetable_version_id, timetable_lesson_id, academic_year_id, session_id, teacher_id, is_lead"
            ") VALUES (1, 1, 1, 1, 1, 1, 1)"
        )
        conn.execute(
            "INSERT INTO timetable_entries ("
            "    id, timetable_version_id, timetable_lesson_id, day_of_week, start_minute, end_minute"
            ") VALUES (1, 1, 1, 1, 480, 510)"
        )

    v3_manager = DatabaseManager(db_path, migrations=DEFAULT_MIGRATIONS[:3])
    upgrade_result = v3_manager.initialize()

    assert upgrade_result.initial_version == 2
    assert upgrade_result.final_version == 3
    assert upgrade_result.applied_versions == (3,)
    assert v3_manager.get_schema_version() == 3

    with v3_manager.connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        custom_indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        triggers = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger'"
        ).fetchall()
        classes_cols = {
            row["name"]: row for row in conn.execute("PRAGMA table_info(classes)").fetchall()
        }
        classes_rows = conn.execute(
            "SELECT id, academic_year_id, session_id, education_level_id, short_name, name, "
            "student_count, home_room_id, is_active, class_teacher_id "
            "FROM classes ORDER BY id"
        ).fetchall()
        teacher_rows = conn.execute(
            "SELECT id, short_name, full_name FROM teachers ORDER BY id"
        ).fetchall()
        version_row = conn.execute(
            "SELECT version_name FROM timetable_versions WHERE id = 1"
        ).fetchone()
        entry_row = conn.execute(
            "SELECT timetable_lesson_id, day_of_week, start_minute, end_minute "
            "FROM timetable_entries WHERE id = 1"
        ).fetchone()
        target_row = conn.execute(
            "SELECT class_id FROM timetable_lesson_targets WHERE id = 1"
        ).fetchone()
        lesson_teacher_row = conn.execute(
            "SELECT teacher_id FROM timetable_lesson_teachers WHERE id = 1"
        ).fetchone()
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        integrity_rows = conn.execute("PRAGMA integrity_check").fetchall()

    assert len(tables) == 44
    assert len(custom_indexes) == 45
    assert len(triggers) == 64
    assert "class_teacher_id" in classes_cols
    assert classes_cols["class_teacher_id"]["notnull"] == 0
    assert [
        (
            r["id"],
            r["academic_year_id"],
            r["session_id"],
            r["education_level_id"],
            r["short_name"],
            r["name"],
            r["student_count"],
            r["home_room_id"],
            r["is_active"],
            r["class_teacher_id"],
        )
        for r in classes_rows
    ] == [
        (1, 1, 1, 1, "1A", "1 Amanah", 32, 1, 1, None),
        (2, 1, 1, 1, "1B", "1 Bestari", 28, None, 0, None),
    ]
    assert [(r["id"], r["short_name"], r["full_name"]) for r in teacher_rows] == [
        (1, "CG A", "Ahmad bin Ali"),
        (2, "CG B", "Siti binti Hassan"),
    ]
    assert version_row is not None
    assert version_row["version_name"] == "Jadual Induk 2026"
    assert entry_row is not None
    assert (
        entry_row["timetable_lesson_id"],
        entry_row["day_of_week"],
        entry_row["start_minute"],
        entry_row["end_minute"],
    ) == (1, 1, 480, 510)
    assert target_row is not None and target_row["class_id"] == 1
    assert lesson_teacher_row is not None and lesson_teacher_row["teacher_id"] == 1
    assert fk_violations == []
    assert [tuple(row) for row in integrity_rows] == [("ok",)]

    # Re-running initialize() on v3 must be a no-op.
    repeat_result = v3_manager.initialize()
    assert repeat_result.initial_version == 3
    assert repeat_result.final_version == 3
    assert repeat_result.applied_versions == ()


def test_v3_classes_class_teacher_id_foreign_key_and_on_delete_restrict(tmp_path: Path) -> None:
    db_path = tmp_path / "classes_fk_v3.db"
    manager = DatabaseManager(db_path)
    manager.initialize()

    with manager.transaction() as conn:
        conn.execute(
            "INSERT INTO academic_years (id, year_code, name, start_date, end_date) "
            "VALUES (1, '2026', 'Tahun 2026', '2026-01-01', '2026-12-31')"
        )
        conn.execute(
            "INSERT INTO school_sessions (id, academic_year_id, session_code, name, sort_order) "
            "VALUES (1, 1, 'PAGI', 'Sesi Pagi', 1)"
        )
        conn.execute(
            "INSERT INTO education_levels (id, academic_year_id, session_id, level_code, name, sort_order) "
            "VALUES (1, 1, 1, 'T1', 'Tingkatan 1', 1)"
        )
        conn.execute(
            "INSERT INTO teachers (id, short_name, full_name) VALUES "
            "(1, 'CG A', 'Ahmad bin Ali'), "
            "(2, 'CG B', 'Siti binti Hassan')"
        )
        # NULL class_teacher_id is permitted.
        conn.execute(
            "INSERT INTO classes (id, academic_year_id, session_id, education_level_id, short_name, name, class_teacher_id) "
            "VALUES (1, 1, 1, 1, '1A', '1 Amanah', NULL)"
        )
        # Valid teacher reference is permitted.
        conn.execute(
            "INSERT INTO classes (id, academic_year_id, session_id, education_level_id, short_name, name, class_teacher_id) "
            "VALUES (2, 1, 1, 1, '1B', '1 Bestari', 1)"
        )
        # Updating to another valid teacher succeeds.
        conn.execute("UPDATE classes SET class_teacher_id = 2 WHERE id = 1")

    # Invalid teacher reference on INSERT or UPDATE must be rejected.
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"), manager.transaction() as conn:
        conn.execute(
            "INSERT INTO classes (id, academic_year_id, session_id, education_level_id, short_name, name, class_teacher_id) "
            "VALUES (3, 1, 1, 1, '1C', '1 Cekal', 999)"
        )

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"), manager.transaction() as conn:
        conn.execute("UPDATE classes SET class_teacher_id = 999 WHERE id = 1")

    # ON DELETE RESTRICT blocks deleting a teacher still referenced as Guru Kelas.
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"), manager.transaction() as conn:
        conn.execute("DELETE FROM teachers WHERE id = 2")

    # Clearing class_teacher_id back to NULL allows deleting the teacher cleanly.
    with manager.transaction() as conn:
        conn.execute("UPDATE classes SET class_teacher_id = NULL WHERE id = 1")
        conn.execute("DELETE FROM teachers WHERE id = 2")
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert [tuple(r) for r in conn.execute("PRAGMA integrity_check").fetchall()] == [("ok",)]


def test_failed_v3_migration_rolls_back_and_preserves_v2(tmp_path: Path) -> None:
    from tavio.database.schema_v3 import MIGRATION_V3_SQL

    db_path = tmp_path / "failed_v3.db"
    v2_manager = DatabaseManager(db_path, migrations=DEFAULT_MIGRATIONS[:2])
    v2_manager.initialize()

    with v2_manager.transaction() as conn:
        conn.execute(
            "INSERT INTO academic_years (id, year_code, name, start_date, end_date) "
            "VALUES (1, '2026', 'Tahun 2026', '2026-01-01', '2026-12-31')"
        )
        conn.execute(
            "INSERT INTO school_sessions (id, academic_year_id, session_code, name, sort_order) "
            "VALUES (1, 1, 'PAGI', 'Sesi Pagi', 1)"
        )
        conn.execute(
            "INSERT INTO education_levels (id, academic_year_id, session_id, level_code, name, sort_order) "
            "VALUES (1, 1, 1, 'T1', 'Tingkatan 1', 1)"
        )
        conn.execute(
            "INSERT INTO classes (id, academic_year_id, session_id, education_level_id, short_name, name) "
            "VALUES (1, 1, 1, 1, '1A', '1 Amanah')"
        )

    broken_v3_migrations = (
        *DEFAULT_MIGRATIONS[:2],
        Migration(
            version=3,
            description="Broken v3 after ALTER TABLE classes",
            sql=f"{MIGRATION_V3_SQL}\nINSERT INTO non_existent_v3_table (id) VALUES (1);",
        ),
    )
    failing_v3_manager = DatabaseManager(db_path, migrations=broken_v3_migrations)

    with pytest.raises(DatabaseMigrationError, match="v3"):
        failing_v3_manager.initialize()

    assert failing_v3_manager.get_schema_version() == 2
    with failing_v3_manager.connection() as conn:
        class_cols = {row["name"] for row in conn.execute("PRAGMA table_info(classes)").fetchall()}
        class_row = conn.execute("SELECT short_name, name FROM classes WHERE id = 1").fetchone()
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        integrity_rows = conn.execute("PRAGMA integrity_check").fetchall()

    assert "class_teacher_id" not in class_cols
    assert class_row is not None
    assert (class_row["short_name"], class_row["name"]) == ("1A", "1 Amanah")
    assert fk_violations == []
    assert [tuple(r) for r in integrity_rows] == [("ok",)]


def test_v3_to_v4_upgrade_drops_legacy_autosave_and_preserves_data(tmp_path: Path) -> None:
    db_path = tmp_path / "upgrade_v3_to_v4.db"
    v3_manager = DatabaseManager(db_path, migrations=DEFAULT_MIGRATIONS[:3])
    v3_init = v3_manager.initialize()
    assert v3_init.final_version == 3

    with v3_manager.transaction() as conn:
        pre_tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        pre_triggers = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'").fetchall()
        }
        assert "timetable_workspace_autosaves" in pre_tables
        assert {"trg_twa_base_version_ins", "trg_twa_base_version_upd"}.issubset(pre_triggers)
        assert (
            conn.execute(
                "SELECT setting_value FROM app_settings WHERE setting_key = 'autosave_interval_minutes'"
            ).fetchone()["setting_value"]
            == "10"
        )

        conn.execute(
            "INSERT INTO app_settings (setting_key, setting_value, value_type, description) "
            "VALUES ('signatory_label_language', 'bm', 'STRING', 'Signatory label language')"
        )
        conn.execute(
            "INSERT INTO school_profile (id, school_name, school_code, school_week_group) "
            "VALUES (1, 'SK Seri Mawar', 'BBA4004', 'A')"
        )
        conn.execute(
            "INSERT INTO academic_years (id, year_code, name, start_date, end_date) "
            "VALUES (1, '2026', 'Tahun 2026', '2026-01-01', '2026-12-31')"
        )
        conn.execute(
            "INSERT INTO school_sessions (id, academic_year_id, session_code, name, sort_order) "
            "VALUES (1, 1, 'PAGI', 'Sesi Pagi', 1)"
        )
        conn.execute(
            "INSERT INTO education_levels (id, academic_year_id, session_id, level_code, name, sort_order) "
            "VALUES (1, 1, 1, 'T1', 'Tingkatan 1', 1)"
        )
        conn.execute(
            "INSERT INTO rooms (id, short_name, name, room_type, capacity) "
            "VALUES (1, 'MK1', 'Makmal Komputer 1', 'SPECIAL', 40)"
        )
        conn.execute(
            "INSERT INTO subjects (id, short_name, name) VALUES (1, 'BM', 'Bahasa Melayu')"
        )
        conn.execute(
            "INSERT INTO teachers (id, short_name, full_name) "
            "VALUES (1, 'CG A', 'Ahmad bin Ali')"
        )
        conn.execute(
            "INSERT INTO classes ("
            "    id, academic_year_id, session_id, education_level_id, short_name, name, class_teacher_id"
            ") VALUES (1, 1, 1, 1, '1A', '1 Amanah', 1)"
        )
        conn.execute(
            "INSERT INTO timetable_versions (id, academic_year_id, session_id, version_number, version_name) "
            "VALUES (1, 1, 1, 1, 'Jadual V1')"
        )
        conn.execute(
            "INSERT INTO timetable_lessons ("
            "    id, timetable_version_id, academic_year_id, session_id, subject_id, "
            "    assignment_type, lessons_per_week, periods_per_lesson"
            ") VALUES (1, 1, 1, 1, 1, 'SINGLE', 1, 1)"
        )
        conn.execute(
            "INSERT INTO timetable_lesson_targets ("
            "    id, timetable_version_id, timetable_lesson_id, academic_year_id, session_id, class_id"
            ") VALUES (1, 1, 1, 1, 1, 1)"
        )
        conn.execute(
            "INSERT INTO timetable_lesson_teachers ("
            "    id, timetable_version_id, timetable_lesson_id, academic_year_id, session_id, teacher_id, is_lead"
            ") VALUES (1, 1, 1, 1, 1, 1, 1)"
        )
        conn.execute(
            "INSERT INTO timetable_entries ("
            "    id, timetable_version_id, timetable_lesson_id, day_of_week, start_minute, end_minute"
            ") VALUES (1, 1, 1, 1, 480, 510)"
        )
        conn.execute(
            "INSERT INTO timetable_workspace_autosaves ("
            "    id, academic_year_id, session_id, base_timetable_version_id, payload_json"
            ") VALUES (1, 1, 1, 1, '{\"legacy\": true}')"
        )

    v4_manager = DatabaseManager(db_path)
    upgrade_result = v4_manager.initialize()

    assert upgrade_result.initial_version == 3
    assert upgrade_result.final_version == 4
    assert upgrade_result.applied_versions == (4,)
    assert v4_manager.get_schema_version() == 4

    with v4_manager.connection() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        custom_indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        triggers = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'").fetchall()
        }
        app_settings_rows = {
            row["setting_key"]: row["setting_value"]
            for row in conn.execute("SELECT setting_key, setting_value FROM app_settings").fetchall()
        }
        school_row = conn.execute(
            "SELECT school_name, school_code, school_week_group FROM school_profile WHERE id = 1"
        ).fetchone()
        room_row = conn.execute(
            "SELECT short_name, name, room_type FROM rooms WHERE id = 1"
        ).fetchone()
        subject_row = conn.execute(
            "SELECT short_name, name FROM subjects WHERE id = 1"
        ).fetchone()
        teacher_row = conn.execute(
            "SELECT short_name, full_name FROM teachers WHERE id = 1"
        ).fetchone()
        class_row = conn.execute(
            "SELECT short_name, name, class_teacher_id FROM classes WHERE id = 1"
        ).fetchone()
        version_row = conn.execute(
            "SELECT version_name FROM timetable_versions WHERE id = 1"
        ).fetchone()
        entry_row = conn.execute(
            "SELECT timetable_lesson_id, day_of_week, start_minute, end_minute "
            "FROM timetable_entries WHERE id = 1"
        ).fetchone()
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        integrity_rows = conn.execute("PRAGMA integrity_check").fetchall()

    assert len(tables) == 43
    assert len(custom_indexes) == 45
    assert len(triggers) == 62
    assert "timetable_workspace_autosaves" not in tables
    assert "trg_twa_base_version_ins" not in triggers
    assert "trg_twa_base_version_upd" not in triggers
    assert "autosave_interval_minutes" not in app_settings_rows
    assert app_settings_rows == {"signatory_label_language": "bm"}
    assert school_row is not None
    assert (school_row["school_name"], school_row["school_code"], school_row["school_week_group"]) == (
        "SK Seri Mawar",
        "BBA4004",
        "A",
    )
    assert room_row is not None
    assert (room_row["short_name"], room_row["name"], room_row["room_type"]) == (
        "MK1",
        "Makmal Komputer 1",
        "SPECIAL",
    )
    assert subject_row is not None
    assert (subject_row["short_name"], subject_row["name"]) == ("BM", "Bahasa Melayu")
    assert teacher_row is not None
    assert (teacher_row["short_name"], teacher_row["full_name"]) == ("CG A", "Ahmad bin Ali")
    assert class_row is not None
    assert (class_row["short_name"], class_row["name"], class_row["class_teacher_id"]) == (
        "1A",
        "1 Amanah",
        1,
    )
    assert version_row is not None and version_row["version_name"] == "Jadual V1"
    assert entry_row is not None
    assert (
        entry_row["timetable_lesson_id"],
        entry_row["day_of_week"],
        entry_row["start_minute"],
        entry_row["end_minute"],
    ) == (1, 1, 480, 510)
    assert fk_violations == []
    assert [tuple(row) for row in integrity_rows] == [("ok",)]

    # Re-running initialize() on v4 must not re-apply any migration.
    repeat_result = v4_manager.initialize()
    assert repeat_result.initial_version == 4
    assert repeat_result.final_version == 4
    assert repeat_result.applied_versions == ()


def test_failed_v4_migration_rolls_back_and_preserves_v3(tmp_path: Path) -> None:
    from tavio.database.schema_v4 import MIGRATION_V4_SQL

    db_path = tmp_path / "failed_v4.db"
    v3_manager = DatabaseManager(db_path, migrations=DEFAULT_MIGRATIONS[:3])
    v3_manager.initialize()

    with v3_manager.transaction() as conn:
        conn.execute(
            "INSERT INTO app_settings (setting_key, setting_value, value_type, description) "
            "VALUES ('signatory_label_language', 'en', 'STRING', 'Signatory label language')"
        )
        conn.execute(
            "INSERT INTO academic_years (id, year_code, name, start_date, end_date) "
            "VALUES (1, '2026', 'Tahun 2026', '2026-01-01', '2026-12-31')"
        )
        conn.execute(
            "INSERT INTO school_sessions (id, academic_year_id, session_code, name, sort_order) "
            "VALUES (1, 1, 'PAGI', 'Sesi Pagi', 1)"
        )
        conn.execute(
            "INSERT INTO timetable_versions (id, academic_year_id, session_id, version_number, version_name) "
            "VALUES (1, 1, 1, 1, 'Jadual Kekal')"
        )
        conn.execute(
            "INSERT INTO timetable_workspace_autosaves ("
            "    id, academic_year_id, session_id, base_timetable_version_id, payload_json"
            ") VALUES (1, 1, 1, 1, '{\"keep\": true}')"
        )

    broken_v4_migrations = (
        *DEFAULT_MIGRATIONS[:3],
        Migration(
            version=4,
            description="Broken v4 after dropping legacy autosave objects",
            sql=f"{MIGRATION_V4_SQL}\nINSERT INTO non_existent_v4_table (id) VALUES (1);",
        ),
    )
    failing_v4_manager = DatabaseManager(db_path, migrations=broken_v4_migrations)

    with pytest.raises(DatabaseMigrationError, match="v4"):
        failing_v4_manager.initialize()

    assert failing_v4_manager.get_schema_version() == 3
    with failing_v4_manager.connection() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        triggers = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'").fetchall()
        }
        app_settings_rows = {
            row["setting_key"]: row["setting_value"]
            for row in conn.execute("SELECT setting_key, setting_value FROM app_settings").fetchall()
        }
        autosave_row = conn.execute(
            "SELECT payload_json FROM timetable_workspace_autosaves WHERE id = 1"
        ).fetchone()
        version_row = conn.execute(
            "SELECT version_name FROM timetable_versions WHERE id = 1"
        ).fetchone()
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        integrity_rows = conn.execute("PRAGMA integrity_check").fetchall()

    assert len(tables) == 44
    assert len(triggers) == 64
    assert "timetable_workspace_autosaves" in tables
    assert {"trg_twa_base_version_ins", "trg_twa_base_version_upd"}.issubset(triggers)
    assert app_settings_rows == {
        "autosave_interval_minutes": "10",
        "signatory_label_language": "en",
    }
    assert autosave_row is not None and autosave_row["payload_json"] == '{"keep": true}'
    assert version_row is not None and version_row["version_name"] == "Jadual Kekal"
    assert fk_violations == []
    assert [tuple(r) for r in integrity_rows] == [("ok",)]


def test_v4_migration_fails_explicitly_when_legacy_objects_missing(tmp_path: Path) -> None:
    db_path = tmp_path / "missing_legacy_v4.db"
    v3_manager = DatabaseManager(db_path, migrations=DEFAULT_MIGRATIONS[:3])
    v3_manager.initialize()

    with v3_manager.transaction() as conn:
        conn.execute("DROP TRIGGER trg_twa_base_version_ins")
        conn.execute("DROP TRIGGER trg_twa_base_version_upd")
        conn.execute("DROP TABLE timetable_workspace_autosaves")

    v4_manager = DatabaseManager(db_path)
    with pytest.raises(DatabaseMigrationError, match="v4"):
        v4_manager.initialize()

    assert v4_manager.get_schema_version() == 3
    with v4_manager.connection() as conn:
        assert (
            conn.execute(
                "SELECT setting_value FROM app_settings WHERE setting_key = 'autosave_interval_minutes'"
            ).fetchone()["setting_value"]
            == "10"
        )


def test_database_package_has_no_ui_or_pyside_dependencies() -> None:
    db_dir = Path(__file__).resolve().parents[1] / "src" / "tavio" / "database"
    py_files = sorted(db_dir.glob("*.py"))
    assert len(py_files) >= 6

    for py_file in py_files:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("PySide6"), py_file.name
                    assert not alias.name.startswith("tavio.ui"), py_file.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("PySide6"), py_file.name
                assert not node.module.startswith("tavio.ui"), py_file.name
