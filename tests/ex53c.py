import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_print_session_for_user(driver):
    # 1. Open the browser and navigate to your MiniShop
    driver.get("http://localhost/minishop/index.php")

    # 2. (Optional) Log in as a user — only if your system requires it
    driver.find_element(By.NAME, "username").send_keys("testuser")
    driver.find_element(By.NAME, "password").send_keys("password123")
    driver.find_element(By.NAME, "login").click()

    # 3. Get and print session cookies
    cookies = driver.get_cookies()
    print("\nSession Cookies:")
    for cookie in cookies:
        print(f"{cookie['name']} = {cookie['value']}")

    # 4. Optionally, access specific cookie like PHPSESSID
    session_id = driver.get_cookie("PHPSESSID")
    if session_id:
        print(f"\nPHPSESSID: {session_id['value']}")
    else:
        print("\nPHPSESSID not found — user might not be logged in.")
