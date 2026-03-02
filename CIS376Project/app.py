from flask import Flask, render_template, request, jsonify
from features.users.login_logic import login

app = Flask(__name__, template_folder='features/users')

@app.route('/')
def home():
    return "Welcome to Service Scheduler!"

@app.route('/login', methods=['GET', 'POST'])
def login_route():
    if request.method == 'GET':
        return render_template('login_view.html')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        result = login(username, password)
        
        if result['success'] == 'True':
            return jsonify({'success': True, 'user': result['user']})
        else:
            return render_template('login_view.html', message=result['message']), 401

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
