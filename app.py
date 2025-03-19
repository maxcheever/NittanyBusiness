from flask import Flask, render_template, request
import sqlite3 as sql
import csv
import hashlib
from datetime import datetime

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'


@app.route('/')
def index():
    initialize_database()
    return render_template('index.html')

def initialize_database():
    create_tables()

    # making these gloabl so they can be used to populate Users and Address (see rationale above load_buyers_info)
    global buyers_info, sellers_info, zipcode_dict
    buyers_info = load_buyers_info()
    sellers_info = load_sellers_info()
    zipcode_dict = load_zipcode_info()

    populate_table_from_csv('Users', './NittanyBusinessDataset_v3/Users.csv', transform_func=transform_user_row)
    populate_table_from_csv('Address', './NittanyBusinessDataset_v3/Address.csv', transform_func=transform_address_row)
    populate_table_from_csv('Buyers', './NittanyBusinessDataset_v3/Buyers.csv')
    populate_table_from_csv('PaymentDetails', './NittanyBusinessDataset_v3/Credit_Cards.csv', transform_func=transform_payment_row)


########## CREATE TABLES ##########

def create_tables():
    """
        Function to create tables that correspond to our requirement analysis in our Phase I NittanyBusiness report
    """
    connection = sql.connect('database.db')
    cursor = connection.cursor()


    # Table 1: Users
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id VARCHAR(255) PRIMARY KEY,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL CHECK (role IN ('Buyer', 'Seller', 'HelpDesk')),
                name VARCHAR(255) NOT NULL,
                address_id INTEGER NOT NULL,
                phone VARCHAR(50),
                FOREIGN KEY (address_id) REFERENCES Address(address_id)
            )
        ''')

    # Table 2: Address
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS Address (
                    address_id VARCHAR(255) PRIMARY KEY,
                    street VARCHAR(255) NOT NULL,
                    city VARCHAR(50) NOT NULL,
                    state VARCHAR(50) NOT NULL,
                    zipcode VARCHAR(20) NOT NULL
                )
            ''')

    # Table 3: Buyers
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS Buyers (
                    user_id VARCHAR(255) PRIMARY KEY,
                    business_name VARCHAR(255) NOT NULL,
                    buyer_address_id VARCHAR(255) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id),
                    FOREIGN KEY (buyer_address_id) REFERENCES Address(address_id)
                )
            ''')

    # Table 4: PaymentDetails
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS PaymentDetails (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(255) NOT NULL,
                card_type VARCHAR(50) NOT NULL CHECK (card_type IN ('Visa', 'Master', 'Discover', 'American Express')),
                card_number VARCHAR(100) NOT NULL,
                expiration_date DATE NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        ''')

    # Table 5: Sellers
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS Sellers (
                user_id VARCHAR(255) PRIMARY KEY,
                business_name VARCHAR(255) NOT NULL,
                business_address INTEGER NOT NULL,
                business_phone VARCHAR(50) NOT NULL,
                bank_routing_number TEXT NOT NULL,
                bank_account_number TEXT NOT NULL,
                balance REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(user_id),
                FOREIGN KEY (business_address) REFERENCES Address(address_id)
            )
        ''')

    # Table 6: HelpDesk (Requests)
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS HelpDesk (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_id VARCHAR(255) NOT NULL,
                request_type VARCHAR(50) NOT NULL CHECK (request_type IN ('Role Conversion', 'New Category', 'ID Change', 'Other')),
                details TEXT NOT NULL,
                status VARCHAR(50) NOT NULL CHECK (status IN ('Pending', 'Approved', 'Rejected')),
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                helpdesk_staff_email TEXT,
                FOREIGN KEY (requester_id) REFERENCES Users(user_id)
            )
        ''')

    # Table 7: Product (Listings)
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS Product (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(255) NOT NULL,
                details TEXT NOT NULL,
                price REAL NOT NULL CHECK (price > 0),
                quantity INTEGER NOT NULL CHECK (quantity >= 0),
                seller_id VARCHAR(255) NOT NULL,
                category_id INTEGER NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES Users(user_id),
                FOREIGN KEY (category_id) REFERENCES CategoryHierarchy(category_id)
            )
        ''')

    # Table 8: Reviews
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS Reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_id VARCHAR(255) NOT NULL,
                product_id INTEGER NOT NULL,
                review_text TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (buyer_id) REFERENCES Users(user_id),
                FOREIGN KEY (product_id) REFERENCES Product(product_id)
            )
        ''')

    # Table 9: Orders
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS Orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_id VARCHAR(255) NOT NULL,
                seller_id VARCHAR(255) NOT NULL,
                product_id INTEGER NOT NULL,
                order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
                status VARCHAR(50) NOT NULL CHECK (status IN ('Completed', 'Canceled', 'Pending')),
                FOREIGN KEY (buyer_id) REFERENCES Users(user_id),
                FOREIGN KEY (seller_id) REFERENCES Users(user_id),
                FOREIGN KEY (product_id) REFERENCES Product(product_id)
            )
        ''')

    # Table 10: CategoryHierarchy (with parent_category as int referencing category_id)
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS CategoryHierarchy (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                parent_category INTEGER,
                FOREIGN KEY (parent_category) REFERENCES CategoryHierarchy(category_id)
            )
        ''')

    # Table 11: ShoppingCart
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS ShoppingCart (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_id VARCHAR(255) NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (buyer_id) REFERENCES Users(user_id),
                FOREIGN KEY (product_id) REFERENCES Product(product_id)
            )
        ''')

    connection.commit()
    connection.close()

########## POPULATE TABLES ##########

def populate_table_from_csv(table_name, csv_file, transform_func=None):
    """
        Generic function to populate a table from a CSV file.
        Takes table name, csv file name, and uses transform_func to populate row
    """
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        headers = next(reader)  # skip header row
        for row in reader:
            if transform_func:
                row = transform_func(row)
            placeholders = ', '.join('?' * len(row))
            query = f'INSERT INTO {table_name} VALUES ({placeholders})'
            cursor.execute(query, row)

    connection.commit()
    connection.close()

########## LOAD PREREQUISITE INFORMATION ##########

# Since we cannot populate the Users table without the information from Buyers.csv and Sellers.csv,
# we have to preload the buyer and seller information in order to create users.
# Intuition would say that we can just populate the Buyers and Sellers tables before Users,
# but this does not make sense because the application logic involves the User being created first

def load_buyers_info():
    """
    Load buyer info from Buyers.csv.
    """
    info = {}
    with open('./NittanyBusinessDataset_v3/Buyers.csv', 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # skip header
        for row in reader:
            email = row[0].strip()
            business_name = row[1].strip()
            buyer_address_id = row[2].strip()  # may convert to int if needed
            info[email] = (business_name, buyer_address_id)
    return info

def load_sellers_info():
    """
    Load seller info from Sellers.csv.
    """
    info = {}
    with open('./NittanyBusinessDataset_v3/Sellers.csv', 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # skip header
        for row in reader:
            email = row[0].strip()
            business_name = row[1].strip()
            business_address = row[2].strip()  # may convert to int if needed
            # other seller details can be processed in the sellers table;
            # for Users we only need name and address_id.
            info[email] = (business_name, business_address)
    return info

def load_zipcode_info():
    """
    Load zipcode info from Zipcode_Info.csv.
    """
    zipcode_dict = {}
    with open('./NittanyBusinessDataset_v3/Zipcode_Info.csv', 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # skip header
        for row in reader:
            zipcode, city, state = row
            zipcode_dict[zipcode.strip()] = (city.strip(), state.strip())
    return zipcode_dict

########## ROW GENERATING FUNCTIONS ##########

def transform_user_row(row):
    """
    Transform a Users.csv row into a Users table row.
    Expected Users.csv columns: email, password
    If the email exists in Buyers or Sellers info, use that data,
    otherwise, default to:
      - role: 'Buyer'
      - name: portion before '@'
      - address_id: 1 (ensure a default address exists)
      - phone: None
    """
    email = row[0].strip()
    pwd = row[1].strip()
    hashed = hash_password(pwd)

    # check if user exists in sellers or buyers info
    if email in sellers_info:
        role = 'Seller'
        name, address_id = sellers_info[email]
        phone = None
    elif email in buyers_info:
        role = 'Buyer'
        name, address_id = buyers_info[email]
        phone = None
    else: # if neither, generate defaults
        role = 'Buyer'
        name = email.split('@')[0] if '@' in email else email
        address_id = 1  # default address_id; ensure a default exists
        phone = None

    return [email, hashed, role, name, address_id, phone]

def hash_password(password):
    """ hash password """
    return hashlib.sha256(password.encode()).hexdigest()

def transform_address_row(row):
    """
    Transform Address.csv row into (address_id, street, city, state, zipcode).
    Expected Address.csv columns: address_id, zipcode, street_num, street_name.
    Uses Zipcode_Info.csv to get city and state.
    """
    zipcode = row[1].strip()
    street = f"{row[2].strip()} {row[3].strip()}"
    if zipcode in zipcode_dict:
        city, state = zipcode_dict[zipcode]
    else:
        city, state = 'Unknown', 'Unknown'
    return [row[0].strip(), street, city, state, zipcode]

def transform_payment_row(row):
    """
    Transform Credit_Cards.csv row into a PaymentDetails table row.
    Expected CSV columns: credit_card_num, card_type, expire_month, expire_year, security_code, Owner_email.
    Uses Owner_email as user_id and credit_card_num as card_number.
    """
    expiration_date = parse_expiration_date(row[2], row[3])
    return [None, row[5].strip(), row[1].strip(), row[0].strip(), expiration_date]

def parse_expiration_date(expire_month, expire_year):
    """Convert expire_month and expire_year into a date string (YYYY-MM-01)."""
    try:
        month = f"{int(expire_month):02d}"
        return f"{expire_year}-{month}-01"
    except Exception:
        return None


if __name__ == "__main__":
    app.run()


