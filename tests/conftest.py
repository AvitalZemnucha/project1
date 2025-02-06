import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import os
import json
import subprocess
import re


def get_chrome_version():
    """Get the installed Chrome version."""
    try:
        # For Windows
        if os.name == 'nt':
            cmd = r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
            output = subprocess.check_output(cmd, shell=True).decode()
            version = re.search(r"\d+\.\d+\.\d+\.\d+", output).group(0)
            return version  # Return full version
        # For Linux
        else:
            cmd = 'google-chrome --version'
            output = subprocess.check_output(cmd, shell=True).decode()
            version = re.search(r"\d+\.\d+\.\d+\.\d+", output).group(0)
            return version  # Return full version
    except:
        return None


@pytest.fixture(scope="session")
def config():
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'config', 'qa_config.json')
    print(f"Loading config from: {config_path}")
    with open(config_path) as config_file:
        config = json.load(config_file)

    # Set headless mode based on CI environment
    config['browser']['headless'] = os.environ.get('CI', 'false').lower() == 'true'
    return config


@pytest.fixture
def driver(config):
    browser = os.environ.get('BROWSER', 'chrome').strip().lower()
    headless = config['browser']['headless']

    print(f"Running tests on {browser} with headless={headless}")

    try:
        if browser == "chrome":
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless=new")

            # Common Chrome options for stability
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-extensions")
            options.add_argument("--proxy-server='direct://'")
            options.add_argument("--proxy-bypass-list=*")
            options.add_argument("--start-maximized")

            # Get Chrome version and install matching driver
            chrome_ver = get_chrome_version()
            if chrome_ver:
                print(f"Detected Chrome version: {chrome_ver}")
                # Use the driver manager's cache_manager to find the right version
                driver_path = ChromeDriverManager().install()
            else:
                print("Could not detect Chrome version, using latest ChromeDriver")
                driver_path = ChromeDriverManager().install()

            service = ChromeService(driver_path)
            driver = webdriver.Chrome(service=service, options=options)

        elif browser == "firefox":
            options = FirefoxOptions()
            if headless:
                options.add_argument("--headless")
            driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        else:
            raise ValueError(f"Unsupported browser: {browser}")

        # Set implicit wait and page load timeout
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)

        yield driver

        # Quit driver after test
        driver.quit()

    except Exception as e:
        print(f"WebDriver setup failed: {str(e)}")
        raise RuntimeError(f"WebDriver initialization error: {str(e)}")


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


# Your other fixtures remain the same


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
