from datetime import datetime

def create_services_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        service_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_name TEXT NOT NULL,
        service_date DATE NOT NULL,
        service_time TIME NOT NULL,
        leader_id INTEGER,
        FOREIGN KEY (leader_id) REFERENCES users(user_id)
        );
    ''')

def create_service(cursor, service_name: str, service_date, service_time, leader_id: int):
   cursor.execute('''
   INSERT INTO services (service_name, service_date, service_time, leader_id)
   VALUES (?, ?, ?, ?)
   ''', (service_name, service_date, service_time, leader_id))

def format_service_datetime(service_date, service_time):  # idk if this format can be used for front end
    dt = datetime.strptime(f"{service_date} {service_time}", "%Y-%m-%d %H:%M")
    return dt.strftime("%-m/%-d/%y, %-I:%M %p")

def get_service_by_id(cursor, service_id): # how do we want to get services?
    cursor.execute('''
    SELECT * FROM services
    WHERE service_id = ?
    ''', (service_id,))
    row = cursor.fetchone()

    if not row:
        return None

    service = dict(row)
    service["formatted_time"] = format_service_datetime(
        service["service_date"], service["service_time"]
    )
    return service

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

def update_service(cursor, service_id, service_name, service_date, service_time, leader_id):
    cursor.execute('''
    UPDATE services
    SET service_name = ?, 
    service_date = ?,
    service_time = ?,
    leader_id = ?
    WHERE service_id = ?
    ''',(service_name, service_date, service_time, leader_id, service_id))

def delete_service(cursor, service_id):
    cursor.execute('''
    DELETE FROM services WHERE service_id = ?
    ''', (service_id,))
