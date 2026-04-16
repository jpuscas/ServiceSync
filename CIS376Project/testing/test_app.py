import json
import os
import sqlite3
import pytest

import app as app_module
import database.connection as connection_module
import main as main_module
from database.connection import ensure_database_initialized
from database.schema import create_database
from features.invitations.invitations_model import create_invitation, get_invitations_by_user
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


def create_verified_user(db_path, username='user1', org_id='1', role='member'):
    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    user_id = create_user(cursor, username, f'{username}@example.com', 'password', org_id=org_id)
    cursor.execute('UPDATE users SET is_verified = 1, role = ? WHERE id = ?', (role, user_id))
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


def test_leader_can_delete_song_in_active_org(temp_app_db):
    org_name = 'Song Delete Org'
    create_verified_user(temp_app_db, username='leader_song_delete', org_id=json.dumps([org_name]), role='leader')

    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    song_id = create_song(cursor, 'Delete Me', 'Artist', 'C', 90, org_id=org_name)
    db.commit()
    db.close()

    client = app_module.app.test_client()
    response = client.post('/login', data={'username': 'leader_song_delete', 'password': 'password'})
    assert response.status_code == 302

    response = client.post(f'/song/{song_id}/delete')
    assert response.status_code == 302

    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) AS total FROM songs WHERE song_id = ?', (song_id,))
    assert cursor.fetchone()['total'] == 0
    db.close()


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
    monkeypatch.setattr(main_module, 'ensure_database_initialized', lambda: (fake_path, False))

    main_module.initialize_database()

    # The initialize_database path should execute and print the expected status.
    captured = capsys.readouterr()
    assert 'Database created at' in captured.out


def test_ensure_database_initialized_creates_sqlite_file(tmp_path):
    db_path = tmp_path / 'created_by_initializer.db'

    created_path, already_exists = ensure_database_initialized(db_path)

    assert created_path == db_path
    assert not already_exists
    assert db_path.exists()


def test_ensure_database_initialized_copies_legacy_database(monkeypatch, tmp_path):
    legacy_path = tmp_path / 'legacy.db'
    default_path = tmp_path / 'nested' / 'project.db'

    legacy_db = sqlite3.connect(str(legacy_path))
    legacy_cursor = legacy_db.cursor()
    legacy_cursor.execute('CREATE TABLE migrated_table (value TEXT NOT NULL)')
    legacy_cursor.execute("INSERT INTO migrated_table (value) VALUES ('kept-data')")
    legacy_db.commit()
    legacy_db.close()

    monkeypatch.setattr(connection_module, 'DEFAULT_DB_PATH', default_path)
    monkeypatch.setattr(connection_module, 'LEGACY_DB_PATH', legacy_path)

    created_path, already_exists = connection_module.ensure_database_initialized()

    assert created_path == default_path
    assert already_exists

    migrated_db = sqlite3.connect(str(default_path))
    migrated_cursor = migrated_db.cursor()
    migrated_cursor.execute('SELECT value FROM migrated_table')
    assert migrated_cursor.fetchone()[0] == 'kept-data'
    migrated_db.close()


def test_delete_service_with_invitations_succeeds(temp_app_db):
    leader_id = create_verified_user(temp_app_db, username='leader_delete', role='leader')
    invited_user_id = create_verified_user(temp_app_db, username='member_delete')

    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("UPDATE users SET role = 'leader' WHERE id = ?", (leader_id,))
    service_id = create_service(cursor, 'Sunday Worship', 'Worship', '2026-04-11', '09:00', leader_id, org_id='1')
    create_invitation(cursor, service_id, invited_user_id, 'Pending', '2026-04-01', '09:00', org_id='1')
    db.commit()
    db.close()

    client = app_module.app.test_client()
    response = client.post('/login', data={'username': 'leader_delete', 'password': 'password'})
    assert response.status_code == 302

    response = client.post(f'/services/{service_id}/delete')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/services')

    db = sqlite3.connect(str(temp_app_db))
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM services WHERE service_id = ?', (service_id,))
    assert cursor.fetchone()[0] == 0
    cursor.execute('SELECT COUNT(*) FROM invitations WHERE service_id = ?', (service_id,))
    assert cursor.fetchone()[0] == 0
    db.close()


