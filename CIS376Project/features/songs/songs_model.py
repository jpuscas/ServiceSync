import sqlite3

def create_songs_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS songs (
        song_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        default_key TEXT NOT NULL,
        default_tempo INTEGER,
        youtube_url TEXT,
        UNIQUE(title, artist)
        );
    ''')

def create_song(cursor, title: str, artist: str, default_key: str, default_tempo: int = None, youtube_url = None):
    try:
       cursor.execute('''
       INSERT INTO songs (title, artist, default_key, default_tempo, youtube_url)
       VALUES (?, ?, ?, ?, ?)
       ''', (title, artist, default_key, default_tempo, youtube_url))

       return cursor.lastrowid
    except sqlite3.IntegrityError:
       return None

def get_song_by_id(cursor, song_id):
    cursor.execute('''
    SELECT * FROM songs
    WHERE song_id = ?
    ''', (song_id,))
    row = cursor.fetchone()
    return row if row else None

def list_songs(cursor):
    cursor.execute('SELECT * FROM songs')
    rows = cursor.fetchall()
    return rows

def search_song(cursor, search_term):
    cursor.execute('''
    SELECT * FROM songs
    WHERE title LIKE ? OR artist LIKE ?
    ''', (f"%{search_term}%", f"%{search_term}%"))

    return cursor.fetchall()

def update_song(cursor, song_id, title, artist, default_key, default_tempo, youtube_url):
    cursor.execute('''
    UPDATE songs
    SET title = ?, 
    artist = ?,
    default_key = ?,
    default_tempo = ?,
    youtube_url = ?
    WHERE song_id = ?
    ''',(title, artist, default_key, default_tempo, youtube_url, song_id))

def delete_song(cursor, song_id: int):
    cursor.execute('''
    DELETE FROM songs WHERE song_id = ?
    ''', (song_id,))