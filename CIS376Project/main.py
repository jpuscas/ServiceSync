from database.connection import get_connection, DEFAULT_DATABASE
from database.schema import create_database
import os

def initialize_database():
    db_already_exists = os.path.exists(DEFAULT_DATABASE)

    db, cursor = get_connection()
    create_database(cursor)
    db.commit()
    db.close()

    if db_already_exists:
        print(f'Database exists at {DEFAULT_DATABASE}. Schema initialized/checked without clearing data.')
    else:
        print(f'Database created at {DEFAULT_DATABASE}.')

if __name__ == '__main__':
    initialize_database()