from database.connection import get_connection
from features.services.service_songs_model import get_service_setlist
from features.services.service_musicians_model import get_musicians_for_service
from features.services.services_model import get_service_by_id

def get_full_service_details(service_id, org_id):
    db, cursor = get_connection()

    try:
        service = get_service_by_id(cursor, service_id, org_id)

        if not service:
            return {
                "success": False,
                "message": "Service not found"
            }

        songs = get_service_setlist(cursor, service_id, org_id)
        musicians = get_musicians_for_service(cursor, service_id, org_id)

        return {
            "success": True,
            "service": dict(service),
            "songs": [dict(s) for s in songs],
            "musicians": musicians
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }
    finally:
        db.close()