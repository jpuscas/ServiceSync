import sqlite3

db = sqlite3.connect('project.db')
cursor = db.cursor()


try:
    cursor.execute('DROP TABLE users')
    db.commit()
except sqlite3.OperationalError as e:
    print(f'Database Error: {e}')


cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    
    password TEXT NOT NULL,
    
    role TEXT NOT NULL DEFAULT 'member',
    
    is_verified INTEGER NOT NULL DEFAULT 0,
    verification_code TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
''')

db.commit()
db.close()







