from flask import Flask, render_template, request
import sqlite3 as sql

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'


@app.route('/')
def index():
    return render_template('index.html')

# renders the add name page and handles user input for first and last names
@app.route('/add_name', methods=['POST', 'GET'])
def add_name():
    error = None
    if request.method == 'POST':
        result = valid_name_add(request.form['FirstName'], request.form['LastName'])
        if result:
            return render_template('add.html', error=error, result=result)
        else:
            error = 'invalid input name'
    return render_template('add.html', error=error)

# renders the delete name page and handles user input for first and last names
@app.route('/delete_name', methods=['POST', 'GET'])
def delete_name():
    error = None
    # in delete, i fetch all records at the beginning so the user can immediately see them
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS patients(pid INTEGER PRIMARY KEY, firstname TEXT, lastname TEXT);')
    cursor = connection.execute('SELECT * FROM patients;')
    result = cursor.fetchall()
    if request.method == 'POST':
        result = valid_name_delete(request.form['FirstName'], request.form['LastName'])
        if result:
            return render_template('delete.html', error=error, result=result)
        else:
            error = 'invalid input name'
    if result:
        return render_template('delete.html', error=error, result=result)
    else:
        return render_template('delete.html', error=error)

# adds valid names to the database
def valid_name_add(first_name, last_name):
    pid = None # setting pid to null (sqlite autogenerates unique key for primary keys if null)
    connection = sql.connect('database.db')
    connection.execute('CREATE TABLE IF NOT EXISTS patients(pid INTEGER PRIMARY KEY, firstname TEXT, lastname TEXT);')
    connection.execute('INSERT INTO patients (pid, firstname, lastname) VALUES (?, ?, ?);', (pid, first_name, last_name))
    connection.commit()
    cursor = connection.execute('SELECT * FROM patients;')
    return cursor.fetchall()

# deletes valid names from the database
def valid_name_delete(first_name, last_name):
    connection = sql.connect('database.db')
    connection.execute('DELETE FROM patients WHERE firstname = ? AND lastname = ?;', (first_name, last_name))
    connection.commit()
    cursor = connection.execute('SELECT * FROM patients;')
    return cursor.fetchall()


if __name__ == "__main__":
    app.run()


