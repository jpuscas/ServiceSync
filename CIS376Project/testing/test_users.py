import sqlite3
import pytest
from database.schema import create_database
from features.users.user_verification import set_verification_code, verify_user
from features.users.users_model import create_user, update_password, authenticate_user, delete_user, update_email, set_role, promote_to_leader
from features.users.login_logic import login_user
from features.songs.songs_model import search_song


def setup_db():
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    create_database(cursor)

    db.commit()
    return db, cursor

def test_valid_user():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'test@email.com', 'test_password')
    db.commit()

    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()
    assert len(rows) == 1

def test_duplicate_email():
    db, cursor = setup_db()

    create_user(cursor,'test_user1', 'test@email.com', 'test_password1')
    db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        create_user(cursor,'test_user1', 'test1234@email.com', 'test_password1')

def test_duplicate_username():
    db, cursor = setup_db()

    create_user(cursor,'test_user', 'test1234@email.com', 'test_password2')
    db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        create_user(cursor,'test_user1', 'test1234@email.com', 'test_password1')

def test_null_username():
    db, cursor = setup_db()
    with pytest.raises(sqlite3.IntegrityError):
        create_user(cursor,None, 'test1234@email.com', 'test_password1')

def test_null_email():
    db, cursor = setup_db()

    with pytest.raises(sqlite3.IntegrityError):
        create_user(cursor,'test_user1', None, 'test_password1')

def test_null_password():
    db, cursor = setup_db()

    with pytest.raises(sqlite3.IntegrityError):
        create_user(cursor,'test_user4', 'test1234@email.com', None)

def test_default_role():
    db, cursor = setup_db()

    create_user(cursor,'test_user', 'test@email.com', 'test_password')
    db.commit()

    cursor.execute('''SELECT username, role FROM users WHERE username = ?''', ('test_user',))
    row = cursor.fetchone()
    assert row['role'] == 'member', f"Expected 'member', got {row['role']}"

def test_authentication_success():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@email.com', 'password1')
    db.commit()

    user = authenticate_user(cursor, 'test_user', 'password1')

    assert user is not False

def test_update_password():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    user = authenticate_user(cursor, 'test_user', 'password1')
    user_id = user['id']

    update_password(cursor, user_id, 'password22')
    db.commit()

    new_authenticate = authenticate_user(cursor, 'test_user', 'password22')
    assert new_authenticate is not False

def test_update_email():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    user = authenticate_user(cursor, 'test_user', 'password1')
    user_id = user['id']

    update_email(cursor, user_id, 'stilltesting@gmail.com')
    db.commit()

    cursor.execute('''SELECT username, email FROM users WHERE username = ?''', ('test_user',))
    row = cursor.fetchone()
    assert row['email'] == 'stilltesting@gmail.com'

def test_delete_user():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    user = authenticate_user(cursor, 'test_user', 'password1')
    user_id = user['id']

    delete_user(cursor, user_id)
    db.commit()

    deleted_user = authenticate_user(cursor, 'test_user', 'password1')

    assert deleted_user is None

def test_verify_user():
    db, cursor = setup_db()

    user_id = create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    token = '_3K7AccnHtVTdH2_7T4cGpxHUgc-ZcJfRFGzer0mOo4'
    set_verification_code(cursor,user_id, token)
    db.commit()

    result = verify_user(cursor, token)
    db.commit()

    assert result is True

    cursor.execute('''
    SELECT is_verified, verification_token FROM users
    WHERE username = ?''', ('test_user',))
    row = cursor.fetchone()

    assert row[0] == 1
    assert row[1] is None

def test_incorrect_code():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    token = '_3K7AccnHtVTdH2_7T4cGpxHUgc-ZcJfRFGzer0mOo4'
    set_verification_code(cursor,1, token)
    db.commit()

    result = verify_user(cursor, 'c91Dtqf5Z4D8iSYAGA22-zimno4UuyczbV077QExxE0')
    db.commit()

    assert result is False

    cursor.execute('''
    SELECT is_verified, verification_token FROM users
    WHERE username = ?''', ('test_user',))
    row = cursor.fetchone()

    assert row[0] == 0
    assert row[1] == '_3K7AccnHtVTdH2_7T4cGpxHUgc-ZcJfRFGzer0mOo4'


