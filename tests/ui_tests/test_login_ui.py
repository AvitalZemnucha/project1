import pytest
from project1.pages.login_page import LoginPage
from project1.constant import *
from project1.config.config import TestConfig


@pytest.mark.ui
@pytest.mark.parametrize("username, password, expected_alert", [
    (VALID_USER, VALID_PASSWORD, None),
    (VALID_USER, INVALID_PASSWORD, ERROR_INVALID_PASSWORD),
    (INVALID_USER, VALID_PASSWORD, ERROR_INVALID_USERNAME),
    ("", "", ERROR_EMPTY_BOTH),
    ("", VALID_PASSWORD, ERROR_EMPTY_USERNAME),
    (VALID_USER, "", ERROR_EMPTY_PASSWORD),
])
def test_login_ui(driver, username, password, expected_alert):
    driver.get(TestConfig.BASE_URL)
    login_page = LoginPage(driver)
    login_page.login(username, password)
    if expected_alert is None:
        assert login_page.is_logged_in(), "Expected to be logged in but failed"
    else:
        assert login_page.get_error_message() == expected_alert, f"Expected alert: {expected_alert}, but got: {login_page.get_error_message()}"
