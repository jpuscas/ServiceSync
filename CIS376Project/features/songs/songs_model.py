import sqlite3
from features.organizations.organizations_model import sanitize_table_prefix, create_org_tables


def _tbl(org_name: str) -> str:
    return f'"{sanitize_table_prefix(org_name)}_songs"'


def create_song(cursor, title: str, artist: str, default_key: str, default_tempo: int = None,
                youtube_url: str = None, chords_pdf: str = None, lyrics_pdf: str = None,
                org_name: str = 'default'):
    """Create a new song and return its ID, or None if duplicate."""
    create_org_tables(cursor, org_name)
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        INSERT INTO {tbl} (title, artist, default_key, default_tempo, youtube_url, chords_pdf, lyrics_pdf)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, artist, default_key, default_tempo, youtube_url, chords_pdf, lyrics_pdf))
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def get_song_by_id(cursor, song_id, org_name: str = 'default'):
    """Retrieve a song by ID."""
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'SELECT * FROM {tbl} WHERE song_id = ?', (song_id,))
        return cursor.fetchone()
    except sqlite3.OperationalError:
        return None


def list_songs(cursor, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'SELECT * FROM {tbl}')
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def search_song(cursor, search_term, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        SELECT * FROM {tbl}
        WHERE (title LIKE ? OR artist LIKE ?)
        ''', (f"%{search_term}%", f"%{search_term}%"))
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def update_song_fields(cursor, song_id: int, org_name: str = 'default', **fields):
    """Update arbitrary song fields."""
    if not fields:
        return
    tbl = _tbl(org_name)
    keys = [f"{k} = ?" for k in fields]
    params = list(fields.values())
    sql = f'UPDATE {tbl} SET {", ".join(keys)} WHERE song_id = ?'
    params.append(song_id)
    try:
        cursor.execute(sql, tuple(params))
    except sqlite3.OperationalError:
        pass


def update_song(cursor, song_id, title=None, artist=None, default_key=None, default_tempo=None,
                youtube_url=None, chords_pdf=None, lyrics_pdf=None, org_name: str = 'default'):
    """Update song fields."""
    fields = {}
    if title is not None: fields['title'] = title
    if artist is not None: fields['artist'] = artist
    if default_key is not None: fields['default_key'] = default_key
    if default_tempo is not None: fields['default_tempo'] = default_tempo
    if youtube_url is not None: fields['youtube_url'] = youtube_url
    if chords_pdf is not None: fields['chords_pdf'] = chords_pdf
    if lyrics_pdf is not None: fields['lyrics_pdf'] = lyrics_pdf
    update_song_fields(cursor, song_id, org_name, **fields)


def delete_song(cursor, song_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'DELETE FROM {tbl} WHERE song_id = ?', (song_id,))
    except sqlite3.OperationalError:
        pass