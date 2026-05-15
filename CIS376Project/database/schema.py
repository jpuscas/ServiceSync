import json
import sys
from pathlib import Path

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from features.organizations.organizations_model import (
    create_organizations_table,
    create_organization_members_table,
    create_org_tables,
    sanitize_table_prefix,
)
from features.users.users_model import create_users_table, normalize_org_memberships
from features.invitations.invitations_model import create_organization_requests_table


# ── Helpers ───────────────────────────────────────────────────────────────────

def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    return cursor.fetchone() is not None


def _get_columns(cursor, table_name: str):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def _ensure_column(cursor, table_name, column_name, column_sql):
    if column_name not in _get_columns(cursor, table_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


# ── Users-table migration (unchanged from before) ────────────────────────────

def _users_table_needs_multi_org_migration(cursor):
    cursor.execute("PRAGMA table_info(users)")
    table_info = cursor.fetchall()
    org_id_column = next((row for row in table_info if row[1] == 'org_id'), None)
    if org_id_column and org_id_column[3] == 1:
        return True
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
    row = cursor.fetchone()
    if not row or not row[0]:
        return False
    table_sql = row[0].lower().replace(' ', '')
    return (
        'unique(username,org_id)' in table_sql
        or 'unique(email,org_id)' in table_sql
        or 'org_idtextnotnull' in table_sql
    )


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
        org_id TEXT DEFAULT NULL,
        is_verified INTEGER NOT NULL DEFAULT 0,
        verification_token TEXT UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    cursor.execute('''
    INSERT OR IGNORE INTO users_multi_org_migration
        (id, username, first_name, last_name, email, phone, carrier, password, org_id,
         is_verified, verification_token, created_at, updated_at)
    SELECT id, username, first_name, last_name, email, phone, carrier, password, org_id,
           is_verified, verification_token, created_at, updated_at
    FROM users
    ''')
    cursor.execute('DROP TABLE users')
    cursor.execute('ALTER TABLE users_multi_org_migration RENAME TO users')
    cursor.execute('PRAGMA foreign_keys = ON;')
    create_users_table(cursor)


def _drop_users_role_column(cursor):
    if not _table_exists(cursor, 'users'):
        return
    if 'role' not in _get_columns(cursor, 'users'):
        return

    cursor.execute('PRAGMA foreign_keys = OFF;')
    cursor.execute('DROP TABLE IF EXISTS users_no_role_migration;')
    cursor.execute('''
    CREATE TABLE users_no_role_migration (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        first_name TEXT,
        last_name TEXT,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        carrier TEXT,
        password TEXT NOT NULL,
        org_id TEXT DEFAULT NULL,
        is_verified INTEGER NOT NULL DEFAULT 0,
        verification_token TEXT UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    cursor.execute('''
    INSERT OR IGNORE INTO users_no_role_migration
        (id, username, first_name, last_name, email, phone, carrier, password, org_id,
         is_verified, verification_token, created_at, updated_at)
    SELECT id, username, first_name, last_name, email, phone, carrier, password, org_id,
           is_verified, verification_token, created_at, updated_at
    FROM users
    ''')
    cursor.execute('DROP TABLE users')
    cursor.execute('ALTER TABLE users_no_role_migration RENAME TO users')
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


# ── Data migration: old shared tables → per-org tables ───────────────────────

def _migrate_to_per_org_tables(cursor):
    """One-time idempotent migration from old org_id-column tables to per-org tables."""
    # Collect all org names referenced anywhere in the old data
    org_names = set()

    if _table_exists(cursor, 'users'):
        cursor.execute(
            "SELECT org_id FROM users WHERE org_id IS NOT NULL AND org_id != '' AND org_id != '[]'"
        )
        for row in cursor.fetchall():
            for org in normalize_org_memberships(row['org_id']):
                if org:
                    org_names.add(org)

    for old_table in ('songs', 'services', 'service_musicians', 'service_songs', 'invitations'):
        if _table_exists(cursor, old_table) and 'org_id' in _get_columns(cursor, old_table):
            cursor.execute(
                f"SELECT DISTINCT org_id FROM {old_table} WHERE org_id IS NOT NULL AND org_id != ''"
            )
            for row in cursor.fetchall():
                if row['org_id']:
                    org_names.add(str(row['org_id']))

    cursor.execute('PRAGMA foreign_keys = OFF;')

    for org_name in org_names:
        tbl = sanitize_table_prefix(org_name)
        cursor.execute("INSERT OR IGNORE INTO organizations (name) VALUES (?)", (org_name,))
        create_org_tables(cursor, org_name)

        # Populate organization_members from users.org_id
        if _table_exists(cursor, 'users'):
            cursor.execute("SELECT id, org_id FROM users WHERE org_id IS NOT NULL")
            for urow in cursor.fetchall():
                if org_name in normalize_org_memberships(urow['org_id']):
                    cursor.execute('''
                        INSERT OR IGNORE INTO organization_members (org_name, user_id, role)
                        VALUES (?, ?, 'member')
                    ''', (org_name, urow['id']))

        # Migrate songs
        if _table_exists(cursor, 'songs') and 'org_id' in _get_columns(cursor, 'songs'):
            cursor.execute(f'''
                INSERT OR IGNORE INTO "{tbl}_songs"
                    (song_id, title, artist, default_key, default_tempo, youtube_url, chords_pdf, lyrics_pdf)
                SELECT song_id, title, artist, default_key, default_tempo, youtube_url, chords_pdf, lyrics_pdf
                FROM songs WHERE org_id = ?
            ''', (org_name,))

        # Migrate services
        if _table_exists(cursor, 'services') and 'org_id' in _get_columns(cursor, 'services'):
            cursor.execute(f'''
                INSERT OR IGNORE INTO "{tbl}_services"
                    (service_id, service_name, service_type, service_date, service_time, leader_id)
                SELECT service_id, service_name, service_type, service_date, service_time, leader_id
                FROM services WHERE org_id = ?
            ''', (org_name,))

        # Migrate service_musicians
        if (_table_exists(cursor, 'service_musicians')
                and 'org_id' in _get_columns(cursor, 'service_musicians')):
            cursor.execute(f'''
                INSERT OR IGNORE INTO "{tbl}_service_musicians"
                    (musicians_id, service_id, user_id, instrument, accepted)
                SELECT musicians_id, service_id, user_id, instrument, accepted
                FROM service_musicians WHERE org_id = ?
            ''', (org_name,))

        # Migrate service_songs
        if (_table_exists(cursor, 'service_songs')
                and 'org_id' in _get_columns(cursor, 'service_songs')):
            cursor.execute(f'''
                INSERT OR IGNORE INTO "{tbl}_service_songs"
                    (service_song_id, service_id, song_id, custom_key, custom_tempo, song_order)
                SELECT service_song_id, service_id, song_id, custom_key, custom_tempo, song_order
                FROM service_songs WHERE org_id = ?
            ''', (org_name,))

        # Migrate invitations
        if (_table_exists(cursor, 'invitations')
                and 'org_id' in _get_columns(cursor, 'invitations')):
            cursor.execute(f'''
                INSERT OR IGNORE INTO "{tbl}_invitations"
                    (invitation_id, service_id, user_id, musicians_id, instrument,
                     invitation_status, invitation_date, invitation_time)
                SELECT invitation_id, service_id, user_id, musicians_id, instrument,
                       invitation_status, invitation_date, invitation_time
                FROM invitations WHERE org_id = ?
            ''', (org_name,))

    cursor.execute('PRAGMA foreign_keys = ON;')

    # Also ensure every org already in organization_members has its tables created
    if _table_exists(cursor, 'organization_members'):
        cursor.execute("SELECT DISTINCT org_name FROM organization_members")
        for row in cursor.fetchall():
            create_org_tables(cursor, row['org_name'])


def _drop_legacy_shared_tables(cursor):
    for table_name in ('invitations', 'service_musicians', 'service_songs', 'services', 'songs'):
        if _table_exists(cursor, table_name):
            cursor.execute(f'DROP TABLE IF EXISTS {table_name}')


# ── Main entry point ──────────────────────────────────────────────────────────

def create_database(cursor):
    """Initialize / update the database schema. Safe to call on an existing database."""
    # Core shared tables
    create_users_table(cursor)
    _migrate_users_table_for_multi_org(cursor)
    _drop_users_role_column(cursor)
    _ensure_column(cursor, 'users', 'org_id', 'org_id TEXT DEFAULT NULL')
    _ensure_column(cursor, 'users', 'carrier', 'carrier TEXT')
    _migrate_existing_user_org_memberships(cursor)

    # Organizations
    create_organizations_table(cursor)
    create_organization_members_table(cursor)

    # Global requests table
    create_organization_requests_table(cursor)

    # Migrate old data and ensure per-org tables exist
    _migrate_to_per_org_tables(cursor)
    _drop_legacy_shared_tables(cursor)


if __name__ == '__main__':
    from database.connection import ensure_database_initialized

    database_path, db_already_exists = ensure_database_initialized()
    if db_already_exists:
        print(f'Database exists at {database_path}. Schema initialized/checked without clearing data.')
    else:
        print(f'Database created at {database_path}.')
