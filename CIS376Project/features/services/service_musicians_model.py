from features.invitations.invitations_model import delete_invitations_for_musician


def create_musicians_table(cursor):
    """Create the service_musicians table."""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS service_musicians (
        musicians_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        instrument TEXT NOT NULL,
        org_id TEXT NOT NULL,
        accepted INTEGER DEFAULT NULL,
        UNIQUE(service_id, user_id, instrument, org_id),


        FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    ''')

def assign_musician(cursor, service_id: int, user_id: int, instrument: str, org_id: str = 'default'):
    """Assign a musician to a service."""
    cursor.execute('''
    INSERT INTO service_musicians (service_id, user_id, instrument, org_id)
    VALUES (?, ?, ?, ?)
    ''', (service_id, user_id, instrument, org_id))

    return cursor.lastrowid  # assignment_id

def get_musicians_for_service(cursor, service_id: int, org_id: str = 'default'):
    cursor.execute('''
    SELECT sm.musicians_id, sm.service_id, sm.user_id, sm.instrument, sm.accepted,
           u.username, u.first_name, u.last_name
    FROM service_musicians sm
    JOIN users u ON sm.user_id = u.id
    WHERE sm.service_id = ? AND sm.org_id = ?
    ORDER BY CASE WHEN sm.accepted = 1 THEN 0 WHEN sm.accepted IS NULL THEN 1 ELSE 2 END,
             sm.musicians_id ASC
    ''', (service_id, org_id))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

#view all assignments for one musician
def get_musicians_assignment(cursor, user_id: int, org_id: str = 'default'):
    cursor.execute('''
    SELECT sm.musicians_id, sm.service_id, sm.instrument, s.service_name, s.service_date
    FROM service_musicians sm
    JOIN services s ON sm.service_id = s.service_id
    WHERE sm.user_id = ? AND sm.org_id = ?
    ORDER BY s.service_date ASC
    ''', (user_id, org_id))

    return cursor.fetchall()

def get_instrument(cursor, service_id: int, instrument: str, org_id: str = 'default'):
    cursor.execute('''
    SELECT user_id
    FROM service_musicians
    WHERE service_id = ? AND instrument = ? AND org_id = ?
    ''', (service_id, instrument, org_id))
    return cursor.fetchall()

def update_musician_fields(cursor, musicians_id: int, org_id: str = None, **fields):
    """Update arbitrary musician fields."""
    if not fields:
        return

    keys = []
    params = []
    for k, v in fields.items():
        keys.append(f"{k} = ?")
        params.append(v)

    sql = f"UPDATE service_musicians SET {', '.join(keys)} WHERE musicians_id = ?"
    params.append(musicians_id)
    if org_id is not None:
        sql += ' AND org_id = ?'
        params.append(org_id)

    cursor.execute(sql, tuple(params))

def update_musician(cursor, musicians_id: int, instrument: str, org_id: str = 'default'):
    """Update musician instrument (legacy function)."""
    update_musician_fields(cursor, musicians_id, org_id, instrument=instrument)
    updated_row = get_musician_row(cursor, musicians_id, org_id)
    if not updated_row:
        return []

    return get_musicians_assignment(cursor, int(updated_row['user_id']), org_id)

def delete_musician(cursor, musicians_id: int, org_id: str = 'default'):
    """Delete a musician assignment by ID."""
    delete_invitations_for_musician(cursor, musicians_id, org_id)
    cursor.execute('''
    DELETE FROM service_musicians
    WHERE musicians_id = ? AND org_id = ?
    ''', (musicians_id, org_id))

def clear_musicians_for_service(cursor, service_id: int, org_id: str = 'default'):
    cursor.execute('''
    DELETE FROM invitations
    WHERE service_id = ? AND org_id = ? AND musicians_id IS NOT NULL
    ''', (service_id, org_id))
    cursor.execute('''
    DELETE FROM service_musicians
    WHERE service_id = ? AND org_id = ?
    ''', (service_id, org_id))

def smart_save_musicians(cursor, service_id: int, assignments: list, org_id: str):
    """Sync musicians for a service while preserving accepted/denied responses."""
    cursor.execute(
        'SELECT musicians_id, user_id, instrument, accepted FROM service_musicians WHERE service_id = ? AND org_id = ?',
        (service_id, org_id)
    )
    existing = {(row['user_id'], row['instrument']): dict(row) for row in cursor.fetchall()}

    new_set = {(int(a['user_id']), a['role']): a for a in assignments}

    # Delete active rows (NULL or accepted=1) that are no longer in new assignments
    for (uid, instr), row in list(existing.items()):
        if row['accepted'] != 0:  # NULL or 1 are manageable
            if (uid, instr) not in new_set:
                delete_invitations_for_musician(cursor, row['musicians_id'], org_id)
                cursor.execute('DELETE FROM service_musicians WHERE musicians_id = ? AND org_id = ?', (row['musicians_id'], org_id))

    # Insert new rows that don't already exist
    for (uid, instr), assignment in new_set.items():
        if (uid, instr) not in existing:
            cursor.execute(
                'INSERT INTO service_musicians (service_id, user_id, instrument, org_id) VALUES (?, ?, ?, ?)',
                (service_id, uid, instr, org_id)
            )

def get_requests_for_user(cursor, user_id: int, org_id: str):
    """Return all service requests for a user, pending first then denied then accepted."""
    cursor.execute('''
    SELECT sm.musicians_id, sm.service_id, sm.instrument, sm.accepted,
           s.service_date, s.service_time, s.service_name
    FROM service_musicians sm
    JOIN services s ON sm.service_id = s.service_id
    WHERE sm.user_id = ? AND sm.org_id = ?
    ORDER BY CASE WHEN sm.accepted IS NULL THEN 0 WHEN sm.accepted = 0 THEN 1 ELSE 2 END,
             s.service_date ASC
    ''', (user_id, org_id))
    return [dict(row) for row in cursor.fetchall()]

def update_musician_response(cursor, musicians_id: int, accepted: int, org_id: str = None):
    if org_id is None:
        cursor.execute('''
        UPDATE service_musicians SET accepted = ? WHERE musicians_id = ?
        ''', (accepted, musicians_id))
    else:
        cursor.execute('''
        UPDATE service_musicians SET accepted = ? WHERE musicians_id = ? AND org_id = ?
        ''', (accepted, musicians_id, org_id))

def reset_musician_request(cursor, musicians_id: int, org_id: str = None):
    if org_id is None:
        cursor.execute('''
        UPDATE service_musicians SET accepted = NULL WHERE musicians_id = ?
        ''', (musicians_id,))
    else:
        cursor.execute('''
        UPDATE service_musicians SET accepted = NULL WHERE musicians_id = ? AND org_id = ?
        ''', (musicians_id, org_id))

def get_musician_row(cursor, musicians_id: int, org_id: str = None):
    query = '''
    SELECT sm.*, u.username, u.first_name, u.last_name
    FROM service_musicians sm
    JOIN users u ON sm.user_id = u.id
    WHERE sm.musicians_id = ?
    '''
    params = [musicians_id]
    if org_id is not None:
        query += ' AND sm.org_id = ?'
        params.append(org_id)

    cursor.execute(query, tuple(params))
    row = cursor.fetchone()
    return dict(row) if row else None
