import sqlite3 as sql
import csv
import hashlib
from datetime import datetime

def initialize_database():
    drop_tables()
    create_tables()

    # making these global so they can be used to populate Users and Address (see rationale above load_buyers_info)
    global buyers_info, sellers_info, zipcode_dict, helpdesk_info
    buyers_info = load_buyers_info()
    sellers_info = load_sellers_info()
    zipcode_dict = load_zipcode_info()
    helpdesk_info = load_helpdesk_info()

    populate_table_from_csv('Users', './NittanyBusinessDataset_v3/Users.csv', transform_func=transform_user_row)
    populate_table_from_csv('Address', './NittanyBusinessDataset_v3/Address.csv', transform_func=transform_address_row)
    populate_table_from_csv('Buyers', './NittanyBusinessDataset_v3/Buyers.csv')
    populate_table_from_csv('PaymentDetails', './NittanyBusinessDataset_v3/Credit_Cards.csv', transform_func=transform_payment_row)
    populate_table_from_csv('Sellers', './NittanyBusinessDataset_v3/Sellers.csv', transform_func=transform_seller_row)
    populate_table_from_csv('HelpDesk', './NittanyBusinessDataset_v3/Requests.csv', transform_func=transform_helpdesk_row)
    populate_table_from_csv('Product', './NittanyBusinessDataset_v3/Product_Listings.csv', transform_func=transform_product_row)
    populate_table_from_csv('Reviews', './NittanyBusinessDataset_v3/Reviews.csv', transform_func=transform_review_row)
    populate_table_from_csv('Orders', './NittanyBusinessDataset_v3/Orders.csv', transform_func=transform_order_row)
    populate_category_hierarchy('./NittanyBusinessDataset_v3/Categories.csv') # doing this differently since it requires going back through table
    update_seller_avg_ratings()

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
                address_id INTEGER,
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
                business_address VARCHAR(255) NOT NULL,
                bank_routing_number TEXT NOT NULL,
                bank_account_number TEXT NOT NULL,
                balance REAL NOT NULL,
                avg_rating REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES Users(user_id),
                FOREIGN KEY (business_address) REFERENCES Address(address_id)
            )
        ''')

    # Table 6: HelpDesk (Requests)
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS HelpDesk (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_id VARCHAR(255) NOT NULL,
                helpdesk_staff_email TEXT,
                request_type VARCHAR(50) NOT NULL CHECK (request_type IN ('MarketAnalysis', 'ChangeID', 'AddCategory', 'Other')),
                details TEXT NOT NULL,
                status INTEGER NOT NULL CHECK (status IN (0, 1, 2)),
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (requester_id) REFERENCES Users(user_id)
            )
        ''')

    # Table 8: Reviews
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS Reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                review_text TEXT NOT NULL,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES Orders(order_id)
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
                FOREIGN KEY (buyer_id) REFERENCES Users(user_id),
                FOREIGN KEY (seller_id) REFERENCES Users(user_id),
                FOREIGN KEY (product_id) REFERENCES Product(product_id)
            )
        ''')

    # Table 10: CategoryHierarchy
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS CategoryHierarchy (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                parent_category INTEGER,
                FOREIGN KEY (parent_category) REFERENCES CategoryHierarchy(category_id)
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
                    category VARCHAR(100) NOT NULL,
                    status INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0,1,2)),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (seller_id) REFERENCES Users(user_id),
                    FOREIGN KEY (category) REFERENCES CategoryHierarchy(name)
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

########## DROP TABLES ##########

def drop_tables():
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    tables = ['Users', 'Address', 'Buyers', 'PaymentDetails', 'Sellers', 'HelpDesk',
              'Product', 'Reviews', 'Orders', 'CategoryHierarchy', 'ShoppingCart']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
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
            query = f'INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})'
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

def load_helpdesk_info():
    """
    Load helpdesk user emails from Requests.csv.
    """
    emails = set()
    with open('./NittanyBusinessDataset_v3/Requests.csv', 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # skip header
        for row in reader:
            staff_email = row[2].strip()
            if staff_email:
                emails.add(staff_email)
    return emails


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
    if email in helpdesk_info:
        role = 'HelpDesk'
        name = email.split('@')[0] if '@' in email else email
        address_id = 1
        phone = None
    elif email in sellers_info:
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

def transform_helpdesk_row(row):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return [row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip(), row[4].strip(), row[5].strip(), timestamp]

def transform_product_row(row):
    """
    Transform Product_Listings.csv row into a Product table row.
    Expected CSV columns: Seller_Email, Listing_ID, Category, Product_Title, Product_Name, Product_Description, Quantity, Product.
    Uses Listing_ID as product_id.
    """
    title = row[3].strip()
    details = row[5].strip()
    price = float(row[7].strip()[1:].replace(',', ''))
    quantity = int(row[6].strip())
    seller_id = row[0].strip()
    category = row[2].strip()
    status = 1
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return [None, title, details, price, quantity,
            seller_id, category, status, created_at]

def transform_review_row(row):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return [None, row[0].strip(), row[1].strip(), row[2].strip(), timestamp]

def transform_order_row(row):
    """
    Transform Orders.csv row into an Orders table row.
    Expected CSV columns: Order_ID, Seller_Email, Listing_ID, Buyer_Email, Date, Quantity, Payment.
    """
    order_id = row[0].strip()
    seller_id = row[1].strip()
    product_id = row[2].strip()
    buyer_id = row[3].strip()
    order_date = row[4].strip()
    quantity = int(row[5].strip())
    amount = float(row[6].strip())
    return [order_id, buyer_id, seller_id, product_id, order_date, quantity, amount]

def transform_seller_row(row):
    """
    Transform a Sellers.csv row to include default avg_rating = 0.
    """
    return row + [0]

def populate_category_hierarchy(csv_file):
    """
    Populate CategoryHierarchy from Categories.csv.
    Expected CSV columns: parent_category, category_name.
    First, inserting all categories with parent_category set to NULL.
    Then updating rows by matching the parent category name to get the parent_category id.
    """
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    category_map = {}
    categories = []

    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            parent_name = row[0].strip() if row[0].strip() != '' else None
            category_name = row[1].strip()
            categories.append((parent_name, category_name))
            cursor.execute('INSERT INTO CategoryHierarchy (name, parent_category) VALUES (?, ?)', (category_name, None))
            category_id = cursor.lastrowid
            category_map[category_name] = category_id

    for parent_name, category_name in categories:
        if parent_name:
            parent_id = category_map.get(parent_name)
            if parent_id:
                category_id = category_map[category_name]
                cursor.execute('UPDATE CategoryHierarchy SET parent_category = ? WHERE category_id = ?',
                               (parent_id, category_id))
    connection.commit()
    connection.close()

def update_seller_avg_ratings():
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE Sellers
        SET avg_rating = COALESCE((
            SELECT AVG(r.rating)
            FROM Reviews r
            JOIN Orders o ON r.order_id = o.order_id
            WHERE o.seller_id = Sellers.user_id
        ), 0)
    ''')
    connection.commit()
    connection.close()
