class TestConfig:
    BASE_URL = "http://localhost:5000"
    API_LOGIN_URL = "http://localhost:5000/login"
    API_LOGOUT_URL = "http://localhost:5000/logout"
    API_BOOKS_URL = "http://localhost:5000/api/books"
    IMPLICIT_WAIT = 10
    EXPLICIT_WAIT = 10
    API_KEY = "your_test_api_key"
    DB_CONNECTION = {
        "host": "localhost",
        "database": "bookstore",
        "user": "test_user",
        "password": "test_password"
    }
    API_LOGIN_PAYLOAD = {
        "username": "test_user",
        "password": "test_pass123"
    }
