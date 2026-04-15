from database.connection import get_connection
from features.services.services_model import create_service

def create_new_service(service_name, service_type, service_date, service_time, leader_id, org_id, cursor=None):
    managed_connection = cursor is None
    db = None
    if managed_connection:
        db, cursor = get_connection()

    try:
        service_id = create_service(cursor, service_name, service_type, service_date, service_time, leader_id, org_id)

        if managed_connection:
            db.commit()

        return {
            "success": True,
            "message": "Service created.",
            "service_id": service_id,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating service: {e}",
            "service_id": None,
        }
    finally:
        if managed_connection and db is not None:
            db.close()