import sqlite3
import bcrypt

conn = sqlite3.connect('project.db')
cursor = conn.cursor()


cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")


conn.commit()
conn.close()







