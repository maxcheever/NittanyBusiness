from flask import Flask, render_template, request
from init_db import initialize_database, hash_password
import sqlite3 as sql

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'

# Initialize the database when app.py is executed
with app.app_context():
    initialize_database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    '''
        Handles user login. Extracts user inputted username and password
        and checks if they are in the User schema
    '''
    if request.method == 'POST':
        # Extract user inputs from the form
        username = request.form['username']
        password = request.form['password']
        # Check if password is correct. Output error if incorrect
        if check_password(username, password):
            return render_template('home.html')
        else:
            return render_template('index.html', message='Username and/or password is incorrect. Please try again.')

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
