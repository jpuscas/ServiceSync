from database.connection import ensure_database_initialized

def initialize_database():
    database_path, db_already_exists = ensure_database_initialized()

    if db_already_exists:
        print(f'Database exists at {database_path}. Schema initialized/checked without clearing data.')
    else:
        print(f'Database created at {database_path}.')

if __name__ == '__main__':
    initialize_database()