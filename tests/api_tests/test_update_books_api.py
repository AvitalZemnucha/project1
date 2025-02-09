import pytest
import logging
import random
import string
from project1.config.config import TestConfig

logger = logging.getLogger('pytest')


@pytest.mark.api
@pytest.mark.parametrize("book_id, author, title, isbn, expected_status, expected_error", [
    (600, "Avital Zemnucha", "The story of my life 2025", "011119852025", 404, "Book not found"),
    (41, "AAAAvital Zemnucha", "The story of my life 2025", "01111985202577", 409,
     ["A book with this title already exists",
      "A book by this author already exists",
      "A book with this ISBN already exists"]),
    (41, "AAAAvital Zemnucha", "The story of my life 2025", "01111985202577", 409,
     ["A book with this title already exists",
      "A book by this author already exists",
      "A book with this ISBN already exists"]),
    (41, "Avital Zemnucha", "AAAThe story of my life 2025", "01111985202577", 409,
     ["A book with this ISBN already exists"]),
    (41, "Avital Zemnucha", "The story of my life 2025", "8989898989", 409, ["A book with this title already exists"]),
    (23, "AAAvital Zemnucha", "AAAThe story of my life 2025", "", 400, "Missing or empty required fields: isbn"),
    (23, "AAAvital Zemnucha", "", "2323232323232", 400, "Missing or empty required fields: title"),
    (23, "", "The story of my life 2025", "2323232323232", 400, "Missing or empty required fields: author"),
    (23, "Test Author", "trigger_error", "1234567890", 500, "This is a simulated internal server error")

])
def test_update_book_negative(api_client, book_id, author, title, isbn, expected_status, expected_error):
    params = {
        "author": author,
        "title": title,
        "isbn": isbn
    }
    response = api_client.put(f"{TestConfig.API_BOOKS_URL}/{book_id}", json=params)
    data = response.json()
    print(f"Response JSON: {data}")

    assert response.status_code == expected_status
    assert data.get("error") == expected_error or data.get("errors") == expected_error
