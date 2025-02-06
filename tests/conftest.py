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
        if os.name == 'nt':
            cmd = r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
            output = subprocess.check_output(cmd, shell=True).decode()
            version = re.search(r"\d+\.\d+\.\d+\.\d+", output).group(0)
            return version
        else:
            cmd = 'google-chrome --version'
            output = subprocess.check_output(cmd, shell=True).decode()
            version = re.search(r"\d+\.\d+\.\d+\.\d+", output).group(0)
            return version
    except:
        return None


@pytest.fixture(scope="session")
def config():
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'config', 'qa_config.json')
    print(f"Loading config from: {config_path}")
    with open(config_path) as config_file:
        config = json.load(config_file)

    # Force headless mode if CI environment is detected
    is_ci = os.environ.get('CI', 'false').lower() == 'true'
    config['browser']['headless'] = is_ci
    print(f"CI Environment detected: {is_ci}, Headless mode: {config['browser']['headless']}")
    return config


@pytest.fixture
def driver(config):
    browser = os.environ.get('BROWSER', 'chrome').strip().lower()
    headless = config['browser']['headless']

    print(f"Running tests on {browser} with headless={headless}")

    try:
        if browser == "chrome":
            options = ChromeOptions()

            # Force headless mode in CI environment
            if os.environ.get('CI', 'false').lower() == 'true':
                print("CI environment detected, forcing headless mode")
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
            elif headless:
                options.add_argument("--headless=new")

            # Common Chrome options for stability
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

            driver_path = ChromeDriverManager().install()
            service = ChromeService(driver_path)
            driver = webdriver.Chrome(service=service, options=options)

        elif browser == "firefox":
            options = FirefoxOptions()
            if headless or os.environ.get('CI', 'false').lower() == 'true':
                options.add_argument("--headless")
            driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        else:
            raise ValueError(f"Unsupported browser: {browser}")

        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)

        yield driver

        driver.quit()

    except Exception as e:
        print(f"WebDriver setup failed: {str(e)}")
        raise RuntimeError(f"WebDriver initialization error: {str(e)}")


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
