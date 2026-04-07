from database.connection import get_connection
from features.invitations.invitations_model import create_invitation
from features.users.users_model import get_user_by_id, get_username_by_email
from features.services.services_model import get_service_by_id
from datetime import datetime


def send_service_invitation(sender_id, service_id, recipient_email):
    db, cursor = get_connection()
    try:
        service = get_service_by_id(cursor, service_id)
        if not service:
            return {"success": False, "message": "Service not found."}

        sender = get_user_by_id(cursor, sender_id)
        is_admin = sender and sender['role'].lower() == 'admin'
        is_leader = service['leader_id'] == sender_id

        if not (is_admin or is_leader):
            return {"success": False, "message": "Permission denied."}

        recipient_username = get_username_by_email(cursor, recipient_email)
        if not recipient_username:
            return {"success": False, "message": "Recipient user not found."}

        cursor.execute("SELECT id FROM users WHERE email = ?", (recipient_email,))
        recipient = cursor.fetchone()
        recipient_id = recipient['id']

        cursor.execute("SELECT 1 FROM invitations WHERE service_id = ? AND user_id = ?", (service_id, recipient_id))
        if cursor.fetchone():
            return {"success": False, "message": "User already invited to this service."}

        now = datetime.now()
        invitation_date = now.strftime("%Y-%m-%d")
        invitation_time = now.strftime("%H:%M")

        create_invitation(cursor, service_id, recipient_id, 'Pending', invitation_date, invitation_time)
        db.commit()

        return {"success": True, "message": f"Invitation sent to {recipient_email}."}

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
    finally:
        db.close()