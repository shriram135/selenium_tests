import time
import pytest
import pymysql  # DB connector
from selenium.webdriver.common.by import By

BASE_URL = "http://localhost/minishop/admin/delete_product.php"
ADD_URL = "http://localhost/minishop/admin/add_product.php"
ADMIN_HOME_URL = "http://localhost/minishop/admin/admin_home.php"

EXPLICIT_WAIT = 10
STEP_DELAY = 2
TYPE_DELAY = 0.15

# --- DB Connection Config ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",     # add password if your MySQL root has one
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


def debug_dump(driver, name="delete_product_debug"):
    with open(f"{name}.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"📝 Saved debug dump: {name}.html")


@pytest.mark.usefixtures("login_admin")
class TestDeleteProduct:
    product_id = None
    product_name = None

    def test_add_product_for_deletion(self, login_admin):
        driver = login_admin
        driver.get(ADD_URL)
        slow_step("Adding product for deletion test")

        TestDeleteProduct.product_name = f"DeleteTest_{int(time.time())}"

        slow_type(driver.find_element(By.ID, "name"), TestDeleteProduct.product_name)
        slow_type(driver.find_element(By.ID, "price"), "456")
        slow_type(driver.find_element(By.ID, "stock"), "20")
        slow_click(driver.find_element(By.CLASS_NAME, "add-btn"))

        # --- Fetch product ID from DB instead of UI ---
        conn = db_connect()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE name=%s", (TestDeleteProduct.product_name,))
            result = cur.fetchone()
            if result:
                TestDeleteProduct.product_id = str(result[0])
                print(f"📌 Captured product ID from DB: {TestDeleteProduct.product_id}")
            else:
                pytest.fail("⚠️ Could not capture product ID from DB after adding")
        conn.close()

    def test_delete_existing_product(self, login_admin):
        driver = login_admin
        if not TestDeleteProduct.product_id:
            pytest.skip("No product added for deletion test")

        driver.get(BASE_URL)
        slow_step(f"Deleting product ID {TestDeleteProduct.product_id}")

        product_id_field = driver.find_element(By.ID, "product_id")
        slow_type(product_id_field, TestDeleteProduct.product_id)
        slow_click(driver.find_element(By.CLASS_NAME, "delete-btn"))

        # --- Validate deletion in DB ---
        conn = db_connect()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE id=%s", (TestDeleteProduct.product_id,))
            result = cur.fetchone()
            conn.close()

            if result:
                pytest.fail(f"⚠️ Product with ID {TestDeleteProduct.product_id} still exists in DB")
            else:
                print(f"✅ Product ID {TestDeleteProduct.product_id} successfully deleted from DB")

    def test_delete_nonexistent_product(self, login_admin):
        driver = login_admin
        driver.get(BASE_URL)
        fake_id = "999999"
        slow_step(f"Trying to delete non-existent product ID {fake_id}")

        slow_type(driver.find_element(By.ID, "product_id"), fake_id)
        slow_click(driver.find_element(By.CLASS_NAME, "delete-btn"))

        # --- Confirm DB still has no such product ---
        conn = db_connect()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE id=%s", (fake_id,))
            result = cur.fetchone()
            conn.close()

            assert result is None, f"⚠️ Unexpectedly found product with ID {fake_id} in DB"
            print(f"✅ No product with ID {fake_id} found in DB (as expected)")

    def test_back_button(self, login_admin):
        """Verify that the back button on delete_product.php navigates to admin_home.php"""
        driver = login_admin
        driver.get(BASE_URL)
        slow_step("Clicking back button on delete_product.php")

        back_btn = driver.find_element(By.CLASS_NAME, "back-btn")
        slow_click(back_btn)

        assert ADMIN_HOME_URL in driver.current_url, "⚠️ Back button did not navigate to admin_home.php"
        print("✅ Back button successfully navigated to admin_home.php")
