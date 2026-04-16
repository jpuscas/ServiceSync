import json
import os
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect
from jinja2 import ChoiceLoader, FileSystemLoader
from database.connection import get_connection
from database.schema import create_database
from features.invitations.invitations_model import accept_invitation, decline_invitation, get_invitation_by_musicians_id, get_invitations_by_user
from features.invitations.send_invitation_logic import send_service_invitation
from features.services.add_song_to_service_logic import replace_service_setlist
from features.services.assign_member_logic import save_members_for_service
from features.services.create_service_logic import create_new_service
from features.services.service_details_logic import get_full_service_details
from features.services.service_musicians_model import get_musicians_for_service, update_musician_response, reset_musician_request, get_musician_row
from features.services.service_songs_model import get_songs_for_service
from features.services.services_model import delete_service, get_service_by_id, list_services, list_services_for_user, update_service
from features.songs.add_song_logic import add_new_song
from features.songs.search_song_logic import perform_song_search

# Ensure DB schema is applied on app start without deleting existing data
_db, _cursor = get_connection()
create_database(_cursor)
_db.commit()
_db.close()
from features.songs.songs_model import list_songs, get_song_by_id, update_song, delete_song
from features.users.login_logic import login_user
from features.users.register_logic import register_user
from features.users.role_logic import has_role
from features.users.user_verification import verify_user
from features.users.users_model import get_user_by_id, list_users, update_password, update_username, update_phone, update_name, update_email

app = Flask(__name__, template_folder='features/users')
app.jinja_loader = ChoiceLoader([
    app.jinja_loader,
    FileSystemLoader(os.path.join(app.root_path, 'features', 'songs')),
])
app.secret_key = 'dev_secret_key'

SERVICE_ROLES = [
    'Singer',
    'Drummer',
    'Bass Guitarist',
    'Electric Guitarist',
    'Pianist',
    'Keyboard',
    'Acoustic Guitarist',
]

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None

    db, cursor = get_connection()
    user_row = get_user_by_id(cursor, user_id)
    db.close()

    if user_row is None:
        session.clear()
        return None

    # Keep session fields in sync in case role/username changed in the database.
    session['username'] = user_row['username']
    session['role'] = user_row['role']
    session['org_id'] = user_row['org_id']

    return {
        'id': user_id,
        'username': user_row['username'],
        'role': user_row['role'],
        'org_id': user_row['org_id'],
    }

def get_current_org_id():
    current_user = get_current_user()
    return current_user['org_id'] if current_user else 1


def is_leader(user=None):
    active_user = user or get_current_user()
    return has_role(active_user, 'leader')

