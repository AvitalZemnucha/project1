from flask import Flask, render_template, request, jsonify, session, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="test_user").first():
            test_user = User(username="test_user", password="test_pass123")
            db.session.add(test_user)
            db.session.commit()


# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Check if the request is JSON
        if request.is_json:
            data = request.get_json()

            if not data:
                return jsonify({"error": "No data provided"}), 400

            username = data.get('username', '').strip()
            password = data.get('password', '').strip()

            if not username or not password:
                return jsonify({"error": "Username and password are required"}), 400

            user = User.query.filter_by(username=username).first()

            if not user:
                return jsonify({"error": "Invalid username"}), 401

            if user.password != password:
                return jsonify({"error": "Invalid password"}), 401

            session['user_id'] = user.id
            return jsonify({"message": "Login successful"}), 200

        # Handle form-based login
        else:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            if not username and not password:
                return render_template('login.html', error="Username and password are required")
            if not username:
                return render_template('login.html', error="Username is required")
            if not password:
                return render_template('login.html', error="Password is required")

            user = User.query.filter_by(username=username).first()

            if not user:
                return render_template('login.html', error="Username not found")
            if user.password != password:
                return render_template('login.html', error="Incorrect password")

            session['user_id'] = user.id
            return redirect(url_for('books'))

    # GET request: Show login page
    return render_template('login.html')


@app.route('/books')
def books():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    books_list = Book.query.all()
    return render_template('books.html', books=books_list)


@app.route('/logout')
def logout():
    # Check if the user is logged in
    if 'user_id' not in session:
        return jsonify({"error": "You are not logged in"}), 403  # Reject if no session exists

    # Ensure the session cookie is sent in the request
    if "session" not in request.cookies:
        return jsonify({"error": "Session cookie missing"}), 403

    # Remove session and return response
    session.pop('user_id', None)
    response = jsonify({"message": "Logged out successfully"})
    response.set_cookie('session', '', expires=0)  # Clears the session cookie
    return response


# API Routes
@app.route('/api/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify([{
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'isbn': book.isbn
    } for book in books])


@app.route('/api/books/search', methods=['GET'])
def search_books():
    query = request.args.get('q', '')
    field = request.args.get('field', 'all')

    if not query:
        return jsonify({'error': 'Search query is required'}), 400

    if field not in ['all', 'title', 'author', 'isbn']:
        return jsonify({'error': 'Invalid search field'}), 400

    books_query = Book.query

    if field == 'all':
        books = books_query.filter(
            (Book.title.ilike(f'%{query}%')) |
            (Book.author.ilike(f'%{query}%')) |
            (Book.isbn.ilike(f'%{query}%'))
        ).all()
    elif field == 'title':
        books = books_query.filter(Book.title.ilike(f'%{query}%')).all()
    elif field == 'author':
        books = books_query.filter(Book.author.ilike(f'%{query}%')).all()
    elif field == 'isbn':
        books = books_query.filter(Book.isbn.ilike(f'%{query}%')).all()

    # **Fix: Return error if no books are found**
    if not books:
        return jsonify({'error': 'No books found matching the search criteria'}), 400

    return jsonify([{
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'isbn': book.isbn
    } for book in books])


@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get(book_id)
    if book is None:
        abort(404)
    return jsonify({
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'isbn': book.isbn
    }), 200


import re


