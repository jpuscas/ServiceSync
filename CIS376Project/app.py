from flask import Flask, render_template, request, jsonify, session, redirect
from database.connection import get_connection
from features.songs.add_song_logic import add_new_song
from features.songs.songs_model import list_songs, search_song
from features.users.login_logic import login_user
from features.users.register_logic import register_user
from features.users.user_verification import verify_user

app = Flask(__name__, template_folder='features/users')
app.secret_key = 'dev_secret_key'

@app.route('/')
def home():
    return "Welcome to Service Scheduler!"

@app.route('/login', methods=['GET', 'POST'])
def login_route():
    message = session.pop('message', None)
    if request.method == 'GET':
        return render_template('login_view.html', message=message)
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db, cursor = get_connection()
        result = login_user(cursor, username, password)
        db.close()
        
        if result['success']:
            return jsonify({'success': True, 'user': result['user']})
        else:
            return render_template('login_view.html', message=result['message']), 401

@app.route('/register', methods=['GET', 'POST'])
def register_route():
    if request.method == 'GET':
        return render_template('register_view.html')
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        db, cursor = get_connection()
        result = register_user(cursor, username, email, password)
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
def songs_route():
    query = request.args.get('q', '').strip()

    db, cursor = get_connection()
    if query:
        rows = search_song(cursor, query)
    else:
        rows = list_songs(cursor)
    db.close()

    songs = []
    for row in rows:
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

    return render_template('songs_view.html', songs=songs, query=query)

@app.route('/add_song', methods=['GET', 'POST'])
def add_song_route():
    if request.method == 'GET':
        return render_template('add_song_view.html')
    
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
        
        result = add_new_song(title, artist, key, tempo, youtube_url, chords_data, lyrics_data)
        
        if result['success']:
            return redirect('/songs')
        else:
            return render_template('add_song_view.html', message=result['message'])

@app.route('/song/<int:song_id>/chords.pdf')
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