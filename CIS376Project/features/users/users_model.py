import json
import sqlite3
import bcrypt


def normalize_org_memberships(raw_org_value):
    if raw_org_value in (None, '', 'null', 'None'):
        return []

    if isinstance(raw_org_value, (list, tuple, set)):
        values = list(raw_org_value)
    elif isinstance(raw_org_value, str):
        stripped = raw_org_value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                values = parsed
            elif parsed in (None, ''):
                values = []
            else:
                values = [parsed]
        except json.JSONDecodeError:
            values = [stripped]
    else:
        values = [raw_org_value]

    normalized = []
    seen = set()
    for value in values:
        cleaned = str(value).strip()
        if not cleaned or cleaned.lower() == 'null':
            continue
        if cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def serialize_org_memberships(org_values):
    return json.dumps(normalize_org_memberships(org_values))


def get_user_org_memberships(user_row):
    if user_row is None:
        return []
    raw_value = user_row['org_id'] if hasattr(user_row, 'keys') else user_row
    return normalize_org_memberships(raw_value)


def get_primary_org(user_row):
    memberships = get_user_org_memberships(user_row)
    return memberships[0] if memberships else None


def user_belongs_to_org(user_row, org_id):
    if not org_id:
        return False
    return str(org_id) in get_user_org_memberships(user_row)


def set_user_org_memberships(cursor, user_id: int, org_values):
    serialized = serialize_org_memberships(org_values) if normalize_org_memberships(org_values) else None
    cursor.execute('''
    UPDATE users
    SET org_id = ?
    WHERE id = ?
    ''', (serialized, user_id))


def add_user_to_org(cursor, user_id: int, org_id: str):
    user_row = get_user_by_id(cursor, user_id)
    memberships = get_user_org_memberships(user_row)
    cleaned_org = (org_id or '').strip()
    if cleaned_org and cleaned_org not in memberships:
        memberships.append(cleaned_org)
    set_user_org_memberships(cursor, user_id, memberships)


def remove_user_from_org(cursor, user_id: int, org_id: str):
    user_row = get_user_by_id(cursor, user_id)
    memberships = get_user_org_memberships(user_row)
    cleaned_org = (org_id or '').strip()
    updated_memberships = [membership for membership in memberships if membership != cleaned_org]
    set_user_org_memberships(cursor, user_id, updated_memberships)
    return updated_memberships


def get_user_by_username(cursor, username: str):
    cursor.execute('''
    SELECT * FROM users WHERE username = ?
    ''', (username,))
    return cursor.fetchone()


def create_users_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        first_name TEXT,
        last_name TEXT,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        
        password TEXT NOT NULL,
        
        role TEXT NOT NULL DEFAULT 'member',
        org_id TEXT DEFAULT NULL,
        
        is_verified INTEGER NOT NULL DEFAULT 0,
        verification_token TEXT UNIQUE,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''' )

    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_user_timestamp 
        AFTER UPDATE ON users
        FOR EACH ROW
        BEGIN
            UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        ''')

def create_user(cursor, username: str, email: str, password: str, first_name: str = None, last_name: str = None, org_id=None): #other objects like phone can be added if necessary
    if password is None:
        raise sqlite3.IntegrityError("NOT NULL constraint failed: users.password")

    hashed_password = hash_password(password)
    serialized_orgs = serialize_org_memberships(org_id) if normalize_org_memberships(org_id) else None

    cursor.execute('''
    INSERT INTO users (username, first_name, last_name, email, password, org_id)
    VALUES (?, ?, ?, ?, ?, ?)    
    ''', (username, first_name or None, last_name or None, email, hashed_password, serialized_orgs))
    
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

def authenticate_user(cursor, username: str, password: str, org_id: str = None):
    cursor.execute('''
    SELECT id, username, password, role, is_verified, org_id
    FROM users 
    WHERE username = ?
    ''', (username,))

    users = cursor.fetchall()

    for user in users:
        stored_hash = user['password']
        if not verify_password(password, stored_hash):
            continue

        memberships = normalize_org_memberships(user['org_id'])
        active_org = str(org_id) if org_id and str(org_id) in memberships else (memberships[0] if memberships else None)

        return {
            'id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'is_verified': user['is_verified'],
            'org_id': active_org,
            'org_ids': memberships,
        }

    return None

def get_username_by_email(cursor, email: str, org_id: str = None):
    cursor.execute('''
    SELECT username, org_id FROM users WHERE email = ?
    ''', (email,))
    rows = cursor.fetchall()
    for row in rows:
        if org_id is None or user_belongs_to_org(row, org_id):
            return row['username']
    return None

def get_user_by_id(cursor, user_id: int):
    cursor.execute('''
    SELECT * FROM users WHERE id = ?
    ''', (user_id,))

    return cursor.fetchone()

def list_users(cursor, org_id: str = None):
    cursor.execute('''
    SELECT id, username, first_name, last_name, email, role, org_id
    FROM users
    ORDER BY username COLLATE NOCASE ASC
    ''')
    rows = cursor.fetchall()
    if org_id is None:
        return rows
    return [row for row in rows if user_belongs_to_org(row, org_id)]

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

def set_role(cursor, user_id: int, new_role: str, org_id: str = None):
    if org_id is not None:
        user = get_user_by_id(cursor, user_id)
        if not user or not user_belongs_to_org(user, org_id):
            return

    cursor.execute('''
    UPDATE users
    SET role = ? 
    WHERE id = ?
    ''', (new_role, user_id))

def promote_to_leader(cursor, admin_id: int, user_id: int, org_id: str = 'default'):
    admin = get_user_by_id(cursor, admin_id)
    if not admin or admin['role'].lower() != 'admin':
        raise ValueError('Only admins can promote users to leader.')

    target_user = get_user_by_id(cursor, user_id)
    if not target_user:
        raise ValueError('User not found in this organization.')

    enforce_org_membership = bool(org_id and org_id != 'default')
    if enforce_org_membership and not user_belongs_to_org(admin, org_id):
        raise ValueError('Only admins can promote users to leader.')
    if enforce_org_membership and not user_belongs_to_org(target_user, org_id):
        raise ValueError('User not found in this organization.')

    set_role(cursor, user_id, 'leader', org_id if enforce_org_membership else None)

def delete_user(cursor, user_id: int):
    cursor.execute('''
    DELETE FROM users WHERE id = ?
    ''', (user_id,))