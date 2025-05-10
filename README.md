# E-Library: A Flask E-Commerce Website

E-Library is a simple e-commerce website built with Flask that allows users to browse, search, and purchase books online. It includes user authentication, shopping cart functionality, order management, and an admin panel.

## Features

- User authentication (register, login, logout)
- Browse books by category
- Search functionality
- Book details page
- Shopping cart
- Checkout process
- Order history
- Admin panel for managing books, users, and orders

## Installation

1. Clone the repository:
\`\`\`bash
git clone https://github.com/yourusername/e-library.git
cd e-library
\`\`\`

2. Create a virtual environment and activate it:
\`\`\`bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
\`\`\`

3. Install the required packages:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. Initialize the database with sample data:
\`\`\`bash
flask init-db
\`\`\`

5. Run the application:
\`\`\`bash
flask run
\`\`\`

6. Open your browser and navigate to `http://127.0.0.1:5000/`

## Project Structure

\`\`\`
e-library/
├── app.py                 # Main application file
├── templates/             # HTML templates
│   ├── base.html          # Base template with layout
│   ├── index.html         # Homepage
│   ├── book_detail.html   # Book details page
│   ├── login.html         # Login page
│   ├── register.html      # Registration page
│   ├── cart.html          # Shopping cart page
│   ├── checkout.html      # Checkout page
│   ├── orders.html        # Order history page
│   ├── admin/             # Admin templates
│       ├── dashboard.html # Admin dashboard
│       ├── books.html     # Manage books
│       ├── users.html     # Manage users
│       ├── orders.html    # Manage orders
├── static/                # Static files (CSS, JS, images)
├── requirements.txt       # Required packages
└── README.md              # Project documentation
\`\`\`

## Database Models

- **User**: Stores user information and authentication details
- **Book**: Contains book information (title, author, price, etc.)
- **CartItem**: Represents items in a user's shopping cart
- **Order**: Stores order information
- **OrderItem**: Represents items in an order

## Usage

### User Functionality

1. **Register/Login**: Create an account or log in to an existing account
2. **Browse Books**: View all books or filter by category
3. **Search**: Search for books by title, author, or category
4. **Add to Cart**: Add books to your shopping cart
5. **Checkout**: Complete the purchase process
6. **View Orders**: See your order history

### Admin Functionality

The first user registered will automatically become an admin. Admin users can:

1. **Manage Books**: Add, edit, or delete books
2. **View Users**: See all registered users
3. **Manage Orders**: View all orders placed on the site

## Requirements

- Python 3.9+
- Flask
- Flask-SQLAlchemy
- Werkzeug

## License

This project is licensed under the MIT License - see the LICENSE file for details.
\`\`\`

```txt file="requirements.txt"
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Werkzeug==3.0.2
