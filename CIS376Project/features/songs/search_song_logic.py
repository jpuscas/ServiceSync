from database.connection import get_connection
from features.songs.songs_model import search_song

def perform_song_search(query):
    db = get_connection()
    cursor = db.cursor()

    try:
        results = search_song(cursor, query)

        song_list = []
        for row in results:
            song_list.append({
                "id": row['song_id'],
                "title": row['title'],
                "artist": row['artist'],
                "key": row['default_key'],
                "tempo": row['default_tempo'],
                "youtube_url": row['youtube_url']
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
        db.close()
