import secrets

def generate_verification_token():
    return secrets.token_urlsafe(32)

print(generate_verification_token())

def set_verification_code(cursor, user_id: int, token: str):
    cursor.execute('''
    UPDATE users
    SET verification_token = ?
    WHERE id = ?
    ''', (token, user_id))

def verify_user(cursor, token: str):
    cursor.execute('''
    SELECT id
    FROM users
    WHERE verification_token = ?
    ''', (token,))

    row = cursor.fetchone()

    if row:
        cursor.execute('''
        UPDATE users
        SET is_verified = 1,
        verification_token = NULL
        WHERE id = ?
        ''', (row['id'],))
        return True

    return False


