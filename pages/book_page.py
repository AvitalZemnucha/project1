from selenium.common import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from project1.config.config import TestConfig
from selenium.webdriver.common.alert import Alert


class BookPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, TestConfig.EXPLICIT_WAIT)
        self.add_new_book_button = (By.ID, "add-book")
        self.book_title_input = (By.ID, "book-title")
        self.book_author_input = (By.ID, "book-author")
        self.book_isbn_input = (By.ID, "book-isbn")
        self.book_save_button = (By.ID, "save-book")
        self.book_cancel_button = (By.ID, "cancel-book")
        self.book_alert = (By.ID, "error-message")
        self.book_edit_button = (By.CSS_SELECTOR, ".edit-btn")
        self.book_delete_button = (By.CSS_SELECTOR, ".delete-btn")
        self.rows = (By.CSS_SELECTOR, "#books-list tr")
        self.columns = (By.TAG_NAME, "td")

    def add_book(self, title, author, isbn):
        self.wait.until(EC.element_to_be_clickable(self.add_new_book_button)).click()
        self.wait.until(EC.presence_of_element_located(self.book_title_input)).send_keys(title)
        self.driver.find_element(*self.book_author_input).send_keys(author)
        self.driver.find_element(*self.book_isbn_input).send_keys(isbn)

    def book_save(self):
        self.driver.find_element(*self.book_save_button).click()

    def book_cancel(self):
        self.driver.find_element(*self.book_cancel_button).click()

    def get_book_alert(self):
        self.wait.until(EC.element_to_be_clickable(self.add_new_book_button)).click()
        self.driver.find_element(*self.book_save_button).click()
        return self.wait.until(EC.presence_of_element_located(self.book_alert)).text

    def book_edit(self, title, author, isbn):
        book_rows = self.driver.find_elements(*self.rows)

        if book_rows:
            # Modify this to select the correct row to edit, for now it's selecting the last row
            last_row = book_rows[-1]
            edit_button = last_row.find_element(*self.book_edit_button)

            # Wait for the edit button to be clickable
            self.wait.until(EC.element_to_be_clickable(edit_button)).click()

            # Wait for the title input to be visible and interactable
            self.wait.until(EC.visibility_of_element_located(self.book_title_input))

            if not title and not author and not isbn:
                # Trigger an alert since no fields are filled
                self.wait.until(EC.presence_of_element_located(self.book_alert))
                alert_text = self.driver.find_element(*self.book_alert).text
                return alert_text  # Return the alert message (or handle as needed)

                # If fields are not empty, fill them
            if title:
                b_title = self.wait.until(EC.element_to_be_clickable(self.book_title_input))
                b_title.clear()
                b_title.send_keys(title)

            if author:
                b_author = self.wait.until(EC.element_to_be_clickable(self.book_author_input))
                b_author.clear()
                b_author.send_keys(author)

            if isbn:
                b_isbn = self.wait.until(EC.element_to_be_clickable(self.book_isbn_input))
                b_isbn.clear()
                b_isbn.send_keys(isbn)

                # Save the changes
            self.driver.find_element(*self.book_save_button).click()

            # Wait until the save button disappears to ensure the save is complete
            self.wait.until(EC.invisibility_of_element_located(self.book_title_input))

    def book_delete(self):
        book_rows = self.driver.find_elements(*self.rows)
        if book_rows:
            last_row = book_rows[-1]  # Get the last book row
            delete_button = last_row.find_element(*self.book_delete_button)  # Find delete button inside the last row
            self.wait.until(EC.element_to_be_clickable(delete_button)).click()
        alert = WebDriverWait(self.driver, TestConfig.EXPLICIT_WAIT).until(EC.alert_is_present())
        alert.accept()
        self.wait.until(EC.staleness_of(last_row))

    def get_book_list(self):
        self.wait.until(EC.presence_of_all_elements_located(self.rows))
        book_rows = self.driver.find_elements(*self.rows)
        books = []
        for row in book_rows:
            columns = row.find_elements(*self.columns)
            if len(columns) >= 4:  # Ensure we have at least 4 columns
                books.append({
                    "number": columns[0].text,
                    "title": columns[1].text,
                    "author": columns[2].text,
                    "isbn": columns[3].text
                })
        return books

    def is_duplicated_message(self):
        # message = WebDriverWait(self.driver, TestConfig.EXPLICIT_WAIT).until(
        #     EC.visibility_of_element_located(self.book_alert))
        message = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located(self.book_alert))
        return message.text
