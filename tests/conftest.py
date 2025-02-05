import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from project1.pages.login_page import LoginPage
from project1.config.config import TestConfig
from project1.constant import VALID_USER, VALID_PASSWORD
import requests
import json
import os
import logging

log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
# Configure logging
logging.basicConfig(
    filename=os.path.join(log_dir, 'test_logs.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


@pytest.fixture(scope="session")
def config():
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'config', 'qa_config.json')
    with open(config_path) as config_file:
        config = json.load(config_file)

    # Override 'headless' setting based on environment
    if os.environ.get('CI', '') == 'true':  # Jenkins environment
        config['browser']['headless'] = True
    else:
        config['browser']['headless'] = False  # Local environment

    return config


@pytest.fixture
def driver(config):
    chrome_options = Options()

    # Set headless mode based on the config
    if config['browser']['headless']:
        chrome_options.add_argument("--headless")

    # Additional options for running in Jenkins
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")

    # Install and set up the WebDriver
    chrome_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    driver.set_window_size(
        config['browser']['window_size']['width'],
        config['browser']['window_size']['height']
    )
    driver.implicitly_wait(10)

    yield driver
    driver.quit()


@pytest.fixture
def logged_in_driver(driver):
    """Logs in the user before running a test."""
    driver.get(f"{TestConfig.BASE_URL}/login")
    login_page = LoginPage(driver)
    login_page.login(VALID_USER, VALID_PASSWORD)
    assert login_page.is_logged_in(), "Expected to be logged in but failed"
    return driver


@pytest.fixture
def api_client(driver):
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TestConfig.API_KEY}"
    })
    return session


@pytest.fixture
def db_connection():
    import psycopg2
    conn = psycopg2.connect(**TestConfig.DB_CONNECTION)
    yield conn
    conn.close()
