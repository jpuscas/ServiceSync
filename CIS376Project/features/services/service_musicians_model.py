def create_musicians_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS service_musicians (
        musicians_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL, 
        user_id INTEGER NOT NULL,
        instrument TEXT NOT NULL,
        UNIQUE(service_id, user_id, instrument),
        
        FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    ''')

def assign_musician(cursor, service_id: int, user_id: int, instrument: str):
    cursor.execute('''
    INSERT INTO service_musicians (service_id, user_id, instrument)
    VALUES (?, ?, ?)
    ''', (service_id, user_id, instrument))

    return cursor.lastrowid #assignment_id

#view all musicians in service
def get_musicians_for_service(cursor, service_id: int):
    cursor.execute('''
    SELECT sm.musicians_id, sm.service_id, sm.user_id, sm.instrument, u.username
    FROM service_musicians sm
    JOIN users u ON sm.user_id = u.id
    WHERE sm.service_id = ?
    ''', (service_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

#view all assignments for one musician
def get_musicians_assignment(cursor, user_id: int):
    cursor.execute('''
    SELECT sm.musicians_id, sm.service_id, sm.instrument, s.service_name, s.service_date
    FROM service_musicians sm
    JOIN services s ON sm.service_id = s.service_id
    WHERE sm.user_id = ?
    ORDER BY s.service_date ASC
    ''', (user_id,))

    return cursor.fetchall()

def get_instrument(cursor, service_id: int, instrument: str):
    cursor.execute('''
        SELECT user_id
        FROM service_musicians
        WHERE service_id = ? AND instrument = ?
    ''', (service_id, instrument))
    return cursor.fetchall()

def update_musician(cursor, musicians_id: int, instrument: str):
    cursor.execute('''
    UPDATE service_musicians
    SET instrument = ?
    WHERE musicians_id = ?
    ''', (instrument, musicians_id))
    return get_musicians_assignment(cursor, musicians_id)

def delete_musician(cursor, musicians_id: int):
    cursor.execute('''
    DELETE FROM service_musicians
    WHERE musicians_id = ?
    ''', (musicians_id,))