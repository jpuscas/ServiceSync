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
        chords_pdf TEXT,
        lyrics_pdf TEXT,
        org_id INTEGER NOT NULL DEFAULT 1,
        UNIQUE(title, artist, org_id)
    );
    ''')

def create_song(cursor, title: str, artist: str, default_key: str, default_tempo: int = None,
                youtube_url: str = None, chords_pdf: str = None, lyrics_pdf: str = None, org_id: int = 1):
    """Create a new song and return its ID, or None if duplicate."""
    try:
        cursor.execute('''
        INSERT INTO songs (title, artist, default_key, default_tempo, youtube_url, chords_pdf, lyrics_pdf, org_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, artist, default_key, default_tempo, youtube_url, chords_pdf, lyrics_pdf, org_id))

        return cursor.lastrowid

    except sqlite3.IntegrityError:
        return None

def get_song_by_id(cursor, song_id, org_id: int = 1):
    """Retrieve a song by ID."""
    cursor.execute('''
    SELECT * FROM songs
    WHERE song_id = ? AND org_id = ?
    ''', (song_id, org_id))
    row = cursor.fetchone()
    return row if row else None

def list_songs(cursor, org_id: int = 1):
    cursor.execute('SELECT * FROM songs WHERE org_id = ?', (org_id,))
    rows = cursor.fetchall()
    return rows

def search_song(cursor, search_term, org_id: int = 1):
    cursor.execute('''
    SELECT * FROM songs
    WHERE (title LIKE ? OR artist LIKE ?) AND org_id = ?
    ''', (f"%{search_term}%", f"%{search_term}%", org_id))

    return cursor.fetchall()

def update_song_fields(cursor, song_id: int, **fields):
    """Update arbitrary song fields."""
    if not fields:
        return

    keys = []
    params = []
    for k, v in fields.items():
        keys.append(f"{k} = ?")
        params.append(v)

    sql = f"UPDATE songs SET {', '.join(keys)} WHERE song_id = ?"
    params.append(song_id)
    cursor.execute(sql, tuple(params))

def update_song(cursor, song_id, title=None, artist=None, default_key=None, default_tempo=None, youtube_url=None, chords_pdf=None, lyrics_pdf=None):
    """Update song fields (legacy function)."""
    fields = {}
    if title is not None: fields['title'] = title
    if artist is not None: fields['artist'] = artist
    if default_key is not None: fields['default_key'] = default_key
    if default_tempo is not None: fields['default_tempo'] = default_tempo
    if youtube_url is not None: fields['youtube_url'] = youtube_url
    if chords_pdf is not None: fields['chords_pdf'] = chords_pdf
    if lyrics_pdf is not None: fields['lyrics_pdf'] = lyrics_pdf
    update_song_fields(cursor, song_id, **fields)

def delete_song(cursor, song_id: int):
    cursor.execute('''
    DELETE FROM songs WHERE song_id = ?
    ''', (song_id,))