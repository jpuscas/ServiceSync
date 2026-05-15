import sqlite3
from features.organizations.organizations_model import sanitize_table_prefix, create_org_tables


def _tbl(org_name: str) -> str:
    return sanitize_table_prefix(org_name)


# ── Global organization_requests table (not per-org) ─────────────────────────

def create_organization_requests_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS organization_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        org_name TEXT NOT NULL,
        request_status TEXT NOT NULL DEFAULT 'Pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        responded_at DATETIME,
        UNIQUE(recipient_id, org_name),
        FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
    );
    ''')


# ── Per-org invitation helpers ────────────────────────────────────────────────

def _get_user_orgs(cursor, user_id: int):
    """Return all org names the user belongs to (via organization_members)."""
    try:
        cursor.execute(
            'SELECT org_name FROM organization_members WHERE user_id = ?', (user_id,)
        )
        return [row['org_name'] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


# ── Invitation CRUD ───────────────────────────────────────────────────────────

def create_invitation(cursor, service_id: int, user_id: int, invitation_status: str,
                      invitation_date: str, invitation_time: str, org_name: str = 'default',
                      musicians_id: int = None, instrument: str = None):
    create_org_tables(cursor, org_name)
    tbl = _tbl(org_name)
    cursor.execute(f'''
        INSERT INTO "{tbl}_invitations"
            (service_id, user_id, musicians_id, instrument, invitation_status, invitation_date, invitation_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (service_id, user_id, musicians_id, instrument, invitation_status, invitation_date, invitation_time))


