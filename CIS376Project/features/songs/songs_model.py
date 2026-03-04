def create_songs_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS songs (
        song_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        default_key TEXT NOT NULL,
        default_tempo INTEGER,
        youtube_url TEXT
        );
    ''')