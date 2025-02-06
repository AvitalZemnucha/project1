import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.core.utils import read_version_from_cmd
import os
import json


@pytest.fixture(scope="session")
def config():
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'config', 'qa_config.json')
    print(f"Loading config from: {config_path}")
    with open(config_path) as config_file:
        config = json.load(config_file)

    # Override headless mode based on CI environment
    config['browser']['headless'] = os.environ.get('CI', '') == 'true'

    return config


@pytest.fixture
def driver(config):
    browser = os.environ.get('BROWSER', 'chrome').strip().lower()
    headless = config['browser']['headless']

    print(f"Running tests on {browser} with headless={headless}")

    if browser == "chrome":
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        try:
            if os.environ.get('CI', '') == 'true':
                # Jenkins environment - try fetching the version differently
                if os.name == 'nt':  # For Windows systems
                    chrome_version_output = read_version_from_cmd(
                        '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --version',
                        r"(\d+\.\d+\.\d+\.\d+)")
                elif os.name == 'posix':  # For Linux/macOS
                    chrome_version_output = read_version_from_cmd("google-chrome --version", r"(\d+\.\d+\.\d+\.\d+)")
                else:
                    chrome_version_output = None

                if chrome_version_output:
                    version = chrome_version_output.strip()
                    try:
                        # Try to install the specific version of ChromeDriver
                        driver_path = ChromeDriverManager(version=version).install()
                    except ValueError as e:
                        print(f"Failed to retrieve ChromeDriver for version {version}: {e}")
                        print("Falling back to latest ChromeDriver version.")
                        driver_path = ChromeDriverManager().install()

            else:
                # Local environment - use the latest version
                driver_path = ChromeDriverManager().install()

            service = ChromeService(driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            return driver

        except Exception as e:
            print(f"ChromeDriver setup failed: {str(e)}")
            raise RuntimeError(f"Chrome WebDriver initialization error: {str(e)}")

    elif browser == "firefox":
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        return driver

    else:
        raise ValueError(f"Unsupported browser: {browser}")


@pytest.fixture
def logged_in_driver(driver):
    from project1.pages.login_page import LoginPage
    from project1.constant import VALID_USER, VALID_PASSWORD
    from project1.config.config import TestConfig

    driver.get(f"{TestConfig.BASE_URL}/login")
    login_page = LoginPage(driver)
    login_page.login(VALID_USER, VALID_PASSWORD)

    assert login_page.is_logged_in(), "Expected to be logged in but failed"

    return driver


@pytest.fixture
def api_client():
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
    import psycopg2
    from project1.config.config import TestConfig

    conn = psycopg2.connect(**TestConfig.DB_CONNECTION)

    yield conn

    conn.close()
