import os
import pytest
import json
import requests
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


# Config fixture to load configuration from JSON or default
@pytest.fixture(scope="session")
def config():
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'config', 'qa_config.json')

    try:
        with open(config_path) as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        config = {
            'browser': {'headless': False, 'window_size': {'height': 1080, 'width': 1920}},
            'logging': {'file_path': 'logs/test_logs.log', 'level': 'INFO'},
            'test_environment': 'qa'
        }

    config['browser']['headless'] = os.environ.get('CI', '') == 'true'
    return config


# Driver fixture for Chrome and Firefox with headless support and version pinning for ChromeDriver in Jenkins
@pytest.fixture
def driver(config):
    browser = os.environ.get('BROWSER', 'chrome').strip().lower()
    headless = os.environ.get('CI', '') == 'true'

    print(f"Running tests on {browser} with headless={headless}")

    if browser == "chrome":
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless")

        # Chrome-specific configuration
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        try:
            # Pinning ChromeDriver version for Jenkins and using the latest for local
            if os.environ.get('CI', '') == 'true':  # Jenkins environment
                driver_path = ChromeDriverManager(version="132.0.6834").install()  # Stable version for Jenkins
            else:  # Local environment
                driver_path = ChromeDriverManager().install()  # Latest version for local
            service = ChromeService(driver_path)
            driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            print(f"ChromeDriver setup failed: {str(e)}")
            raise RuntimeError(f"Chrome WebDriver initialization error: {str(e)}")

    elif browser == "firefox":
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")

        try:
            driver = webdriver.Firefox(
                service=FirefoxService(GeckoDriverManager().install()),
                options=options
            )
        except Exception as e:
            print(f"FirefoxDriver setup failed: {str(e)}")
            raise RuntimeError(f"Firefox WebDriver initialization error: {str(e)}")

    else:
        raise ValueError(f"Unsupported browser: {browser}")

    # Set window size from config
    driver.set_window_size(
        config['browser']['window_size']['width'],
        config['browser']['window_size']['height']
    )

    yield driver
    driver.quit()


# Logged in driver fixture
@pytest.fixture
def logged_in_driver(driver):
    from project1.pages.login_page import LoginPage
    from project1.constant import VALID_USER, VALID_PASSWORD
    from project1.config.config import TestConfig

    driver.get(f"{TestConfig.BASE_URL}/login")
    login_page = LoginPage(driver)
    login_page.login(VALID_USER, VALID_PASSWORD)

    assert login_page.is_logged_in(), "Login failed"
    return driver


# API client fixture
@pytest.fixture
def api_client():
    from project1.config.config import TestConfig

    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TestConfig.API_KEY}"
    })

    return session


# Database connection fixture
@pytest.fixture
def db_connection():
    from project1.config.config import TestConfig

    conn = psycopg2.connect(**TestConfig.DB_CONNECTION)
    yield conn
    conn.close()


# Custom command-line option for environment selection
def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="qa",
        help="Specify test environment: qa, staging, prod"
    )


# Test environment fixture (session scoped)
@pytest.fixture(scope="session")
def test_environment(request):
    return request.config.getoption("--env")
