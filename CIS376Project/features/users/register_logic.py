import sqlite3
from features.users.users_model import create_user
from features.users.login_logic import login_user
from features.users.user_verification import generate_verification_token, set_verification_code


def register_user(cursor, username: str, email: str, password: str, org_id: int = 1, first_name: str = None,last_name: str = None):
    username = (username or "").strip()
    email = (email or "").strip().lower()
    password = password or ""
    first_name = (first_name or "").strip() or None
    last_name = (last_name or "").strip() or None

    if not username or not email or not password:
        return {"success": False, "message": "Enter a username, email, and password."}

    cursor.execute("SELECT username FROM users WHERE email = ? AND org_id = ?", (email, org_id))
    row = cursor.fetchone()
    existing_username = row['username'] if row else None

    if existing_username:
        login_result = login_user(cursor, existing_username, password, org_id)
        if login_result.get("success") is True:
            return {
                "success": True,
                "already_exists": True,
                "message": "Account already exists (signing in).",
                "user": login_result.get("user")
            }

        return {
            "success": False,
            "already_exists": True,
            "message": f"Account already exists. {login_result['message']}"
        }

    try:
        user_id = create_user(cursor, username, email, password, first_name, last_name, org_id)

        token = generate_verification_token()
        set_verification_code(cursor, user_id, token)

        return {
            "success": True,
            "already_exists": False,
            "message": "Account created. Please check your email for verification instructions.",
            "token": token
        }
    except sqlite3.IntegrityError:
        return {
            "success": False,
            "already_exists": True,
            "message": "Username taken."
        }