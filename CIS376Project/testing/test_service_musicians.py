import sqlite3
from database.schema import create_database
from features.users.users_model import create_user
from features.services.services_model import create_service
from features.services.service_musicians_model import (assign_musician, get_musicians_assignment,
                                                       get_musicians_for_service,get_instrument,
                                                       update_musician, delete_musician)

def setup_db():
    db = sqlite3.connect(':memory:')
    cursor = db.cursor()

    create_database(cursor)

    db.commit()
    return db, cursor

def test_valid_musician():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_user(cursor, 'user2', 'user2@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    musician = assign_musician(cursor,1, 1, "Guitar")
    db.commit()

    assert musician == 1
