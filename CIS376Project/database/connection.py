import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / 'project.db'


def get_connection(database=DEFAULT_DB_PATH):
    db = sqlite3.connect(str(database))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")
    cursor = db.cursor()
    return db, cursor