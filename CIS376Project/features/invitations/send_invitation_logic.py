from database.connection import get_connection
from features.invitations.invitations_model import create_invitation, get_invitation_by_musicians_id, get_invitation_by_service_user, update_invitation_details
from features.users.users_model import get_user_by_id, user_belongs_to_org
from features.services.services_model import get_service_by_id
from datetime import datetime
from features.email.EmailNotif import send_email
from features.SMS.TextNotif import send_text


def send_service_invitation(sender_id, service_id, recipient_email=None, org_id='default', recipient_user_id=None, musicians_id=None, instrument=None, cursor=None, force_resend=False):
    managed_connection = cursor is None
    db = None
    if managed_connection:
        db, cursor = get_connection()

    try:
        service = get_service_by_id(cursor, service_id, org_id)
        if not service:
            return {"success": False, "message": "Service not found"}

        sender = get_user_by_id(cursor, sender_id)
        if not sender or not user_belongs_to_org(sender, org_id):
            return {"success": False, "message": "Sender does not belong to this organization."}

        is_admin = sender['role'].lower() == 'admin'
        is_leader = service['leader_id'] == sender_id

        if not (is_admin or is_leader):
            return {"success": False, "message": "Permission denied."}

        recipient = None
        if recipient_user_id is not None:
            recipient = get_user_by_id(cursor, recipient_user_id)
            if recipient and not user_belongs_to_org(recipient, org_id):
                recipient = None
        elif recipient_email:
            cursor.execute("SELECT id, username, email, org_id FROM users WHERE email = ? AND org_id = ?", (recipient_email, org_id))
            recipient = cursor.fetchone()

        if not recipient:
            return {"success": False, "message": "Recipient user not found in this organization."}

        recipient_id = recipient['id']
        if recipient_email is None:
            recipient_keys = recipient.keys() if hasattr(recipient, 'keys') else []
            if 'email' in recipient_keys:
                recipient_email = recipient['email']
            elif 'username' in recipient_keys:
                recipient_email = recipient['username']
            else:
                recipient_email = str(recipient_id)

        existing_invitation = get_invitation_by_service_user(cursor, service_id, recipient_id, org_id)

        if existing_invitation and not force_resend:
            return {"success": True, "message": "Invitation already exists.", "invitation_id": existing_invitation['invitation_id']}

        now = datetime.now()
        invitation_date = now.strftime("%Y-%m-%d")
        invitation_time = now.strftime("%H:%M")

        if existing_invitation:
            update_invitation_details(
                cursor,
                existing_invitation['invitation_id'],
                'Pending',
                invitation_date,
                invitation_time,
                org_id,
                musicians_id=musicians_id,
                instrument=instrument,
            )
            invitation_id = existing_invitation['invitation_id']
        else:
            create_invitation(
                cursor,
                service_id,
                recipient_id,
                'Pending',
                invitation_date,
                invitation_time,
                org_id,
                musicians_id=musicians_id,
                instrument=instrument,
            )
            invitation_id = cursor.lastrowid

        if managed_connection:
            db.commit()

        try:
            Message = (
                f"You have been requested to join a service! \n"
                f"Date: {service['service_date']}\n"
                f"Time: {service['service_time']}\n"
                f"Role: {instrument}\n"
                f"Please log into ServiceSync to ACCEPT or DENY the request.\n"
            )
            send_email(recipient_email, Message)
        except Exception as email_error:
            print(f"Failed to send service invitation email: {email_error}")

        recipient_row = get_user_by_id(cursor, recipient_id)
        if recipient_row and recipient_row.get('phone') and recipient_row.get('carrier'):
            try:
                send_text(
                    recipient_row['phone'],
                    recipient_row['carrier'],
                    f"You have a new service invitation for {service['service_name']}."
                )
            except Exception as e:
                print(f"Failed to send text notification: {e}")

        return {"success": True, "message": f"Invitation sent to {recipient_email}.", "invitation_id": invitation_id}

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
    finally:
        if managed_connection and db is not None:
            db.close()