def require_login(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if get_current_user() is None:
            session['message'] = 'Please log in to continue.'
            return redirect('/login')
        return view_function(*args, **kwargs)
    return wrapped_view

def require_leader(redirect_path='/'):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped_view(*args, **kwargs):
            current_user = get_current_user()
            if current_user is None:
                session['message'] = 'Please log in to continue.'
                return redirect('/login')
            if not is_leader(current_user):
                session['message'] = 'Leader access is required for that action.'
                return redirect(redirect_path)
            return view_function(*args, **kwargs)
        return wrapped_view
    return decorator

def serialize_song(song_row):
    return {
        'song_id': song_row['song_id'],
        'title': song_row['title'],
        'artist': song_row['artist'],
        'default_key': song_row['default_key'],
        'default_tempo': song_row['default_tempo'],
        'youtube_url': song_row['youtube_url'],
        'has_chords_pdf': 1 if song_row['chords_pdf'] else 0,
        'has_lyrics_pdf': 1 if song_row['lyrics_pdf'] else 0,
    }

def serialize_user(user_row):
    return {
        'id': user_row['id'],
        'username': user_row['username'],
        'first_name': user_row['first_name'] or '',
        'last_name': user_row['last_name'] or '',
        'email': user_row['email'],
        'role': user_row['role'],
    }

def build_service_detail(cursor, service_row, org_id: int = 1):
    if not service_row:
        return None

    result = get_full_service_details(service_row['service_id'], org_id, cursor=cursor)
    if not result['success']:
        return None

    detail = result['service']
    detail['assignments'] = result['musicians']
    detail['songs'] = result['songs']
    detail['title'] = detail['service_date']
    return detail

def normalize_song_ids(song_payload):
    ordered_song_ids = []
    for song_item in song_payload:
        song_id = song_item.get('song_id') if isinstance(song_item, dict) else song_item
        if song_id in (None, ''):
            continue
        ordered_song_ids.append(int(song_id))
    return ordered_song_ids

def get_selected_songs_by_ids(all_songs, song_ids):
    song_lookup = {song['song_id']: song for song in all_songs}
    return [song_lookup[song_id] for song_id in song_ids if song_id in song_lookup]

def parse_service_payload(form):
    service_date = (form.get('service_date') or '').strip()
    service_time = (form.get('service_time') or '09:00').strip() or '09:00'
    leader_id_raw = (form.get('leader_id') or '').strip()
    leader_id = int(leader_id_raw) if leader_id_raw else None
    assignments_raw = form.get('role_assignments') or '[]'
    song_ids_raw = form.get('song_ids') or '[]'

    assignments_payload = json.loads(assignments_raw)
    song_ids_payload = json.loads(song_ids_raw)

    assignments = []
    for assignment in assignments_payload:
        role_name = (assignment.get('role') or '').strip()
        user_id_raw = assignment.get('user_id')
        if not role_name or user_id_raw in (None, ''):
            continue
        assignments.append({
            'role': role_name,
            'user_id': int(user_id_raw),
        })

    song_ids = normalize_song_ids(song_ids_payload)

    if not service_date:
        raise ValueError('Service date is required.')

    return {
        'service_name': 'Worship Service',
        'service_type': 'Worship',
        'service_date': service_date,
        'service_time': service_time,
        'leader_id': leader_id,
        'assignments': assignments,
        'song_ids': song_ids,
    }

def parse_json_list(raw_value):
    try:
        parsed = json.loads(raw_value or '[]')
        return parsed if isinstance(parsed, list) else []
    except (TypeError, json.JSONDecodeError):
        return []

def serialize_invitation_request(invitation_row):
    status = invitation_row['invitation_status']
    accepted = None
    if status == 'Accepted':
        accepted = 1
    elif status == 'Declined':
        accepted = 0

    return {
        'invitation_id': invitation_row['invitation_id'],
        'musicians_id': invitation_row['musicians_id'],
        'service_id': invitation_row['service_id'],
        'instrument': invitation_row['instrument'] or '',
        'accepted': accepted,
        'service_date': invitation_row['service_date'],
        'service_time': invitation_row['service_time'],
        'service_name': invitation_row['service_name'],
    }

def save_service_relations(cursor, service_id, assignments, song_ids, org_id: int = 1, sender_id=None):
    if sender_id is not None:
        member_result = save_members_for_service(sender_id, service_id, assignments, org_id, cursor=cursor)
        if not member_result['success']:
            raise ValueError(member_result['message'])
    else:
        member_result = save_members_for_service(0, service_id, assignments, org_id, cursor=cursor)
        if not member_result['success'] and member_result['message'] != 'Permission denied.':
            raise ValueError(member_result['message'])

    if sender_id is not None:
        for assignment_row in get_musicians_for_service(cursor, service_id, org_id):
            send_service_invitation(
                sender_id,
                service_id,
                org_id=org_id,
                recipient_user_id=assignment_row['user_id'],
                musicians_id=assignment_row['musicians_id'],
                instrument=assignment_row['instrument'],
                cursor=cursor,
            )

    songs_result = replace_service_setlist(service_id, song_ids, org_id, cursor=cursor)
    if not songs_result['success']:
        raise ValueError(songs_result['message'])

def load_service_page_context(selected_service_id=None, filter_user_id=None, org_id: int = 1):
    db, cursor = get_connection()
    users = [serialize_user(user) for user in list_users(cursor, org_id)]
    songs = [serialize_song(song) for song in list_songs(cursor, org_id)]
    if filter_user_id is not None:
        services = [dict(row) for row in list_services_for_user(cursor, filter_user_id, org_id)]
    else:
        services = [dict(row) for row in list_services(cursor, org_id)]

    selected_service = None
    if selected_service_id is not None:
        selected_service = build_service_detail(cursor, get_service_by_id(cursor, selected_service_id, org_id), org_id)
    elif services:
        selected_service = build_service_detail(cursor, get_service_by_id(cursor, services[0]['service_id'], org_id), org_id)

    db.close()
    return users, songs, services, selected_service

@app.route('/')
def home():
    return render_template(
        'home_view.html',
        current_user=get_current_user(),
        can_manage=is_leader(),
        message=session.pop('message', None),
    )

@app.route('/login', methods=['GET', 'POST'])
def login_route():
    message = session.pop('message', None)
    if request.method == 'GET':
        return render_template('login_view.html', message=message)
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        org_id_raw = request.form.get('org_id', '1')
        try:
            org_id = int(org_id_raw)
        except (TypeError, ValueError):
            org_id = 1
        
        db, cursor = get_connection()
        result = login_user(cursor, username, password, org_id)
        db.close()
        
        if result['success']:
            session['user_id'] = result['user']['id']
            session['username'] = result['user']['username']
            session['role'] = result['user']['role']
            session['org_id'] = result['user']['org_id']
            session['message'] = f"Logged in as {result['user']['username']}."
            return redirect('/')
        else:
            return render_template('login_view.html', message=result['message']), 401

@app.route('/logout', methods=['POST'])
def logout_route():
    session.clear()
    session['message'] = 'You have been logged out.'
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register_route():
    if request.method == 'GET':
        return render_template('register_view.html')
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        org_id_raw = request.form.get('org_id', '1')
        try:
            org_id = int(org_id_raw)
        except (TypeError, ValueError):
            org_id = 1
        
        db, cursor = get_connection()
        result = register_user(cursor, username, email, password, org_id, first_name, last_name)
        if result['success']:
            db.commit()
            session['verification_token'] = result['token']
            return redirect('/verify')
        db.close()
        
        return render_template('register_view.html', message=result['message'])

@app.route('/verify', methods=['GET', 'POST'])
def verify_route():
    if request.method == 'GET':
        token = session.get('verification_token')
        return render_template('verify_view.html', token=token)
    
    token = request.form.get('token')
    
    db, cursor = get_connection()
    success = verify_user(cursor, token)
    if success:
        db.commit()
        session.pop('verification_token', None)
        session['message'] = 'Account verified successfully. You can now log in.'
        return redirect('/login')
    else:
        db.close()
        return render_template('verify_view.html', message="Invalid verification token.", token=session.get('verification_token'))

@app.route('/songs', methods=['GET'])
@require_login
def songs_route():
    query = request.args.get('q', '').strip()
    current_user = get_current_user()
    org_id = current_user['org_id']

    db, cursor = get_connection()
    result = perform_song_search(query, org_id, cursor=cursor)
    db.close()

    songs = []
    for row in result['results']:
        songs.append({
            "song_id": row['song_id'],
            "title": row['title'],
            "artist": row['artist'],
            "default_key": row['default_key'],
            "default_tempo": row['default_tempo'],
            "youtube_url": row['youtube_url'],
            "chords_pdf": row['chords_pdf'],
            "lyrics_pdf": row['lyrics_pdf'],
        })

    return render_template(
        'songs_view.html',
        songs=songs,
        query=query,
        current_user=current_user,
        can_manage=is_leader(current_user),
        message=session.pop('message', None),
    )

@app.route('/api/songs', methods=['GET'])
@require_login
def songs_api_route():
    query = request.args.get('q', '').strip()
    current_user = get_current_user()
    org_id = current_user['org_id']

    db, cursor = get_connection()
    result = perform_song_search(query, org_id, cursor=cursor)
    db.close()

    return jsonify({'songs': result['results']})

@app.route('/services/new', methods=['GET', 'POST'])
@require_leader('/services')
def create_service_route():
    current_user = get_current_user()
    org_id = current_user['org_id']
    users, songs, _, _ = load_service_page_context(org_id=org_id)

    if request.method == 'GET':
        return render_template(
            'create_service_view.html',
            roles=SERVICE_ROLES,
            users=users,
            songs=songs,
            message=None,
            form_data={'service_date': '', 'service_time': '09:00', 'leader_id': ''},
            selected_assignments=[],
            selected_songs=[],
            current_user=current_user,
            can_manage=True,
        )

    try:
        payload = parse_service_payload(request.form)
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        selected_assignments = parse_json_list(request.form.get('role_assignments'))
        selected_song_ids = [int(song_id) for song_id in parse_json_list(request.form.get('song_ids')) if str(song_id).strip()]
        return render_template(
            'create_service_view.html',
            roles=SERVICE_ROLES,
            users=users,
            songs=songs,
            message=str(error),
            form_data={
                'service_date': request.form.get('service_date', ''),
                'service_time': request.form.get('service_time', '09:00'),
                'leader_id': request.form.get('leader_id', ''),
            },
            selected_assignments=selected_assignments,
            selected_songs=get_selected_songs_by_ids(songs, selected_song_ids),
            current_user=current_user,
            can_manage=True,
        ), 400

    db, cursor = get_connection()
    create_result = create_new_service(
        payload['service_name'],
        payload['service_type'],
        payload['service_date'],
        payload['service_time'],
        payload['leader_id'],
        org_id,
        cursor=cursor,
    )
    if not create_result['success']:
        db.close()
        return render_template(
            'create_service_view.html',
            roles=SERVICE_ROLES,
            users=users,
            songs=songs,
            message=create_result['message'],
            form_data={
                'service_date': request.form.get('service_date', ''),
                'service_time': request.form.get('service_time', '09:00'),
                'leader_id': request.form.get('leader_id', ''),
            },
            selected_assignments=payload['assignments'],
            selected_songs=get_selected_songs_by_ids(songs, payload['song_ids']),
            current_user=current_user,
            can_manage=True,
        ), 400

    service_id = create_result['service_id']
    save_service_relations(cursor, service_id, payload['assignments'], payload['song_ids'], org_id, sender_id=current_user['id'])
    db.commit()
    db.close()

    return redirect(f'/services/{service_id}')

@app.route('/services', methods=['GET'])
@require_login
def services_route():
    current_user = get_current_user()
    org_id = current_user['org_id']
    member_filter = None if is_leader(current_user) else current_user['id']
    users, songs, services, selected_service = load_service_page_context(filter_user_id=member_filter, org_id=org_id)
    return render_template(
        'services_view.html',
        roles=SERVICE_ROLES,
        users=users,
        songs=songs,
        services=services,
        selected_service=selected_service,
        message=session.pop('message', None),
        current_user=current_user,
        can_manage=is_leader(current_user),
    )

@app.route('/services/<int:service_id>', methods=['GET'])
@require_login
def service_detail_route(service_id):
    current_user = get_current_user()
    org_id = current_user['org_id']
    member_filter = None if is_leader(current_user) else current_user['id']
    users, songs, services, selected_service = load_service_page_context(service_id, filter_user_id=member_filter, org_id=org_id)
    if selected_service is None:
        return redirect('/services')

    return render_template(
        'services_view.html',
        roles=SERVICE_ROLES,
        users=users,
        songs=songs,
        services=services,
        selected_service=selected_service,
        message=session.pop('message', None),
        current_user=current_user,
        can_manage=is_leader(current_user),
    )

@app.route('/services/<int:service_id>/edit', methods=['POST'])
@require_leader('/services')
def update_service_route(service_id):
    current_user = get_current_user()
    org_id = current_user['org_id']
    try:
        payload = parse_service_payload(request.form)
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        users, songs, services, selected_service = load_service_page_context(service_id, org_id=org_id)
        if selected_service is None:
            return redirect('/services')

        selected_service['service_date'] = request.form.get('service_date', selected_service['service_date'])
        selected_service['service_time'] = request.form.get('service_time', selected_service['service_time'])
        selected_service['leader_id'] = request.form.get('leader_id', selected_service.get('leader_id') or '')
        selected_service['assignments'] = parse_json_list(request.form.get('role_assignments'))
        selected_song_ids = normalize_song_ids(parse_json_list(request.form.get('song_ids')))
        selected_service['songs'] = get_selected_songs_by_ids(songs, selected_song_ids)

        return render_template(
            'services_view.html',
            roles=SERVICE_ROLES,
            users=users,
            songs=songs,
            services=services,
            selected_service=selected_service,
            message=str(error),
            current_user=current_user,
            can_manage=True,
        ), 400

    db, cursor = get_connection()
    if get_service_by_id(cursor, service_id, org_id) is None:
        db.close()
        return redirect('/services')

    update_service(
        cursor,
        service_id,
        payload['service_name'],
        payload['service_type'],
        payload['service_date'],
        payload['service_time'],
        payload['leader_id'],
        org_id,
    )
    save_service_relations(cursor, service_id, payload['assignments'], payload['song_ids'], org_id, sender_id=current_user['id'])
    db.commit()
    db.close()

    return redirect(f'/services/{service_id}')

@app.route('/services/<int:service_id>/delete', methods=['POST'])
@require_leader('/services')
def delete_service_route(service_id):
    current_user = get_current_user()
    org_id = current_user['org_id']
    db, cursor = get_connection()
    if get_service_by_id(cursor, service_id, org_id) is not None:
        delete_service(cursor, service_id, org_id)
        db.commit()
    db.close()
    return redirect('/services')

@app.route('/my-requests', methods=['GET'])
@require_login
def my_requests_route():
    current_user = get_current_user()
    org_id = current_user['org_id']
    db, cursor = get_connection()
    requests = [serialize_invitation_request(row) for row in get_invitations_by_user(cursor, current_user['id'], org_id) if row['musicians_id'] is not None]
    db.close()
    return render_template(
        'my_requests_view.html',
        requests=requests,
        current_user=current_user,
        can_manage=is_leader(current_user),
        message=session.pop('message', None),
    )

@app.route('/requests/<int:musicians_id>/accept', methods=['POST'])
@require_login
def accept_request_route(musicians_id):
    current_user = get_current_user()
    org_id = current_user['org_id']
    db, cursor = get_connection()
    row = get_invitation_by_musicians_id(cursor, musicians_id, org_id)
    if row is None or row['user_id'] != current_user['id']:
        db.close()
        session['message'] = 'Request not found.'
        return redirect('/my-requests')
    accept_invitation(cursor, row['invitation_id'], org_id)
    update_musician_response(cursor, musicians_id, 1, org_id)
    db.commit()
    db.close()
    session['message'] = 'You have accepted the request.'
    return redirect('/my-requests')

@app.route('/requests/<int:musicians_id>/decline', methods=['POST'])
@require_login
def decline_request_route(musicians_id):
    current_user = get_current_user()
    org_id = current_user['org_id']
    db, cursor = get_connection()
    row = get_invitation_by_musicians_id(cursor, musicians_id, org_id)
    if row is None or row['user_id'] != current_user['id']:
        db.close()
        session['message'] = 'Request not found.'
        return redirect('/my-requests')
    decline_invitation(cursor, row['invitation_id'], org_id)
    update_musician_response(cursor, musicians_id, 0, org_id)
    db.commit()
    db.close()
    session['message'] = 'You have declined the request.'
    return redirect('/my-requests')

@app.route('/services/<int:service_id>/rerequest/<int:musicians_id>', methods=['POST'])
@require_leader('/services')
def rerequest_musician_route(service_id, musicians_id):
    current_user = get_current_user()
    org_id = current_user['org_id']
    db, cursor = get_connection()
    row = get_musician_row(cursor, musicians_id, org_id)
    if row is None or row['service_id'] != service_id:
        db.close()
        session['message'] = 'Assignment not found.'
        return redirect(f'/services/{service_id}')
    result = send_service_invitation(
        current_user['id'],
        service_id,
        org_id=org_id,
        recipient_user_id=row['user_id'],
        musicians_id=musicians_id,
        instrument=row['instrument'],
        cursor=cursor,
        force_resend=True,
    )
    if not result['success']:
        db.close()
        session['message'] = result['message']
        return redirect(f'/services/{service_id}')
    reset_musician_request(cursor, musicians_id, org_id)
    db.commit()
    db.close()
    session['message'] = 'Re-request sent.'
    return redirect(f'/services/{service_id}')

@app.route('/add_song', methods=['GET', 'POST'])
@require_leader('/songs')
def add_song_route():
    current_user = get_current_user()
    if request.method == 'GET':
        return render_template('add_song_view.html', current_user=current_user, can_manage=True)
    
    if request.method == 'POST':
        title = request.form.get('title')
        artist = request.form.get('artist')
        key = request.form.get('key')
        tempo = request.form.get('tempo')
        youtube_url = request.form.get('youtube_url')
        
        # Handle file uploads
        chords_pdf = request.files.get('chords_pdf')
        lyrics_pdf = request.files.get('lyrics_pdf')
        
        chords_data = chords_pdf.read() if chords_pdf and chords_pdf.filename else None
        lyrics_data = lyrics_pdf.read() if lyrics_pdf and lyrics_pdf.filename else None
        
        # Convert tempo to int if provided
        if tempo:
            try:
                tempo = int(tempo)
            except ValueError:
                tempo = None
        
        result = add_new_song(title, artist, key, current_user['org_id'], tempo, youtube_url, chords_data, lyrics_data)
        
        if result['success']:
            return redirect('/songs')
        else:
            return render_template('add_song_view.html', message=result['message'], current_user=current_user, can_manage=True)

@app.route('/profile', methods=['GET'])
@require_login
def profile_route():
    current_user = get_current_user()
    db, cursor = get_connection()
    user_row = get_user_by_id(cursor, current_user['id'])
    db.close()
    return render_template(
        'profile_view.html',
        current_user=current_user,
        user=user_row,
        can_manage=is_leader(current_user),
        message=session.pop('message', None),
    )

@app.route('/profile/name', methods=['POST'])
@require_login
def profile_update_name():
    first_name = (request.form.get('first_name') or '').strip()
    last_name = (request.form.get('last_name') or '').strip()
    current_user = get_current_user()
    db, cursor = get_connection()
    update_name(cursor, current_user['id'], first_name, last_name)
    db.commit()
    db.close()
    session['message'] = 'Name updated.'
    return redirect('/profile')

@app.route('/profile/username', methods=['POST'])
@require_login
def profile_update_username():
    new_username = (request.form.get('username') or '').strip()
    if not new_username:
        session['message'] = 'Username cannot be empty.'
        return redirect('/profile')
    current_user = get_current_user()
    db, cursor = get_connection()
    try:
        update_username(cursor, current_user['id'], new_username)
        db.commit()
        session['username'] = new_username
        session['message'] = 'Username updated.'
    except Exception:
        session['message'] = 'That username is already taken.'
    finally:
        db.close()
    return redirect('/profile')

@app.route('/profile/email', methods=['POST'])
@require_login
def profile_update_email():
    new_email = (request.form.get('email') or '').strip()
    if not new_email:
        session['message'] = 'Email cannot be empty.'
        return redirect('/profile')
    current_user = get_current_user()
    db, cursor = get_connection()
    try:
        update_email(cursor, current_user['id'], new_email)
        db.commit()
        session['message'] = 'Email updated.'
    except Exception:
        session['message'] = 'That email is already in use.'
    finally:
        db.close()
    return redirect('/profile')

@app.route('/profile/password', methods=['POST'])
@require_login
def profile_update_password():
    new_password = request.form.get('password') or ''
    if len(new_password) < 6:
        session['message'] = 'Password must be at least 6 characters.'
        return redirect('/profile')
    current_user = get_current_user()
    db, cursor = get_connection()
    update_password(cursor, current_user['id'], new_password)
    db.commit()
    db.close()
    session['message'] = 'Password updated.'
    return redirect('/profile')

@app.route('/profile/phone', methods=['POST'])
@require_login
def profile_update_phone():
    phone = (request.form.get('phone') or '').strip()
    current_user = get_current_user()
    db, cursor = get_connection()
    update_phone(cursor, current_user['id'], phone or None)
    db.commit()
    db.close()
    session['message'] = 'Phone number updated.'
    return redirect('/profile')

@app.route('/song/<int:song_id>/edit', methods=['POST'])
@require_leader('/songs')
def edit_song_route(song_id):
    db, cursor = get_connection()
    existing = get_song_by_id(cursor, song_id)
    if existing is None:
        db.close()
        return redirect('/songs')

    title = (request.form.get('title') or '').strip()
    artist = (request.form.get('artist') or '').strip()
    key = (request.form.get('key') or '').strip()
    tempo_raw = request.form.get('tempo', '').strip()
    youtube_url = (request.form.get('youtube_url') or '').strip() or None

    try:
        tempo = int(tempo_raw) if tempo_raw else None
    except ValueError:
        tempo = None

    chords_pdf = request.files.get('chords_pdf')
    lyrics_pdf = request.files.get('lyrics_pdf')
    chords_data = chords_pdf.read() if chords_pdf and chords_pdf.filename else existing['chords_pdf']
    lyrics_data = lyrics_pdf.read() if lyrics_pdf and lyrics_pdf.filename else existing['lyrics_pdf']

    if not title or not artist or not key:
        session['message'] = 'Title, artist, and key are required.'
        db.close()
        return redirect('/songs')

    update_song(cursor, song_id, title, artist, key, tempo, youtube_url, chords_data, lyrics_data)
    db.commit()
    db.close()
    session['message'] = f'\u201c{title}\u201d updated successfully.'
    return redirect('/songs')

@app.route('/song/<int:song_id>/delete', methods=['POST'])
@require_leader('/songs')
def delete_song_route(song_id):
    db, cursor = get_connection()
    row = get_song_by_id(cursor, song_id)
    if row:
        delete_song(cursor, song_id)
        db.commit()
        session['message'] = f'\u201c{row["title"]}\u201d deleted.'
    db.close()
    return redirect('/songs')

@app.route('/song/<int:song_id>/chords.pdf')
@require_login
def get_chords_pdf(song_id):
    db, cursor = get_connection()
    cursor.execute("SELECT chords_pdf FROM songs WHERE song_id = ?", (song_id,))
    row = cursor.fetchone()
    db.close()
    if row and row['chords_pdf']:
        from flask import send_file, io
        return send_file(io.BytesIO(row['chords_pdf']), mimetype='application/pdf', as_attachment=True, download_name=f'song_{song_id}_chords.pdf')
    else:
        return "PDF not found", 404

@app.route('/song/<int:song_id>/lyrics.pdf')
@require_login
def get_lyrics_pdf(song_id):
    db, cursor = get_connection()
    cursor.execute("SELECT lyrics_pdf FROM songs WHERE song_id = ?", (song_id,))
    row = cursor.fetchone()
    db.close()
    if row and row['lyrics_pdf']:
        from flask import send_file, io
        return send_file(io.BytesIO(row['lyrics_pdf']), mimetype='application/pdf', as_attachment=True, download_name=f'song_{song_id}_lyrics.pdf')
    else:
        return "PDF not found", 404

if __name__ == '__main__':


    app.run(debug=True, host='localhost', port=5000)