def test_service_page_locks_pending_and_accepted_assignments_for_leaders(temp_app_db):
    leader_id = create_verified_user(temp_app_db, username='leader_locked', role='leader', org_id='org-lock')
    member_id = create_verified_user(temp_app_db, username='member_locked', role='member', org_id='org-lock')

    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    service_id = create_service(cursor, 'Locked Service', 'Worship', '2026-04-18', '09:00', leader_id, org_id='org-lock')
    cursor.execute("INSERT INTO service_musicians (service_id, user_id, instrument, org_id, accepted) VALUES (?, ?, ?, ?, ?)", (service_id, member_id, 'Singer', 'org-lock', None))
    db.commit()
    db.close()

    client = app_module.app.test_client()
    response = client.post('/login', data={'username': 'leader_locked', 'password': 'password'})
    assert response.status_code == 302

    response = client.get(f'/services/{service_id}')
    assert response.status_code == 200
    assert b'const isLockedAssignment = Boolean(assignment.user_id) && Boolean(assignment.musicians_id) && assignment.accepted !== 0;' in response.data


def test_organization_request_accepts_and_adds_user_to_org(temp_app_db):
    org_name = 'Golgotha Romanian Baptist Church'
    create_verified_user(temp_app_db, username='leader_org', org_id=json.dumps([org_name]), role='leader')
    create_verified_user(temp_app_db, username='member_org', org_id='[]')

    client = app_module.app.test_client()
    response = client.post('/login', data={'username': 'leader_org', 'password': 'password'})
    assert response.status_code == 302

    response = client.post('/organization-requests/send', data={'recipient_username': 'member_org'})
    assert response.status_code == 302

    client.post('/logout')
    response = client.post('/login', data={'username': 'member_org', 'password': 'password'})
    assert response.status_code == 302

    response = client.get('/my-requests')
    assert response.status_code == 200
    assert b'Join Organization' in response.data
    assert org_name.encode() in response.data

    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("SELECT request_id FROM organization_requests WHERE org_name = ?", (org_name,))
    request_id = cursor.fetchone()['request_id']
    db.close()

    response = client.post(f'/organization-requests/{request_id}/accept', follow_redirects=True)
    assert response.status_code == 200
    assert org_name.encode() in response.data

    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("SELECT org_id FROM users WHERE username = 'member_org'")
    memberships = json.loads(cursor.fetchone()['org_id'])
    assert org_name in memberships
    db.close()


def test_member_only_sees_assigned_services_in_active_org(temp_app_db):
    org_one = 'Org One'
    org_two = 'Org Two'
    leader_id = create_verified_user(temp_app_db, username='leader_services', org_id=json.dumps([org_one]), role='leader')
    member_id = create_verified_user(temp_app_db, username='member_services', org_id=json.dumps([org_one, org_two]))

    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    service_visible_id = create_service(cursor, 'Visible Service', 'Worship', '2026-04-11', '09:00', leader_id, org_id=org_one)
    service_hidden_same_org_id = create_service(cursor, 'Hidden Same Org', 'Worship', '2026-04-12', '09:00', leader_id, org_id=org_one)
    service_other_org_id = create_service(cursor, 'Hidden Other Org', 'Worship', '2026-04-13', '09:00', leader_id, org_id=org_two)
    cursor.execute("INSERT INTO service_musicians (service_id, user_id, instrument, org_id) VALUES (?, ?, ?, ?)", (service_visible_id, member_id, 'Singer', org_one))
    cursor.execute("INSERT INTO service_musicians (service_id, user_id, instrument, org_id) VALUES (?, ?, ?, ?)", (service_other_org_id, member_id, 'Singer', org_two))
    db.commit()
    db.close()

    client = app_module.app.test_client()
    response = client.post('/login', data={'username': 'member_services', 'password': 'password'})
    assert response.status_code == 302

    with client.session_transaction() as sess:
        sess['org_id'] = org_one

    response = client.get('/services')
    assert response.status_code == 200
    assert b'2026-04-11' in response.data
    assert b'2026-04-12' not in response.data
    assert b'2026-04-13' not in response.data


def test_organization_page_shows_search_and_member_tools(temp_app_db):
    org_name = 'Org Manage'
    create_verified_user(temp_app_db, username='leader_manage', org_id=json.dumps([org_name]), role='leader')
    create_verified_user(temp_app_db, username='member_manage', org_id=json.dumps([org_name]), role='member')
    create_verified_user(temp_app_db, username='outside_manage', org_id='[]', role='member')

    client = app_module.app.test_client()
    response = client.post('/login', data={'username': 'leader_manage', 'password': 'password'})
    assert response.status_code == 302

    response = client.get('/organization-requests')
    assert response.status_code == 200
    assert b'Organization</h1>' in response.data
    assert b'type="search"' in response.data
    assert b'member_manage' in response.data
    assert b'Promote to Leader' in response.data
    assert b'Remove from Organization' in response.data


