import sqlite3
from features.organizations.organizations_model import sanitize_table_prefix, create_org_tables


def _tbl(org_name: str) -> str:
    return sanitize_table_prefix(org_name)


def assign_musician(cursor, service_id: int, user_id: int, instrument: str, org_name: str = 'default'):
    """Assign a musician to a service."""
    create_org_tables(cursor, org_name)
    tbl = _tbl(org_name)
    cursor.execute(f'''
    INSERT INTO "{tbl}_service_musicians" (service_id, user_id, instrument)
    VALUES (?, ?, ?)
    ''', (service_id, user_id, instrument))
    return cursor.lastrowid


def get_musicians_for_service(cursor, service_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        SELECT sm.musicians_id, sm.service_id, sm.user_id, sm.instrument, sm.accepted,
               u.username, u.first_name, u.last_name
        FROM "{tbl}_service_musicians" sm
        JOIN users u ON sm.user_id = u.id
        WHERE sm.service_id = ?
        ORDER BY CASE WHEN sm.accepted = 1 THEN 0 WHEN sm.accepted IS NULL THEN 1 ELSE 2 END,
                 sm.musicians_id ASC
        ''', (service_id,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def get_musicians_assignment(cursor, user_id: int, org_name: str = 'default'):
    """View all assignments for one musician."""
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        SELECT sm.musicians_id, sm.service_id, sm.instrument, s.service_name, s.service_date
        FROM "{tbl}_service_musicians" sm
        JOIN "{tbl}_services" s ON sm.service_id = s.service_id
        WHERE sm.user_id = ?
        ORDER BY s.service_date ASC
        ''', (user_id,))
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def get_instrument(cursor, service_id: int, instrument: str, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        SELECT user_id
        FROM "{tbl}_service_musicians"
        WHERE service_id = ? AND instrument = ?
        ''', (service_id, instrument))
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def update_musician_fields(cursor, musicians_id: int, org_name: str = None, **fields):
    """Update arbitrary musician fields."""
    if not fields:
        return
    tbl = _tbl(org_name or 'default')
    keys = [f"{k} = ?" for k in fields]
    params = list(fields.values())
    sql = f'UPDATE "{tbl}_service_musicians" SET {", ".join(keys)} WHERE musicians_id = ?'
    params.append(musicians_id)
    try:
        cursor.execute(sql, tuple(params))
    except sqlite3.OperationalError:
        pass


def update_musician(cursor, musicians_id: int, instrument: str, org_name: str = 'default'):
    """Update musician instrument."""
    update_musician_fields(cursor, musicians_id, org_name, instrument=instrument)
    updated_row = get_musician_row(cursor, musicians_id, org_name)
    if not updated_row:
        return []
    return get_musicians_assignment(cursor, int(updated_row['user_id']), org_name)


def _delete_invitations_for_musician(cursor, musicians_id: int, org_name: str):
    """Delete invitations linked to a musicians_id from the org's invitations table."""
    from features.invitations.invitations_model import delete_invitations_for_musician
    delete_invitations_for_musician(cursor, musicians_id, org_name)


def delete_musician(cursor, musicians_id: int, org_name: str = 'default'):
    """Delete a musician assignment by ID."""
    _delete_invitations_for_musician(cursor, musicians_id, org_name)
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        DELETE FROM "{tbl}_service_musicians"
        WHERE musicians_id = ?
        ''', (musicians_id,))
    except sqlite3.OperationalError:
        pass


def clear_musicians_for_service(cursor, service_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        DELETE FROM "{tbl}_invitations"
        WHERE service_id = ? AND musicians_id IS NOT NULL
        ''', (service_id,))
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute(f'''
        DELETE FROM "{tbl}_service_musicians"
        WHERE service_id = ?
        ''', (service_id,))
    except sqlite3.OperationalError:
        pass


def smart_save_musicians(cursor, service_id, assignments, org_name):
    """Sync musicians for a service while preserving accepted/denied responses."""
    tbl = _tbl(org_name)
    try:
        cursor.execute(
            f'SELECT musicians_id, user_id, instrument, accepted FROM "{tbl}_service_musicians" WHERE service_id = ?',
            (service_id,)
        )
        existing_rows = [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        existing_rows = []

    existing_by_user = {row['user_id']: row for row in existing_rows}
    new_user_ids = set()

    for assignment in assignments:
        user_id_raw = assignment.get('user_id')
        role_name = (assignment.get('role') or '').strip()
        if user_id_raw in (None, '') or not role_name:
            continue
        user_id = int(user_id_raw)
        new_user_ids.add(user_id)

        if user_id in existing_by_user:
            existing_row = existing_by_user[user_id]
            try:
                cursor.execute(
                    f'UPDATE "{tbl}_service_musicians" SET instrument = ? WHERE musicians_id = ?',
                    (role_name, existing_row['musicians_id'])
                )
            except sqlite3.OperationalError:
                pass
        else:
            create_org_tables(cursor, org_name)
            try:
                cursor.execute(
                    f'INSERT INTO "{tbl}_service_musicians" (service_id, user_id, instrument) VALUES (?, ?, ?)',
                    (service_id, user_id, role_name)
                )
            except sqlite3.OperationalError:
                pass

    for row in existing_rows:
        if row['user_id'] not in new_user_ids and row['accepted'] != 0:
            _delete_invitations_for_musician(cursor, row['musicians_id'], org_name)
            try:
                cursor.execute(
                    f'DELETE FROM "{tbl}_service_musicians" WHERE musicians_id = ?',
                    (row['musicians_id'],)
                )
            except sqlite3.OperationalError:
                pass


def get_requests_for_user(cursor, user_id: int, org_name: str):
    """Return all service requests for a user, pending first then denied then accepted."""
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        SELECT sm.musicians_id, sm.service_id, sm.instrument, sm.accepted,
               s.service_date, s.service_time, s.service_name
        FROM "{tbl}_service_musicians" sm
        JOIN "{tbl}_services" s ON sm.service_id = s.service_id
        WHERE sm.user_id = ?
        ORDER BY CASE WHEN sm.accepted IS NULL THEN 0 WHEN sm.accepted = 0 THEN 1 ELSE 2 END,
                 s.service_date ASC
        ''', (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def update_musician_response(cursor, musicians_id: int, accepted: int, org_name: str = None):
    if org_name is None:
        return
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        UPDATE "{tbl}_service_musicians" SET accepted = ? WHERE musicians_id = ?
        ''', (accepted, musicians_id))
    except sqlite3.OperationalError:
        pass


def reset_musician_request(cursor, musicians_id: int, org_name: str = None):
    if org_name is None:
        return
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        UPDATE "{tbl}_service_musicians" SET accepted = NULL WHERE musicians_id = ?
        ''', (musicians_id,))
    except sqlite3.OperationalError:
        pass


def get_musician_row(cursor, musicians_id: int, org_name: str = None):
    tbl = _tbl(org_name or 'default')
    try:
        cursor.execute(f'''
        SELECT sm.*, u.username, u.first_name, u.last_name
        FROM "{tbl}_service_musicians" sm
        JOIN users u ON sm.user_id = u.id
        WHERE sm.musicians_id = ?
        ''', (musicians_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.OperationalError:
        return None
