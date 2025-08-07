import time
import pytest
import pymysql
from selenium.webdriver.common.by import By

BASE_URL = "http://localhost/minishop/admin/update_stock.php"
ADD_URL = "http://localhost/minishop/admin/add_product.php"
ADMIN_HOME_URL = "http://localhost/minishop/admin/admin_home.php"

EXPLICIT_WAIT = 10
STEP_DELAY = 2
TYPE_DELAY = 0.15

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",   # add password if needed
    "database": "mini_shop"
}


def db_connect():
    return pymysql.connect(**DB_CONFIG)


def slow_step(msg, wait=STEP_DELAY):
    print(f"⏳ {msg} (waiting {wait}s)")
    time.sleep(wait)


def slow_type(element, text, delay=TYPE_DELAY):
    for char in str(text):
        element.send_keys(char)
        time.sleep(delay)


def slow_click(element, wait=STEP_DELAY):
    element.click()
    time.sleep(wait)


@pytest.mark.usefixtures("login_admin")
class TestUpdateStock:
    product_id = None
    product_name = None
    original_stock = None

    def test_add_product_for_stock_update(self, login_admin):
        """Add a product and capture its ID + stock from DB."""
        driver = login_admin
        driver.get(ADD_URL)
        slow_step("Adding product for stock update test")

        TestUpdateStock.product_name = f"StockTest_{int(time.time())}"

        slow_type(driver.find_element(By.ID, "name"), TestUpdateStock.product_name)
        slow_type(driver.find_element(By.ID, "price"), "789")
        slow_type(driver.find_element(By.ID, "stock"), "20")
        slow_click(driver.find_element(By.CLASS_NAME, "add-btn"))

        conn = db_connect()
        with conn.cursor() as cur:
            cur.execute("SELECT id, stock FROM products WHERE name=%s", (TestUpdateStock.product_name,))
            result = cur.fetchone()
            if result:
                TestUpdateStock.product_id = str(result[0])
                TestUpdateStock.original_stock = int(result[1])
                print(f"📌 Added product ID {TestUpdateStock.product_id}, stock {TestUpdateStock.original_stock}")
            else:
                pytest.fail("⚠️ Could not capture product ID from DB after adding")
        conn.close()

    def test_reduce_existing_product_stock(self, login_admin):
        """Reduce stock of the added product and validate DB update."""
        driver = login_admin
        if not TestUpdateStock.product_id:
            pytest.skip("No product added for update stock test")

        driver.get(BASE_URL)
        slow_step(f"Checking product ID {TestUpdateStock.product_id}")

        # Step 1: Find product
        slow_type(driver.find_element(By.ID, "product_id"), TestUpdateStock.product_id)
        slow_click(driver.find_element(By.NAME, "check_product"))

        # Step 2: Enter reduced stock
        new_stock = max(0, TestUpdateStock.original_stock - 5)
        slow_type(driver.find_element(By.ID, "new_stock"), str(new_stock))
        slow_click(driver.find_element(By.NAME, "update_stock"))

        # Validate DB update
        conn = db_connect()
        with conn.cursor() as cur:
            cur.execute("SELECT stock FROM products WHERE id=%s", (TestUpdateStock.product_id,))
            result = cur.fetchone()
            conn.close()

            assert result and int(result[0]) == new_stock, (
                f"⚠️ Stock not reduced in DB. Expected {new_stock}, got {result}"
            )
            print(f"✅ Stock for product ID {TestUpdateStock.product_id} reduced to {new_stock} in DB")

    def test_update_nonexistent_product_stock(self, login_admin):
        """Try to update a non-existent product and confirm DB unaffected."""
        driver = login_admin
        driver.get(BASE_URL)
        fake_id = "999999"
        slow_step(f"Trying to update stock for non-existent product ID {fake_id}")

        slow_type(driver.find_element(By.ID, "product_id"), fake_id)
        slow_click(driver.find_element(By.NAME, "check_product"))

        conn = db_connect()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE id=%s", (fake_id,))
            result = cur.fetchone()
            conn.close()

            assert result is None, f"⚠️ Unexpectedly found product with ID {fake_id} in DB"
            print(f"✅ No product with ID {fake_id} found in DB (as expected)")

    def test_back_button(self, login_admin):
        """Check that back button works correctly."""
        driver = login_admin
        driver.get(BASE_URL)
        slow_step("Clicking back button on update_stock.php")

        back_btn = driver.find_element(By.CLASS_NAME, "back-btn")
        slow_click(back_btn)

        assert ADMIN_HOME_URL in driver.current_url, "⚠️ Back button did not navigate to admin_home.php"
        print("✅ Back button successfully navigated to admin_home.php")
