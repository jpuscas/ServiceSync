from .standard_datetime import normalize_date, normalize_time

def create_services_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        service_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_name TEXT NOT NULL,
        service_type TEXT NOT NULL,
        service_date DATE NOT NULL,
        service_time TIME NOT NULL,
        leader_id INTEGER,
        FOREIGN KEY (leader_id) REFERENCES users(id)
    );
    ''')

def create_service(cursor, service_name: str, service_type: str, service_date: str, service_time: str, leader_id: int):
    service_date = normalize_date(service_date)
    service_time = normalize_time(service_time)

    cursor.execute('''
    INSERT INTO services (service_name, service_type, service_date, service_time, leader_id)
    VALUES (?, ?, ?, ?, ?)
    ''', (service_name, service_type, service_date, service_time, leader_id))

def get_service_by_type(cursor, service_type):
    cursor.execute('''
    SELECT * FROM services
    WHERE service_type = ?
    ORDER BY service_date, service_time
    ''', (service_type,))
    return cursor.fetchall()

def search_service(cursor, search_term):
    cursor.execute('''
    SELECT * FROM services
    WHERE service_name LIKE ?
    ORDER BY service_date, service_time
    ''', (f"%{search_term}%",))
    return cursor.fetchall()

def list_services(cursor):
    cursor.execute('''
    SELECT s.*, u.username AS leader_name
    FROM services s
    LEFT JOIN users u ON s.leader_id = u.id
    ORDER BY service_date, service_time
    ''')
    return cursor.fetchall()

def update_service_fields(cursor, service_id: int, **fields):
    """Update arbitrary service fields, normalizing dates/times."""
    if not fields:
        return

    # Normalize date/time if provided
    if 'service_date' in fields:
        fields['service_date'] = normalize_date(fields['service_date'])
    if 'service_time' in fields:
        fields['service_time'] = normalize_time(fields['service_time'])

    keys = []
    params = []
    for k, v in fields.items():
        keys.append(f"{k} = ?")
        params.append(v)

    sql = f"UPDATE services SET {', '.join(keys)} WHERE service_id = ?"
    params.append(service_id)
    cursor.execute(sql, tuple(params))

def update_service(cursor, service_id, service_name=None, service_type=None, service_date=None, service_time=None, leader_id=None):
    """Update service fields (legacy function)."""
    fields = {}
    if service_name is not None: fields['service_name'] = service_name
    if service_type is not None: fields['service_type'] = service_type
    if service_date is not None: fields['service_date'] = service_date
    if service_time is not None: fields['service_time'] = service_time
    if leader_id is not None: fields['leader_id'] = leader_id
    update_service_fields(cursor, service_id, **fields)

def delete_service(cursor, service_id: int):
    """Delete a service by ID."""
    cursor.execute('''
    DELETE FROM services
    WHERE service_id = ?
    ''', (service_id,))
