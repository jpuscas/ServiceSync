from database.connection import get_connection
from database.schema import create_database

def initialize_database():
    db = get_connection()
    cursor = db.cursor()

    create_database(cursor)

    db.commit()
    db.close()

if __name__ == '__main__':
    initialize_database()
    print('Database created successfully.')