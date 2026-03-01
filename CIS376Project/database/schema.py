from features.users.users_model import create_users_table

def create_database(cursor):
    create_users_table(cursor)