import sqlite3
from features.users.users_model import create_user, get_username_by_email
from features.users.login_logic import login_user

def register_user(cursor, username: str, email: str, password: str):
    username = (username or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    #if one of the fields is left blank
    if not username or not email or not password:
        return {"success": False, "message": "Enter a username, email, and password."}

    #check if user with email exists
    existing_username = get_username_by_email(cursor, email)
    if existing_username:
        login_result = login_user(cursor, existing_username, password)
        if login_result.get("success") is True:
            return{
                "success": True,
                "already_exists": True,
                "message": "Account already exists (signing in).",
                "user": login_result.get("user")
            }

        return{
            "success": False,
            "already_exists": True,
            "message": f"Account already exists. {login_result['message']}"
        }

    #account is created unless the username is taken.
    try:
        create_user(cursor, username, email, password)
        return{
            "success": True,
            "already_exists": False,
            "message": "Account created."
        }
    except sqlite3.IntegrityError:
        return{
            "success": False,
            "already_exists": True,
            "message": "Username taken."
        }