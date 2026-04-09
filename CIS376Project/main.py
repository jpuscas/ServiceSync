from database.connection import get_connection, DEFAULT_DB_PATH
from database.schema import create_database
import os

def initialize_database():
    db_already_exists = os.path.exists(DEFAULT_DB_PATH)

    db, cursor = get_connection()
    create_database(cursor)
    db.commit()
    db.close()

    if db_already_exists:
        print(f'Database exists at {DEFAULT_DB_PATH}. Schema initialized/checked without clearing data.')
    else:
        print(f'Database created at {DEFAULT_DB_PATH}.')

if __name__ == '__main__':
    initialize_database()