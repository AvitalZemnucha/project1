from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from project1.config.config import TestConfig


class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, TestConfig.EXPLICIT_WAIT)
        self.username_input = (By.ID, 'username')
        self.password_input = (By.ID, 'password')
        self.login_button = (By.CSS_SELECTOR, "button[type='submit']")

        self.error_message_path = (By.CSS_SELECTOR, ".error-message")

        self.logout_button = (By.ID, "logout")

    def login(self, username, password):
        self.wait.until(EC.visibility_of_element_located(self.username_input)).send_keys(username)
        self.wait.until(EC.visibility_of_element_located(self.password_input)).send_keys(password)
        self.wait.until(EC.element_to_be_clickable(self.login_button)).click()

    def get_error_message(self):
        alert = self.wait.until(EC.visibility_of_element_located(self.error_message_path))
        return alert.text

    def is_logged_in(self):
        if self.wait.until(EC.presence_of_element_located(self.logout_button)):
            return True
