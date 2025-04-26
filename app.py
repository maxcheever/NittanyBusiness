from flask import Flask, render_template, request, session, redirect, url_for
from init_db import initialize_database, hash_password
from datetime import datetime
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

# USER REGISTRATION
@app.route('/registration', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        connection = sql.connect('database.db')
        # Extract user inputs from the form
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        name = request.form['name']
        role = request.form['role']
        try:
            if check_password(username, password):
                connection.execute('INSERT INTO Users VALUES (?, ?, ?, ?, ?, ?)', (username, hashed_password, role, name, None, None))
                connection.commit()
                connection.close()
                return redirect(url_for('login'))
            else:
                return render_template('registration.html', message='Registration Failed. User Already Registered.')
        except:
            return render_template('registration.html', message='Registration Failed. Please try again.')
    return render_template('registration.html')

# Product Listing Management

@app.route('/seller/products')
def seller_products():
    '''
    Page that displays products registered by the seller
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Check if it's a seller account
    if session.get('user_type') != 'Seller':
        return redirect(url_for('home'))

    seller_id = session.get('user_id')

    # Get active products (status=1)
    conn = sql.connect('database.db')
    conn.row_factory = sql.Row

    # Retrieve active products
    active_cursor = conn.execute('''
        SELECT p.*, c.name as category_name 
        FROM Product p
        JOIN CategoryHierarchy c ON p.category = c.name
        WHERE p.seller_id = ? AND p.status = 1
        ORDER BY p.created_at DESC
    ''', (seller_id,))
    active_products = active_cursor.fetchall()

    # Retrieve inactive/sold products
    inactive_cursor = conn.execute('''
        SELECT p.*, c.name as category_name 
        FROM Product p
        JOIN CategoryHierarchy c ON p.category = c.name
        WHERE p.seller_id = ? AND p.status IN (0, 2)
        ORDER BY p.created_at DESC
    ''', (seller_id,))
    inactive_products = inactive_cursor.fetchall()

    conn.close()

    return render_template('seller_products.html',
                           active_products=active_products,
                           inactive_products=inactive_products,
                           user_type=session.get('user_type'))


@app.route('/seller/products/new', methods=['GET', 'POST'])
def new_product():
    '''
    New product registration page and processing
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Check if it's a seller account
    if session.get('user_type') != 'Seller':
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Get data from the form
        title = request.form['title']
        details = request.form['description']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        category_id = request.form['category_id']
        seller_id = session.get('user_id')

        # Get category name
        conn = sql.connect('database.db')
        cursor = conn.execute('SELECT name FROM CategoryHierarchy WHERE category_id = ?', (category_id,))
        category_name = cursor.fetchone()[0]

        # Register the product
        conn.execute('''
            INSERT INTO Product (title, details, price, quantity, seller_id, category, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'))
        ''', (title, details, price, quantity, seller_id, category_name))
        conn.commit()
        conn.close()

        return redirect(url_for('seller_products'))

    # For GET requests, retrieve category list
    conn = sql.connect('database.db')
    conn.row_factory = sql.Row
    cursor = conn.execute('SELECT * FROM CategoryHierarchy ORDER BY name')
    categories = cursor.fetchall()
    conn.close()

    return render_template('new_product.html',
                           categories=categories,
                           user_type=session.get('user_type'))


@app.route('/seller/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    '''
    Product information editing page and processing
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Check if it's a seller account
    if session.get('user_type') != 'Seller':
        return redirect(url_for('home'))

    conn = sql.connect('database.db')
    conn.row_factory = sql.Row

    # First, verify if this product belongs to the currently logged-in seller
    cursor = conn.execute('SELECT seller_id FROM Product WHERE product_id = ?', (product_id,))
    product_seller = cursor.fetchone()

    if not product_seller or product_seller['seller_id'] != session.get('user_id'):
        conn.close()
        return redirect(url_for('seller_products'))

    if request.method == 'POST':
        # Get data from the form
        title = request.form['title']
        details = request.form['description']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        status = int(request.form['status'])

        # Update product information
        conn.execute('''
            UPDATE Product 
            SET title = ?, details = ?, price = ?, quantity = ?, status = ?
            WHERE product_id = ?
        ''', (title, details, price, quantity, status, product_id))
        conn.commit()

        # Check if the product is sold out
        if quantity == 0 and status == 1:
            conn.execute('UPDATE Product SET status = 2 WHERE product_id = ?', (product_id,))
            conn.commit()

        conn.close()
        return redirect(url_for('seller_products'))

    # For GET requests, retrieve product information
    cursor = conn.execute('''
        SELECT p.*, c.name as category_name 
        FROM Product p
        JOIN CategoryHierarchy c ON p.category = c.name
        WHERE p.product_id = ?
    ''', (product_id,))
    product = cursor.fetchone()

    if not product:
        conn.close()
        return redirect(url_for('seller_products'))

    conn.close()
    return render_template('edit_product.html',
                           product=product,
                           user_type=session.get('user_type'))


@app.route('/seller/products/activate/<int:product_id>')
def activate_product(product_id):
    '''
    Product activation processing
    '''
    if not session.get('logged_in') or session.get('user_type') != 'Seller':
        return redirect(url_for('login'))

    conn = sql.connect('database.db')

    # First, verify if this product belongs to the currently logged-in seller
    cursor = conn.execute('SELECT seller_id, quantity FROM Product WHERE product_id = ?', (product_id,))
    product = cursor.fetchone()

    if not product or product[0] != session.get('user_id'):
        conn.close()
        return redirect(url_for('seller_products'))

    # If product quantity is 0, set status to 2 (Sold), otherwise set to 1 (Active)
    new_status = 2 if product[1] == 0 else 1

    conn.execute('UPDATE Product SET status = ? WHERE product_id = ?', (new_status, product_id))
    conn.commit()
    conn.close()

    return redirect(url_for('seller_products'))


@app.route('/seller/products/deactivate/<int:product_id>')
def deactivate_product(product_id):
    '''
    Product deactivation processing
    '''
    if not session.get('logged_in') or session.get('user_type') != 'Seller':
        return redirect(url_for('login'))

    conn = sql.connect('database.db')

    # First, verify if this product belongs to the currently logged-in seller
    cursor = conn.execute('SELECT seller_id FROM Product WHERE product_id = ?', (product_id,))
    product_seller = cursor.fetchone()

    if not product_seller or product_seller[0] != session.get('user_id'):
        conn.close()
        return redirect(url_for('seller_products'))

    conn.execute('UPDATE Product SET status = 0 WHERE product_id = ?', (product_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('seller_products'))


#Temporary Code for Browse

@app.route('/products')
def browse_products():
    '''
    Displays a list of product categories for browsing
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Get root category (All)
    conn = sql.connect('database.db')
    conn.row_factory = sql.Row

    # Get all top-level categories (categories that have 'All' as parent)
    cursor = conn.execute('''
        SELECT c1.* 
        FROM CategoryHierarchy c1
        JOIN CategoryHierarchy c2 ON c1.parent_category = c2.category_id
        WHERE c2.name = 'All'
        ORDER BY c1.name
    ''')
    categories = cursor.fetchall()

    # Get a few featured products for display
    product_cursor = conn.execute('''
        SELECT p.*, s.business_name as seller_name
        FROM Product p
        JOIN Sellers s ON p.seller_id = s.user_id
        WHERE p.status = 1 AND p.quantity > 0
        ORDER BY p.created_at DESC
        LIMIT 10
    ''')
    featured_products = product_cursor.fetchall()

    conn.close()

    return render_template('products.html',
                           categories=categories,
                           featured_products=featured_products,
                           user_type=session.get('user_type'))


@app.route('/products/category/<int:category_id>')
def browse_category(category_id):
    '''
    Displays subcategories and products in a specific category
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sql.connect('database.db')
    conn.row_factory = sql.Row

    # Get current category info
    cursor = conn.execute('SELECT * FROM CategoryHierarchy WHERE category_id = ?', (category_id,))
    current_category = cursor.fetchone()

    if not current_category:
        conn.close()
        return redirect(url_for('browse_products'))

    # Get subcategories
    sub_cursor = conn.execute('''
        SELECT * FROM CategoryHierarchy 
        WHERE parent_category = ? 
        ORDER BY name
    ''', (category_id,))
    subcategories = sub_cursor.fetchall()

    # Get products in this category
    product_cursor = conn.execute('''
        SELECT p.*, s.business_name as seller_name
        FROM Product p
        JOIN Sellers s ON p.seller_id = s.user_id
        WHERE p.category = ? AND p.status = 1 AND p.quantity > 0
        ORDER BY p.created_at DESC
    ''', (current_category['name'],))
    products = product_cursor.fetchall()

    conn.close()

    return render_template('category.html',
                           current_category=current_category,
                           subcategories=subcategories,
                           products=products,
                           user_type=session.get('user_type'))


@app.route('/products/view/<int:product_id>')
def view_product(product_id):
    '''
    Displays detailed information about a specific product
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sql.connect('database.db')
    conn.row_factory = sql.Row

    # Get product details
    cursor = conn.execute('''
        SELECT p.*, c.name as category_name
        FROM Product p
        JOIN CategoryHierarchy c ON p.category = c.name
        WHERE p.product_id = ? AND p.status = 1
    ''', (product_id,))
    product = cursor.fetchone()

    if not product:
        conn.close()
        return redirect(url_for('browse_products'))

    # Get seller info
    seller_cursor = conn.execute('''
        SELECT s.business_name, s.user_id, s.avg_rating
        FROM Sellers s
        WHERE s.user_id = ?
    ''', (product['seller_id'],))
    seller = seller_cursor.fetchone()

    # Get product reviews
    review_cursor = conn.execute('''
        SELECT r.*
        FROM Reviews r
        JOIN Orders o ON r.order_id = o.order_id
        WHERE o.product_id = ?
        ORDER BY r.timestamp DESC
    ''', (product_id,))
    reviews = review_cursor.fetchall()

    conn.close()

    return render_template('product_detail.html',
                           product=product,
                           seller_name=seller['business_name'] if seller else "Unknown Seller",
                           seller_id=seller['user_id'] if seller else None,
                           seller_rating=seller['avg_rating'] if seller else None,
                           reviews=reviews,
                           user_type=session.get('user_type'))

#Order Management
@app.route('/order/create/<int:product_id>', methods=['POST'])
def create_order(product_id):
    '''
    Creates a new order from product details page
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Only buyers can place orders
    if session.get('user_type') != 'Buyer':
        return redirect(url_for('home'))

    # Get quantity from form
    quantity = int(request.form.get('quantity', 1))

    # Get product details
    conn = sql.connect('database.db')
    conn.row_factory = sql.Row

    cursor = conn.execute('''
        SELECT p.*, s.user_id as seller_id, s.business_name as seller_name
        FROM Product p
        JOIN Sellers s ON p.seller_id = s.user_id
        WHERE p.product_id = ? AND p.status = 1
    ''', (product_id,))
    product = cursor.fetchone()

    conn.close()

    if not product or product['quantity'] < quantity:
        return redirect(url_for('view_product', product_id=product_id))

    # Store order info in session for review page
    session['pending_order'] = {
        'product_id': product_id,
        'product_title': product['title'],
        'seller_id': product['seller_id'],
        'seller_name': product['seller_name'],
        'quantity': quantity,
        'price': product['price'],
        'total_amount': product['price'] * quantity
    }

    return redirect(url_for('review_order'))


@app.route('/order/review', methods=['GET'])
def review_order():
    '''
    Review order details before proceeding to payment
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Only buyers can place orders
    if session.get('user_type') != 'Buyer':
        return redirect(url_for('home'))

    # Check if there's a pending order
    pending_order = session.get('pending_order')
    if not pending_order:
        return redirect(url_for('browse_products'))

    return render_template('order_review.html',
                           order=pending_order,
                           user_type=session.get('user_type'))


@app.route('/order/payment', methods=['GET', 'POST'])
def payment():
    '''
    Process payment for an order
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Only buyers can place orders
    if session.get('user_type') != 'Buyer':
        return redirect(url_for('home'))

    # Check if there's a pending order
    pending_order = session.get('pending_order')
    if not pending_order:
        return redirect(url_for('browse_products'))

    if request.method == 'POST':
        # Get credit card info from form
        card_type = request.form.get('card_type')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')

        # Begin transaction
        conn = sql.connect('database.db')
        conn.row_factory = sql.Row

        try:
            # 1. Get latest product info to ensure it's still available
            cursor = conn.execute('''
                SELECT * FROM Product WHERE product_id = ? AND status = 1
            ''', (pending_order['product_id'],))
            product = cursor.fetchone()

            if not product or product['quantity'] < pending_order['quantity']:
                conn.close()
                return render_template('payment.html',
                                       order=pending_order,
                                       error="Product no longer available in requested quantity.",
                                       user_type=session.get('user_type'))

            # 2. Create the order record
            conn.execute('''
                INSERT INTO Orders (buyer_id, seller_id, product_id, order_date, quantity, amount)
                VALUES (?, ?, ?, datetime('now'), ?, ?)
            ''', (session.get('user_id'),
                  pending_order['seller_id'],
                  pending_order['product_id'],
                  pending_order['quantity'],
                  pending_order['total_amount']))

            # Get the new order ID
            cursor = conn.execute('SELECT last_insert_rowid()')
            order_id = cursor.fetchone()[0]

            # 3. Update product quantity
            new_quantity = product['quantity'] - pending_order['quantity']
            new_status = 2 if new_quantity == 0 else 1  # Set to 'sold' if quantity is 0

            conn.execute('''
                UPDATE Product 
                SET quantity = ?, status = ?
                WHERE product_id = ?
            ''', (new_quantity, new_status, pending_order['product_id']))

            # 4. Update seller balance
            conn.execute('''
                UPDATE Sellers
                SET balance = balance + ?
                WHERE user_id = ?
            ''', (pending_order['total_amount'], pending_order['seller_id']))

            # Commit the transaction
            conn.commit()

            # Clear the pending order from session
            session.pop('pending_order', None)

            # Store completed order for confirmation page
            session['completed_order'] = {
                'order_id': order_id,
                'product_title': pending_order['product_title'],
                'seller_id': pending_order['seller_id'],
                'seller_name': pending_order['seller_name'],
                'quantity': pending_order['quantity'],
                'total_amount': pending_order['total_amount']
            }

            conn.close()
            return redirect(url_for('order_complete'))

        except Exception as e:
            # Rollback in case of error
            conn.rollback()
            conn.close()
            return render_template('payment.html',
                                   order=pending_order,
                                   error=f"An error occurred: {str(e)}",
                                   user_type=session.get('user_type'))

    # GET request - display payment form
    # Get buyer's saved payment methods
    conn = sql.connect('database.db')
    conn.row_factory = sql.Row

    cursor = conn.execute('''
        SELECT * FROM PaymentDetails
        WHERE user_id = ?
        ORDER BY payment_id DESC
    ''', (session.get('user_id'),))
    saved_cards = cursor.fetchall()

    conn.close()

    return render_template('payment.html',
                           order=pending_order,
                           saved_cards=saved_cards,
                           user_type=session.get('user_type'))


@app.route('/order/complete')
def order_complete():
    '''
    Display order confirmation page
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    completed_order = session.get('completed_order')
    # Retrieve the average rating for the product
    conn = sql.connect('database.db')
    print(completed_order)
    print(completed_order['seller_id'])
    cursor = conn.execute('SELECT avg_rating FROM Sellers WHERE user_id = ?', (completed_order['seller_id'],))
    completed_order['seller_rating'] = cursor.fetchone()[0]
    conn.close()
    if not completed_order:
        return redirect(url_for('home'))

    # Clear the completed order from session after showing confirmation
    session.pop('completed_order', None)

    return render_template('order_complete.html',
                           order=completed_order,
                           user_type=session.get('user_type'))

@app.route('/orders')
def view_orders():
    '''
    Displays orders placed by the buyer
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Only buyers can view order history
    if session.get('user_type') != 'Buyer':
        return redirect(url_for('home'))

    buyer_id = session.get('user_id')

    # Retrieve order history
    conn = sql.connect('database.db')
    conn.row_factory = sql.Row

    cursor = conn.execute('''
        SELECT o.*, p.title as product_title, s.business_name as seller_name 
        FROM Orders o
        JOIN Product p ON o.product_id = p.product_id
        JOIN Sellers s ON o.seller_id = s.user_id
        WHERE o.buyer_id = ?
        ORDER BY o.order_date DESC
    ''', (buyer_id,))
    orders = cursor.fetchall()

    conn.close()

    return render_template('orders.html',
                          orders=orders,
                          user_type=session.get('user_type'))


@app.route('/orders/view/<int:order_id>')
def view_order_details(order_id):
    '''
    Displays detailed information about a specific order
    '''
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Only buyers can view order details
    if session.get('user_type') != 'Buyer':
        return redirect(url_for('home'))

    buyer_id = session.get('user_id')

    conn = sql.connect('database.db')
    conn.row_factory = sql.Row

    # Get order information (verify this order belongs to the current buyer)
    cursor = conn.execute('''
        SELECT o.*, p.title as product_title, p.details as product_details, 
               p.price as unit_price, s.business_name as seller_name
        FROM Orders o
        JOIN Product p ON o.product_id = p.product_id
        JOIN Sellers s ON o.seller_id = s.user_id
        WHERE o.order_id = ? AND o.buyer_id = ?
    ''', (order_id, buyer_id))
    order = cursor.fetchone()

    if not order:
        conn.close()
        return redirect(url_for('view_orders'))

    # Retrieve seller's average rating
    rating_row = conn.execute('SELECT avg_rating FROM Sellers WHERE user_id = ?', (order['seller_id'],)).fetchone()
    seller_rating = rating_row[0] if rating_row else 0

    # Check if there's a review for this order
    review_cursor = conn.execute('''
        SELECT * FROM Reviews
        WHERE order_id = ?
    ''', (order_id,))
    review = review_cursor.fetchone()

    conn.close()

    return render_template('order_detail.html',
                          order=order,
                          review=review,
                          seller_rating=seller_rating,
                          user_type=session.get('user_type'))

@app.route('/review/<int:order_id>')
def leave_review(order_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    # Make sure that the user is a buyer since only buyers can leave reviews
    if session.get('user_type') == 'Buyer':
        return render_template('review.html', order_id=order_id)
    else:
        return redirect(url_for('home'))

@app.route('/submit_review/<int:order_id>', methods=['POST'])
def submit_review(order_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Retrieve relevant information pertaining to the product review
    rating = int(request.form['rating'])
    review_text = request.form['review_text']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Connect to the database to update
    conn = sql.connect('database.db')
    cursor = conn.cursor()

    try:
        # Insert the review into the database (Reviews schema)
        cursor.execute('INSERT INTO Reviews (order_id, rating, review_text, timestamp) VALUES (?, ?, ?, ?)', (order_id, rating, review_text, timestamp))
        # Retrieve the seller's ID
        cursor.execute('SELECT seller_id FROM Orders WHERE order_id = ?', (order_id,))

        result = cursor.fetchone()
        if result:
            seller_id = result[0]
            # Update the seller's average rating
            cursor.execute('SELECT AVG(rating) FROM Reviews WHERE order_id IN (SELECT order_id FROM Orders WHERE seller_id = ?)',(seller_id,))
            avg_rating = cursor.fetchone()[0] or 0
            cursor.execute('UPDATE Sellers SET avg_rating = ? WHERE user_id = ?', (avg_rating, seller_id))
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise

    finally:
        conn.close()

    return redirect(url_for('view_order_details', order_id=order_id))

if __name__ == "__main__":
    app.run()
