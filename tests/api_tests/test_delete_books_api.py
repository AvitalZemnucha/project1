import pytest
import logging
from project1.config.config import TestConfig
import random

logger = logging.getLogger('pytest')


@pytest.mark.api
@pytest.mark.parametrize("book_id, expected_status, expected_error", [
    ("khkhkhk", 404, "Resource not found"),
    (-1, 404, "Resource not found"),
    (999999, 404, "Book not found")
])
def test_deleting_invalid_or_non_existing_book(api_client, book_id, expected_status, expected_error):
    response = api_client.delete(f"{TestConfig.API_BOOKS_URL}/{book_id}")
    data = response.json()
    assert response.status_code == expected_status
    assert data['error'] == expected_error


@pytest.mark.api
def test_deleting_an_existing_book(api_client):
    get_response = api_client.get(TestConfig.API_BOOKS_URL)
    assert get_response.status_code == 200
    books_data = get_response.json()
    if not books_data:
        pytest.skip("No books available to delete")

    random_book = random.choice(books_data)
    book_id = random_book["id"]

    delete_response = api_client.delete(f"{TestConfig.API_BOOKS_URL}/{book_id}")

    assert delete_response.status_code == 204, f"Failed to delete book with ID {book_id}"

    check_response = api_client.get(f"{TestConfig.API_BOOKS_URL}/{book_id}")
    assert check_response.status_code == 404, f"Book with ID {book_id} still exists after deletion"


@pytest.mark.api
def test_deleting_a_non_existing_book(api_client):
    get_response = api_client.get(TestConfig.API_BOOKS_URL)
    assert get_response.status_code == 200
    books_data = get_response.json()
    if not books_data:
        random_book = random.choice(books_data)
        book_id = random_book["id"]
        delete_response = api_client.delete(f"{TestConfig.API_BOOKS_URL}/{book_id}")
        assert delete_response.status_code == 404, f"Book with ID {book_id} still exists after deletion"
