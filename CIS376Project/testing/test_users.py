import sqlite3
import pytest
from database.schema import create_database
from features.users.users_model import create_user, update_password, authenticate_user, delete_user, update_email


def setup_db():
    db = sqlite3.connect(':memory:')
    cursor = db.cursor()

    create_database(cursor)

    db.commit()
    return db, cursor

def test_valid_user():
    db, cursor = setup_db()

    cursor.execute('''
        INSERT INTO users (username, email, password)
        VALUES (?,?,?)
        ''', ('test_user', 'test@email.com', 'test_password'))

    db.commit()

    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()
    assert len(rows) == 1

def test_duplicate_email():
    db, cursor = setup_db()

    cursor.execute('''
    INSERT INTO users (username, email, password)
    VALUES (?,?,?)
    ''', ('test_user1', 'test@email.com', 'test_password1'))

    db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute('''
        INSERT INTO users (username, email, password)
        VALUES (?,?,?)
        ''', ('test_user1', 'test1234@email.com', 'test_password1'))

def test_duplicate_username():
    db, cursor = setup_db()

    cursor.execute('''
    INSERT INTO users (username, email, password)
    VALUES (?,?,?)
    ''', ('test_user', 'test1234@email.com', 'test_password2'))

    db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute('''
        INSERT INTO users (username, email, password)
        VALUES (?,?,?)
        ''', ('test_user1', 'test1234@email.com', 'test_password1'))

def test_null_username():
    db, cursor = setup_db()
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute('''
        INSERT INTO users (username, email, password)
        VALUES (?,?,?)
        ''', (None, 'test1234@email.com', 'test_password1'))

def test_null_email():
    db, cursor = setup_db()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute('''
        INSERT INTO users (username, email, password)
        VALUES (?,?,?)
        ''', ('test_user1', None, 'test_password1'))

def test_null_password():
    db, cursor = setup_db()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute('''
        INSERT INTO users (username, email, password)
        VALUES (?,?,?)
        ''', ('test_user4', 'test1234@email.com', None))

def test_default_role():
    db, cursor = setup_db()

    cursor.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?,?,?)
            ''', ('test_user', 'test@email.com', 'test_password'))

    cursor.execute('''SELECT username, role FROM users WHERE username = ?''', ('test_user',))
    rows = cursor.fetchone()

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
    user_id = user[0]

    update_password(cursor, user_id, 'password22')
    db.commit()

    new_authenticate = authenticate_user(cursor, 'test_user', 'password22')
    assert new_authenticate is not False

def test_update_email():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    user = authenticate_user(cursor, 'test_user', 'password1')
    user_id = user[0]

    update_email(cursor, user_id, 'stilltesting@gmail.com')
    db.commit()

    cursor.execute('''SELECT username, email FROM users WHERE username = ?''', ('test_user',))
    rows = cursor.fetchone()
    print(rows)

def test_delete_user():
    db, cursor = setup_db()

    create_user(cursor, 'test_user', 'testuser@gmail.com', 'password1')
    db.commit()

    user = authenticate_user(cursor, 'test_user', 'password1')
    user_id = user[0]

    delete_user(cursor, user_id)
    db.commit()

    deleted_user = authenticate_user(cursor, 'test_user', 'password1')

    assert deleted_user is False
