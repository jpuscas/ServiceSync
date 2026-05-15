from database.connection import get_connection
from features.songs.songs_model import list_songs, search_song

def perform_song_search(query, org_name, cursor=None):
    managed_connection = cursor is None
    db = None
    if managed_connection:
        db, cursor = get_connection()

    try:
        query = (query or '').strip()
        results = search_song(cursor, query, org_name) if query else list_songs(cursor, org_name)

        song_list = []
        for row in results:
            song_list.append({
                "song_id": row['song_id'],
                "title": row['title'],
                "artist": row['artist'],
                "default_key": row['default_key'],
                "default_tempo": row['default_tempo'],
                "youtube_url": row['youtube_url'],
                "chords_pdf": row['chords_pdf'],
                "lyrics_pdf": row['lyrics_pdf']
            })

        return {
            "success": True,
            "results": song_list,
            "count": len(song_list)
        }

    except Exception as e:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "message": f"Search error: {e}"
        }
    finally:
        if managed_connection and db is not None:
            db.close()
