## Project Description / Context

NittanyBusiness is a prototype web application for a B2B online marketplace, designed to streamline procurement for small and medium-sized enterprises (SMEs) by connecting them with trusted suppliers. Built with Flask, Python, and SQLite, this system supports role-based access (Buyer, Seller, HelpDesk) and demonstrates core e-commerce flows (user authentication, category browsing, product listings, order processing, reviews, and search) backed by a relational database design.

___

## Directory Structure/File Organization

```plaintext
NittanyBusiness/
├── app.py
├── init_db.py
├── database.db
└── templates/
    ├── category.html
    ├── edit_product.html
    ├── email_change_request.html
    ├── email_change_success.html
    ├── home.html
    ├── index.html
    ├── new_product.html
    ├── order_complete.html
    ├── order_detail.html
    ├── order_review.html
    ├── orders.html
    ├── payment.html
    ├── product_detail.html
    ├── products.html
    ├── registration.html
    ├── review.html
    ├── search_results.html
    ├── seller_feedback.html
    ├── seller_products.html
    └── user_profile.html
```

The files in our app are organized with the following logic: 
At the top level, we have all of our business logic in `app.py`. 
This file contains the routines that sit between the front end
(`.html` files in `templates`) and the backend of our application
(the database, `database.db`). The main application logic defined 
here allows us to give users permissioned
access to retrieve and send data to and from the database. The logic 
to initialize the database is contained within `init_db.py`, which
contains all `CREATE TABLE` statements and fills the database according
to the provided csv files. In the `templates` directory, we have the html
files for the frontend of our application, outlining the visual user
experience and containing forms that hold data for our business logic
in `app.py` to use in order to query 
and display information to and from the database.

___

## Implemented Features and Functionalities
For this application, we implemented the following 8 core features as outlined in the assignment description (no extra credit features): 
1. **User Login**  
   - Secure authentication by email & password (hashed in the database).  
   - Role detection (Buyer, Seller, HelpDesk) on login.  
   - Redirection to a role-specific welcome/dashboard page.  
     - *Buyer*: manage profile, browse categories/products, shopping cart, place orders.  
     - *Seller*: view/edit published products, manage inventory, read buyer feedback.  
     - *HelpDesk*: view & claim pending requests (e.g., category-creation, email-change), manage users.

2. **Category Hierarchy**  
   - Dynamic retrieval of “All” → subcategories → products from the database.  
   - Clickable navigation: drilling into subcategories and viewing associated products.  
   - Product links lead to detailed pages (price, seller info, reviews & ratings).  
   - Implementation note: categories and their tree structure are queried on demand, not hard-coded.

3. **Product Listing Management**  
   - Sellers can create a listing by providing title, description, category, price & quantity.  
   - Listings default to **active**; sellers can edit details or mark them **inactive**.  
   - Inventory depletion automatically flags listings as **sold** when quantity reaches zero.  
   - Historical records retained in the database even after deactivation.

4. **Order Management**  
   - Buyers select quantity on the product page, review order summary (item, seller, unit price, total).  
   - Secure checkout with new or saved credit-card details.  
   - On confirmation:  
     - Inventory updated and status toggled to **sold** if depleted.  
     - Seller’s account balance credited with the order total.

5. **Product & Seller Review**  
   - Post-purchase, buyers can submit a ★1–5 rating and textual review.  
   - Ratings update the seller’s average score, visible on product pages and confirmations.

6. **Product Search**  
   - Keyword search over product title, description, category, or seller name.  
   - Optional price-range filtering.  
   - Results display name, price, seller info, and availability.  
   - Implemented via SQL queries—no external search libraries.

7. **User Registration**  
   - Self-service sign-up for Buyers and Sellers 
   - Capture role and essential personal details for authentication and profile management.

8. **User Profile Update**  
   - Logged-in users can update personal details (name, address, etc.) 
   - Customers can also update their email (user ID) by submitting a request to the helpdesk.

---


## How to Run
1. Open PyCharm and select 'Import Project' or 'Open' to load this folder
2. Right-click on app.py and hit Run 'Flask (app.py)'
3. PyCharm will start the server and output the message 'Running on http://127.0.0.1:5000/'
4. Click the provided link or copy it into a browser to access the application
