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

def create_service(cursor, service_name: str, service_type, service_date, service_time, leader_id: int):

    service_date = normalize_date(service_date)
    service_time = normalize_time(service_time)

    cursor.execute('''
    INSERT INTO services (service_name, service_type, service_date, service_time, leader_id)
    VALUES (?, ?, ?, ?, ?)
    ''', (service_name, service_type, service_date, service_time, leader_id))

    return cursor.lastrowid

def get_service_by_id(cursor, service_id: int):
    cursor.execute('''
    SELECT s.*, u.username AS leader_name
    FROM services s
    LEFT JOIN users u ON s.leader_id = u.id
    WHERE s.service_id = ?
    ''', (service_id,))
    return cursor.fetchone()

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

def list_services_for_user(cursor, user_id: int):
    cursor.execute('''
    SELECT DISTINCT s.*, u.username AS leader_name
    FROM services s
    LEFT JOIN users u ON s.leader_id = u.id
    LEFT JOIN service_musicians sm ON sm.service_id = s.service_id
    WHERE (sm.user_id = ? AND (sm.accepted IS NULL OR sm.accepted = 1))
       OR s.leader_id = ?
    ORDER BY s.service_date, s.service_time
    ''', (user_id, user_id))
    return cursor.fetchall()

def update_service(cursor, service_id, service_name, service_type, service_date, service_time, leader_id):

    service_date = normalize_date(service_date)
    service_time = normalize_time(service_time)

    cursor.execute('''
    UPDATE services
    SET service_name = ?,
    service_type = ?, 
    service_date = ?,
    service_time = ?,
    leader_id = ?
    WHERE service_id = ?
    ''',(service_name, service_type, service_date, service_time, leader_id, service_id))

    row = get_service_by_id(cursor, service_id)
    return [row] if row else []

def delete_service(cursor, service_id: int):
    cursor.execute('''
    DELETE FROM services 
    WHERE service_id = ?
    ''', (service_id,))
