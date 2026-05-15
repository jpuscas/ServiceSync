import re
import sqlite3
import json


# ── Utility ──────────────────────────────────────────────────────────────────

def sanitize_table_prefix(org_name: str) -> str:
    """Convert an org name to a safe, lowercase SQL table-name prefix.

    Example: 'Golgotha Romanian Baptist Church' -> 'golgotha_romanian_baptist_church'
    """
    prefix = re.sub(r'[^a-z0-9]+', '_', (org_name or '').strip().lower()).strip('_')
    if not prefix:
        raise ValueError(f"Cannot derive a valid table prefix from org name: {org_name!r}")
    return prefix


# ── Core shared tables ────────────────────────────────────────────────────────

def create_organizations_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')


def create_organization_members_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS organization_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_name TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL DEFAULT 'member',
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(org_name, user_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    ''')


# ── Per-org table creation ────────────────────────────────────────────────────

def create_org_songs_table(cursor, org_name: str):
    tbl = sanitize_table_prefix(org_name)
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS "{tbl}_songs" (
        song_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        default_key TEXT NOT NULL,
        default_tempo INTEGER,
        youtube_url TEXT,
        chords_pdf BLOB,
        lyrics_pdf BLOB,
        UNIQUE(title, artist)
    );
    ''')


def create_org_services_table(cursor, org_name: str):
    tbl = sanitize_table_prefix(org_name)
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS "{tbl}_services" (
        service_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_name TEXT NOT NULL,
        service_type TEXT NOT NULL,
        service_date DATE NOT NULL,
        service_time TIME NOT NULL,
        leader_id INTEGER,
        FOREIGN KEY (leader_id) REFERENCES users(id)
    );
    ''')


def create_org_service_musicians_table(cursor, org_name: str):
    tbl = sanitize_table_prefix(org_name)
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS "{tbl}_service_musicians" (
        musicians_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        instrument TEXT NOT NULL,
        accepted INTEGER DEFAULT NULL,
        UNIQUE(service_id, user_id, instrument),
        FOREIGN KEY (service_id) REFERENCES "{tbl}_services"(service_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    ''')


def create_org_service_songs_table(cursor, org_name: str):
    tbl = sanitize_table_prefix(org_name)
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS "{tbl}_service_songs" (
        service_song_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,
        custom_key TEXT,
        custom_tempo INTEGER,
        song_order INTEGER,
        UNIQUE(service_id, song_id),
        FOREIGN KEY (service_id) REFERENCES "{tbl}_services"(service_id) ON DELETE CASCADE,
        FOREIGN KEY (song_id) REFERENCES "{tbl}_songs"(song_id) ON DELETE CASCADE
    );
    ''')


def create_org_invitations_table(cursor, org_name: str):
    tbl = sanitize_table_prefix(org_name)
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS "{tbl}_invitations" (
        invitation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        musicians_id INTEGER,
        instrument TEXT,
        invitation_status TEXT NOT NULL DEFAULT 'Pending',
        invitation_date DATE NOT NULL,
        invitation_time TIME NOT NULL,
        FOREIGN KEY (service_id) REFERENCES "{tbl}_services"(service_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    ''')


def create_org_tables(cursor, org_name: str):
    """Create all five per-org data tables. Safe to call multiple times (IF NOT EXISTS)."""
    create_org_songs_table(cursor, org_name)
    create_org_services_table(cursor, org_name)
    create_org_service_musicians_table(cursor, org_name)
    create_org_service_songs_table(cursor, org_name)
    create_org_invitations_table(cursor, org_name)


# ── Organization CRUD ─────────────────────────────────────────────────────────

def create_organization(cursor, org_name: str) -> int:
    """Insert into organizations (if not exists) and create all per-org tables. Returns org id."""
    cursor.execute('INSERT OR IGNORE INTO organizations (name) VALUES (?)', (org_name,))
    create_org_tables(cursor, org_name)
    cursor.execute('SELECT id FROM organizations WHERE name = ?', (org_name,))
    row = cursor.fetchone()
    return row['id'] if row else None


def _normalize_memberships(raw_org_value):
    if raw_org_value in (None, ''):
        return []
    if isinstance(raw_org_value, list):
        return [str(value).strip() for value in raw_org_value if str(value).strip()]
    raw_text = str(raw_org_value).strip()
    if not raw_text:
        return []
    if raw_text.startswith('['):
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, list):
                return [str(value).strip() for value in parsed if str(value).strip()]
        except Exception:
            pass
    return [raw_text]


