# Service Scheduler

## Setup Instructions

### First Time Setup (Any Device)

1. **Install Python** (3.9+) from [python.org](https://www.python.org/)

2. **Clone the repository** and navigate to it:
   ```bash
   git clone <repo-url>
   cd CIS-376-Project-ServiceSchedul
   ```

3. **Create a virtual environment**:
   ```powershell
   python -m venv venv
   ```

4. **Install dependencies**:
   ```powershell
   venv\Scripts\python -m pip install -r requirements.txt
   ```

5. **Initialize the database**:
   ```powershell
   venv\Scripts\python CIS376Project\main.py
   ```

6. **Run the Flask application**:
   ```powershell
   cd CIS376Project
   ..\venv\Scripts\python app.py
   ```

7. **Access the login page**:
   Open your browser and go to: `http://localhost:5000/login`

### Create a Test User

In a new terminal:
```powershell
cd CIS376Project
..\venv\Scripts\python -c "from database.connection import get_connection; from features.users.users_model import create_user; conn = get_connection(); cursor = conn.cursor(); create_user(cursor, 'testuser', 'test@example.com', 'password123'); conn.commit(); conn.close(); print('Test user created!')"
```

Login with:
- **Username**: testuser
- **Password**: password123

### Project Structure

```
CIS376Project/
├── main.py                 # Database initialization
├── app.py                  # Flask application
├── database/
│   ├── connection.py       # Database connection
│   └── schema.py           # Database schema setup
└── features/
    └── users/
        ├── login_logic.py  # Login business logic
        ├── login_view.html # Login page UI
        ├── users_model.py  # User model and authentication
        └── user_verification.py
```
