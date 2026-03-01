import sqlite3

def get_connection(db_name = 'project.db'):
    db = sqlite3.connect(db_name)
    db.execute("PRAGMA foreign_keys = ON;")
    return db