def create_musicians_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS service_musicians (
        musicians_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL, 
        user_id INTEGER NOT NULL,
        instrument TEXT NOT NULL,
        
        FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        );
    ''')

def assign_musician(cursor, service_id: int, user_id: int, instrument: str):
    cursor.execute('''
    INSERT INTO service_musicians (service_id, user_id, instrument)
    VALUES (?, ?, ?)
    ''', (service_id, user_id, instrument))

    return cursor.lastrowid #assignment_id

def get_musicians_for_service(cursor, assignment_id: int):
    cursor.execute('''
    SELECT sm.musicians_id, sm.service_id, sm.instrument, u.username
    FROM service_musicians sm
    JOIN users u ON sm.user_id = u.id
    WHERE sm.service_id = ?
    ''', (assignment_id,))
    rows = cursor.fetchall()
    print([dict(row) for row in rows])

def get_musicians_assignment(cursor, assignment_id: int):
    cursor.execute('''
    SELECT musicians_id, service_id, user_id, instrument
    FROM service_musicians
    WHERE musicians_id = ?
    ''', (assignment_id,))

    return cursor.fetchone()

def get_instrument(cursor, service_id: int, instrument: str):
    cursor.execute('''
        SELECT user_id
        FROM service_musicians
        WHERE service_id = ? AND instrument = ?
    ''', (service_id, instrument))

    return cursor.fetchall()

def update_musician(cursor, assignment_id: int, instrument: str):
    cursor.execute('''
    UPDATE service_musicians
    SET instrument = ?
    WHERE id = ?
    ''', (instrument, assignment_id))

    return get_musicians_assignment(cursor, assignment_id)

def delete_musician(cursor, assignment_id: int):
    cursor.execute('''
    DELETE FROM service_musicians
    WHERE id = ?
    ''', (assignment_id,))