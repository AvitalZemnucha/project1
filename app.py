# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
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
        # Create test user if it doesn't exist
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
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Validation checks
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


@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.get_json()

    # Validate required fields
    if not all(key in data for key in ['title', 'author', 'isbn']):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if the book already exists by ISBN (or title/author combination)
    existing_book = Book.query.filter_by(isbn=data['isbn']).first()
    if existing_book:
        return jsonify({'error': 'Duplicate book detected! The book is already in the list.'}), 409

    try:
        new_book = Book(
            title=data['title'],
            author=data['author'],
            isbn=data['isbn']
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
    book = Book.query.get_or_404(book_id)
    data = request.get_json()

    if not all(key in data for key in ['title', 'author', 'isbn']):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        book.title = data['title']
        book.author = data['author']
        book.isbn = data['isbn']
        db.session.commit()
        return jsonify({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'isbn': book.isbn
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    return jsonify({
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'isbn': book.isbn
    })


@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    try:
        db.session.delete(book)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True, port=5000)
