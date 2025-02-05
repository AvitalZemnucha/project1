import os
import json
import logging
import pytest
import requests
import mysql.connector
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from project1.pages.login_page import LoginPage
from project1.config.config import TestConfig
from project1.constant import VALID_USER, VALID_PASSWORD

# 📂 Configure logging
log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(log_dir, 'test_logs.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# 🛠 Load Configuration
@pytest.fixture(scope="session")
def config():
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'config', 'qa_config.json')
    with open(config_path) as config_file:
        config = json.load(config_file)

    # Override 'headless' setting in Jenkins
    if os.getenv("CI", "false").lower() == "true":
        config['browser']['headless'] = True
    return config


# 🌐 Cross-browser driver fixture
def get_browser_driver(browser_type, headless):
    if browser_type == "chrome":
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless")
        driver_service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=driver_service, options=options)

    elif browser_type == "firefox":
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        driver_service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=driver_service, options=options)

    else:
        raise ValueError(f"Unsupported browser: {browser_type}")


# 🚀 Browser Fixture (Cross-browser Support)
@pytest.fixture(scope="function")
def driver(config):
    browser = os.environ.get('BROWSER', 'chrome').lower()
    headless = config['browser'].get('headless', False)

    driver = get_browser_driver(browser, headless)
    driver.set_window_size(config['browser']['window_size']['width'], config['browser']['window_size']['height'])
    driver.implicitly_wait(10)

    yield driver
    driver.quit()


# 🔐 Login Fixture (Runs Before Tests)
@pytest.fixture
def logged_in_driver(driver):
    driver.get(f"{TestConfig.BASE_URL}/login")
    login_page = LoginPage(driver)
    login_page.login(VALID_USER, VALID_PASSWORD)
    assert login_page.is_logged_in(), "Expected to be logged in but failed"
    return driver


# 🌍 API Testing Fixture
@pytest.fixture
def api_client():
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TestConfig.API_KEY}"
    })
    return session


# 🛢 Database Fixture (PostgreSQL)
@pytest.fixture(scope="session")
def db_connection():
    conn = psycopg2.connect(**TestConfig.DB_CONNECTION)
    yield conn
    conn.close()


# 🛢 Database Fixture (MySQL)
@pytest.fixture(scope="session")
def mysql_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="avitalz",
        database="sakila"
    )
    yield connection
    connection.close()
