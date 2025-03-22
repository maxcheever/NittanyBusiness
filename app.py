from flask import Flask, render_template, request

import sqlite3 as sql
from init_db import initialize_database, hash_password

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'

# initialize database when app is run
# with app.app_context():
    # initialize_database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

def check_password(username: str, password: str) -> bool:
    # Encrypt the password
    encrypted_password = hash_password(password)

    # Connect to database
    connection = sql.connect('database.db')
    info = connection.execute('SELECT * FROM Users WHERE user_id = :username AND password = :password')



    return False


if __name__ == "__main__":
    app.run()


