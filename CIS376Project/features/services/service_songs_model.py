def create_service_songs_table(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS service_songs (
        service_song_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        song_id INTEGER NOT NULL,
        custom_key TEXT,
        custom_tempo INTEGER,
        song_order INTEGER,
        FOREIGN KEY (service_id) REFERENCES services(service_id),
        FOREIGN KEY (song_id) REFERENCES songs(song_id)    
    ''')
