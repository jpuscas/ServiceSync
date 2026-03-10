import sqlite3
from database.schema import create_database
from features.services.services_model import create_service, format_service_datetime


def setup_db():
    db = sqlite3.connect(':memory:')
    cursor = db.cursor()

    create_database(cursor)

    db.commit()
    return db, cursor

def test_valid_service():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', '3/8/2026', '9:30', 1)
    db.commit()

    cursor.execute('SELECT * FROM services')
    rows = cursor.fetchall()
    assert len(rows) == 1

def test_format_services_datetime(): #doesn't work properly
    time = format_service_datetime("2026-03-08", "09:30")

    assert time == '3/8/26, 9:30 AM'

def test_get_service_by_id():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', '3/8/2026', '9:30', 1)
    db.commit()