from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def test_open_minishop_home():
    # Setup Chrome
    driver = webdriver.Chrome()
    driver.maximize_window()

    # Step 1: Open the browser and navigate to the site
    driver.get("http://localhost/minishop/index.php")

    time.sleep(2)  # Let the page load

    # Step 2: Verify title or a specific element
    assert "MiniShop" in driver.title or driver.find_element(By.TAG_NAME, "body"), "❌ Home page did not load"

    print("✅ Home page opened successfully.")
    driver.quit()

# Run it directly if this script is standalone
if __name__ == "__main__":
    test_open_minishop_home()
