from database.connection import get_connection
from features.services.service_songs_model import add_song_to_service

def add_song_to_setlist(service_id, song_id, p_key, p_tempo, order, org_id):
    db, cursor = get_connection()

    try:
        new_id = add_song_to_service(cursor, service_id, song_id, p_key, p_tempo, order, org_id)
        db.commit()

        return {
            "success": True,
            "message": "Song added.",
            "service_song_id": new_id
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error, song not added: {e}",
            "service_song_id": None
        }

    finally:
        db.close()