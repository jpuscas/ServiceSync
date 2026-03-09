from flask import Flask, render_template, request, jsonify, session, redirect
from database.connection import get_connection
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
        
        db = get_connection()
        cursor = db.cursor()
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
        
        db = get_connection()
        cursor = db.cursor()
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
    
    db = get_connection()
    cursor = db.cursor()
    success = verify_user(cursor, token)
    if success:
        db.commit()
        session.pop('verification_token', None)
        session['message'] = 'Account verified successfully. You can now log in.'
        return redirect('/login')
    else:
        db.close()
        return render_template('verify_view.html', message="Invalid verification token.", token=session.get('verification_token'))

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)