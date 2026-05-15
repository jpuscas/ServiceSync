from database.connection import get_connection
from features.songs.songs_model import create_song

def add_new_song(title, artist, key, org_name, tempo=None, youtube_url=None, chords_pdf=None, lyrics_pdf=None):
    db, cursor = get_connection()

    try:
        song_id = create_song(cursor, title, artist, key, tempo, youtube_url, chords_pdf, lyrics_pdf, org_name)

        db.commit()

        return {
            "success": True,
            "message": "Song added.",
            "id": song_id
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error, song not added: {e}",
            "id": None
        }
    finally:
        db.close()
