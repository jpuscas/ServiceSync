from database.connection import get_connection
from features.users.users_model import set_role


def has_role(user, role_name):
    if not user:
        return False

    if isinstance(user, dict):
        current_role = user.get('role', '')
    else:
        current_role = getattr(user, 'role', '')

    return str(current_role).lower() == str(role_name).lower()

def set_member_role(user_id, new_role):
    db, cursor = get_connection()

    try:
        set_role(cursor, user_id, new_role)
        db.commit()

        return {
            "success": True,
            "message": f"Role set to {new_role}."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating role: {e}"
        }
    finally:
        db.close()