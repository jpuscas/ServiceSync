import sqlite3

def get_connection(database = 'project.db'):
    db = sqlite3.connect(database)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")
    cursor = db.cursor()
    return db, cursor