# Service Scheduler

A Flask-based worship service planning application for churches and ministry teams. The app helps leaders organize services, assign musicians, manage songs, and coordinate requests across organizations.

---

## Overview

Service Scheduler is designed to make weekly planning easier for worship leaders and team members.

With this app, users can:
- register and verify an account,
- log in and manage a personal profile,
- view upcoming services assigned to them,
- accept or decline service requests,
- browse and search the song library,
- create and manage services as a leader,
- manage organization membership and leader access.

Signed-out users are automatically taken to the login page first.

---

## Main Features

### Member Features
- Secure account registration and login
- Account verification flow
- Personal profile management
- View only the services relevant to the logged-in user and active organization
- Accept or decline service requests from the My Requests page

### Leader Features
- Create, edit, and delete services
- Assign musicians to roles
- Re-request musicians when needed
- Add songs to a service setlist
- Manage organization membership
- Promote members to leaders or demote leaders back to members
- Remove users from an organization
- Send organization join requests by username

### Organization Support
- Users can belong to multiple organizations
- Leaders manage people inside their current organization
- Organization join requests appear in My Requests
- Services are filtered by assignment and organization membership

---

## Tech Stack

- Python
- Flask
- SQLite
- Jinja2 templates
- bcrypt for password hashing
- pytest for testing

---

## Project Structure

```text
CIS-376-Project/
├── README.md
├── requirements.txt
└── CIS376Project/
    ├── app.py                 # Main Flask application
    ├── main.py                # Database initialization entry point
    ├── project.db             # SQLite database created at runtime
    ├── database/              # Database connection and schema setup
    ├── features/
    │   ├── users/             # Login, registration, profile, templates
    │   ├── services/          # Service creation, details, assignments
    │   ├── songs/             # Song library and song management
    │   └── invitations/       # Service and organization requests
    └── testing/               # Automated pytest regression tests
    |__ views/
```

---

## Requirements

- Python 3.10 or newer
- pip
- A terminal such as PowerShell or Command Prompt

---

## Installation and Setup

### 1. Clone the repository

```powershell
HTTP for cloning
https://github.com/jnorman42/CIS-376-Project.git

We recommend cloning in your ide instead of terminal
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

**PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Command Prompt**
```cmd
.\.venv\Scripts\activate.bat
```
**Alternative**
source .venv/bin/activate



### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Database is already in the github as it was force pushed 
1. Run:
cd CIS376Project
2. You can run:
```
python3 main.py 
```
but it will just say:
Database exists at YOUR-PROJECT-LOCATION/CIS376Project/project.db. Schema initialized/checked without clearing data.





### 6. Start the application

```powershell
python3 app.py
or 
py app.py
or
python app.py
```
pick the one that works with your python version

### 7. Open the app in your browser

Go to:
http://localhost:5000
or
http://localhost:5000/login

It will not work in Safari
We recommend Firefox

---

## First-Time Use

1. Register a new account.
2. Complete the verification step using the token shown by the app.
3. Log in.
4. You will see the member portion

1. If you want to see admin page log in with the hard coded admin credentials
username: jasonpuscas
password: password
2. Log in.
3. You will see the leader portion and have leader capabilities

---

## Running Tests

To run the full automated test suite:

```powershell
cd CIS376Project
python -m pytest -q
```
Current Test Coverage:

<img width="575" height="416" alt="Screenshot 2026-04-16 124836" src="https://github.com/user-attachments/assets/6f536da9-3dd0-41a3-8961-d82d19c6d350" />

---

## 2 Common Workflow

### For Members
1. Log in
2. Open My Requests
3. Accept or decline invitations
4. View assigned services
5. Review the setlist and service details

### For Leaders
1. Log in
2. Open Organization to manage people
3. Create a new service
4. Assign musicians to roles
5. Add songs to the service
6. Send or re-send requests as needed

---

## Database Notes

- The project uses SQLite.
- The database file is created automatically when initialized.
- Existing databases are preserved and updated through schema checks.
- User organization membership supports multiple organizations.

---

## Troubleshooting

### App will not start
- Make sure the virtual environment is activated.
- Confirm dependencies are installed from the requirements file.
- Ensure you are running the command from the project folder.

### Port 5000 is already in use
- Close the existing process using that port, or restart your terminal and run the app again.

### Database issues
- Run the database initializer again:

```powershell
python CIS376Project\main.py
```

### Tests are failing
- Make sure dependencies are installed.
- Run the tests from inside the CIS376Project folder.

---

## Current Status

The application includes verified regression coverage for authentication, services, invitations, organization management, and database behavior.

---

## Future Developement

1. Text notifications for service or organization requests


## Authors

Jason Puscas
Josh Norman
Owen Bassharah

---

## License

This project is intended for educational use unless your team adds a different license.