def get_invitation_by_musicians_id(cursor, musicians_id: int, org_name: str = None):
    """Look up an invitation by musicians_id.

    If org_name is given, search only that org's table.
    If org_name is None, search all orgs stored in organization_members.
    """
    if org_name is not None:
        tbl = _tbl(org_name)
        try:
            cursor.execute(f'''
                SELECT i.*, s.service_name, s.service_date, s.service_time,
                       COALESCE(i.instrument, sm.instrument) AS instrument,
                       '{org_name}' AS org_name
                FROM "{tbl}_invitations" i
                JOIN "{tbl}_services" s ON i.service_id = s.service_id
                LEFT JOIN "{tbl}_service_musicians" sm ON i.musicians_id = sm.musicians_id
                WHERE i.musicians_id = ?
            ''', (musicians_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.OperationalError:
            return None
    else:
        # Search all known orgs
        try:
            cursor.execute("SELECT DISTINCT org_name FROM organization_members")
            orgs = [r['org_name'] for r in cursor.fetchall()]
        except sqlite3.OperationalError:
            orgs = []
        for org in orgs:
            result = get_invitation_by_musicians_id(cursor, musicians_id, org)
            if result:
                return result
        return None


def get_invitation_by_service_user(cursor, service_id: int, user_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
            SELECT *
            FROM "{tbl}_invitations"
            WHERE service_id = ? AND user_id = ?
            ORDER BY invitation_id DESC
            LIMIT 1
        ''', (service_id, user_id))
        return cursor.fetchone()
    except sqlite3.OperationalError:
        return None


def get_invitations_by_user(cursor, user_id: int, org_name: str = None):
    """Return invitations for a user.

    If org_name is given, return only that org's invitations.
    If None, return invitations from all orgs the user belongs to.
    Each returned dict includes an 'org_name' key.
    """
    if org_name is not None:
        orgs = [org_name]
    else:
        orgs = _get_user_orgs(cursor, user_id)

    all_rows = []
    for org in orgs:
        tbl = _tbl(org)
        try:
            cursor.execute(f'''
                SELECT i.*, s.service_name, s.service_date, s.service_time,
                       COALESCE(i.instrument, sm.instrument) AS instrument
                FROM "{tbl}_invitations" i
                JOIN "{tbl}_services" s ON i.service_id = s.service_id
                LEFT JOIN "{tbl}_service_musicians" sm ON i.musicians_id = sm.musicians_id
                WHERE i.user_id = ?
                ORDER BY s.service_date, s.service_time
            ''', (user_id,))
            for row in cursor.fetchall():
                row_dict = dict(row)
                row_dict['org_name'] = org
                all_rows.append(row_dict)
        except sqlite3.OperationalError:
            pass
    return all_rows


def get_invitations_by_service(cursor, service_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
            SELECT i.*, u.username AS user_name,
                   COALESCE(i.instrument, sm.instrument) AS instrument
            FROM "{tbl}_invitations" i
            JOIN users u ON i.user_id = u.id
            LEFT JOIN "{tbl}_service_musicians" sm ON i.musicians_id = sm.musicians_id
            WHERE i.service_id = ?
            ORDER BY i.invitation_date, i.invitation_time
        ''', (service_id,))
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def get_accepted_invitations_by_user(cursor, user_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
            SELECT i.*, s.service_name, s.service_date, s.service_time,
                   COALESCE(i.instrument, sm.instrument) AS instrument
            FROM "{tbl}_invitations" i
            JOIN "{tbl}_services" s ON i.service_id = s.service_id
            LEFT JOIN "{tbl}_service_musicians" sm ON i.musicians_id = sm.musicians_id
            WHERE i.user_id = ? AND i.invitation_status = 'Accepted'
            ORDER BY s.service_date, s.service_time
        ''', (user_id,))
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def get_declined_invitations_by_user(cursor, user_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
            SELECT i.*, s.service_name, s.service_date, s.service_time,
                   COALESCE(i.instrument, sm.instrument) AS instrument
            FROM "{tbl}_invitations" i
            JOIN "{tbl}_services" s ON i.service_id = s.service_id
            LEFT JOIN "{tbl}_service_musicians" sm ON i.musicians_id = sm.musicians_id
            WHERE i.user_id = ? AND i.invitation_status = 'Declined'
            ORDER BY s.service_date, s.service_time
        ''', (user_id,))
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def get_service_attendees(cursor, service_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
            SELECT i.*, u.id AS user_id, u.username, u.email,
                   COALESCE(i.instrument, sm.instrument) AS instrument
            FROM "{tbl}_invitations" i
            JOIN users u ON i.user_id = u.id
            LEFT JOIN "{tbl}_service_musicians" sm ON i.musicians_id = sm.musicians_id
            WHERE i.service_id = ? AND i.invitation_status = 'Accepted'
            ORDER BY u.username
        ''', (service_id,))
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def update_invitation_status(cursor, invitation_id: int, new_status: str, org_name: str = None):
    if org_name is None:
        return
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
            UPDATE "{tbl}_invitations"
            SET invitation_status = ?
            WHERE invitation_id = ?
        ''', (new_status, invitation_id))
    except sqlite3.OperationalError:
        pass


def update_invitation_details(cursor, invitation_id: int, invitation_status: str,
                               invitation_date: str, invitation_time: str,
                               org_name: str = 'default', musicians_id: int = None,
                               instrument: str = None):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
            UPDATE "{tbl}_invitations"
            SET invitation_status = ?,
                invitation_date = ?,
                invitation_time = ?,
                musicians_id = ?,
                instrument = ?
            WHERE invitation_id = ?
        ''', (invitation_status, invitation_date, invitation_time, musicians_id, instrument, invitation_id))
    except sqlite3.OperationalError:
        pass


def accept_invitation(cursor, invitation_id: int, org_name: str = None):
    update_invitation_status(cursor, invitation_id, 'Accepted', org_name)


def decline_invitation(cursor, invitation_id: int, org_name: str = None):
    update_invitation_status(cursor, invitation_id, 'Declined', org_name)


def delete_invitation(cursor, invitation_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
            DELETE FROM "{tbl}_invitations"
            WHERE invitation_id = ?
        ''', (invitation_id,))
    except sqlite3.OperationalError:
        pass


def delete_invitations_for_musician(cursor, musicians_id: int, org_name: str = None):
    if org_name is None:
        return
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
            DELETE FROM "{tbl}_invitations"
            WHERE musicians_id = ?
        ''', (musicians_id,))
    except sqlite3.OperationalError:
        pass


# ── Organization request helpers (global table) ───────────────────────────────

def delete_organization_requests_for_user_org(cursor, recipient_id: int, org_name: str):
    cursor.execute('''
        DELETE FROM organization_requests
        WHERE recipient_id = ? AND org_name = ?
    ''', (recipient_id, org_name))


def create_organization_request(cursor, sender_id: int, recipient_id: int, org_name: str):
    cursor.execute('''
        INSERT INTO organization_requests (sender_id, recipient_id, org_name)
        VALUES (?, ?, ?)
        ON CONFLICT(recipient_id, org_name) DO UPDATE SET
            sender_id = excluded.sender_id,
            request_status = 'Pending',
            created_at = CURRENT_TIMESTAMP,
            responded_at = NULL
    ''', (sender_id, recipient_id, org_name))


def get_organization_requests_by_user(cursor, recipient_id: int):
    cursor.execute('''
        SELECT r.*, u.username AS sender_username
        FROM organization_requests r
        JOIN users u ON r.sender_id = u.id
        WHERE r.recipient_id = ?
        ORDER BY r.created_at DESC
    ''', (recipient_id,))
    return cursor.fetchall()


def get_organization_request_by_id(cursor, request_id: int):
    cursor.execute('''
        SELECT r.*, u.username AS sender_username
        FROM organization_requests r
        JOIN users u ON r.sender_id = u.id
        WHERE r.request_id = ?
    ''', (request_id,))
    return cursor.fetchone()


def delete_organization_request(cursor, request_id: int):
    cursor.execute('''
        DELETE FROM organization_requests
        WHERE request_id = ?
    ''', (request_id,))


def update_organization_request_status(cursor, request_id: int, status: str):
    cursor.execute('''
        UPDATE organization_requests
        SET request_status = ?, responded_at = CURRENT_TIMESTAMP
        WHERE request_id = ?
    ''', (status, request_id))
