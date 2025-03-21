from flask import Flask, render_template, request
import sqlite3 as sql
from init_db import initialize_database

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'

# initialize database when app is run
with app.app_context():
    initialize_database()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run()


