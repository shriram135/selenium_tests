from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def test_open_and_close_browser():
    # Setup Chrome options
    options = Options()
    options.add_argument("--start-maximized")

    # Use Selenium Manager (no need for chromedriver.exe path)
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost/minishop/index.php")

        # wait a bit to allow CSS & resources to load
        time.sleep(3)

        # Check title or URL
        assert "Mini Shop" in driver.title or "index" in driver.current_url

        # Verify CSS <link> is loaded
        css_links = driver.find_elements(By.TAG_NAME, "link")
        print("\nLoaded CSS files:")
        for link in css_links:
            href = link.get_attribute("href")
            if href:
                print(href)

        assert any("css" in link.get_attribute("href") for link in css_links), \
            "❌ No CSS file detected!"

        print("✅ Page loaded with CSS successfully.")

    finally:
        time.sleep(5)  # keep browser open for observation
        driver.quit()
