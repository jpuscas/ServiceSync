import sqlite3
import bcrypt

def create_users_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        first_name TEXT,
        last_name TEXT,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        
        password TEXT NOT NULL,
        
        role TEXT NOT NULL DEFAULT 'member',
        
        is_verified INTEGER NOT NULL DEFAULT 0,
        verification_token TEXT UNIQUE,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_user_timestamp 
        AFTER UPDATE ON users
        FOR EACH ROW
        BEGIN
            UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        ''')

def create_user(cursor, username: str, email: str, password: str, first_name: str = None, last_name: str = None):
    if password is None:
        raise sqlite3.IntegrityError("NOT NULL constraint failed: users.password")

    hashed_password = hash_password(password)

    cursor.execute('''
    INSERT INTO users (username, first_name, last_name, email, password)
    VALUES (?, ?, ?, ?, ?)    
    ''', (username, first_name or None, last_name or None, email, hashed_password))
    
    return cursor.lastrowid

def hash_password(password: str) -> str:
    password_bytes = password.encode ('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, stored_hash: str) -> bool:
    plain_bytes = plain_password.encode('utf-8')
    stored_bytes = stored_hash.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, stored_bytes)

def authenticate_user(cursor, username: str, password: str):
    cursor.execute('''
    SELECT id, username, password, role, is_verified
    FROM users 
    WHERE username = ?
    ''', (username,))

    user = cursor.fetchone()

    if not user:
        return None

    stored_hash = user['password'] #password in table schema

    if not verify_password(password, stored_hash):
        return None

    return {
        'id': user[0],
        'username': user[1],
        'role': user[3],
        'is_verified': user[4]
    }

def get_username_by_email(cursor, email: str):
    cursor.execute('''
    SELECT username FROM users WHERE email = ?
    ''', (email,))
    row = cursor.fetchone()
    return row[0] if row else None

def get_user_by_id(cursor, user_id: int):
    cursor.execute('''
    SELECT * FROM users WHERE id = ?
    ''', (user_id,))

    return cursor.fetchone()

def list_users(cursor):
    cursor.execute('''
    SELECT id, username, first_name, last_name, email, role
    FROM users
    ORDER BY username COLLATE NOCASE ASC
    ''')
    return cursor.fetchall()

def update_password(cursor, user_id: int, new_password: str):
    new_hashed = hash_password(new_password)

    cursor.execute('''
    UPDATE users
    SET password = ?
    WHERE id = ?
    ''', (new_hashed, user_id))

def update_email(cursor, user_id: int, new_email: str):
    cursor.execute('''
    UPDATE users
    SET email = ?
    WHERE id = ?
    ''', (new_email, user_id))

def update_username(cursor, user_id: int, new_username: str):
    cursor.execute('''
    UPDATE users
    SET username = ?
    WHERE id = ?
    ''', (new_username, user_id))

def update_name(cursor, user_id: int, first_name: str, last_name: str):
    cursor.execute('''
    UPDATE users
    SET first_name = ?, last_name = ?
    WHERE id = ?
    ''', (first_name or None, last_name or None, user_id))

def update_phone(cursor, user_id: int, phone: str):
    cursor.execute('''
    UPDATE users
    SET phone = ?
    WHERE id = ?
    ''', (phone, user_id))

def set_role(cursor, user_id: int, new_role: str):
    cursor.execute('''
    UPDATE users
    SET role = ? 
    WHERE id = ?
    ''', (new_role, user_id))

def delete_user(cursor, user_id: int):
    cursor.execute('''
    DELETE FROM users WHERE id = ?
    ''', (user_id,))