from features.users.users_model import authenticate_user

def login_user(cursor, username, password):
    user = authenticate_user(cursor, username, password)

    if not user:
        return { 'success': False,
                 'message': 'Invalid username and/or password.' }

    if not user['is_verified']:
        return { 'success': False,
                 'message': 'Account not verified. ' }

    return{
        'success': True,
        'user': user
    }


