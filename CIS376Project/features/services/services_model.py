import sqlite3
from .standard_datetime import normalize_date, normalize_time
from features.organizations.organizations_model import sanitize_table_prefix, create_org_tables


def _tbl(org_name: str) -> str:
    return sanitize_table_prefix(org_name)


def create_service(cursor, service_name: str, service_type: str, service_date: str,
                   service_time: str, leader_id: int, org_name: str = 'default'):
    service_date = normalize_date(service_date)
    service_time = normalize_time(service_time)
    create_org_tables(cursor, org_name)
    tbl = _tbl(org_name)
    cursor.execute(f'''
    INSERT INTO "{tbl}_services" (service_name, service_type, service_date, service_time, leader_id)
    VALUES (?, ?, ?, ?, ?)
    ''', (service_name, service_type, service_date, service_time, leader_id))
    return cursor.lastrowid


def get_service_by_id(cursor, service_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        SELECT s.*, u.username AS leader_name
        FROM "{tbl}_services" s
        LEFT JOIN users u ON s.leader_id = u.id
        WHERE s.service_id = ?
        ''', (service_id,))
        return cursor.fetchone()
    except sqlite3.OperationalError:
        return None


def get_service_by_type(cursor, service_type, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        SELECT * FROM "{tbl}_services"
        WHERE service_type = ?
        ORDER BY service_date, service_time
        ''', (service_type,))
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def search_service(cursor, search_term, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        SELECT * FROM "{tbl}_services"
        WHERE service_name LIKE ?
        ORDER BY service_date, service_time
        ''', (f"%{search_term}%",))
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def list_services(cursor, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        SELECT s.*, u.username AS leader_name
        FROM "{tbl}_services" s
        LEFT JOIN users u ON s.leader_id = u.id
        ORDER BY service_date, service_time
        ''')
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def list_services_for_user(cursor, user_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        SELECT DISTINCT s.*, u.username AS leader_name
        FROM "{tbl}_services" s
        LEFT JOIN users u ON s.leader_id = u.id
        LEFT JOIN "{tbl}_service_musicians" sm ON sm.service_id = s.service_id
        WHERE ((sm.user_id = ? AND (sm.accepted IS NULL OR sm.accepted = 1)) OR s.leader_id = ?)
        ORDER BY s.service_date, s.service_time
        ''', (user_id, user_id))
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def update_service_fields(cursor, service_id: int, org_name: str = None, **fields):
    """Update arbitrary service fields, normalizing dates/times."""
    if not fields:
        return
    if 'service_date' in fields:
        fields['service_date'] = normalize_date(fields['service_date'])
    if 'service_time' in fields:
        fields['service_time'] = normalize_time(fields['service_time'])
    tbl = _tbl(org_name or 'default')
    keys = [f"{k} = ?" for k in fields]
    params = list(fields.values())
    sql = f'UPDATE "{tbl}_services" SET {", ".join(keys)} WHERE service_id = ?'
    params.append(service_id)
    try:
        cursor.execute(sql, tuple(params))
    except sqlite3.OperationalError:
        pass


def update_service(cursor, service_id, service_name=None, service_type=None, service_date=None,
                   service_time=None, leader_id=None, org_name=None):
    """Update service fields."""
    fields = {}
    if service_name is not None: fields['service_name'] = service_name
    if service_type is not None: fields['service_type'] = service_type
    if service_date is not None: fields['service_date'] = service_date
    if service_time is not None: fields['service_time'] = service_time
    if leader_id is not None: fields['leader_id'] = leader_id
    update_service_fields(cursor, service_id, org_name, **fields)
    row = get_service_by_id(cursor, service_id, org_name or 'default')
    return [row] if row else []


def delete_service(cursor, service_id: int, org_name: str = 'default'):
    """Delete a service by ID along with all dependent rows."""
    create_org_tables(cursor, org_name)
    tbl = _tbl(org_name)
    for dependent in (f'"{tbl}_invitations"', f'"{tbl}_service_songs"', f'"{tbl}_service_musicians"'):
        try:
            cursor.execute(f'DELETE FROM {dependent} WHERE service_id = ?', (service_id,))
        except sqlite3.OperationalError:
            pass
    try:
        cursor.execute(f'DELETE FROM "{tbl}_services" WHERE service_id = ?', (service_id,))
    except sqlite3.OperationalError:
        pass
