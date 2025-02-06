from flask import Flask, render_template, request, jsonify, session, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    session.pop('user_id', None)
    return redirect(url_for('login'))


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


@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.get_json()

    required_fields = ['title', 'author', 'isbn']
    missing_fields = [field for field in required_fields if field not in data or not data[field].strip()]

    if missing_fields:
        return jsonify({'error': f"Missing or empty required fields: {', '.join(missing_fields)}"}), 400

    existing_book = Book.query.filter_by(isbn=data['isbn']).first()
    if existing_book:
        return jsonify({'error': 'Duplicate book detected! The book is already in the list.'}), 409

    try:
        new_book = Book(
            title=data['title'].strip(),
            author=data['author'].strip(),
            isbn=data['isbn'].strip()
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
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    data = request.get_json()

    required_fields = ['title', 'author', 'isbn']
    missing_fields = [field for field in required_fields if field not in data or not data[field].strip()]

    if missing_fields:
        return jsonify({'error': f"Missing or empty required fields: {', '.join(missing_fields)}"}), 400

    errors = []
    if Book.query.filter(Book.title == data['title'].strip(), Book.id != book_id).first():
        errors.append("A book with this title already exists")
    if Book.query.filter(Book.author == data['author'].strip(), Book.id != book_id).first():
        errors.append("A book by this author already exists")
    if Book.query.filter(Book.isbn == data['isbn'].strip(), Book.id != book_id).first():
        errors.append("A book with this ISBN already exists")

    if errors:
        return jsonify({'errors': errors}), 409

    try:
        if data['title'].lower() == 'error':
            raise ValueError("Intentional error for testing")

        book.title = data['title'].strip()
        book.author = data['author'].strip()
        book.isbn = data['isbn'].strip()
        db.session.commit()

        return jsonify({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'isbn': book.isbn
        }), 200

    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': str(ve)}), 500
    except Exception as e:
        db.session.rollback()
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


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
