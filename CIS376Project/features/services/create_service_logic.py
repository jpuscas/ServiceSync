from database.connection import get_connection
from features.services.services_model import create_service

def create_new_service(service_name, service_type, service_date, service_time, leader_id, org_id):
    db, cursor = get_connection()

    try:
        create_service(cursor, service_name, service_type, service_date, service_time, leader_id, org_id)

        db.commit()

        return {
            "success": True,
            "message": "Service created."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating service: {e}"
        }
    finally:
        db.close()