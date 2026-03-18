def create_service_songs_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS service_songs (
        service_song_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,
        performance_key TEXT NOT NULL,
        performance_tempo INTEGER,
        song_order INTEGER NOT NULL,
        
        UNIQUE(service_id, song_id),
        
        FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
        FOREIGN KEY (song_id) REFERENCES songs(song_id) ON DELETE CASCADE
        );    
    ''')

def add_song_to_service(cursor, service_id: int, song_id: int, p_key: str, p_tempo: int, order: int):
    cursor.execute('''
    INSERT INTO service_songs (service_id, song_id, performance_key, performance_tempo, song_order)
    VALUES (?, ?, ?, ?, ?)
    ''', (service_id, song_id, p_key, p_tempo, order))
    return cursor.lastrowid

def get_service_setlist(cursor, service_id: int):
    cursor.execute('''
    SELECT ss.*, s.title, s.artist
    FROM service_songs ss
    JOIN songs s on ss.song_id = s.song_id
    WHERE ss.service_id = ?
    ORDER by ss.song_order ASC
    ''', (service_id,))
    return cursor.fetchall()

def update_song_in_setlist(cursor, service_song_id: int, p_key: str, p_tempo: int, order: int, service_id):
    cursor.execute('''
    UPDATE service_songs
    SET performance_key = ?, performance_tempo = ?, song_order = ? 
    WHERE service_song_id = ? AND service_id = ?
    ''', (p_key, p_tempo, order, service_song_id, service_id))
    return get_service_setlist(cursor, service_id)
    #insert order is cursor, service_song_id, p_key, p_tempo, song_order, service_id

def remove_song_from_service(cursor, service_song_id: int):
    cursor.execute('''
    DELETE FROM service_songs
    WHERE service_song_id = ?
    ''', (service_song_id,))