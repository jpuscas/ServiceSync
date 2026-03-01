from database.connection import get_connection
from features.users.users_model import authenticate_user

def login(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    user = authenticate_user(cursor, username, password)
    conn.close()

    if not user:
        return { 'success': 'False',
                 'message': 'Invalid username and/or password.' }

    if not user[6]:
        return { 'success': 'False',
                 'message': 'Account not verified. ' }

    return{
        'success': 'True',
        'user': {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'phone': user[3],
            'role': user[5]
        }
    }


