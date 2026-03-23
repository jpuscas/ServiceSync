from database.connection import get_connection
from features.services.service_songs_model import get_service_setlist
from features.services.service_musicians_model import get_musicians_for_service

def get_full_service_details(service_id):
    db, cursor = get_connection()

    try:
        cursor.execute('''
        SELECT * FROM services 
        WHERE service_id = ?
        ''', (service_id,))
        service = cursor.fetchone()

        if not service:
            return {
                "success": False,
                "message": "Service not found"
            }

        songs = get_service_setlist(cursor, service_id)
        musicians = get_musicians_for_service(cursor, service_id)

        return {
            "success": True,
            "service": dict(service),
            "songs": [dict(s) for s in songs],
            "musicians": musicians
        }
    finally:
        db.close()