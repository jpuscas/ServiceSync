import sqlite3
import pytest
from database.schema import create_database
from features.songs.songs_model import (search_song, update_song, delete_song,
                                        get_song_by_id, create_song, list_songs)


def setup_db():
    db = sqlite3.connect(':memory:')
    cursor = db.cursor()

    create_database(cursor)

    db.commit()
    return db, cursor

def test_valid_song():
    db, cursor = setup_db()

    create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G',
                120, 'youtube.com/amazinggrace')
    db.commit()

    cursor.execute('SELECT * FROM songs')
    rows = cursor.fetchall()
    assert len(rows) == 1

def test_get_song_by_id():
    db, cursor = setup_db()

    create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G',
                120, 'youtube.com/amazinggrace')
    db.commit()

    row = get_song_by_id(cursor, 1)

    assert row[1] == 'Amazing Grace'
    assert row[2] == 'Chris Tomlin'

def test_get_song_by_title():
    db, cursor = setup_db()

    create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G',
                120, 'youtube.com/amazinggrace')
    db.commit()

    results = search_song(cursor, 'Amazing')

    assert len(results) == 1
    assert results[0][1] == 'Amazing Grace'

def test_get_song_by_artist():
    db, cursor = setup_db()

    create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G',
                120, 'youtube.com/amazinggrace')
    db.commit()

    results = search_song(cursor, 'Chris')

    assert len(results) == 1
    assert results[0][2] == 'Chris Tomlin'

def test_list_songs():
    db, cursor = setup_db()

    create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G',
                120, 'youtube.com/amazinggrace')
    create_song(cursor, 'How He Loves', 'Chris Tomlin', 'C',
                80, 'youtube.com/howheloves')
    db.commit()

    rows = list_songs(cursor)

    assert len(rows) == 2
    assert rows[0][1] == 'Amazing Grace'
    assert rows[1][1] == 'How He Loves'

def test_search_song_not_found():
    db, cursor = setup_db()

    results = search_song(cursor, "Nothing")

    assert len(results) == 0

def test_update_song():
    db, cursor = setup_db()

    create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G',
                120, 'youtube.com/amazinggrace')
    db.commit()

    update_song(cursor, '1', 'How He Loves Us',
                'Chris Tomlin', 'G', 120,
                'youtube.com/howhelovesus')
    db.commit()

    cursor.execute('''SELECT title, artist FROM songs 
    WHERE song_id = ?''', (1,))
    rows = cursor.fetchone()

    assert rows[0] == 'How He Loves Us'

def test_delete_song():
    db, cursor = setup_db()

    create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G',
                120, 'youtube.com/amazinggrace')
    db.commit()

    delete_song(cursor, 1)
    db.commit()

    deleted_song = get_song_by_id(cursor, 1)

    assert deleted_song is None
