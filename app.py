from flask import Flask, render_template, request, session, redirect, url_for
from init_db import initialize_database, hash_password
import sqlite3 as sql

app = Flask(__name__)
app.secret_key = 'd8hKHndjUxkiw168'

host = 'http://127.0.0.1:5000/'

# Initialize the database when app.py is executed
with app.app_context():
    initialize_database()

@app.route('/', methods=['GET', 'POST'])
def login():
    '''
        Handles both displaying the login form and processing login attempts
    '''
    if request.method == 'POST':
        # Extract user inputs from the form
        username = request.form['username']
        password = request.form['password']
        # Check if password is correct. Output error if incorrect
        if check_password(username, password):
            session['user_id'] = username
            session['name'] = get_name(username)
            session['user_type'] = get_user_type(username)
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            return render_template('index.html', message='Username and/or password is incorrect. Please try again.')
    return render_template('index.html')

@app.route('/home')
def home():
    '''
        Home page after successful login
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_type = session.get('user_type')
    return render_template('home.html', user_type=user_type)

@app.route('/logout')
def logout():
    '''
        Clears the session and redirects to login page
    '''
    session.clear()
    return redirect(url_for('login'))

# @app.route('/signup')
# def signup():
#     return render_template('signup.html')

def get_user_type(username: str):
    conn = sql.connect('database.db')
    cursor = conn.execute(
        'SELECT role FROM Users WHERE user_id = ?',
        (username,)               # <-- note the comma
    )
    row = cursor.fetchone()
    conn.close()
    if row and row[0] in ('Buyer', 'Seller', 'HelpDesk'):
        return row[0]
    return None

def get_name(username: str):
    conn = sql.connect('database.db')
    cursor = conn.execute(
        'SELECT name FROM Users WHERE user_id = ?',
        (username,)  # <-- note the comma
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def check_password(username: str, password: str) -> bool:
    '''
        Checks if the username and password match
        Input:
            - username [str]: The inputted username by the user
            - password [str]: The inputted password by the user
        Output:
            - bool: Whether the password matches the username
    '''
    # Encrypt the password
    encrypted_password = hash_password(password)
    # Check if username + password match in the database
    connection = sql.connect('database.db')
    info = connection.execute('SELECT * FROM Users WHERE user_id = ? AND password = ?', (username, encrypted_password))
    if info.fetchall():
        return True
    return False

if __name__ == "__main__":
    app.run()
