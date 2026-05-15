from database.connection import get_connection
from features.services.service_musicians_model import assign_musician, smart_save_musicians
from features.services.services_model import get_service_by_id
from features.users.users_model import get_user_by_id, get_user_by_username
from features.organizations.organizations_model import user_in_org, get_org_member_role


def _validate_service_access(cursor, admin_id, service_id, org_name):
    service = get_service_by_id(cursor, service_id, org_name)
    if not service:
        return None, {"success": False, "message": "Service not found."}

    admin_user = get_user_by_id(cursor, admin_id)
    if not admin_user or not user_in_org(cursor, admin_id, org_name):
        return None, {"success": False, "message": "Sender does not belong to this organization."}

    is_leader = get_org_member_role(cursor, org_name, admin_id) == 'leader' or service['leader_id'] == admin_id

    if not is_leader:
        return None, {"success": False, "message": "Permission denied."}

    return service, None


def _validate_unique_assignments(assignments):
    seen_user_ids = set()

    for assignment in assignments:
        user_id = assignment.get('user_id')
        if user_id in (None, ''):
            continue

        normalized_user_id = int(user_id)
        if normalized_user_id in seen_user_ids:
            return {
                "success": False,
                "message": "That person is already assigned to this service. Remove them from the service first before requesting them again."
            }
        seen_user_ids.add(normalized_user_id)

    return {"success": True}


def add_member_to_service(admin_id, service_id, member_username, role_name, org_name, member_user_id=None, cursor=None):
    managed_connection = cursor is None
    db = None
    if managed_connection:
        db, cursor = get_connection()

    try:
        service, error = _validate_service_access(cursor, admin_id, service_id, org_name)
        if error is not None:
            return error

        member = None
        if member_user_id is not None:
            member = get_user_by_id(cursor, member_user_id)
            if member and not user_in_org(cursor, member['id'], org_name):
                member = None
        else:
            member = get_user_by_username(cursor, member_username)
            if member and not user_in_org(cursor, member['id'], org_name):
                member = None

        if not member:
            return {"success": False, "message": f"User '{member_username}' not found in this organization."}

        assign_musician(cursor, service_id, member['id'], role_name, org_name)
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


def save_members_for_service(admin_id, service_id, assignments, org_name, cursor=None):
    managed_connection = cursor is None
    db = None
    if managed_connection:
        db, cursor = get_connection()

    try:
        if admin_id not in (None, 0):
            _, error = _validate_service_access(cursor, admin_id, service_id, org_name)
            if error is not None:
                return error
        elif get_service_by_id(cursor, service_id, org_name) is None:
            return {"success": False, "message": "Service not found."}

        validation_result = _validate_unique_assignments(assignments)
        if not validation_result['success']:
            return validation_result

        smart_save_musicians(cursor, service_id, assignments, org_name)
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