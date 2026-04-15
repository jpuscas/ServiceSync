import sqlite3

def create_service_songs_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS service_songs (
        service_song_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,
        custom_key TEXT,
        custom_tempo INTEGER,
        song_order INTEGER,
        org_id TEXT NOT NULL DEFAULT 'default',

        UNIQUE(service_id, song_id, org_id),

        FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
        FOREIGN KEY (song_id) REFERENCES songs(song_id) ON DELETE CASCADE
        );
    ''')

def add_song_to_service(cursor, service_id: int, song_id: int, custom_key=None, custom_tempo=None, song_order=None, org_id: str = 'default'):
    """Add a song to a service setlist."""
    cursor.execute('''
    INSERT INTO service_songs (service_id, song_id, custom_key, custom_tempo, song_order, org_id)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (service_id, song_id, custom_key, custom_tempo, song_order, org_id))
    return cursor.lastrowid

def get_songs_for_service(cursor, service_id: int, org_id: str = 'default'):
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
    WHERE ss.service_id = ? AND ss.org_id = ?
    ORDER BY COALESCE(ss.song_order, 999999), ss.service_song_id ASC
    ''', (service_id, org_id))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_service_setlist(cursor, service_id: int, org_id: str = 'default'):
    # Alias for get_songs_for_service, kept for backward compatibility with existing tests.
    return get_songs_for_service(cursor, service_id, org_id)

def update_song_in_setlist(cursor, service_song_id: int, custom_key, custom_tempo, song_order, service_id, org_id: str = 'default'):
    cursor.execute('''
    UPDATE service_songs
    SET custom_key = ?, custom_tempo = ?, song_order = ?
    WHERE service_song_id = ? AND service_id = ? AND org_id = ?
    ''', (custom_key, custom_tempo, song_order, service_song_id, service_id, org_id))
    return get_songs_for_service(cursor, service_id, org_id)

def remove_song_from_service(cursor, service_song_id: int, org_id: str = 'default'):
    cursor.execute('''
    DELETE FROM service_songs
    WHERE service_song_id = ? AND org_id = ?
    ''', (service_song_id, org_id))

def clear_songs_for_service(cursor, service_id: int, org_id: str = 'default'):
    cursor.execute('''
    DELETE FROM service_songs
    WHERE service_id = ? AND org_id = ?
    ''', (service_id, org_id))
