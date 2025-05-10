from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    stock = db.Column(db.Integer, default=10)
    cart_items = db.relationship('CartItem', backref='book', lazy=True)
    order_items = db.relationship('OrderItem', backref='book', lazy=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)

# Helper functions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('You do not have permission to access this page', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    books = Book.query.all()
    return render_template('index.html', books=books)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book_detail.html', book=book)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        
        # Make the first user an admin
        if User.query.count() == 0:
            new_user.is_admin = True
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/add_to_cart/<int:book_id>', methods=['POST'])
@login_required
def add_to_cart(book_id):
    book = Book.query.get_or_404(book_id)
    quantity = int(request.form.get('quantity', 1))
    
    # Check if book is already in cart
    cart_item = CartItem.query.filter_by(user_id=session['user_id'], book_id=book_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=session['user_id'], book_id=book_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    flash(f'Added {book.title} to your cart', 'success')
    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/cart')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
    total = sum(item.book.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    
    # Ensure the cart item belongs to the current user
    if cart_item.user_id != session['user_id']:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('view_cart'))
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        db.session.delete(cart_item)
    else:
        cart_item.quantity = quantity
    
    db.session.commit()
    flash('Cart updated', 'success')
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
    
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('view_cart'))
    
    total = sum(item.book.price * item.quantity for item in cart_items)
    
    if request.method == 'POST':
        # Create a new order
        new_order = Order(user_id=session['user_id'], total_price=total)
        db.session.add(new_order)
        db.session.flush()  # Get the order ID
        
        # Add order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                book_id=item.book_id,
                quantity=item.quantity,
                price=item.book.price
            )
            db.session.add(order_item)
            
            # Update book stock
            book = item.book
            book.stock -= item.quantity
            
            # Remove from cart
            db.session.delete(item)
        
        db.session.commit()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=new_order.id))
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Ensure the order belongs to the current user
    if order.user_id != session['user_id']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    return render_template('order_confirmation.html', order=order)

@app.route('/orders')
@login_required
def view_orders():
    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.date_ordered.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/search')
def search():
    query = request.args.get('query', '')
    books = Book.query.filter(
        (Book.title.ilike(f'%{query}%')) | 
        (Book.author.ilike(f'%{query}%')) |
        (Book.category.ilike(f'%{query}%'))
    ).all()
    return render_template('search_results.html', books=books, query=query)

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    books_count = Book.query.count()
    users_count = User.query.count()
    orders_count = Order.query.count()
    recent_orders = Order.query.order_by(Order.date_ordered.desc()).limit(5).all()
    return render_template('admin/dashboard.html', 
                          books_count=books_count, 
                          users_count=users_count, 
                          orders_count=orders_count,
                          recent_orders=recent_orders)

@app.route('/admin/books')
@admin_required
def admin_books():
    books = Book.query.all()
    return render_template('admin/books.html', books=books)

@app.route('/admin/books/add', methods=['GET', 'POST'])
@admin_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        image_url = request.form.get('image_url')
        category = request.form.get('category')
        stock = int(request.form.get('stock', 10))
        
        new_book = Book(
            title=title,
            author=author,
            description=description,
            price=price,
            image_url=image_url,
            category=category,
            stock=stock
        )
        
        db.session.add(new_book)
        db.session.commit()
        
        flash('Book added successfully', 'success')
        return redirect(url_for('admin_books'))
    
    return render_template('admin/add_book.html')

@app.route('/admin/books/edit/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.description = request.form.get('description')
        book.price = float(request.form.get('price'))
        book.image_url = request.form.get('image_url')
        book.category = request.form.get('category')
        book.stock = int(request.form.get('stock', 10))
        
        db.session.commit()
        
        flash('Book updated successfully', 'success')
        return redirect(url_for('admin_books'))
    
    return render_template('admin/edit_book.html', book=book)

@app.route('/admin/books/delete/<int:book_id>', methods=['POST'])
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    
    flash('Book deleted successfully', 'success')
    return redirect(url_for('admin_books'))

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/orders')
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.date_ordered.desc()).all()
    return render_template('admin/orders.html', orders=orders)

