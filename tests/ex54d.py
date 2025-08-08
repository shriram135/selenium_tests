import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

USERNAME = "user"     # Change to a valid username
PASSWORD = "123"      # Change to matching password
BASE_URL = "http://localhost/miniishop/index.php"

def start_driver():
    options = Options()
    options.add_argument("--window-size=1280,800")
    return webdriver.Chrome(options=options)

def login_and_get_session(driver):
    driver.get(BASE_URL)

    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    time.sleep(2)  # Wait for login

    cookies = driver.get_cookies()
    session_id = driver.get_cookie("PHPSESSID")
    return cookies, session_id

def test_session_behavior():
    print("\n=== Test 1: Login and Get Session ===")
    driver = start_driver()
    cookies, session_id = login_and_get_session(driver)

    print("\n--- Cookies after login ---")
    for cookie in cookies:
        print(f"{cookie['name']} = {cookie['value']}")

    if session_id:
        print(f"\nPHPSESSID: {session_id['value']}")
    else:
        print("\nNo PHPSESSID found — login might have failed.")

    driver.quit()
    print("\nBrowser closed. Waiting 3 seconds before reopening...")
    time.sleep(3)

    print("\n=== Test 2: Reopen Browser and Check Session ===")
    driver2 = start_driver()
    driver2.get(BASE_URL)
    time.sleep(2)

    # This check depends on your app showing login form when logged out
    if "username" in driver2.page_source.lower():
        print("✅ Session ended — user is logged out.")
    else:
        print("⚠ Session persisted — user is still logged in.")

    driver2.quit()