def delete_organization(cursor, org_name: str):
    tbl = sanitize_table_prefix(org_name)

    # Remove org from users.org_id cache across all users.
    cursor.execute('SELECT id, org_id FROM users')
    for user_row in cursor.fetchall():
        memberships = _normalize_memberships(user_row['org_id'])
        filtered_memberships = [membership for membership in memberships if membership != org_name]
        cursor.execute(
            'UPDATE users SET org_id = ? WHERE id = ?',
            (json.dumps(filtered_memberships), user_row['id']),
        )

    cursor.execute('DELETE FROM organization_requests WHERE org_name = ?', (org_name,))
    cursor.execute('DELETE FROM organization_members WHERE org_name = ?', (org_name,))
    cursor.execute('DELETE FROM organizations WHERE name = ?', (org_name,))

    # Drop per-organization data tables.
    cursor.execute(f'DROP TABLE IF EXISTS "{tbl}_invitations"')
    cursor.execute(f'DROP TABLE IF EXISTS "{tbl}_service_songs"')
    cursor.execute(f'DROP TABLE IF EXISTS "{tbl}_service_musicians"')
    cursor.execute(f'DROP TABLE IF EXISTS "{tbl}_services"')
    cursor.execute(f'DROP TABLE IF EXISTS "{tbl}_songs"')


def get_org_by_name(cursor, org_name: str):
    cursor.execute('SELECT * FROM organizations WHERE name = ?', (org_name,))
    return cursor.fetchone()


def get_all_organizations(cursor):
    cursor.execute('SELECT * FROM organizations ORDER BY name COLLATE NOCASE ASC')
    return cursor.fetchall()


# ── Membership ────────────────────────────────────────────────────────────────

def add_org_member(cursor, org_name: str, user_id: int, role: str = 'member'):
    """Add a user to an org's member list. Ensures org and tables exist first."""
    create_organization(cursor, org_name)
    cursor.execute('''
    INSERT OR IGNORE INTO organization_members (org_name, user_id, role)
    VALUES (?, ?, ?)
    ''', (org_name, user_id, role))


def remove_org_member(cursor, org_name: str, user_id: int):
    cursor.execute('''
    DELETE FROM organization_members
    WHERE org_name = ? AND user_id = ?
    ''', (org_name, user_id))


def user_in_org(cursor, user_id: int, org_name: str) -> bool:
    """Return True if the user is a member of the given organization."""
    cursor.execute('''
    SELECT 1 FROM organization_members
    WHERE org_name = ? AND user_id = ?
    ''', (org_name, user_id))
    return cursor.fetchone() is not None


def get_user_orgs(cursor, user_id: int):
    """Return a list of org names the user belongs to, ordered by join date."""
    cursor.execute('''
    SELECT org_name FROM organization_members
    WHERE user_id = ?
    ORDER BY joined_at ASC
    ''', (user_id,))
    return [row['org_name'] for row in cursor.fetchall()]


def get_org_members(cursor, org_name: str):
    """Return all users in an organization with their org-level role."""
    cursor.execute('''
    SELECT u.id, u.username, u.first_name, u.last_name, u.email,
           om.role AS org_role
    FROM organization_members om
    JOIN users u ON om.user_id = u.id
    WHERE om.org_name = ?
    ORDER BY u.username COLLATE NOCASE ASC
    ''', (org_name,))
    return cursor.fetchall()


def set_org_member_role(cursor, org_name: str, user_id: int, role: str):
    cursor.execute('''
    UPDATE organization_members
    SET role = ?
    WHERE org_name = ? AND user_id = ?
    ''', (role, org_name, user_id))


def get_org_member_role(cursor, org_name: str, user_id: int):
    cursor.execute('''
    SELECT role FROM organization_members
    WHERE org_name = ? AND user_id = ?
    ''', (org_name, user_id))
    row = cursor.fetchone()
    return row['role'] if row else None


def get_user_org_memberships_with_roles(cursor, user_id: int):
    cursor.execute('''
    SELECT org_name, role
    FROM organization_members
    WHERE user_id = ?
    ORDER BY joined_at ASC
    ''', (user_id,))
    return cursor.fetchall()
