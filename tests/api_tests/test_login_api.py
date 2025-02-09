import pytest
import logging
from project1.config.config import TestConfig

logger = logging.getLogger('pytest')


@pytest.mark.api
@pytest.mark.parametrize("username, password, expected_response, expected_message", [
    ("test_user", "test_pass123", 200, "Login successful"),
    ("test_user", "test_pass", 401, "Invalid password"),
    ("test_user333", "test_pass123", 401, "Invalid username"),
    ("", "test_pass123", 400, "Username and password are required"),
    ("test_user", "", 400, "Username and password are required"),
    ("", "", 400, "Username and password are required")
])
def test_login_with_valid_and_invalid_credentials(api_client, username, password, expected_response, expected_message):
    payload = {
        "username": username,
        "password": password
    }
    response = api_client.post(TestConfig.API_LOGIN_URL, json=payload)
    data = response.json()
    assert response.status_code == expected_response
    if response.status_code == 200:
        assert data['message'] == expected_message
    else:
        assert data["error"] == expected_message


@pytest.mark.api
def test_logout_after_login(api_client):
    response = api_client.post(TestConfig.API_LOGIN_URL, json=TestConfig.API_LOGIN_PAYLOAD)
    assert response.status_code == 200
    response_logout = api_client.get(TestConfig.API_LOGOUT_URL)
    assert response_logout.status_code == 200


@pytest.mark.api
def test_logout_without_login(api_client):
    response = api_client.get(TestConfig.API_LOGOUT_URL)
    data = response.json()
    assert response.status_code == 403
    assert data['error'] == "You are not logged in"
