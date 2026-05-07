import json
import sys
from pathlib import Path

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from features.services.service_musicians_model import create_musicians_table
from features.services.service_songs_model import create_service_songs_table
from features.services.services_model import create_services_table
from features.songs.songs_model import create_songs_table
from features.users.users_model import create_users_table
from features.invitations.invitations_model import create_invitations_table, create_organization_requests_table



def _ensure_column(cursor, table_name, column_name, column_sql):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if column_name in existing_columns:
        return
    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


def _users_table_needs_multi_org_migration(cursor):
    cursor.execute("PRAGMA table_info(users)")
    table_info = cursor.fetchall()
    org_id_column = next((row for row in table_info if row[1] == 'org_id'), None)
    if org_id_column and org_id_column[3] == 1:
        return True

    cursor.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'users'")
    row = cursor.fetchone()
    if not row or not row[0]:
        return False
    table_sql = row[0].lower().replace(' ', '')
    return 'unique(username,org_id)' in table_sql or 'unique(email,org_id)' in table_sql or 'org_idtextnotnull' in table_sql


def _migrate_users_table_for_multi_org(cursor):
    if not _users_table_needs_multi_org_migration(cursor):
        return

    cursor.execute('PRAGMA foreign_keys = OFF;')
    cursor.execute('DROP TABLE IF EXISTS users_multi_org_migration;')
    cursor.execute('''
    CREATE TABLE users_multi_org_migration (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        first_name TEXT,
        last_name TEXT,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        carrier TEXT,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'member',
        org_id TEXT DEFAULT NULL,
        is_verified INTEGER NOT NULL DEFAULT 0,
        verification_token TEXT UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    cursor.execute('''
    INSERT OR IGNORE INTO users_multi_org_migration (id, username, first_name, last_name, email, phone, password, role, org_id, is_verified, verification_token, created_at, updated_at)
    SELECT id, username, first_name, last_name, email, phone, carrier, password, role, org_id, is_verified, verification_token, created_at, updated_at
    FROM users
    ''')
    cursor.execute('DROP TABLE users')
    cursor.execute('ALTER TABLE users_multi_org_migration RENAME TO users')
    cursor.execute('PRAGMA foreign_keys = ON;')
    create_users_table(cursor)


def _migrate_existing_user_org_memberships(cursor):
    cursor.execute("SELECT id, username, org_id FROM users")
    rows = cursor.fetchall()
    jason_orgs = json.dumps(['Golgotha Romanian Baptist Church'])

    for row in rows:
        username = (row['username'] or '').strip().lower()
        raw_org = row['org_id']
        if username == 'jasonpuscas':
            cursor.execute("UPDATE users SET org_id = ? WHERE id = ?", (jason_orgs, row['id']))
            continue

        if raw_org in (None, '', '[]'):
            continue

        raw_text = str(raw_org).strip()
        if raw_text.startswith('['):
            continue

        cursor.execute("UPDATE users SET org_id = NULL WHERE id = ?", (row['id'],))


def create_database(cursor):
    # Table creation is idempotent to avoid recreating/clearing existing data.
    create_users_table(cursor)
    _migrate_users_table_for_multi_org(cursor)
    _ensure_column(cursor, 'users', 'org_id', "org_id TEXT DEFAULT NULL")
    _ensure_column(cursor, 'users', 'carrier', "carrier TEXT")
    _migrate_existing_user_org_memberships(cursor)
    
    create_songs_table(cursor)
    _ensure_column(cursor, 'songs', 'org_id', "org_id TEXT NOT NULL DEFAULT 'default'")

    # Add new columns for PDFs if they don't exist (safe if DB already has them)
    try:
        cursor.execute("ALTER TABLE songs ADD COLUMN chords_pdf BLOB;")
    except Exception:
        pass  # Column already exists or alter not needed
    try:
        cursor.execute("ALTER TABLE songs ADD COLUMN lyrics_pdf BLOB;")
    except Exception:
        pass  # Column already exists or alter not needed

    create_services_table(cursor)
    _ensure_column(cursor, 'services', 'service_name', "service_name TEXT NOT NULL DEFAULT 'Worship Service'")
    _ensure_column(cursor, 'services', 'service_type', "service_type TEXT NOT NULL DEFAULT 'Worship'")
    _ensure_column(cursor, 'services', 'service_date', "service_date DATE NOT NULL DEFAULT '1970-01-01'")
    _ensure_column(cursor, 'services', 'service_time', "service_time TIME NOT NULL DEFAULT '09:00'")
    _ensure_column(cursor, 'services', 'leader_id', 'leader_id INTEGER')
    _ensure_column(cursor, 'services', 'org_id', "org_id TEXT NOT NULL DEFAULT 'default'")
    
    create_musicians_table(cursor)
    _ensure_column(cursor, 'service_musicians', 'org_id', "org_id TEXT NOT NULL DEFAULT 'default'")
    
    create_service_songs_table(cursor)
    _ensure_column(cursor, 'service_songs', 'org_id', "org_id TEXT NOT NULL DEFAULT 'default'")
    
    create_invitations_table(cursor)
    _ensure_column(cursor, 'invitations', 'musicians_id', 'musicians_id INTEGER')
    _ensure_column(cursor, 'invitations', 'instrument', 'instrument TEXT')
    _ensure_column(cursor, 'invitations', 'org_id', "org_id TEXT NOT NULL DEFAULT 'default'")

    create_organization_requests_table(cursor)


if __name__ == '__main__':
    from database.connection import ensure_database_initialized

    database_path, db_already_exists = ensure_database_initialized()
    if db_already_exists:
        print(f'Database exists at {database_path}. Schema initialized/checked without clearing data.')
    else:
        print(f'Database created at {database_path}.')
