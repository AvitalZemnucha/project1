import pytest
import logging
from project1.config.config import TestConfig

logger = logging.getLogger('pytest')


@pytest.mark.api
def test_get_all_books(api_client):
    response = api_client.get(TestConfig.API_BOOKS_URL)
    data = response.json()
    assert response.status_code == 200
    assert len(data) > 0
    expected_keys = {"author", "id", "isbn", "title"}
    assert expected_keys.issubset(data[0].keys())
    assert data[0]['title'] == "Mama Mia"


@pytest.mark.parametrize("book_id, expected_status, expected_error", [
    (26, 200, None),
    ("", 404, "Resource not found"),
    (999, 404, "Resource not found"),
    ("uuuuu", 404, "Resource not found")

])
@pytest.mark.api
def test_get_book_by_id_negative_positive(api_client, book_id, expected_status, expected_error):
    response = api_client.get(f"{TestConfig.API_BOOKS_URL}/{book_id}")
    data = response.json()
    assert response.status_code == expected_status
    if expected_status == 200:
        assert "id" in data and type(data['id']) == int
        assert "author" in data and type(data['author']) == str
        assert "title" in data and type(data['title']) == str
        assert "isbn" in data and type(data['isbn']) == str
    else:
        assert data['error'] == expected_error


@pytest.mark.parametrize("q, field, expected_status, expected_error", [
    ("Mama mia", "title", 200, None),
    ("John Doe", "author", 200, None),
    ("5729134851528", "isbn", 200, None),
    ("Mama mia", "title_id_autor", 400, "Invalid search field"),
    ("Titanic", "title", 400, "No books found matching the search criteria"),
    ("John Doe", "", 200, None),
    ("", "", 400, "Search query is required"),
])
@pytest.mark.api
def test_search_book(api_client, q, field, expected_status, expected_error):
    param = {
        "q": q
    }
    if field:
        param["field"] = field
    response = api_client.get(f"{TestConfig.API_BOOKS_URL}/search", params=param)
    data = response.json()
    assert response.status_code == expected_status
    if expected_status == 200:
        assert "author" in data[0]
        assert "id" in data[0]
        assert "title" in data[0]
        assert "isbn" in data[0]

    else:
        assert data['error'] == expected_error
