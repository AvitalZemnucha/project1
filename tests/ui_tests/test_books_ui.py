import time

import pytest
from project1.pages.book_page import BookPage
from project1.constant import *
from project1.config.config import TestConfig
from project1.utils.utils import generate_random_string, generate_random_isbn


@pytest.mark.ui
@pytest.mark.parametrize("title, author, isbn, expected_field_updated, expected_alert", BOOK_TEST_CASES)
def test_add_book(logged_in_driver, title, author, isbn, expected_field_updated, expected_alert):
    logged_in_driver.get(f"{TestConfig.BASE_URL}/{BOOKS_URL}")
    book_page = BookPage(logged_in_driver)
    before_edit = book_page.get_book_list()
    alert_text = book_page.add_book(title, author, isbn)

    if alert_text:
        logged_in_driver.refresh()
        after_edit = book_page.get_book_list()
        assert len(before_edit) == len(after_edit), "Book was not updated!"
        updated_book = after_edit[-1]
        if "title" in expected_field_updated:
            assert updated_book["title"] == title, f"Title was not updated to {title}"
        if "author" in expected_field_updated:
            assert updated_book["author"] == author, f"Author was not updated to {author}"
        if "isbn" in expected_field_updated:
            assert updated_book["isbn"] == str(isbn), f"ISBN was not updated to {isbn}"


@pytest.mark.ui
def test_cancel_book(logged_in_driver):
    random_title = generate_random_string(10)
    random_author = generate_random_string(8)
    random_isbn = generate_random_isbn()

    logged_in_driver.get(f"{TestConfig.BASE_URL}/{BOOKS_URL}")
    book_page = BookPage(logged_in_driver)
    book_page.add_book(random_title, random_author, random_isbn)
    book_page.book_cancel()
    logged_in_driver.refresh()
    book_list = book_page.get_book_list()
    assert book_list, "Book list is empty"
    last_book = book_list[-1]
    assert last_book['title'] != random_title


@pytest.mark.ui
def test_delete_book(logged_in_driver):
    logged_in_driver.get(f"{TestConfig.BASE_URL}/{BOOKS_URL}")
    book_page = BookPage(logged_in_driver)
    book_list_before = book_page.get_book_list()
    book_page.book_delete()
    book_list_after = book_page.get_book_list()
    assert len(book_list_after) == len(book_list_before) - 1, "Book was not deleted!"


@pytest.mark.ui
@pytest.mark.parametrize("title, author, isbn, expected_field_updated, expected_alert", BOOK_TEST_CASES)
def test_edit_book(logged_in_driver, title, author, isbn, expected_field_updated, expected_alert):
    logged_in_driver.get(f"{TestConfig.BASE_URL}/{BOOKS_URL}")
    book_page = BookPage(logged_in_driver)
    before_edit = book_page.get_book_list()
    alert_text = book_page.book_edit(title, author, isbn)
    if alert_text:
        logged_in_driver.refresh()
        after_edit = book_page.get_book_list()
        assert len(before_edit) == len(after_edit), "Book was not updated!"
        updated_book = after_edit[-1]
        if "title" in expected_field_updated:
            assert updated_book["title"] == title, f"Title was not updated to {title}"
        if "author" in expected_field_updated:
            assert updated_book["author"] == author, f"Author was not updated to {author}"
        if "isbn" in expected_field_updated:
            assert updated_book["isbn"] == str(isbn), f"ISBN was not updated to {isbn}"


def test_duplicate_book(logged_in_driver):
    random_title = generate_random_string(10)
    random_author = generate_random_string(8)
    random_isbn = generate_random_isbn()
    logged_in_driver.get(f"{TestConfig.BASE_URL}/{BOOKS_URL}")
    book_page = BookPage(logged_in_driver)
    book_page.add_book(random_title, random_author, random_isbn)
    print(f"first time = random title: {random_title}, random_author:{random_author}, random_isbn:{random_isbn}")
    book_page.book_save()
    logged_in_driver.refresh()
    # random_isbn1 = generate_random_isbn()
    book_page.add_book(random_title, random_author, random_isbn)
    print(f"second time = random title: {random_title}, random_author:{random_author}, random_isbn:{random_isbn}")
    book_page.book_save()
    # time.sleep(2)
    alert_text = book_page.is_duplicated_message()
    assert alert_text is not None, "Expected an alert, but none was found!"
    assert "Duplicate book detected! The book is already in the list." == alert_text, f"Unexpected alert text: {alert_text}"