def test_leader_can_update_org_member_role_and_remove_member(temp_app_db):
    org_name = 'Org Manage'
    create_verified_user(temp_app_db, username='leader_admin', org_id=json.dumps([org_name]), role='leader')
    member_id = create_verified_user(temp_app_db, username='member_admin', org_id=json.dumps([org_name]), role='member')

    client = app_module.app.test_client()
    response = client.post('/login', data={'username': 'leader_admin', 'password': 'password'})
    assert response.status_code == 302

    response = client.post(f'/organization/members/{member_id}/role', data={'role': 'leader'})
    assert response.status_code == 302

    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (member_id,))
    assert cursor.fetchone()['role'] == 'leader'

    response = client.post(f'/organization/members/{member_id}/role', data={'role': 'member'})
    assert response.status_code == 302
    cursor.execute('SELECT role FROM users WHERE id = ?', (member_id,))
    assert cursor.fetchone()['role'] == 'member'

    response = client.post(f'/organization/members/{member_id}/remove')
    assert response.status_code == 302
    cursor.execute('SELECT org_id FROM users WHERE id = ?', (member_id,))
    row = cursor.fetchone()
    memberships = json.loads(row['org_id']) if row and row['org_id'] else []
    db.close()
    assert org_name not in memberships


def test_removed_user_no_longer_sees_org_request(temp_app_db):
    org_name = 'Org Cleanup'
    create_verified_user(temp_app_db, username='leader_cleanup', org_id=json.dumps([org_name]), role='leader')
    create_verified_user(temp_app_db, username='andrew_cleanup', org_id='[]', role='member')

    leader_client = app_module.app.test_client()
    response = leader_client.post('/login', data={'username': 'leader_cleanup', 'password': 'password'})
    assert response.status_code == 302
    response = leader_client.post('/organization-requests/send', data={'recipient_username': 'andrew_cleanup'})
    assert response.status_code == 302

    member_client = app_module.app.test_client()
    response = member_client.post('/login', data={'username': 'andrew_cleanup', 'password': 'password'})
    assert response.status_code == 302

    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("SELECT request_id FROM organization_requests WHERE recipient_id = (SELECT id FROM users WHERE username = 'andrew_cleanup') AND org_name = ?", (org_name,))
    request_id = cursor.fetchone()['request_id']
    db.close()

    response = member_client.post(f'/organization-requests/{request_id}/accept', follow_redirects=True)
    assert response.status_code == 200
    assert org_name.encode() in response.data

    response = leader_client.post('/organization/members/2/remove')
    assert response.status_code == 302

    response = member_client.get('/my-requests')
    assert response.status_code == 200
    assert org_name.encode() not in response.data


def test_removed_service_member_no_longer_sees_request(temp_app_db):
    org_name = 'Service Cleanup'
    leader_id = create_verified_user(temp_app_db, username='leader_service_cleanup', org_id=json.dumps([org_name]), role='leader')
    member_id = create_verified_user(temp_app_db, username='andrew_service_cleanup', org_id=json.dumps([org_name]), role='member')

    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    service_id = create_service(cursor, 'Cleanup Service', 'Worship', '2026-05-01', '09:00', leader_id, org_id=org_name)
    app_module.save_service_relations(cursor, service_id, [{'role': 'Singer', 'user_id': member_id}], [], org_id=org_name, sender_id=leader_id)
    db.commit()
    app_module.save_service_relations(cursor, service_id, [], [], org_id=org_name, sender_id=leader_id)
    db.commit()
    db.close()

    client = app_module.app.test_client()
    response = client.post('/login', data={'username': 'andrew_service_cleanup', 'password': 'password'})
    assert response.status_code == 302

    response = client.get('/my-requests')
    assert response.status_code == 200
    assert b'Cleanup Service' not in response.data
    assert b'2026-05-01' not in response.data


def test_save_service_relations_and_detail(temp_app_db):
    create_verified_user(temp_app_db, username='leader', org_id='org-1')
    db = sqlite3.connect(str(temp_app_db))
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    service_id = create_service(cursor, 'Sunday Worship', 'Worship', '2026-04-11', '09:00', 1, org_id='org-1')
    create_song(cursor, 'Song A', 'Artist A', 'G', 80, org_id='org-1')
    create_song(cursor, 'Song B', 'Artist B', 'D', 90, org_id='org-1')
    db.commit()

    app_module.save_service_relations(cursor, service_id, [{'role': 'Singer', 'user_id': 1}], [1, 2], org_id='org-1', sender_id=1)
    db.commit()

    cursor.execute('SELECT * FROM service_songs WHERE service_id = ?', (service_id,))
    rows = cursor.fetchall()
    assert len(rows) == 2

    invitations = get_invitations_by_user(cursor, 1, 'org-1')
    assert len(invitations) == 1
    assert invitations[0]['invitation_status'] == 'Pending'

    cursor.execute('SELECT * FROM services WHERE service_id = ?', (service_id,))
    service_row = cursor.fetchone()
    detail = app_module.build_service_detail(cursor, service_row, org_id='org-1')
    assert detail['service_id'] == service_id
    assert 'songs' in detail
    db.close()
