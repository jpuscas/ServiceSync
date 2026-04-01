import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DEFAULT_DATABASE = os.path.join(BASE_DIR, 'project.db')

def get_connection(database=None):
    if database is None:
        database = DEFAULT_DATABASE

    # Avoid creating directories for in-memory DB or when database path has no directory
    db_dir = os.path.dirname(database)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    db = sqlite3.connect(database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")
    cursor = db.cursor()
    return db, cursor