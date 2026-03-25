import sqlite3

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
    """Add a song to a service setlist."""
    cursor.execute('''
    INSERT INTO service_songs (service_id, song_id, performance_key, performance_tempo, song_order)
    VALUES (?, ?, ?, ?, ?)
    ''', (service_id, song_id, p_key, p_tempo, order))
    return cursor.lastrowid

def get_service_setlist(cursor, service_id: int):
    cursor.execute('''
    SELECT ss.*, s.title, s.artist
    FROM service_songs ss
    JOIN songs s ON ss.song_id = s.song_id
    WHERE ss.service_id = ?
    ORDER BY ss.song_order ASC
    ''', (service_id,))
    return cursor.fetchall()

def update_service_song_fields(cursor, service_song_id: int, **fields):
    """Update arbitrary service song fields."""
    if not fields:
        return

    keys = []
    params = []
    for k, v in fields.items():
        keys.append(f"{k} = ?")
        params.append(v)

    sql = f"UPDATE service_songs SET {', '.join(keys)} WHERE service_song_id = ?"
    params.append(service_song_id)
    cursor.execute(sql, tuple(params))

def update_song_in_setlist(cursor, service_song_id: int, p_key: str, p_tempo: int, order: int, service_id):
    """Update song in setlist (legacy function)."""
    update_service_song_fields(cursor, service_song_id, performance_key=p_key, performance_tempo=p_tempo, song_order=order)
    return get_service_setlist(cursor, service_id)

def remove_song_from_service(cursor, service_song_id: int):
    cursor.execute('''
    DELETE FROM service_songs
    WHERE service_song_id = ?
    ''', (service_song_id,))