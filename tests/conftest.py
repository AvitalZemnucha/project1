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
import requests
import psycopg2


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
            # Automatically fetch the latest ChromeDriver version
            driver_path = ChromeDriverManager().install()  # Use the latest version for both Jenkins and local
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


@pytest.fixture
def api_client():
    from project1.config.config import TestConfig

    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TestConfig.API_KEY}"
    })

    return session


@pytest.fixture
def db_connection():
    from project1.config.config import TestConfig

    conn = psycopg2.connect(**TestConfig.DB_CONNECTION)
    yield conn
    conn.close()


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="qa",
        help="Specify test environment: qa, staging, prod"
    )


@pytest.fixture(scope="session")
def test_environment(request):
    return request.config.getoption("--env")
