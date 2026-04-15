import shutil
import sys
import sqlite3
from pathlib import Path

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / 'project.db'
LEGACY_DB_PATH = Path(__file__).resolve().parents[2] / 'project.db'


def resolve_database_path(database=None):
    return DEFAULT_DB_PATH if database is None else Path(database)


def prepare_database_path(database=None):
    database_path = resolve_database_path(database)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    if database is None and not database_path.exists() and LEGACY_DB_PATH.exists():
        shutil.copy2(LEGACY_DB_PATH, database_path)

    return database_path


def get_connection(database=None):
    database_path = prepare_database_path(database)
    db = sqlite3.connect(str(database_path))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")
    cursor = db.cursor()
    return db, cursor


def ensure_database_initialized(database=None):
    from database.schema import create_database

    database_path = prepare_database_path(database)
    db_already_exists = database_path.exists()

    db, cursor = get_connection(database_path)
    create_database(cursor)
    db.commit()
    db.close()

    return database_path, db_already_exists


if __name__ == '__main__':
    database_path, db_already_exists = ensure_database_initialized()
    if db_already_exists:
        print(f'Database exists at {database_path}. Schema initialized/checked without clearing data.')
    else:
        print(f'Database created at {database_path}.')