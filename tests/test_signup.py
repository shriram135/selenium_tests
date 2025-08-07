import time
import pytest
import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ---------- Selenium Driver Fixture ----------
@pytest.fixture
def driver():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    yield driver
    time.sleep(2)  # pause to visually confirm before closing
    driver.quit()


# ---------- Helper Functions ----------
def wait_for_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def human_typing(element, text, delay=0.15):
    """Type characters slowly to mimic human input"""
    for char in text:
        element.send_keys(char)
        time.sleep(delay)


def delete_user(username):
    """Delete a user from the DB if exists"""
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # update if you set a password
        database="mini_shop"
    )
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = %s", (username,))
    conn.commit()
    cursor.close()
    conn.close()


# ---------- Cleanup Fixture ----------
@pytest.fixture
def cleanup_user():
    created_users = []

    yield created_users  # test will append usernames to this list

    # after test, delete all created users
    for username in created_users:
        delete_user(username)


# ---------- Tests ----------
def test_unique_signup(driver, cleanup_user):
    base_url = "http://localhost/minishop/signup.php"
    driver.get(base_url)

    username = f"user_{int(time.time())}"
    password = "TestPass123"

    human_typing(wait_for_element(driver, By.ID, "username"), username)
    human_typing(driver.find_element(By.ID, "password"), password)
    human_typing(driver.find_element(By.ID, "confirm"), password)
    driver.find_element(By.CSS_SELECTOR, "button.signup-btn").click()

    success_msg = wait_for_element(driver, By.CLASS_NAME, "success").text
    assert "Account created successfully" in success_msg

    cleanup_user.append(username)  # mark for DB cleanup


def test_duplicate_signup(driver, cleanup_user):
    base_url = "http://localhost/minishop/signup.php"
    driver.get(base_url)

    username = f"fixed_test_user_{int(time.time())}"
    password = "TestPass123"

    # First signup
    human_typing(wait_for_element(driver, By.ID, "username"), username)
    human_typing(driver.find_element(By.ID, "password"), password)
    human_typing(driver.find_element(By.ID, "confirm"), password)
    driver.find_element(By.CSS_SELECTOR, "button.signup-btn").click()
    time.sleep(1)

    # Second attempt (duplicate)
    driver.get(base_url)
    human_typing(wait_for_element(driver, By.ID, "username"), username)
    human_typing(driver.find_element(By.ID, "password"), password)
    human_typing(driver.find_element(By.ID, "confirm"), password)
    driver.find_element(By.CSS_SELECTOR, "button.signup-btn").click()

    error_msg = wait_for_element(driver, By.CLASS_NAME, "error").text
    assert "Username already taken" in error_msg

    cleanup_user.append(username)  # cleanup after test


def test_password_mismatch(driver):
    base_url = "http://localhost/minishop/signup.php"
    driver.get(base_url)

    username = f"user_mismatch_{int(time.time())}"
    human_typing(wait_for_element(driver, By.ID, "username"), username)
    human_typing(driver.find_element(By.ID, "password"), "password123")
    human_typing(driver.find_element(By.ID, "confirm"), "differentpass")
    driver.find_element(By.CSS_SELECTOR, "button.signup-btn").click()

    error_msg = wait_for_element(driver, By.CLASS_NAME, "error").text
    assert "Passwords do not match" in error_msg
