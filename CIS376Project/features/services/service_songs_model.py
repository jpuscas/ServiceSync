import sqlite3
from features.organizations.organizations_model import sanitize_table_prefix, create_org_tables


def _tbl(org_name: str) -> str:
    return sanitize_table_prefix(org_name)


def add_song_to_service(cursor, service_id: int, song_id: int, custom_key=None,
                        custom_tempo=None, song_order=None, org_name: str = 'default'):
    """Add a song to a service setlist."""
    create_org_tables(cursor, org_name)
    tbl = _tbl(org_name)
    cursor.execute(f'''
    INSERT INTO "{tbl}_service_songs" (service_id, song_id, custom_key, custom_tempo, song_order)
    VALUES (?, ?, ?, ?, ?)
    ''', (service_id, song_id, custom_key, custom_tempo, song_order))
    return cursor.lastrowid


def get_songs_for_service(cursor, service_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
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
        FROM "{tbl}_service_songs" ss
        JOIN "{tbl}_songs" s ON ss.song_id = s.song_id
        WHERE ss.service_id = ?
        ORDER BY COALESCE(ss.song_order, 999999), ss.service_song_id ASC
        ''', (service_id,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def get_service_setlist(cursor, service_id: int, org_name: str = 'default'):
    """Alias for get_songs_for_service (kept for backward compatibility)."""
    return get_songs_for_service(cursor, service_id, org_name)


def update_song_in_setlist(cursor, service_song_id: int, custom_key, custom_tempo,
                           song_order, service_id, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        UPDATE "{tbl}_service_songs"
        SET custom_key = ?, custom_tempo = ?, song_order = ?
        WHERE service_song_id = ? AND service_id = ?
        ''', (custom_key, custom_tempo, song_order, service_song_id, service_id))
    except sqlite3.OperationalError:
        pass
    return get_songs_for_service(cursor, service_id, org_name)


def remove_song_from_service(cursor, service_song_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        DELETE FROM "{tbl}_service_songs"
        WHERE service_song_id = ?
        ''', (service_song_id,))
    except sqlite3.OperationalError:
        pass


def clear_songs_for_service(cursor, service_id: int, org_name: str = 'default'):
    tbl = _tbl(org_name)
    try:
        cursor.execute(f'''
        DELETE FROM "{tbl}_service_songs"
        WHERE service_id = ?
        ''', (service_id,))
    except sqlite3.OperationalError:
        pass