# Initialize the database
@app.cli.command('init-db')
def init_db_command():
    db.create_all()
    
    # Add sample data if database is empty
    if Book.query.count() == 0:
        sample_books = [
            {
                'title': 'Python Crash Course',
                'author': 'Eric Matthes',
                'description': 'A hands-on, project-based introduction to programming.',
                'price': 29.99,
                'image_url': 'https://m.media-amazon.com/images/I/71L4J6Vf-LL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Programming',
                'stock': 15
            },
            {
                'title': 'Clean Code',
                'author': 'Robert C. Martin',
                'description': 'A handbook of agile software craftsmanship.',
                'price': 34.99,
                'image_url': 'https://m.media-amazon.com/images/I/41xShlnTZTL._SX376_BO1,204,203,200_.jpg',
                'category': 'Programming',
                'stock': 10
            },
            {
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'description': 'A classic novel about the American Dream.',
                'price': 12.99,
                'image_url': 'https://m.media-amazon.com/images/I/71FTb9X6wsL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Fiction',
                'stock': 20
            },
            {
                'title': 'To Kill a Mockingbird',
                'author': 'Harper Lee',
                'description': 'A novel about racial injustice and moral growth.',
                'price': 14.99,
                'image_url': 'https://m.media-amazon.com/images/I/71FxgtFKcQL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Fiction',
                'stock': 18
            },
            {
                'title': 'The Art of War',
                'author': 'Sun Tzu',
                'description': 'An ancient Chinese text on military strategy.',
                'price': 9.99,
                'image_url': 'https://m.media-amazon.com/images/I/71dNsRuYL7L._AC_UF1000,1000_QL80_.jpg',
                'category': 'Philosophy',
                'stock': 25
            },
            {
                'title': 'The Alchemist',
                'author': 'Paulo Coelho',
                'description': 'A philosophical novel about following your dreams.',
                'price': 15.99,
                'image_url': 'https://m.media-amazon.com/images/I/71zHDXu1TlL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Fiction',
                'stock': 22
            },
            {
                'title': 'Sapiens: A Brief History of Humankind',
                'author': 'Yuval Noah Harari',
                'description': 'A survey of the history of humankind from the evolution of archaic human species in the Stone Age up to the twenty-first century.',
                'price': 24.99,
                'image_url': 'https://m.media-amazon.com/images/I/71N3-2sYDRL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Non-Fiction',
                'stock': 17
            },
            {
                'title': 'Thinking, Fast and Slow',
                'author': 'Daniel Kahneman',
                'description': 'A book that summarizes research that Kahneman conducted over decades, often in collaboration with Amos Tversky.',
                'price': 19.99,
                'image_url': 'https://m.media-amazon.com/images/I/61fdrEuPJwL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Psychology',
                'stock': 14
            },
            {
                'title': 'The Pragmatic Programmer',
                'author': 'Andrew Hunt and David Thomas',
                'description': 'A guide to software development best practices.',
                'price': 39.99,
                'image_url': 'https://m.media-amazon.com/images/I/51W1sBPO7tL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Programming',
                'stock': 12
            },
            {
                'title': 'Dune',
                'author': 'Frank Herbert',
                'description': 'A science fiction novel about a desert planet and its inhabitants.',
                'price': 18.99,
                'image_url': 'https://m.media-amazon.com/images/I/81ym3QUd3KL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Science Fiction',
                'stock': 20
            },
            {
                'title': 'The Hobbit',
                'author': 'J.R.R. Tolkien',
                'description': 'A fantasy novel about a hobbit who goes on an adventure.',
                'price': 16.99,
                'image_url': 'https://m.media-amazon.com/images/I/710+HcoP38L._AC_UF1000,1000_QL80_.jpg',
                'category': 'Fantasy',
                'stock': 25
            },
            {
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'description': 'A romantic novel of manners about the pursuit of marriage in early 19th-century England.',
                'price': 11.99,
                'image_url': 'https://m.media-amazon.com/images/I/71Q1tPupKjL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Fiction',
                'stock': 18
            },
            {
                'title': 'The Catcher in the Rye',
                'author': 'J.D. Salinger',
                'description': 'A novel about a teenager\'s experiences in New York City.',
                'price': 13.99,
                'image_url': 'https://m.media-amazon.com/images/I/61fgOuZfBGL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Fiction',
                'stock': 15
            },
            {
                'title': 'The Lord of the Rings',
                'author': 'J.R.R. Tolkien',
                'description': 'An epic high-fantasy novel about a quest to destroy a powerful ring.',
                'price': 29.99,
                'image_url': 'https://m.media-amazon.com/images/I/71jLBXtWJWL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Fantasy',
                'stock': 22
            },
            {
                'title': 'Harry Potter and the Philosopher\'s Stone',
                'author': 'J.K. Rowling',
                'description': 'The first novel in the Harry Potter series about a young wizard.',
                'price': 17.99,
                'image_url': 'https://m.media-amazon.com/images/I/81iqZ2HHD-L._AC_UF1000,1000_QL80_.jpg',
                'category': 'Fantasy',
                'stock': 30
            },
            {
                'title': 'The Da Vinci Code',
                'author': 'Dan Brown',
                'description': 'A mystery thriller novel about a murder in the Louvre Museum in Paris.',
                'price': 15.99,
                'image_url': 'https://m.media-amazon.com/images/I/91Q5dCjc2KL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Mystery',
                'stock': 20
            },
            {
                'title': 'The Hunger Games',
                'author': 'Suzanne Collins',
                'description': 'A dystopian novel set in a post-apocalyptic society.',
                'price': 14.99,
                'image_url': 'https://m.media-amazon.com/images/I/71WSzS6zvCL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Science Fiction',
                'stock': 25
            },
            {
                'title': 'The Shining',
                'author': 'Stephen King',
                'description': 'A horror novel about a family staying at an isolated hotel.',
                'price': 16.99,
                'image_url': 'https://m.media-amazon.com/images/I/71tFhdcC0XL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Horror',
                'stock': 18
            },
            {
                'title': 'The Girl with the Dragon Tattoo',
                'author': 'Stieg Larsson',
                'description': 'A psychological thriller novel about a journalist and a hacker.',
                'price': 18.99,
                'image_url': 'https://m.media-amazon.com/images/I/81+LZJKrhmL._AC_UF1000,1000_QL80_.jpg',
                'category': 'Mystery',
                'stock': 15
            },
            {
                'title': 'The Road',
                'author': 'Cormac McCarthy',
                'description': 'A post-apocalyptic novel about a father and son\'s journey.',
                'price': 15.99,
                'image_url': 'https://m.media-amazon.com/images/I/71IJ1HC2a0L._AC_UF1000,1000_QL80_.jpg',
                'category': 'Fiction',
                'stock': 12
            }
        ]
        
        for book_data in sample_books:
            book = Book(**book_data)
            db.session.add(book)
        
        db.session.commit()
        print('Initialized the database with sample data.')
    else:
        print('Database already contains data.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
