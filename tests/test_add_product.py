import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost/minishop/admin/add_product.php"

# Default wait settings
EXPLICIT_WAIT = 15   # max seconds to wait for an element
STEP_DELAY = 3       # seconds to pause after each action

def slow_step(msg, wait=STEP_DELAY):
    """Utility to add logs and pause for stability."""
    print(f"⏳ {msg} (waiting {wait}s)")
    time.sleep(wait)

def debug_dump(driver, name="add_product_debug"):
    """Dump HTML source for debugging failures."""
    with open(f"{name}.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"📝 Saved debug dump: {name}.html")

@pytest.mark.usefixtures("login_admin")
class TestAddProduct:
    added_product = None  # shared across all tests

    def test_page_loads(self, login_admin):
        driver = login_admin
        slow_step("Opening Add Product Page")
        driver.get(BASE_URL)

        try:
            title = WebDriverWait(driver, EXPLICIT_WAIT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "add-product-title"))
            ).text
            slow_step("Page title loaded")
            print(f"📌 Found page title: {title}")
            assert "Add New Product" in title
        except Exception:
            debug_dump(driver, "add_product_page_load_failure")
            pytest.fail("⚠️ Add Product page did not load correctly")

    def test_form_fields_present(self, login_admin):
        driver = login_admin
        driver.get(BASE_URL)
        slow_step("Checking form fields")
        fields = ["name", "price", "stock"]
        for field_id in fields:
            try:
                field = WebDriverWait(driver, EXPLICIT_WAIT).until(
                    EC.presence_of_element_located((By.ID, field_id))
                )
                slow_step(f"Found field: {field_id}")
                print(f"📌 Found form field: {field_id}")
                assert field.is_displayed()
            except Exception:
                debug_dump(driver, f"missing_field_{field_id}")
                pytest.fail(f"⚠️ Missing input field: {field_id}")

    def test_add_new_product(self, login_admin):
        driver = login_admin
        driver.get(BASE_URL)
        slow_step("Adding new product")

        # Generate a unique product name
        product_name = f"TestProduct_{int(time.time())}"
        driver.find_element(By.ID, "name").send_keys(product_name)
        slow_step("Entered product name")
        driver.find_element(By.ID, "price").send_keys("12345")
        slow_step("Entered product price")
        driver.find_element(By.ID, "stock").send_keys("10")
        slow_step("Entered product stock")

        # Submit form
        driver.find_element(By.CLASS_NAME, "add-btn").click()
        slow_step("Submitted product form", wait=4)

        # Wait for redirect back to admin_home.php
        WebDriverWait(driver, EXPLICIT_WAIT).until(EC.url_contains("admin_home.php"))
        print(f"📌 Successfully added new product: {product_name}")
        assert "admin_home.php" in driver.current_url

        # Store the product name for duplicate test
        TestAddProduct.added_product = product_name

    def test_duplicate_product_error(self, login_admin):
        driver = login_admin

        # Ensure we have a product to duplicate
        product_name = TestAddProduct.added_product
        if not product_name:
            pytest.skip("No product added in previous test; skipping duplicate test")

        driver.get(BASE_URL)
        slow_step(f"Trying to add duplicate product: {product_name}")

        # Fill in the duplicate product form
        driver.find_element(By.ID, "name").send_keys(product_name)
        slow_step("Entered duplicate product name")
        driver.find_element(By.ID, "price").send_keys("999")
        slow_step("Entered duplicate price")
        driver.find_element(By.ID, "stock").send_keys("5")
        slow_step("Entered duplicate stock")
        driver.find_element(By.CLASS_NAME, "add-btn").click()
        slow_step("Submitted duplicate product form", wait=4)

        try:
            error = WebDriverWait(driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "error"))
            ).text
            print(f"📌 Error displayed: {error}")
            assert "Product already exists" in error
        except Exception:
            debug_dump(driver, "duplicate_product_error_failure")
            pytest.fail(f"⚠️ No error shown for duplicate product: {product_name}")

    def test_back_button_redirects(self, login_admin):
        driver = login_admin
        driver.get(BASE_URL)
        slow_step("Locating Back button")
        back_btn = WebDriverWait(driver, EXPLICIT_WAIT).until(
            EC.presence_of_element_located((By.LINK_TEXT, "⬅ Back"))
        )
        back_btn.click()
        slow_step("Clicked Back button", wait=4)
        WebDriverWait(driver, EXPLICIT_WAIT).until(EC.url_contains("admin_home.php"))
        print(f"📌 Redirected to: {driver.current_url}")
        assert "admin_home.php" in driver.current_url, "⚠️ Back button did not redirect to admin_home.php"
