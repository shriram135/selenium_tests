import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost/minishop/admin/admin_home.php"

def slow_step(msg, wait=3):
    print(f"⏳ {msg} (waiting {wait}s)")
    time.sleep(wait)

def debug_dump(driver, name="admin_debug"):
    with open(f"{name}.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    driver.save_screenshot(f"{name}.png")
    print(f"📝 Saved debug dump: {name}.html and {name}.png")

@pytest.mark.usefixtures("login_admin")
class TestAdminHome:

    def test_page_loads(self, login_admin):
        driver = login_admin
        driver.get(BASE_URL)

        try:
            heading = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h2"))
            ).text
            print(f"📌 Found heading: {heading}")
            assert "Admin" in heading
        except Exception:
            debug_dump(driver, "admin_page_load_failure")
            pytest.fail("⚠️ Admin home page did not load correctly")

    def test_dashboard_cards(self, login_admin):
        driver = login_admin
        driver.get(BASE_URL)

        cards = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "card"))
        )
        print(f"📌 Found {len(cards)} dashboard cards")
        assert len(cards) >= 1

    def test_admin_links_navigation(self, login_admin):
        driver = login_admin
        driver.get(BASE_URL)

        links = {
            "Add Product": "add_product.php",
            "Delete Products": "delete_product.php",
            "Update Stock": "update_stock.php",
        }

        for link_text, expected_href in links.items():
            try:
                link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.LINK_TEXT, link_text))
                )
                print(f"📌 Clicking link: {link.text}")
                link.click()
                slow_step(f"Waiting for page: {expected_href}")

                WebDriverWait(driver, 10).until(EC.url_contains(expected_href))
                current_url = driver.current_url
                print(f"📌 Now at: {current_url}")
                assert expected_href in current_url

                driver.get(BASE_URL)
                slow_step("Back to Admin Home")
            except Exception:
                debug_dump(driver, f"link_fail_{link_text.replace(' ', '_')}")
                pytest.fail(f"⚠️ Navigation failed for: {link_text}")

    def test_product_table_present(self, login_admin):
        driver = login_admin
        driver.get(BASE_URL)

        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )

        headers = [th.text for th in table.find_elements(By.TAG_NAME, "th")]
        print(f"📌 Table headers: {headers}")
        assert "Product Name" in headers
        assert "Price (₹)" in headers
        assert "Stock" in headers

    def test_back_button_redirects(self, login_admin):
        driver = login_admin
        driver.get(BASE_URL)

        back_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "← Back to Index"))
        )
        back_btn.click()
        slow_step("Clicked back button")
        WebDriverWait(driver, 10).until(EC.url_contains("index.php"))
        assert "index.php" in driver.current_url
