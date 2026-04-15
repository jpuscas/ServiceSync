import json
import os
import sqlite3
import pytest

import app as app_module
import main as main_module
from database.schema import create_database
from features.users.users_model import create_user
from features.services.services_model import create_service
from features.songs.songs_model import create_song


@pytest.fixture(autouse=True)
def temp_app_db(monkeypatch, tmp_path):
    db_path = tmp_path / 'app_test.db'

    def get_connection(database=None):
        database = db_path if database is None else database
        db = sqlite3.connect(str(database))
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON;')
        return db, db.cursor()

    monkeypatch.setattr(app_module, 'get_connection', get_connection)
    db, cursor = get_connection()
    create_database(cursor)
    db.commit()
    db.close()

    return db_path


def create_verified_user(db_path, username='user1', org_id='1'):
    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    user_id = create_user(cursor, username, f'{username}@example.com', 'password', org_id=org_id)
    cursor.execute('UPDATE users SET is_verified = 1 WHERE id = ?', (user_id,))
    db.commit()
    db.close()
    return user_id


def test_parse_service_payload_and_helpers():
    payload = app_module.parse_service_payload({
        'service_date': '2026-04-11',
        'service_time': '10:30',
        'leader_id': '2',
        'role_assignments': json.dumps([{'role': 'Singer', 'user_id': '4'}, {'role': '', 'user_id': '5'}]),
        'song_ids': json.dumps([1, '2', '', None]),
    })

    assert payload['service_name'] == 'Worship Service'
    assert payload['service_type'] == 'Worship'
    assert payload['leader_id'] == 2
    assert payload['song_ids'] == [1, 2]
    assert payload['assignments'] == [{'role': 'Singer', 'user_id': 4}]

    assert app_module.normalize_song_ids([{'song_id': '3'}, 4, '', None]) == [3, 4]
    assert app_module.get_selected_songs_by_ids(
        [{'song_id': 1, 'title': 'A'}, {'song_id': 2, 'title': 'B'}],
        [2, 3],
    ) == [{'song_id': 2, 'title': 'B'}]
    assert app_module.parse_json_list('not json') == []
    assert app_module.parse_json_list(json.dumps([1, 2])) == [1, 2]


def test_parse_service_payload_requires_date():
    with pytest.raises(ValueError):
        app_module.parse_service_payload({'service_time': '09:00'})


def test_is_leader_helper():
    assert app_module.is_leader({'role': 'leader'})
    assert not app_module.is_leader({'role': 'member'})
    with app_module.app.test_request_context():
        assert not app_module.is_leader(None)


def test_build_service_detail_returns_none_for_missing_row():
    assert app_module.build_service_detail(None, None) is None


def test_load_service_page_context_returns_empty_lists(temp_app_db):
    users, songs, services, selected_service = app_module.load_service_page_context(org_id='org-1')
    assert users == []
    assert songs == []
    assert services == []
    assert selected_service is None


def test_login_and_logout_routes(temp_app_db):
    create_verified_user(temp_app_db)

    client = app_module.app.test_client()
    response = client.post('/login', data={'username': 'user1', 'password': 'password'})
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')

    response = client.get('/songs')
    assert response.status_code == 200
    assert b'Songs' in response.data or b'<html' in response.data

    response = client.post('/logout')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login')


def test_login_route_returns_401_for_bad_password(temp_app_db):
    create_verified_user(temp_app_db)
    client = app_module.app.test_client()
    response = client.post('/login', data={'username': 'user1', 'password': 'wrong'})
    assert response.status_code == 401
    assert b'Invalid username and/or password.' in response.data


def test_register_and_verify_routes(temp_app_db):
    client = app_module.app.test_client()

    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'secret',
        'first_name': 'New',
        'last_name': 'User',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/verify')

    with client.session_transaction() as sess:
        token = sess.get('verification_token')
    assert token is not None

    response = client.post('/verify', data={'token': 'invalid-token'})
    assert response.status_code == 200
    assert b'Invalid verification token' in response.data


def test_main_initialize_database_creates_file(monkeypatch, tmp_path, capsys):
    fake_path = tmp_path / 'dbfile.db'
    monkeypatch.setattr(main_module.os.path, 'exists', lambda path: False)

    def fake_get_connection(database=None):
        assert database is None or str(database) == str(fake_path)
        db = sqlite3.connect(str(fake_path))
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON;')
        return db, db.cursor()

    monkeypatch.setattr(main_module, 'get_connection', fake_get_connection)
    monkeypatch.setattr(main_module, 'DEFAULT_DB_PATH', fake_path)

    main_module.initialize_database()

    # The initialize_database path should execute and print the expected status.
    captured = capsys.readouterr()
    assert 'Database created at' in captured.out


def test_save_service_relations_and_detail(temp_app_db):
    create_verified_user(temp_app_db, username='leader', org_id='org-1')
    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    service_id = create_service(cursor, 'Sunday Worship', 'Worship', '2026-04-11', '09:00', 1, org_id='org-1')
    create_song(cursor, 'Song A', 'Artist A', 'G', 80, org_id='org-1')
    create_song(cursor, 'Song B', 'Artist B', 'D', 90, org_id='org-1')
    db.commit()

    app_module.save_service_relations(cursor, service_id, [{'role': 'Singer', 'user_id': 1}], [1, 2], org_id='org-1')
    db.commit()

    cursor.execute('SELECT * FROM service_songs WHERE service_id = ?', (service_id,))
    rows = cursor.fetchall()
    assert len(rows) == 2

    cursor.execute('SELECT * FROM services WHERE service_id = ?', (service_id,))
    service_row = cursor.fetchone()
    detail = app_module.build_service_detail(cursor, service_row, org_id='org-1')
    assert detail['service_id'] == service_id
    assert 'songs' in detail
    db.close()
