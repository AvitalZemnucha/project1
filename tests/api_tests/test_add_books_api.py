import pytest
import logging
import random
import string
from project1.config.config import TestConfig

logger = logging.getLogger('pytest')


@pytest.mark.parametrize("title, author, isbn, expected_status, expected_error", [
    ("The story of my life 2025", "Avital Zemnucha", "1234567890", 409,
     "Duplicate book detected! The book is already in the list."),
    ("", "Tofi222", "1020306050", 400, "Missing or empty required fields: title"),
    ("Kofkof", "", "1020306050", 400, "Missing or empty required fields: author"),
    ("Kofkof", "Tofi222", "", 400, "Missing or empty required fields: isbn"),
    ("", "", "", 400, "Missing or empty required fields: title, author, isbn"),
    ("?#$%^&", "Hihi", "1020306050", 400,
     "Title contains special characters, only alphanumeric characters and spaces are allowed."),
    ("MipMip", "MipMip12121", "1020306050", 400, "Author name cannot contain numbers."),
    ("MipMip", "Hihi", "20AAAA203030", 400, "ISBN must be numeric and either 10 or 13 digits long."),

])
@pytest.mark.api
def test_create_book_negative(api_client, title, author, isbn, expected_status, expected_error):
    params = {
        "title": title,
        "author": author,
        "isbn": isbn
    }
    response = api_client.post(TestConfig.API_BOOKS_URL, json=params)
    data = response.json()
    assert response.status_code == expected_status
    assert data['error'] == expected_error


@pytest.mark.api
def test_create_new_book(api_client):  ###verify that it  doesn't exist, use random to generate new book
    # Generate a random book
    title = "Book " + ''.join(random.choices(string.ascii_letters, k=5))
    author = "Author " + ''.join(random.choices(string.ascii_letters, k=5))
    isbn = ''.join(random.choices(string.digits, k=10))

    response = api_client.get(TestConfig.API_BOOKS_URL)
    existing_books = response.json()
    for book in existing_books:
        if book['title'] == title and book['author'] == author and book['isbn'] == isbn:
            pytest.skip("Generated book already exists, skipping test.")

    params = {
        "title": title,
        "author": author,
        "isbn": isbn
    }

    response = api_client.post(TestConfig.API_BOOKS_URL, json=params)
    data = response.json()
    assert response.status_code == 201
    assert data['author'] == author
    assert data['title'] == title
    assert data['isbn'] == isbn
