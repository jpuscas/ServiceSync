from database.connection import get_connection
from database.schema import create_database

def initialize_database():
    db = get_connection()
    cursor = db.cursor()

    create_database(cursor)

    db.commit()
    
    # Verify table was created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f'Tables in database: {tables}')
    
    db.close()

if __name__ == '__main__':
    initialize_database()
    print('Database created successfully.')