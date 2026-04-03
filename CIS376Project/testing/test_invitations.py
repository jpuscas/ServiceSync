from database.connection import get_connection
from database.schema import create_database
from features.users import create_user
from features.services import create_service
from features.invitations import (create_invitation,
                                   get_invitations_by_user, get_invitations_by_service,  
                                   update_invitation_status, delete_invitation)


def setup_db():
    db, cursor = get_connection(':memory:')

    create_database(cursor)

    db.commit()
    return db, cursor

def test_valid_invitation():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    create_invitation(cursor, 1, 1, 'Pending', '3/1/2026', '10:00 AM')
    db.commit()

    invitations = get_invitations_by_user(cursor, 1)
    assert len(invitations) == 1
    assert invitations[0]['invitation_status'] == 'Pending'
    assert invitations[0]['service_name'] == 'Sunday Worship'

def test_get_invitations_by_service():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    create_invitation(cursor, 1, 1, 'Pending', '3/1/2026', '10:00 AM')
    db.commit()

    invitations = get_invitations_by_service(cursor, 1)
    assert len(invitations) == 1
    assert invitations[0]['invitation_status'] == 'Pending'
    assert invitations[0]['user_name'] == 'user1'

def test_update_invitation_status():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    create_invitation(cursor, 1, 1, 'Pending', '3/1/2026', '10:00 AM')
    db.commit()

    invitations = get_invitations_by_user(cursor, 1)
    invitation_id = invitations[0]['invitation_id']
    update_invitation_status(cursor, invitation_id, 'Accepted')
    db.commit()

    updated_invitations = get_invitations_by_user(cursor, 1)
    assert updated_invitations[0]['invitation_status'] == 'Accepted'

def test_delete_invitation():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    create_invitation(cursor, 1, 1, 'Pending', '3/1/2026', '10:00 AM')
    db.commit()

    invitations = get_invitations_by_user(cursor, 1)
    invitation_id = invitations[0]['invitation_id']
    delete_invitation(cursor, invitation_id)
    db.commit()

    deleted_invitations = get_invitations_by_user(cursor, 1)
    assert len(deleted_invitations) == 0