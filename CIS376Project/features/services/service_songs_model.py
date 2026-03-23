def create_service_songs_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS service_songs (
        service_song_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,
        custom_key TEXT,
        custom_tempo INTEGER,
        song_order INTEGER,
        FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
        FOREIGN KEY (song_id) REFERENCES songs(song_id) ON DELETE CASCADE
        );
    ''')

def add_song_to_service(cursor, service_id: int, song_id: int, custom_key=None, custom_tempo=None, song_order=None):
    cursor.execute('''
    INSERT INTO service_songs (service_id, song_id, custom_key, custom_tempo, song_order)
    VALUES (?, ?, ?, ?, ?)
    ''', (service_id, song_id, custom_key, custom_tempo, song_order))
    return cursor.lastrowid

def get_songs_for_service(cursor, service_id: int):
    cursor.execute('''
    SELECT ss.service_song_id,
           ss.service_id,
           ss.song_id,
           ss.song_order,
           COALESCE(ss.custom_key, s.default_key) AS song_key,
           COALESCE(ss.custom_tempo, s.default_tempo) AS song_tempo,
           s.title,
           s.artist,
           s.default_key,
           s.default_tempo,
        s.youtube_url,
        CASE WHEN s.chords_pdf IS NOT NULL THEN 1 ELSE 0 END AS has_chords_pdf,
        CASE WHEN s.lyrics_pdf IS NOT NULL THEN 1 ELSE 0 END AS has_lyrics_pdf
    FROM service_songs ss
    JOIN songs s ON ss.song_id = s.song_id
    WHERE ss.service_id = ?
    ORDER BY COALESCE(ss.song_order, 999999), ss.service_song_id ASC
    ''', (service_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def clear_songs_for_service(cursor, service_id: int):
    cursor.execute('''
    DELETE FROM service_songs
    WHERE service_id = ?
    ''', (service_id,))
