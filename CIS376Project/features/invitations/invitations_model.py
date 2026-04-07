def create_invitations_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invitations (
        invitation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        invitation_status TEXT NOT NULL DEFAULT 'Pending',
        invitation_date DATE NOT NULL,
        invitation_time TIME NOT NULL,
        org_id INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (service_id) REFERENCES services(service_id),
        FOREIGN KEY (user_id) REFERENCES users(id)
        );  
    ''')

def create_invitation(cursor, service_id: int, user_id: int, invitation_status: str, invitation_date: str, invitation_time: str, org_id: int = 1):
    cursor.execute('''
        INSERT INTO invitations (service_id, user_id, invitation_status, invitation_date, invitation_time, org_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (service_id, user_id, invitation_status, invitation_date, invitation_time, org_id))

def get_invitations_by_user(cursor, user_id: int, org_id: int = 1):
    cursor.execute('''
        SELECT i.*, s.service_name, s.service_date, s.service_time
        FROM invitations i
        JOIN services s ON i.service_id = s.service_id
        WHERE i.user_id = ? AND i.org_id = ?
        ORDER BY s.service_date, s.service_time
    ''', (user_id, org_id))
    return cursor.fetchall()

def get_invitations_by_service(cursor, service_id: int, org_id: int = 1):
    cursor.execute('''
        SELECT i.*, u.username AS user_name
        FROM invitations i
        JOIN users u ON i.user_id = u.id
        WHERE i.service_id = ? AND i.org_id = ?
        ORDER BY i.invitation_date, i.invitation_time
    ''', (service_id, org_id))
    return cursor.fetchall()

def get_accepted_invitations_by_user(cursor, user_id: int, org_id: int = 1):
    cursor.execute('''
        SELECT i.*, s.service_name, s.service_date, s.service_time
        FROM invitations i
        JOIN services s ON i.service_id = s.service_id
        WHERE i.user_id = ? AND i.invitation_status = 'Accepted' AND i.org_id = ?
        ORDER BY s.service_date, s.service_time
    ''', (user_id, org_id))
    return cursor.fetchall()

def get_declined_invitations_by_user(cursor, user_id: int, org_id: int = 1):
    cursor.execute('''
        SELECT i.*, s.service_name, s.service_date, s.service_time
        FROM invitations i
        JOIN services s ON i.service_id = s.service_id
        WHERE i.user_id = ? AND i.invitation_status = 'Declined' AND i.org_id = ?
        ORDER BY s.service_date, s.service_time
    ''', (user_id, org_id))
    return cursor.fetchall()

def get_service_attendees(cursor, service_id: int, org_id: int = 1):
    cursor.execute('''
        SELECT i.*, u.id AS user_id, u.username, u.email
        FROM invitations i
        JOIN users u ON i.user_id = u.id
        WHERE i.service_id = ? AND i.invitation_status = 'Accepted' AND i.org_id = ?
        ORDER BY u.username
    ''', (service_id, org_id))
    return cursor.fetchall()

def update_invitation_status(cursor, invitation_id: int, new_status: str):
    cursor.execute('''
        UPDATE invitations
        SET invitation_status = ?
        WHERE invitation_id = ?
    ''', (new_status, invitation_id))

def accept_invitation(cursor, invitation_id: int):
    update_invitation_status(cursor, invitation_id, 'Accepted')


def decline_invitation(cursor, invitation_id: int):
    update_invitation_status(cursor, invitation_id, 'Declined')


def delete_invitation(cursor, invitation_id: int, org_id: int = 1):
    cursor.execute('''
        DELETE FROM invitations
        WHERE invitation_id = ? AND org_id = ?
    ''', (invitation_id, org_id))