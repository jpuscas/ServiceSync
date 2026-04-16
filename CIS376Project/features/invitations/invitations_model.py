def create_invitations_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invitations (
        invitation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        musicians_id INTEGER,
        instrument TEXT,
        invitation_status TEXT NOT NULL DEFAULT 'Pending',
        invitation_date DATE NOT NULL,
        invitation_time TIME NOT NULL,
        org_id TEXT NOT NULL DEFAULT 'default',
        FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );  
    ''')


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

def create_invitation(cursor, service_id: int, user_id: int, invitation_status: str, invitation_date: str, invitation_time: str, org_id: str = 'default', musicians_id: int = None, instrument: str = None):
    cursor.execute('''
        INSERT INTO invitations (service_id, user_id, musicians_id, instrument, invitation_status, invitation_date, invitation_time, org_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (service_id, user_id, musicians_id, instrument, invitation_status, invitation_date, invitation_time, org_id))


def get_invitation_by_musicians_id(cursor, musicians_id: int, org_id: str = None):
    query = '''
        SELECT i.*, s.service_name, s.service_date, s.service_time,
               COALESCE(i.instrument, sm.instrument) AS instrument
        FROM invitations i
        JOIN services s ON i.service_id = s.service_id
        LEFT JOIN service_musicians sm ON i.musicians_id = sm.musicians_id
        WHERE i.musicians_id = ?
    '''
    params = [musicians_id]
    if org_id is not None:
        query += ' AND i.org_id = ?'
        params.append(org_id)
    cursor.execute(query, tuple(params))
    return cursor.fetchone()


def get_invitation_by_service_user(cursor, service_id: int, user_id: int, org_id: str = 'default'):
    cursor.execute('''
        SELECT *
        FROM invitations
        WHERE service_id = ? AND user_id = ? AND org_id = ?
        ORDER BY invitation_id DESC
        LIMIT 1
    ''', (service_id, user_id, org_id))
    return cursor.fetchone()

def get_invitations_by_user(cursor, user_id: int, org_id: str = None):
    query = '''
        SELECT i.*, s.service_name, s.service_date, s.service_time,
               COALESCE(i.instrument, sm.instrument) AS instrument
        FROM invitations i
        JOIN services s ON i.service_id = s.service_id
        LEFT JOIN service_musicians sm ON i.musicians_id = sm.musicians_id
        WHERE i.user_id = ?
    '''
    params = [user_id]
    if org_id is not None:
        query += ' AND i.org_id = ?'
        params.append(org_id)
    query += ' ORDER BY s.service_date, s.service_time'
    cursor.execute(query, tuple(params))
    return cursor.fetchall()

def get_invitations_by_service(cursor, service_id: int, org_id: str = 'default'):
    cursor.execute('''
        SELECT i.*, u.username AS user_name,
               COALESCE(i.instrument, sm.instrument) AS instrument
        FROM invitations i
        JOIN users u ON i.user_id = u.id
        LEFT JOIN service_musicians sm ON i.musicians_id = sm.musicians_id
        WHERE i.service_id = ? AND i.org_id = ?
        ORDER BY i.invitation_date, i.invitation_time
    ''', (service_id, org_id))
    return cursor.fetchall()

def get_accepted_invitations_by_user(cursor, user_id: int, org_id: str = 'default'):
    cursor.execute('''
        SELECT i.*, s.service_name, s.service_date, s.service_time,
               COALESCE(i.instrument, sm.instrument) AS instrument
        FROM invitations i
        JOIN services s ON i.service_id = s.service_id
        LEFT JOIN service_musicians sm ON i.musicians_id = sm.musicians_id
        WHERE i.user_id = ? AND i.invitation_status = 'Accepted' AND i.org_id = ?
        ORDER BY s.service_date, s.service_time
    ''', (user_id, org_id))
    return cursor.fetchall()

def get_declined_invitations_by_user(cursor, user_id: int, org_id: str = 'default'):
    cursor.execute('''
        SELECT i.*, s.service_name, s.service_date, s.service_time,
               COALESCE(i.instrument, sm.instrument) AS instrument
        FROM invitations i
        JOIN services s ON i.service_id = s.service_id
        LEFT JOIN service_musicians sm ON i.musicians_id = sm.musicians_id
        WHERE i.user_id = ? AND i.invitation_status = 'Declined' AND i.org_id = ?
        ORDER BY s.service_date, s.service_time
    ''', (user_id, org_id))
    return cursor.fetchall()

def get_service_attendees(cursor, service_id: int, org_id: str = 'default'):
    cursor.execute('''
        SELECT i.*, u.id AS user_id, u.username, u.email,
               COALESCE(i.instrument, sm.instrument) AS instrument
        FROM invitations i
        JOIN users u ON i.user_id = u.id
        LEFT JOIN service_musicians sm ON i.musicians_id = sm.musicians_id
        WHERE i.service_id = ? AND i.invitation_status = 'Accepted' AND i.org_id = ?
        ORDER BY u.username
    ''', (service_id, org_id))
    return cursor.fetchall()

def update_invitation_status(cursor, invitation_id: int, new_status: str, org_id: str = None):
    if org_id is None:
        cursor.execute('''
            UPDATE invitations
            SET invitation_status = ?
            WHERE invitation_id = ?
        ''', (new_status, invitation_id))
        return

    cursor.execute('''
        UPDATE invitations
        SET invitation_status = ?
        WHERE invitation_id = ? AND org_id = ?
    ''', (new_status, invitation_id, org_id))

def update_invitation_details(cursor, invitation_id: int, invitation_status: str, invitation_date: str, invitation_time: str, org_id: str = 'default', musicians_id: int = None, instrument: str = None):
    cursor.execute('''
        UPDATE invitations
        SET invitation_status = ?,
            invitation_date = ?,
            invitation_time = ?,
            musicians_id = ?,
            instrument = ?
        WHERE invitation_id = ? AND org_id = ?
    ''', (invitation_status, invitation_date, invitation_time, musicians_id, instrument, invitation_id, org_id))


def accept_invitation(cursor, invitation_id: int, org_id: str = None):
    update_invitation_status(cursor, invitation_id, 'Accepted', org_id)


def decline_invitation(cursor, invitation_id: int, org_id: str = None):
    update_invitation_status(cursor, invitation_id, 'Declined', org_id)


def delete_invitation(cursor, invitation_id: int, org_id: str = 'default'):
    cursor.execute('''
        DELETE FROM invitations
        WHERE invitation_id = ? AND org_id = ?
    ''', (invitation_id, org_id))


def delete_invitations_for_musician(cursor, musicians_id: int, org_id: str = None):
    if org_id is None:
        cursor.execute('''
            DELETE FROM invitations
            WHERE musicians_id = ?
        ''', (musicians_id,))
        return

    cursor.execute('''
        DELETE FROM invitations
        WHERE musicians_id = ? AND org_id = ?
    ''', (musicians_id, org_id))


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


def update_organization_request_status(cursor, request_id: int, status: str):
    cursor.execute('''
        UPDATE organization_requests
        SET request_status = ?, responded_at = CURRENT_TIMESTAMP
        WHERE request_id = ?
    ''', (status, request_id))