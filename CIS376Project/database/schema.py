from features.services.service_musicians_model import create_musicians_table
from features.services.service_songs_model import create_service_songs_table
from features.services.services_model import create_services_table
from features.songs.songs_model import create_songs_table
from features.users.users_model import create_users_table
from features.invitations.invitations_model import create_invitations_table



def _ensure_column(cursor, table_name, column_name, column_sql):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if column_name in existing_columns:
        return
    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")

def create_database(cursor):
    # Table creation is idempotent to avoid recreating/clearing existing data.
    create_users_table(cursor)
    _ensure_column(cursor, 'users', 'org_id', "org_id TEXT NOT NULL DEFAULT 'default'")
    
    create_songs_table(cursor)
    _ensure_column(cursor, 'songs', 'org_id', "org_id TEXT NOT NULL DEFAULT 'default'")

    # Add new columns for PDFs if they don't exist (safe if DB already has them)
    try:
        cursor.execute("ALTER TABLE songs ADD COLUMN chords_pdf BLOB;")
    except Exception:
        pass  # Column already exists or alter not needed
    try:
        cursor.execute("ALTER TABLE songs ADD COLUMN lyrics_pdf BLOB;")
    except Exception:
        pass  # Column already exists or alter not needed

    create_services_table(cursor)
    _ensure_column(cursor, 'services', 'service_name', "service_name TEXT NOT NULL DEFAULT 'Worship Service'")
    _ensure_column(cursor, 'services', 'service_type', "service_type TEXT NOT NULL DEFAULT 'Worship'")
    _ensure_column(cursor, 'services', 'service_date', "service_date DATE NOT NULL DEFAULT '1970-01-01'")
    _ensure_column(cursor, 'services', 'service_time', "service_time TIME NOT NULL DEFAULT '09:00'")
    _ensure_column(cursor, 'services', 'leader_id', 'leader_id INTEGER')
    _ensure_column(cursor, 'services', 'org_id', "org_id TEXT NOT NULL DEFAULT 'default'")
    
    create_musicians_table(cursor)
    _ensure_column(cursor, 'service_musicians', 'org_id', "org_id TEXT NOT NULL DEFAULT 'default'")
    
    create_service_songs_table(cursor)
    _ensure_column(cursor, 'service_songs', 'org_id', "org_id TEXT NOT NULL DEFAULT 'default'")
    
    create_invitations_table(cursor)
    _ensure_column(cursor, 'invitations', 'org_id', "org_id TEXT NOT NULL DEFAULT 'default'")
