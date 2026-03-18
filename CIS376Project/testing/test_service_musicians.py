from database.connection import get_connection
from database.schema import create_database
from features.users.users_model import create_user
from features.services.services_model import create_service
from features.services.service_musicians_model import (assign_musician, get_musicians_assignment,
                                                       get_musicians_for_service,get_instrument,
                                                       update_musician, delete_musician)

def setup_db():
    db, cursor = get_connection(':memory:')

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

    musician = assign_musician(cursor,1, 1, 'Guitar')
    db.commit()

    assert musician == 1
    row = get_musicians_assignment(cursor, musician)
    assert row[0][2] == 'Guitar'

def test_get_musicians_for_service():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_user(cursor, 'user2', 'user2@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    assign_musician(cursor, 1, 1, 'Guitar')
    assign_musician(cursor, 1, 2, 'Piano')
    db.commit()

    musicians = get_musicians_for_service(cursor, 1)

    assert len(musicians) == 2
    assert musicians[0]['instrument'] == 'Guitar'
    assert musicians[1]['instrument'] == 'Piano'

def test_get_musicians_assignment():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_user(cursor, 'user2', 'user2@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    assign_musician(cursor, 1, 1, 'Guitar')
    assign_musician(cursor, 1, 2, 'Piano')
    db.commit()

    row = get_musicians_assignment(cursor, 2)

    assert row[0][0] == 2  #musicians_id
    assert row[0][1] == 1  #service_id
    assert row[0][2] == 'Piano'  #instrument
    assert row[0][3] == 'Sunday Worship' #service_name
    assert row[0][4] == '2026-03-08'  #service_date

def test_get_instrument():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_user(cursor, 'user2', 'user2@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    assign_musician(cursor, 1, 1, 'Guitar')
    assign_musician(cursor, 1, 2, 'Guitar')
    db.commit()

    rows = get_instrument(cursor, 1, 'Guitar')

    assert rows[0]['user_id'] == 1
    assert rows[1]['user_id'] == 2


def test_update_musician():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    assign_musician(cursor, 1, 1, 'Guitar')
    db.commit()

    musician = update_musician(cursor, 1, 'Piano')
    db.commit()

    assert musician[0][2] == 'Piano'

def test_delete_musician():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    assign_musician(cursor, 1, 1, 'Guitar')
    db.commit()

    delete_musician(cursor, 1)
    db.commit()

    row = get_musicians_assignment(cursor, 1)
    assert row == []

def test_get_no_musicians():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    row = get_musicians_for_service(cursor, 1)

    assert row == []

def test_invalid_musician_id():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    assign_musician(cursor, 1, 1, 'Guitar')
    db.commit()

    row = get_musicians_assignment(cursor, 25)

    assert row == [] #should this be none or []

def test_get_invalid_instrument():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    assign_musician(cursor, 1, 1, 'Guitar')
    db.commit()

    rows = get_instrument(cursor, 1, 'Drums')

    assert rows == []