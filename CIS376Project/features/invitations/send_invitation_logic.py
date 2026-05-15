from database.connection import get_connection
from features.invitations.invitations_model import create_invitation, get_invitation_by_musicians_id, get_invitation_by_service_user, update_invitation_details
from features.users.users_model import get_user_by_id
from features.organizations.organizations_model import user_in_org, get_org_member_role
from features.services.services_model import get_service_by_id
from datetime import datetime
from features.email.EmailNotif import send_email
from features.SMS.TextNotif import send_text


def _send_sms_notification(recipient_row, message_text):
    if not recipient_row:
        return None

    phone = recipient_row['phone'] if 'phone' in recipient_row.keys() else None
    carrier = recipient_row['carrier'] if 'carrier' in recipient_row.keys() else None
    username = recipient_row['username'] if 'username' in recipient_row.keys() else 'the recipient'

    if not phone or not carrier:
        return None

    try:
        send_text(
            phone,
            carrier,
            message_text,
        )
        return None
    except Exception as error:
        return f"Text notification could not be sent to {username}: {error}"


def _build_service_invitation_message(service, instrument):
    role_text = instrument or 'Unassigned'
    return (
        f"You have been requested to join a service!\n"
        f"Service: {service['service_name']}\n"
        f"Date: {service['service_date']}\n"
        f"Time: {service['service_time']}\n"
        f"Role: {role_text}\n"
    )


def send_service_invitation(sender_id, service_id, recipient_email=None, org_name='default', recipient_user_id=None, musicians_id=None, instrument=None, cursor=None, force_resend=False):
    managed_connection = cursor is None
    db = None
    if managed_connection:
        db, cursor = get_connection()

    try:
        service = get_service_by_id(cursor, service_id, org_name)
        if not service:
            return {"success": False, "message": "Service not found"}

        sender = get_user_by_id(cursor, sender_id)
        if not sender or not user_in_org(cursor, sender_id, org_name):
            return {"success": False, "message": "Sender does not belong to this organization."}

        is_leader = get_org_member_role(cursor, org_name, sender_id) == 'leader' or service['leader_id'] == sender_id

        if not is_leader:
            return {"success": False, "message": "Permission denied."}

        recipient = None
        if recipient_user_id is not None:
            recipient = get_user_by_id(cursor, recipient_user_id)
            if recipient and not user_in_org(cursor, recipient_user_id, org_name):
                recipient = None
        elif recipient_email:
            cursor.execute("SELECT id, username, email FROM users WHERE email = ?", (recipient_email,))
            candidate = cursor.fetchone()
            if candidate and user_in_org(cursor, candidate['id'], org_name):
                recipient = candidate

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

        existing_invitation = get_invitation_by_service_user(cursor, service_id, recipient_id, org_name)

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
                org_name,
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
                org_name,
                musicians_id=musicians_id,
                instrument=instrument,
            )
            invitation_id = cursor.lastrowid

        if managed_connection:
            db.commit()

        invitation_message = _build_service_invitation_message(service, instrument)

        try:
            send_email(recipient_email, invitation_message)
        except Exception as email_error:
            print(f"Failed to send service invitation email: {email_error}")

        recipient_row = get_user_by_id(cursor, recipient_id)
        sms_warning = _send_sms_notification(
            recipient_row,
            invitation_message,
        )

        result = {"success": True, "message": f"Invitation sent to {recipient_email}.", "invitation_id": invitation_id}
        if sms_warning:
            result["text_warning"] = sms_warning
        return result

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
    finally:
        if managed_connection and db is not None:
            db.close()