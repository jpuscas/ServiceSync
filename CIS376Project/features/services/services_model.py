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
        FOREIGN KEY (leader_id) REFERENCES users(user_id)
        );
    ''')

def create_service(cursor, service_name: str, service_type, service_date, service_time, leader_id: int):

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
    ''', (service_type,))
    row = cursor.fetchone()
    return row if row else None

def search_service(cursor, search_term):
    cursor.execute('''
    SELECT * FROM services
    WHERE service_name LIKE ?
    ''', (f"%{search_term}%",))
    return cursor.fetchall()

def list_services(cursor):
    cursor.execute('''
    SELECT s.*, u.username AS leader_name
    FROM services s
    LEFT JOIN users u ON s.leader_id = u.user_id
    ORDER BY service_date, service_time
    ''')
    return cursor.fetchall()

def update_service(cursor, service_id, service_type, service_name, service_date, service_time, leader_id):
    cursor.execute('''
    UPDATE services
    SET service_name = ?,
    service_type = ?, 
    service_date = ?,
    service_time = ?,
    leader_id = ?
    WHERE service_id = ?
    ''',(service_name, service_type, service_date, service_time, leader_id, service_id))

def delete_service(cursor, service_id):
    cursor.execute('''
    DELETE FROM services WHERE service_id = ?
    ''', (service_id,))