@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.get_json()

    required_fields = ['title', 'author', 'isbn']
    missing_fields = [field for field in required_fields if field not in data or not data[field].strip()]

    if missing_fields:
        return jsonify({'error': f"Missing or empty required fields: {', '.join(missing_fields)}"}), 400

    # Check for duplicate ISBN
    existing_book = Book.query.filter_by(isbn=data['isbn']).first()
    if existing_book:
        return jsonify({'error': 'Duplicate book detected! The book is already in the list.'}), 409

    try:
        # Title, author, and ISBN must not be empty or whitespace only
        title = data['title'].strip()
        author = data['author'].strip()
        isbn = data['isbn'].strip()

        if not title or not author or not isbn:
            return jsonify({'error': 'Title, Author, or ISBN cannot be empty or whitespace only.'}), 400

        # Check for special characters in title
        if not re.match("^[a-zA-Z0-9\s]*$", title):  # Only alphanumeric and space allowed
            return jsonify({
                'error': 'Title contains special characters, only alphanumeric characters and spaces are allowed.'}), 400

        # Check if author contains numbers
        if re.search(r'\d', author):  # If any digit is found in author name
            return jsonify({'error': 'Author name cannot contain numbers.'}), 400

        # Validate ISBN (should only contain digits and be 10 or 13 characters long)
        if not re.match(r'^\d{10}(\d{3})?$', isbn):  # Matches 10 or 13 digit ISBN
            return jsonify({'error': 'ISBN must be numeric and either 10 or 13 digits long.'}), 400

        new_book = Book(
            title=title,
            author=author,
            isbn=isbn
        )
        db.session.add(new_book)
        db.session.commit()

        return jsonify({
            'id': new_book.id,
            'title': new_book.title,
            'author': new_book.author,
            'isbn': new_book.isbn
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    app.logger.info(f"Received PUT request for book ID {book_id}")
    app.logger.info(f"Request headers: {dict(request.headers)}")

    # Ensure we have JSON data
    if not request.is_json:
        app.logger.error("Request does not contain JSON data")
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    # Parse the incoming JSON data
    try:
        data = request.get_json()
        app.logger.info(f"Request data: {data}")
    except Exception as e:
        app.logger.error(f"Error parsing JSON data: {e}")
        return jsonify({'error': 'Invalid JSON format'}), 400

    # Simulate an internal server error for testing
    if data.get('title', '').lower() == 'trigger_error':
        app.logger.error("Intentional internal server error triggered")
        return jsonify({"error": "This is a simulated internal server error"}), 500

    # Fetch the book by ID
    book = Book.query.get(book_id)
    if not book:
        app.logger.error(f"Book with ID {book_id} not found")
        return jsonify({'error': 'Book not found'}), 404

    # Validate required fields (ensure they exist in request data)
    required_fields = ['title', 'author', 'isbn']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        error_message = f"Missing required fields: {', '.join(missing_fields)}"
        app.logger.error(error_message)
        return jsonify({'error': error_message}), 400

    # Strip values and check for empty fields
    title = data['title'].strip()
    author = data['author'].strip()
    isbn = data['isbn'].strip()

    empty_fields = [field for field in required_fields if not data[field].strip()]
    if empty_fields:
        error_message = f"Missing or empty required fields: {', '.join(empty_fields)}"
        app.logger.error(error_message)
        return jsonify({'error': error_message}), 400

    # Check for conflicts with other books
    errors = []

    # Title conflict check
    if Book.query.filter(Book.title == title, Book.id != book_id).first():
        errors.append("A book with this title already exists")

    # Author conflict check
    if Book.query.filter(Book.author == author, Book.id != book_id).first():
        errors.append("A book by this author already exists")

    # ISBN conflict check
    if Book.query.filter(Book.isbn == isbn, Book.id != book_id).first():
        errors.append("A book with this ISBN already exists")

    # If any conflicts exist, return all errors with a 409 status
    if errors:
        app.logger.info(f"Validation errors found: {errors}")
        return jsonify({'errors': errors}), 409

    # Update the book record
    try:
        book.title = title
        book.author = author
        book.isbn = isbn
        db.session.commit()

        app.logger.info(f"Successfully updated book {book_id}")
        return jsonify({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'isbn': book.isbn
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating book: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    try:
        db.session.delete(book)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Resource not found"}), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(error):
    if request.path.startswith('/api/'):
        return jsonify({"error": "An unexpected error occurred"}), 500
    return render_template('500.html'), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
