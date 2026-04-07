import sqlite3
import pytest
from database.schema import create_database
from features.songs.songs_model import (search_song, update_song, delete_song,
                                        get_song_by_id, create_song, list_songs)

def setup_db():
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
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

    assert row['title'] == 'Amazing Grace'
    assert row['artist'] == 'Chris Tomlin'

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

    results = search_song(cursor, 'Nothing')

    assert len(results) == 0

def test_special_character():
    db, cursor = setup_db()

    create_song(cursor, "He's Amazing", 'Chris Tomlin', 'C',
                80, 'youtube.com')
    db.commit()

    results = search_song(cursor, "He's")

    assert len(results) == 1
    assert results[0][1] == "He's Amazing"

def test_default_tempo_none():
    db, cursor = setup_db()

    song_id = create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'C',
                None, 'youtube.com')
    db.commit()

    assert song_id is not None

    cursor.execute("SELECT default_tempo FROM songs WHERE song_id = ?", (song_id,))
    row = cursor.fetchone()
    assert row['default_tempo'] is None

    results = search_song(cursor, 'Amazing')

    assert len(results) == 1
    assert results[0]['default_tempo'] is None

def test_duplicate_song():
    db, cursor = setup_db()

    create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G')
    db.commit()

    result = create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G')

    assert result is None

def test_update_song():
    db, cursor = setup_db()

    song_id = create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G',
                120, 'youtube.com/amazinggrace')
    db.commit()

    update_song(cursor, song_id, 'How He Loves Us',
                'Chris Tomlin', 'G', 120,
                'youtube.com/howhelovesus', 'hhl.pdf', 'hhl_lyrics.pdf')
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

def test_sql_injection_prevention_songs():
    """Test that song search is protected against SQL injection."""
    db, cursor = setup_db()

    # Create a test song
    create_song(cursor, 'Amazing Grace', 'Chris Tomlin', 'G', 120, 'youtube.com/amazinggrace')
    db.commit()

    # Test normal search works
    results = search_song(cursor, 'Amazing')
    assert len(results) == 1

    # Test SQL injection attempt doesn't work
    malicious_search = "' OR '1'='1"
    results = search_song(cursor, malicious_search)
    # Should return empty results, not all songs
    assert len(results) == 0

    # Test another injection attempt
    malicious_search2 = "%' UNION SELECT * FROM users --"
    results = search_song(cursor, malicious_search2)
    assert len(results) == 0