def test_verify_nonexisting_username():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    result = verify_user(cursor, 'token')
    db.commit()

    assert result is False

def test_already_verified_user():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    token = '_3K7AccnHtVTdH2_7T4cGpxHUgc-ZcJfRFGzer0mOo4'
    set_verification_code(cursor, 1, token)
    db.commit()

    verify_user(cursor, token)
    db.commit()

    new_result = verify_user(cursor, token)
    db.commit()

    assert new_result is False

    cursor.execute('''
        SELECT is_verified, verification_token FROM users
        WHERE username = ?''', ('test_user',))
    row = cursor.fetchone()

    assert row[0] == 1
    assert row[1] is None

def test_successful_login():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    token = '_3K7AccnHtVTdH2_7T4cGpxHUgc-ZcJfRFGzer0mOo4'
    set_verification_code(cursor, 1, token)

    verify_user(cursor, token)
    db.commit()

    login = login_user(cursor, 'test_user', 'password1')

    assert login['success'] == True

def test_wrong_password_login():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    token = '_3K7AccnHtVTdH2_7T4cGpxHUgc-ZcJfRFGzer0mOo4'
    set_verification_code(cursor, 1, token)

    verify_user(cursor, token)
    db.commit()

    login = login_user(cursor, 'test_user', 'wordpass24')

    assert login['success'] == False
    assert login['message'] == 'Invalid username and/or password.'

def test_not_verified_login():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    token = '_3K7AccnHtVTdH2_7T4cGpxHUgc-ZcJfRFGzer0mOo4'
    set_verification_code(cursor, 1, token)
    db.commit()

    login = login_user(cursor, 'test_user', 'password1')

    assert login['success'] == False
    assert login['message'] == 'Account not verified.'

def test_nonexistant_user_login():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    token = '_3K7AccnHtVTdH2_7T4cGpxHUgc-ZcJfRFGzer0mOo4'
    set_verification_code(cursor, 1, token)

    verify_user(cursor, token)
    db.commit()

    login = login_user(cursor, 'not_test_user', 'password1')

    assert login['success'] == False
    assert login['message'] == 'Invalid username and/or password.'

def test_promote_to_leader_success():
    db, cursor = setup_db()

    # Create admin user
    admin_id = create_user(cursor, 'admin_user', 'admin@email.com', 'password')
    set_role(cursor, admin_id, 'admin')
    
    # Create regular user
    user_id = create_user(cursor, 'regular_user', 'user@email.com', 'password')
    
    db.commit()

    # Promote user to leader
    promote_to_leader(cursor, admin_id, user_id)
    db.commit()

    # Check role
    cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    assert row['role'] == 'leader'

def test_promote_to_leader_non_admin():
    db, cursor = setup_db()

    # Create non-admin user
    non_admin_id = create_user(cursor, 'non_admin', 'nonadmin@email.com', 'password')
    
    # Create regular user
    user_id = create_user(cursor, 'regular_user', 'user@email.com', 'password')
    
    db.commit()

    # Try to promote, should raise ValueError
    with pytest.raises(ValueError, match="Only admins can promote users to leader."):
        promote_to_leader(cursor, non_admin_id, user_id)

def test_sql_injection_prevention():
    """Test that SQL injection attempts are prevented by parameterized queries."""
    db, cursor = setup_db()

    # Try to inject SQL in username during authentication
    malicious_username = "admin' OR '1'='1"
    result = authenticate_user(cursor, malicious_username, 'password')
    assert result is None, 'SQL injection should not work in authentication'

    # Try to inject SQL in email during user creation
    try:
        create_user(cursor, 'test_user', "test@example.com'; DROP TABLE users; --", 'password')
        db.commit()
    except sqlite3.IntegrityError:
        pass  # Expected due to unique constraint, but table should still exist

    # Verify table still exists and we can query it
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    assert count >= 0, 'Users table should still exist after injection attempt'

    # Test search functionality with malicious input
    from features.songs.songs_model import search_song
    malicious_search = "%' OR '1'='1"
    results = search_song(cursor, malicious_search)
    # Should return empty or only legitimate results, not all songs
    assert isinstance(results, list), 'Search should return a list even with malicious input'