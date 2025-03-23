# Nittany Business Phase II

## Context
Phase II of the NittanyBusiness Project requires us to handle the two following tasks: Database Population and User Login. Database population requires us to create tables with the necessary primary keys and populate the tables with the data from the provided CSV files. Each password in the CSV file also needs be securely hashed. In our implementation, we chose to use SHA-256. For User Login, we are asked to create a login page for users (seller, buyer, and help desk). The system recognizes a user by their email (username) and password. For security reasons, passwords must be hashed when stored and must not be visible while being entered. SHA-256 was used again for password hashing and masking was applied to ensure that passwords are concealed during user input. Additionally, for unsuccessful login attempts, we output an error message letting the user that their username and/or password is incorrect. 

## Files
1. `app.py`
- This is the main Flask application file that starts the web server and defines the routes for the application. Upon execution, it automatically initializes the database via the `initialize_database()` from `init_db.py`
- GET `/` route displays the login page by rendering `index.html`
- POST `/` route processes information from the login form by extracting the username and password from the request. After, it calls `check_password()` to verify the credentials of the user. If the authentication is successful, the application renders `home.html`. Otherwise, it renders `index.html` again but with an error message
- **Password Verification**: Implemented as a helper function called `check_password()`. The function hashes the user's inputted password and checks it against the stored value in the SQLite database
2. `init_db.py`
- This file is responsible for setting up and populating the database of our application. It contains all the code and functions necessary to create tables and load data from the CSV files
- **Creating Tables**: The `create_tables()` function creates several tables (e.g. Users, Address, Buyers, PaymentDetails, etc.) using SQL commands
- **Populating Tables**: Imports data into tables from various CSV files using `populate_table_from_csv()`. Calls specific transformation functions to convert CSV row data into the correct format before inserting into the respective table
- Helper functions were also implemented to accommodate the database initialization process. `hash_password()` encrypts user passwords using SHA-256. There are multiple transformation functions that adjust the CSV data to match the database schema. Last, we had a helper function that handles parent-child relationships between different categories
3. `index.htnml`
- Login page of the application where users input their username and password
- Provides a login form with fields for username and password and uses the POST method to send login data to the server
- Contains a section that displays an error mesage when the credentials don't match what is stored in the database
4. `home.html`
- Serves as a simple confirmation page that is displayed upon successfully logging in

## Testing
To test a failed login, we used...
- **Username**: o5mrsfw0@nittybiz.com
- **Password**: hello
  
To test a successful login, we used...
- **Username**: o5mrsfw0@nittybiz.com
- **Password**: 9057bc90227bb3025b8e2a4049763407678525e5165192e463c27871af3f2893

## How to Run
1. Open PyCharm and select 'Import Project' or 'Open' to load this folder
2. Right-click on app.py and hit Run 'Flask (app.py)'
3. PyCharm will start the server and output the message 'Running on http://127.0.0.1:5000/'
4. Click the provided link or copy it into a browser to access the application
