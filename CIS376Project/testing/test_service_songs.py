import pytest
import sqlite3
from database.connection import get_connection
from database.schema import create_database
from features.services.service_songs_model import add_song_to_service, get_service_setlist, update_song_in_setlist, \
    remove_song_from_service
from features.services.services_model import create_service
from features.songs.songs_model import create_song
from features.users.users_model import create_user


def setup_db():
    db, cursor = get_connection(':memory:')

    create_database(cursor)

    db.commit()
    return db, cursor

def create_setlist():
    db, cursor = setup_db()

    create_user(cursor, 'user1', 'user1@gmail.com', 'pass')
    create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G',
                80, 'youtube.com/amazinggrace', 'amazinggrace.pdf', 'ag_lyrics.pdf', org_name='org-1')
    create_song(cursor, 'Because He Lives', 'Phil Wickham', 'G',
                65, 'youtube.com/bhl', 'bhl.pdf', 'bhl_lyrics.pdf', org_name='org-1')
    create_song(cursor, 'Praise', 'Brandon Lake', 'C',
                100, 'youtube.com/praise', 'praise.pdf', 'praise_lyrics.pdf', org_name='org-1')
    create_service(cursor, 'Sunday Worship', 'Worship', '3/15/2026', '9:00 AM', 1, org_name='org-1')
    db.commit()

    return db, cursor

def test_add_song_to_service():
    db, cursor = create_setlist()

    add_song_to_service(cursor, 1, 1,'G', 80, 3, 'org-1')
    add_song_to_service(cursor, 1, 2, 'G', 75, 2, 'org-1')
    add_song_to_service(cursor, 1, 3, 'D',110 , 1, 'org-1')
    db.commit()

    setlist = get_service_setlist(cursor, 1, 'org-1')

    assert len(setlist) == 3

    assert setlist[0]['song_id'] == 3
    assert setlist[0]['song_order'] == 1
    assert setlist[0]['title'] == 'Praise'

    assert setlist[1]['song_id'] == 2
    assert setlist[1]['song_order'] == 2
    assert setlist[1]['title'] == 'Because He Lives'

    assert setlist[2]['song_id'] == 1
    assert setlist[2]['song_order'] == 3
    assert setlist[2]['title'] == 'Amazing Grace'

def test_duplicate_song():
    db, cursor = create_setlist()

    add_song_to_service(cursor, 1, 1, 'G', 80, 1, 'org-1')
    with pytest.raises(sqlite3.IntegrityError):
        add_song_to_service(cursor, 1, 1, 'G', 75, 2, 'org-1')
    db.commit()

def test_update_song_in_setlist():
    db, cursor = create_setlist()

    add_song_to_service(cursor, 1, 1, 'G', 80, 1, 'org-1')
    add_song_to_service(cursor, 1, 2, 'G', 75, 2, 'org-1')
    db.commit()

    updated_setlist = update_song_in_setlist(cursor, 1, 'A', 75, 1, 1, 'org-1')

    assert updated_setlist[0]['song_key'] == 'A'
    assert updated_setlist[0]['song_tempo'] == 75
    assert updated_setlist[0]['song_order'] == 1

def test_remove_song_from_service():
    db, cursor = create_setlist()

    add_song_to_service(cursor, 1, 1, 'G', 80, 1, 'org-1')
    db.commit()

    remove_song_from_service(cursor, 1, 'org-1')
    db.commit()

    rows = get_service_setlist(cursor, 1, 'org-1')

    assert rows == []


def test_remove_song_from_service_ignores_wrong_org():
    db, cursor = create_setlist()

    add_song_to_service(cursor, 1, 1, 'G', 80, 1, 'org-1')
    db.commit()

    remove_song_from_service(cursor, 1, org_name='org-2')
    db.commit()

    rows = get_service_setlist(cursor, 1, 'org-1')
    assert len(rows) == 1
    assert rows[0]['song_id'] == 1


def test_reorder_songs():
    db, cursor = create_setlist()

    add_song_to_service(cursor, 1, 1, 'G', 80, 1, 'org-1') # Song A
    add_song_to_service(cursor, 1, 2, 'G', 75, 2, 'org-1') # Song B
    db.commit()

    update_song_in_setlist(cursor, 2, 'G', 75, 1, 1, 'org-1')
    update_song_in_setlist(cursor, 1, 'G', 80, 2, 1, 'org-1')
    db.commit()

    setlist = get_service_setlist(cursor, 1, 'org-1')
    assert setlist[0]['song_id'] == 2
    assert setlist[1]['song_id'] == 1

def test_cascade_delete_service():
    db, cursor = create_setlist()
    add_song_to_service(cursor, 1, 1, 'G', 80, 1, 'org-1')
    db.commit()

    from features.services.services_model import delete_service
    delete_service(cursor, 1, 'org-1')
    db.commit()

    cursor.execute("SELECT * FROM org_1_service_songs WHERE service_id = 1")
    assert cursor.fetchone() is None

def test_partial_update():
    db, cursor = create_setlist()
    add_song_to_service(cursor, 1, 1, 'G', 80, 5, 'org-1')
    db.commit()

    update_song_in_setlist(cursor, 1, 'Bb', 80, 5, 1, 'org-1')
    db.commit()

    setlist = get_service_setlist(cursor, 1, 'org-1')
    assert setlist[0]['song_key'] == 'Bb'
    assert setlist[0]['song_order'] == 5