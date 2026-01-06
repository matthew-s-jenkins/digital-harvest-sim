"""
Digital Harvest - Database Migration Runner

This module handles automatic schema migrations for SQLite database.
Migrations are Python files in the migrations/ folder with a run(conn) function.

Migration files should be named: migration_NNN_description.py

The schema_version table tracks which migrations have been applied.
"""

import sqlite3
from pathlib import Path
import re
import importlib.util


def get_db_path():
    """Return the path to the SQLite database file"""
    return Path(__file__).parent / "data" / "digitalharvest.db"


def get_migrations_path():
    """Return the path to the migrations folder"""
    return Path(__file__).parent / "migrations"


def get_current_version(conn):
    """
    Get the current schema version from the database.

    Returns:
        int: The highest migration version applied, or 0 if no migrations
    """
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0
    except sqlite3.OperationalError:
        # schema_version table doesn't exist yet - create it
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                description TEXT,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        return 0


def get_pending_migrations():
    """
    Get list of migration files that haven't been applied yet.

    Returns:
        list: List of tuples (version, filepath, description)
    """
    migrations_path = get_migrations_path()

    # Create migrations directory if it doesn't exist
    migrations_path.mkdir(parents=True, exist_ok=True)

    # Pattern to match migration files: migration_NNN_description.py
    pattern = re.compile(r'^migration_(\d{3})_(.+)\.py$')

    migrations = []
    if migrations_path.exists():
        for file in sorted(migrations_path.glob('migration_*.py')):
            match = pattern.match(file.name)
            if match:
                version = int(match.group(1))
                description = match.group(2).replace('_', ' ')
                migrations.append((version, file, description))

    return migrations


def apply_migration(conn, version, filepath, description):
    """
    Apply a single Python migration file to the database.

    Args:
        conn: SQLite connection
        version (int): Migration version number
        filepath (Path): Path to the migration Python file
        description (str): Human-readable description

    Returns:
        bool: True if successful, False otherwise
    """
    cursor = conn.cursor()

    try:
        print(f"  Applying migration {version}: {description}...", end=" ")

        # Import the migration module dynamically
        spec = importlib.util.spec_from_file_location(f"migration_{version}", filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Call the run(conn) function
        if hasattr(module, 'run'):
            module.run(conn)
        else:
            print("[ERROR] No run(conn) function found")
            return False

        # Record this migration in schema_version
        cursor.execute("""
            INSERT INTO schema_version (version, description)
            VALUES (?, ?)
        """, (version, description))

        conn.commit()
        print("[OK]")
        return True

    except Exception as e:
        print(f"[ERROR]")
        print(f"    Error: {e}")
        conn.rollback()
        return False


def run_all_pending():
    """
    Run all pending migrations.

    Returns:
        int: Number of migrations applied
    """
    db_path = get_db_path()

    if not db_path.exists():
        # No database yet, nothing to migrate
        return 0

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        current_version = get_current_version(conn)
        all_migrations = get_pending_migrations()

        # Filter to only pending migrations
        pending = [m for m in all_migrations if m[0] > current_version]

        if not pending:
            return 0

        print(f"Found {len(pending)} pending migration(s):")

        applied = 0
        for version, filepath, description in pending:
            if apply_migration(conn, version, filepath, description):
                applied += 1
            else:
                print(f"  [ERROR] Migration {version} failed. Stopping.")
                break

        return applied

    finally:
        conn.close()


def list_migrations():
    """Print a list of all migrations and their status"""
    db_path = get_db_path()

    if not db_path.exists():
        print("Database does not exist yet.")
        return

    conn = sqlite3.connect(str(db_path))
    current_version = get_current_version(conn)
    conn.close()

    all_migrations = get_pending_migrations()

    if not all_migrations:
        print("No migrations found in migrations/")
        return

    print()
    print("Migration Status:")
    print("=" * 60)

    for version, filepath, description in all_migrations:
        status = "[APPLIED]" if version <= current_version else "[PENDING]"
        print(f"{version:03d}. {description:<40} {status}")

    print()
    print(f"Current schema version: {current_version}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_migrations()
    else:
        print("=" * 60)
        print("Digital Harvest - Migration Runner")
        print("=" * 60)
        print()

        applied = run_all_pending()

        if applied > 0:
            print()
            print(f"[OK] Applied {applied} migration(s) successfully!")
        elif applied == 0:
            print("[OK] No pending migrations.")
        else:
            print("[ERROR] Migration failed.")
