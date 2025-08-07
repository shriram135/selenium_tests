import pytest
from selenium import webdriver

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_open_browser_and_delete_cookies(driver):
    driver.get("http://localhost/minishop/index.php")
    
    # Get initial PHPSESSID
    initial_session = None
    for cookie in driver.get_cookies():
        if cookie['name'] == 'PHPSESSID':
            initial_session = cookie['value']
            break

    # Delete all cookies
    driver.delete_all_cookies()
    driver.refresh()

    # Get new PHPSESSID after refresh
    new_session = None
    for cookie in driver.get_cookies():
        if cookie['name'] == 'PHPSESSID':
            new_session = cookie['value']
            break

    assert new_session != initial_session, "❌ Session not regenerated after deleting cookies"
