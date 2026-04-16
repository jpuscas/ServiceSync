from database.connection import get_connection
from features.services.service_songs_model import add_song_to_service, clear_songs_for_service

def add_song_to_setlist(service_id, song_id, p_key, p_tempo, order, org_id, cursor=None):
    managed_connection = cursor is None
    db = None
    if managed_connection:
        db, cursor = get_connection()

    try:
        new_id = add_song_to_service(cursor, service_id, song_id, p_key, p_tempo, order, org_id)
        if managed_connection:
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
        if managed_connection and db is not None:
            db.close()


def replace_service_setlist(service_id, song_ids, org_id, cursor=None):
    managed_connection = cursor is None
    db = None
    if managed_connection:
        db, cursor = get_connection()

    try:
        clear_songs_for_service(cursor, service_id, org_id)
        created_ids = []
        for index, song_id in enumerate(song_ids, start=1):
            result = add_song_to_setlist(service_id, song_id, None, None, index, org_id, cursor=cursor)
            if not result['success']:
                return result
            created_ids.append(result['service_song_id'])

        if managed_connection:
            db.commit()

        return {
            "success": True,
            "message": "Setlist updated.",
            "service_song_ids": created_ids,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating setlist: {e}",
            "service_song_ids": [],
        }
    finally:
        if managed_connection and db is not None:
            db.close()