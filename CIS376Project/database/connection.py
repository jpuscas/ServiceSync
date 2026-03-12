import sqlite3

def get_connection():
    db = sqlite3.connect('project.db')
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")
    return db