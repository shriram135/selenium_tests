import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

USERNAME = "user"     # change to an existing DB username
PASSWORD = "123"      # change to that user's password

@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--window-size=1280,800")  # Set window size
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_print_session_for_user(driver):
    # 1. Open login page
    driver.get("http://localhost/miniishop/index.php")

    # 2. Fill username and password fields
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)

    # 3. Submit form
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # 4. Wait for redirect
    time.sleep(2)

    # 5. Print all cookies
    cookies = driver.get_cookies()
    print("\n--- All Cookies ---")
    for cookie in cookies:
        print(f"{cookie['name']} = {cookie['value']}")

    # 6. Print PHPSESSID specifically
    session_id = driver.get_cookie("PHPSESSID")
    if session_id:
        print(f"\nPHPSESSID: {session_id['value']}")
    else:
        print("\nPHPSESSID not found — login might have failed.")

    # 7. Close window and check session end (manually)
    print("\nClosing browser window to test if session ends...")
    time.sleep(2)

