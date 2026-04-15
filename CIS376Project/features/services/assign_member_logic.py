from database.connection import get_connection
from features.services.service_musicians_model import assign_musician, smart_save_musicians
from features.services.services_model import get_service_by_id
from features.users.users_model import get_user_by_id


def _validate_service_access(cursor, admin_id, service_id, org_id):
    service = get_service_by_id(cursor, service_id, org_id)
    if not service:
        return None, {"success": False, "message": "Service not found."}

    admin_user = get_user_by_id(cursor, admin_id)
    if not admin_user or admin_user['org_id'] != org_id:
        return None, {"success": False, "message": "Sender does not belong to this organization."}

    is_admin = admin_user['role'].lower() == 'admin'
    is_leader = service['leader_id'] == admin_id

    if not (is_admin or is_leader):
        return None, {"success": False, "message": "Permission denied."}

    return service, None


def add_member_to_service(admin_id, service_id, member_username, role_name, org_id, member_user_id=None, cursor=None):
    managed_connection = cursor is None
    db = None
    if managed_connection:
        db, cursor = get_connection()

    try:
        service, error = _validate_service_access(cursor, admin_id, service_id, org_id)
        if error is not None:
            return error

        member = None
        if member_user_id is not None:
            member = get_user_by_id(cursor, member_user_id)
            if member and member['org_id'] != org_id:
                member = None
        else:
            cursor.execute("SELECT id FROM users WHERE username = ? AND org_id = ?", (member_username, org_id))
            member = cursor.fetchone()

        if not member:
            return {"success": False, "message": f"User '{member_username}' not found in this organization."}

        assign_musician(cursor, service_id, member['id'], role_name, org_id)
        if managed_connection:
            db.commit()

        return {
            "success": True,
            "message": f"Added {member_username} as {role_name} to {service['service_name']}."
        }

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
    finally:
        if managed_connection and db is not None:
            db.close()


def save_members_for_service(admin_id, service_id, assignments, org_id, cursor=None):
    managed_connection = cursor is None
    db = None
    if managed_connection:
        db, cursor = get_connection()

    try:
        if admin_id not in (None, 0):
            _, error = _validate_service_access(cursor, admin_id, service_id, org_id)
            if error is not None:
                return error
        elif get_service_by_id(cursor, service_id, org_id) is None:
            return {"success": False, "message": "Service not found."}

        smart_save_musicians(cursor, service_id, assignments, org_id)
        if managed_connection:
            db.commit()

        return {
            "success": True,
            "message": "Members updated.",
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
    finally:
        if managed_connection and db is not None:
            db.close()