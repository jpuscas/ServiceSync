from features.services.service_musicians_model import create_musicians_table
from features.services.service_songs_model import create_service_songs_table
from features.services.services_model import create_services_table
from features.songs.songs_model import create_songs_table
from features.users.users_model import create_users_table

def create_database(cursor):
    create_users_table(cursor)
    create_songs_table(cursor)
    create_services_table(cursor)
    create_musicians_table(cursor)
    #create_service_songs_table(cursor)
