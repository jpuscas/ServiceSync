from database.connection import get_connection
from features.services.service_musicians_model import assign_musician
from features.services.services_model import get_service_by_id
from features.users.users_model import get_user_by_id, get_user_by_username


def add_member_to_service(admin_id, service_id, member_username, role_name):
    db, cursor = get_connection()
    try:
        service = get_service_by_id(cursor, service_id)
        if not service:
            return {"success": False, "message": "Service not found."}

        admin_user = get_user_by_id(cursor, admin_id)
        is_admin = admin_user and admin_user['role'].lower() == 'admin'
        is_leader = service['leader_id'] == admin_id

        if not (is_admin or is_leader):
            return {"success": False, "message": "Permission denied."}

        member = get_user_by_username(cursor, member_username)
        if not member:
            return {"success": False, "message": f"User '{member_username}' not found."}

        assign_musician(cursor, service_id, member['id'], role_name)
        db.commit()

        return {
            "success": True,
            "message": f"Added {member_username} as {role_name} to {service['service_name']}."
        }

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
    finally:
        db.close()