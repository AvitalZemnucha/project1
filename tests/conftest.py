import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import os
import json


@pytest.fixture(scope="session")
def config():
    """
    Load configuration settings from a JSON file and override headless mode if running in CI (Jenkins).
    """
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'config', 'qa_config.json')
    print(f"Loading config from: {config_path}")  # Debug print
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
    """
       Initialize a WebDriver instance based on the browser specified in the environment variable.
       """
    browser = os.environ.get('BROWSER', 'chrome').strip().lower()  # Ensure no extra spaces
    headless = os.environ.get('HEADLESS', 'false').strip().lower() == 'true'

    print(f"Running tests on {browser} with headless={headless}")  # Debug print

    if browser == "chrome":
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    elif browser == "firefox":
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
    else:
        raise ValueError(f"Unsupported browser: {browser}")

    return driver


@pytest.fixture
def logged_in_driver(driver):
    """
    Logs in the user before running a test.
    """
    from project1.pages.login_page import LoginPage
    from project1.constant import VALID_USER, VALID_PASSWORD

    driver.get(f"{TestConfig.BASE_URL}/login")
    login_page = LoginPage(driver)
    login_page.login(VALID_USER, VALID_PASSWORD)

    assert login_page.is_logged_in(), "Expected to be logged in but failed"

    return driver


@pytest.fixture
def api_client():
    """
    Create an API client session for making HTTP requests.
    """
    import requests
    from project1.config.config import TestConfig

    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TestConfig.API_KEY}"
    })

    return session


@pytest.fixture
def db_connection():
    """
    Set up a database connection for tests.
    """
    import psycopg2
    from project1.config.config import TestConfig

    conn = psycopg2.connect(**TestConfig.DB_CONNECTION)

    yield conn

    conn.close()
