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
   INSERT INTO services (name, date, time, leader_id)
   VALUES (?, ?, ?, ?)
   ''', (service_name, service_date, service_time, leader_id))

def get_service_by_id(cursor, service_id): # how do we want to get services?
    cursor.execute('''
    SELECT * FROM services
    WHERE service_id = ?
    ''', (service_id,))
    row = cursor.fetchone()
    return row if row else None

def search_service(cursor, search_term):
    cursor.execute('''
    SELECT * FROM services
    WHERE service_name LIKE ?
    ''', (f"%{search_term}%",))

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
