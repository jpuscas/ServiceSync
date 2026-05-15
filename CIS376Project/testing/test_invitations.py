from database.connection import get_connection
from database.schema import create_database
from features.users import create_user
from features.services import create_service
from features.invitations import (
    create_invitation,
    get_invitations_by_user,
    get_invitations_by_service,
    get_invitation_by_musicians_id,
    update_invitation_status,
    accept_invitation,
    decline_invitation,
    get_accepted_invitations_by_user,
    get_declined_invitations_by_user,
    get_service_attendees,
    delete_invitation,
)


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

    create_invitation(cursor, 1, 1, 'Pending', '3/1/2026', '10:00 AM', musicians_id=11, instrument='Guitar')
    db.commit()

    invitations = get_invitations_by_user(cursor, 1, 'default')
    assert len(invitations) == 1
    assert invitations[0]['invitation_status'] == 'Pending'
    assert invitations[0]['service_name'] == 'Sunday Worship'
    assert invitations[0]['instrument'] == 'Guitar'

def test_get_invitations_by_service():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    create_invitation(cursor, 1, 1, 'Pending', '3/1/2026', '10:00 AM', musicians_id=12, instrument='Drums')
    db.commit()

    invitations = get_invitations_by_service(cursor, 1, 'default')
    assert len(invitations) == 1
    assert invitations[0]['invitation_status'] == 'Pending'
    assert invitations[0]['user_name'] == 'user1'
    assert invitations[0]['instrument'] == 'Drums'


def test_accept_decline_and_service_attendees():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_user(cursor, 'user2', 'user2@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship', '3/8/2026', '9:00 AM', 1)
    db.commit()

    create_invitation(cursor, 1, 1, 'Pending', '3/1/2026', '10:00 AM', musicians_id=21, instrument='Singer')
    create_invitation(cursor, 1, 2, 'Pending', '3/1/2026', '10:00 AM', musicians_id=22, instrument='Piano')
    db.commit()

    invitations_before = get_invitations_by_service(cursor, 1, 'default')
    assert len(invitations_before) == 2

    accept_invitation(cursor, invitations_before[0]['invitation_id'], 'default')
    decline_invitation(cursor, invitations_before[1]['invitation_id'], 'default')
    db.commit()

    accepted = get_accepted_invitations_by_user(cursor, 1, 'default')
    declined = get_declined_invitations_by_user(cursor, 2, 'default')
    assert len(accepted) == 1
    assert len(declined) == 1

    attendees = get_service_attendees(cursor, 1, 'default')
    assert len(attendees) == 1
    assert attendees[0]['username'] == 'user1'
    assert attendees[0]['instrument'] == 'Singer'


def test_get_invitation_by_musicians_id():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship', '3/8/2026', '9:00 AM', 1)
    db.commit()

    create_invitation(cursor, 1, 1, 'Pending', '3/1/2026', '10:00 AM', musicians_id=31, instrument='Bass')
    db.commit()

    invitation = get_invitation_by_musicians_id(cursor, 31, 'default')
    assert invitation['service_name'] == 'Sunday Worship'
    assert invitation['instrument'] == 'Bass'


def test_update_invitation_status():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    create_invitation(cursor, 1, 1, 'Pending', '3/1/2026', '10:00 AM', musicians_id=41)
    db.commit()

    invitations = get_invitations_by_user(cursor, 1, 'default')
    invitation_id = invitations[0]['invitation_id']
    update_invitation_status(cursor, invitation_id, 'Accepted', 'default')
    db.commit()

    updated_invitations = get_invitations_by_user(cursor, 1, 'default')
    assert updated_invitations[0]['invitation_status'] == 'Accepted'

def test_delete_invitation():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_service(cursor, 'Sunday Worship', 'Worship',
                   '3/8/2026', '9:00 AM', 1)
    db.commit()

    create_invitation(cursor, 1, 1, 'Pending', '3/1/2026', '10:00 AM', musicians_id=51)
    db.commit()

    invitations = get_invitations_by_user(cursor, 1, 'default')
    invitation_id = invitations[0]['invitation_id']
    delete_invitation(cursor, invitation_id)
    db.commit()

    deleted_invitations = get_invitations_by_user(cursor, 1, 'default')
    assert len(deleted_invitations) == 0