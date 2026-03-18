import sqlite3
import pytest
from database.schema import create_database
from features.services.services_model import (create_service, get_service_by_type, list_services,
    search_service, update_service, delete_service)

def setup_db():
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    create_database(cursor)

    db.commit()
    return db, cursor

def test_valid_service():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:30 AM', 1)
    db.commit()

    cursor.execute('SELECT * FROM services')
    rows = cursor.fetchall()
    assert len(rows) == 1

def test_normalized_input():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-08', '9:30', 1)
    db.commit()

    cursor.execute('''SELECT service_date, service_time FROM services 
           WHERE service_id = ?''', (1,))
    row = cursor.fetchone()

    assert row['service_date'] == '2026-03-08'
    assert row['service_time'] == '09:30'

def test_invalid_date_handling():
    db, cursor = setup_db()

    with pytest.raises(ValueError):
        create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026/03/08', '9:30', 1)

def test_invalid_time_handling():
    db, cursor = setup_db()

    with pytest.raises(ValueError):
        create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-08', '9:99', 1)

def test_get_service_by_type():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-08','09:30', 1)
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-15', '09:30', 1)
    db.commit()

    rows = get_service_by_type(cursor, 'Worship')

    assert len(rows) == 2
    assert rows[0]['service_name'] == 'Sunday Worship'
    assert rows[1]['service_name'] == 'Sunday Worship'

def test_list_services():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-08', '09:30', 1)
    create_service(cursor, 'Youth Group', 'Youth',
                   '2026-03-08', '18:30', 1)
    db.commit()

    rows = list_services(cursor)

    assert len(rows) == 2
    assert rows[0]['service_name'] == 'Sunday Worship'
    assert rows[1]['service_name'] == 'Youth Group'

def test_search_service_by_name():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-08', '09:30', 1)
    db.commit()

    results = search_service(cursor, 'Sunday')

    assert len(results) == 1
    assert results[0]['service_name'] == 'Sunday Worship'

def test_search_service_by_case():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-08', '09:30', 1)
    db.commit()

    results = search_service(cursor, 'sunday')

    assert len(results) == 1
    assert results[0]['service_name'] == 'Sunday Worship'

def test_search_service_not_found():
    db, cursor = setup_db()

    results = search_service(cursor, "Nothing")

    assert len(results) == 0

def test_order_services():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-08', '09:30', 1)
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-15', '09:30', 1)
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-08', '11:30', 2)
    db.commit()

    rows = list_services(cursor)

    assert len(rows) == 3
    assert rows[0][3] == '2026-03-08' and rows[0][4] == '09:30'
    assert rows[1][3] == '2026-03-08' and rows[1][4] == '11:30'
    assert rows[2][3] == '2026-03-15' and rows[2][4] == '09:30'

def test_update_service():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-08', '09:30', 1)
    db.commit()

    update_service(cursor, 1, 'Sunday Worship', 'Worship',
                   '2026-03-08', '10:00', 1)
    db.commit()

    cursor.execute('''SELECT service_name, service_time FROM services 
        WHERE service_id = ?''', (1,))
    rows = cursor.fetchone()

    assert rows['service_time'] == '10:00'

def test_delete_service():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-08', '09:30', 1)
    db.commit()

    delete_service(cursor, 1)
    db.commit()

    deleted_service = get_service_by_type(cursor, 'Worship')

    assert deleted_service == []

def test_delete_nonexistant_service():
    db, cursor = setup_db()
    delete_service(cursor, 1)
    db.commit()

    deleted_service = get_service_by_type(cursor, 'Worship')

    assert deleted_service == []

def test_full_service_test():
    db, cursor = setup_db()

    create_service(cursor, 'Sunday Worship', 'Worship',
                   '2026-03-08', '09:30', 1)
    db.commit()

    services = get_service_by_type(cursor, 'Worship')
    assert len(services) == 1
    assert services[0][1] == 'Sunday Worship'
    assert services[0][3] == '2026-03-08'
    assert services[0][4] == '09:30'

    service_list = list_services(cursor)
    assert len(service_list) == 1
    assert service_list[0][4] == '09:30'

    update_service(cursor, 1, 'Sunday Worship', 'Worship',
                   '2026-03-08', '09:45', 1)
    db.commit()

    new_service = list_services(cursor)
    assert new_service[0][4] == '09:45'

    delete_service(cursor, 1)
    db.commit()

    deleted_service = get_service_by_type(cursor, 'Worship')
    assert deleted_service == []

