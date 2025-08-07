import time
import pytest
import mysql.connector
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost/minishop/customer/customer_home.php"

# ---------- DB CONFIG ----------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",       # change if needed
    "password": "",       # change if needed
    "database": "mini_shop"
}

# ---------- DB HELPERS ----------
def get_user_id(username):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    print(f"📝 get_user_id('{username}') -> {result}")
    return result[0] if result else None

def get_cart_item(user_id, product_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, user_id, product_id, quantity, bought
        FROM cart 
        WHERE user_id = %s AND product_id = %s AND bought = 'no'
        """,
        (user_id, product_id),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"📝 Cart rows for user_id={user_id}, product_id={product_id}: {rows}")
    return rows[0][3] if rows else None

def get_product_id_by_name(name):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products WHERE name = %s", (name,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    print(f"📝 get_product_id_by_name('{name}') -> {result}")
    return result[0] if result else None

# ---------- UTILS ----------
def slow_step(msg, wait=3):
    print(f"⏳ {msg} (waiting {wait}s)")
    time.sleep(wait)

def debug_dump(driver, name="debug"):
    html_path = f"{name}.html"
    png_path = f"{name}.png"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    driver.save_screenshot(png_path)
    print(f"📝 Saved debug dump: {html_path}, screenshot: {png_path}")

# ---------- TESTS ----------
@pytest.mark.usefixtures("login_customer")
class TestCustomerHome:

    def test_page_loads(self, login_customer):
        driver = login_customer
        slow_step("Loading customer home page")
        driver.get(BASE_URL)
        assert "Mini Shop" in driver.title
        welcome_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h2"))
        ).text
        print(f"📌 Found welcome text: {welcome_text}")
        assert "Welcome" in welcome_text

    def test_product_listing(self, login_customer):
        driver = login_customer
        slow_step("Checking product listing")
        driver.get(BASE_URL)
        products = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "product-box"))
        )
        print(f"📌 Found {len(products)} products.")
        assert len(products) > 0, "No products displayed"

    def test_search_functionality(self, login_customer):
        driver = login_customer
        slow_step("Testing search functionality")

        driver.get(BASE_URL)
        first_product_name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-box h3"))
        ).text
        query = first_product_name.split()[0]

        driver.get(BASE_URL + f"?search={query}")
        slow_step(f"Searching for '{query}'", wait=2)

        results_ui = [
            el.text for el in WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-box h3"))
            )
        ]
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE name LIKE %s", (f"%{query}%",))
        results_db = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        print(f"📌 UI search results: {results_ui}")
        print(f"📌 DB search results: {results_db}")
        assert set(results_ui).issubset(set(results_db))

    def test_add_to_cart_and_db_sync(self, login_customer):
        driver = login_customer
        username = "abc"
        product_name = "botte"  # ensure this matches DB exactly
        slow_step("Testing add to cart with fixed user/product")

        user_id = get_user_id(username)
        assert user_id is not None, f"⚠️ Test user '{username}' not found in DB"

        product_id = get_product_id_by_name(product_name)
        assert product_id is not None, f"⚠️ Test product '{product_name}' not found in DB"

        driver.get(BASE_URL)

        product_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//div[contains(@class,'product-box')]//h3[text()='{product_name}']/ancestor::div[contains(@class,'product-box')]")
            )
        )

        qty_input = product_box.find_element(By.CLASS_NAME, "qty-input")
        plus_btn = product_box.find_element(By.CLASS_NAME, "plus")
        add_btn = product_box.find_element(By.CLASS_NAME, "add-btn")

        slow_step("Clicking + button", wait=2)
        driver.execute_script("arguments[0].click();", plus_btn)
        new_qty = int(driver.execute_script("return arguments[0].value;", qty_input))
        print(f"📌 Quantity in UI: {new_qty}")

        slow_step("Clicking Add to Cart", wait=2)
        driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(3)

        db_qty = get_cart_item(user_id, product_id)

        if db_qty is None:
            debug_dump(driver, "cart_failure")
            pytest.fail(f"No cart entry found for user_id={user_id}, product_id={product_id}. "
                        f"Check if Add to Cart inserts correctly.")
        else:
            print(f"📌 DB quantity: {db_qty}, Expected: {new_qty}")
            assert db_qty == new_qty, f"Expected {new_qty}, found {db_qty} in DB"

    def test_logout_button(self, login_customer):
        driver = login_customer
        slow_step("Testing logout button")
        driver.get(BASE_URL)

        logout_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Logout"))
        )
        logout_btn.click()
        slow_step("Clicked Logout", wait=2)

        WebDriverWait(driver, 10).until(EC.url_changes(BASE_URL))
        current_url = driver.current_url.lower()
        print(f"📌 Redirected to: {current_url}")

        assert "index.php" in current_url or "login" in current_url, \
            f"Expected redirect to login/index.php, but got {current_url}"
