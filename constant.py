# URLs
LOGIN_URL = "login"
BOOKS_URL = "books"

# Test User Credentials
VALID_USER = "test_user"
VALID_PASSWORD = "test_pass123"
INVALID_USER = "wrong_user"
INVALID_PASSWORD = "wrong_password"

# Error Messages
ERROR_EMPTY_USERNAME = "Username is required"
ERROR_EMPTY_PASSWORD = "Password is required"
ERROR_INVALID_USERNAME = "Username not found"
ERROR_INVALID_PASSWORD = "Incorrect password"
ERROR_EMPTY_BOTH = "Username and password are required"

# Test Book Data
TEST_BOOK = {
    "title": "Test Book",
    "author": "Test Author",
    "isbn": "1234567890"
}

# Common Test Data for Book Tests
from project1.utils.utils import generate_random_string, generate_random_isbn

BOOK_TEST_CASES = [
    (generate_random_string(6), "", "", ["title"], None),
    ("", generate_random_string(6), "", ["author"], None),
    ("", "", generate_random_isbn(), ["isbn"], None),
    (generate_random_string(6), generate_random_string(6), "", ["title", "author"], None),
    (generate_random_string(6), "", generate_random_isbn(), ["title", "isbn"], None),
    ("", generate_random_string(6), generate_random_isbn(), ["author", "isbn"], None),
    (generate_random_string(6), generate_random_string(6), generate_random_isbn(), ["title", "author", "isbn"], None),
    ("", "", "", [], "Please fill out at least one field.")
]
