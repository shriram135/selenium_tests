import time
import pytest
import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.fixture
def driver():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    yield driver
    time.sleep(2)  # pause so you can see results
    driver.quit()


def wait_for_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def human_typing(element, text, delay=0.2):
    for char in text:
        element.send_keys(char)
        time.sleep(delay)


# --- Database helpers ---
def create_user(username, password, role="customer"):
    conn = mysql.connector.connect(
        host="localhost", user="root", password="", database="mini_shop"
    )
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (%s, MD5(%s), %s)",
        (username, password, role),
    )
    conn.commit()
    cursor.close()
    conn.close()


def delete_user(username):
    conn = mysql.connector.connect(
        host="localhost", user="root", password="", database="mini_shop"
    )
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = %s", (username,))
    conn.commit()
    cursor.close()
    conn.close()


# --- TESTS ---
def test_admin_login(driver):
    base_url = "http://localhost/minishop/index.php"
    driver.get(base_url)

    human_typing(wait_for_element(driver, By.ID, "username"), "admin")
    human_typing(driver.find_element(By.ID, "password"), "admin123")
    driver.find_element(By.CSS_SELECTOR, "button.login-btn").click()

    WebDriverWait(driver, 10).until(EC.url_contains("admin_home.php"))
    assert "admin_home.php" in driver.current_url


def test_customer_login(driver):
    base_url = "http://localhost/minishop/index.php"
    username = f"user_{int(time.time())}"
    password = "CustPass123"

    # Create a customer before test
    create_user(username, password, role="customer")

    driver.get(base_url)
    human_typing(wait_for_element(driver, By.ID, "username"), username)
    human_typing(driver.find_element(By.ID, "password"), password)
    driver.find_element(By.CSS_SELECTOR, "button.login-btn").click()

    WebDriverWait(driver, 10).until(EC.url_contains("customer_home.php"))
    assert "customer_home.php" in driver.current_url

    delete_user(username)


def test_invalid_login(driver):
    base_url = "http://localhost/minishop/index.php"
    driver.get(base_url)

    human_typing(wait_for_element(driver, By.ID, "username"), "fakeuser")
    human_typing(driver.find_element(By.ID, "password"), "wrongpass")
    driver.find_element(By.CSS_SELECTOR, "button.login-btn").click()

    error_msg = wait_for_element(driver, By.CLASS_NAME, "error").text
    assert "Invalid username or password." in error_msg


# def test_empty_fields(driver):
#     base_url = "http://localhost/minishop/index.php"
#     driver.get(base_url)a

#     driver.find_element(By.CSS_SELECTOR, "button.login-btn").click()
#     error_msg = wait_for_element(driver, By.CLASS_NAME, "error").text
#     assert "All fields are required." in error_msg
