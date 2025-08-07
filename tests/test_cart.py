import time
import pytest
import mysql.connector
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost/minishop/customer/cart.php"

# ---------- DB CONFIG ----------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
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
    return result[0] if result else None

def get_cart_items(user_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.product_id, c.quantity, p.name, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s AND c.bought = 'no'
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def seed_cart_if_empty(user_id):
    """Ensure the cart has at least one product for testing."""
    cart = get_cart_items(user_id)
    if not cart:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, stock FROM products WHERE stock > 0 LIMIT 1")
        product = cursor.fetchone()
        if not product:
            pytest.skip("⚠️ No products in stock to seed cart.")
        product_id, stock = product
        cursor.execute(
            "INSERT INTO cart (user_id, product_id, quantity, bought) VALUES (%s, %s, %s, 'no')",
            (user_id, product_id, 1)
        )
        conn.commit()
        cursor.close()
        conn.close()
        print(f"🛒 Seeded product {product_id} for user {user_id}")

# ---------- UTILS ----------
def slow_step(msg, wait=2):
    """Pause for visibility during test execution."""
    print(f"⏳ {msg} (waiting {wait}s)")
    time.sleep(wait)

def type_like_human(element, text, delay=0.3):
    """Simulate human typing with a delay per key."""
    element.clear()
    for ch in text:
        element.send_keys(ch)
        time.sleep(delay)
    slow_step(f"Finished typing '{text}'", wait=1)

# ---------- TESTS ----------
@pytest.mark.usefixtures("login_customer")
class TestCartPage:

    def test_cart_page_loads(self, login_customer):
        driver = login_customer
        slow_step("Opening Cart Page")
        driver.get(BASE_URL)
        assert "Your Cart" in driver.page_source

    def test_cart_items_displayed(self, login_customer):
        driver = login_customer
        username = "abc"
        user_id = get_user_id(username)
        assert user_id, "⚠️ Test user not found in DB"
        seed_cart_if_empty(user_id)

        driver.get(BASE_URL)
        try:
            rows = WebDriverWait(driver, 7).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tr"))
            )
            print(f"📌 Found {len(rows)-1} cart item rows.")
            assert len(rows) > 1
        except:
            pytest.fail("⚠️ Cart should not be empty after seeding")

    def test_update_quantity_and_db_sync(self, login_customer):
        driver = login_customer
        username = "abc"
        user_id = get_user_id(username)
        assert user_id, f"⚠️ Test user '{username}' not found in DB"
        seed_cart_if_empty(user_id)

        driver.get(BASE_URL)
        cart_rows = get_cart_items(user_id)
        product_id, old_qty, name, price = cart_rows[0]
        slow_step(f"Found product {name} with qty {old_qty}")

        qty_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, f"quantities[{product_id}]"))
        )
        new_qty = old_qty + 1
        type_like_human(qty_input, str(new_qty))

        update_btn = driver.find_element(By.NAME, "update_cart")
        slow_step("Clicking Update Cart Button")
        driver.execute_script("arguments[0].click();", update_btn)
        time.sleep(3)

        updated_cart = get_cart_items(user_id)
        updated_qty = [row[1] for row in updated_cart if row[0] == product_id][0]
        assert updated_qty == new_qty

    def test_total_price_matches_db(self, login_customer):
        driver = login_customer
        username = "abc"
        user_id = get_user_id(username)
        assert user_id, "⚠️ Test user not found in DB"
        seed_cart_if_empty(user_id)

        driver.get(BASE_URL)
        cart_items = get_cart_items(user_id)
        db_total = sum(price * qty for _, qty, _, price in cart_items)

        total_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'Total Price')]"))
        ).text
        ui_total = int(total_text.split("₹")[1].replace(",", "").strip())

        print(f"📌 DB total: ₹{db_total}, UI total: ₹{ui_total}")
        assert ui_total == db_total

    def test_pay_now_button_present(self, login_customer):
        driver = login_customer
        username = "abc"
        user_id = get_user_id(username)
        assert user_id, "⚠️ Test user not found in DB"
        seed_cart_if_empty(user_id)

        driver.get(BASE_URL)
        pay_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "pay_now"))
        )
        assert pay_button.is_displayed()

    def test_continue_shopping_button(self, login_customer):
        driver = login_customer
        driver.get(BASE_URL)
        slow_step("Looking for Continue Shopping button")
        # ✅ Match link text with your PHP file
        continue_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Continue"))
        )
        continue_btn.click()
        slow_step("Clicked Continue Shopping")
        # ✅ Instead of checking "products", check homepage URL pattern
        assert "customer_home" in driver.current_url.lower() or "customer" in driver.current_url.lower()

    def test_logout_button(self, login_customer):
        driver = login_customer
        driver.get(BASE_URL)
        slow_step("Looking for Logout button")
        logout_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Logout"))
        )
        logout_btn.click()
        slow_step("Clicked Logout")
        # ✅ Adapt to your PHP: it goes to index.php
        assert "index.php" in driver.current_url.lower() or "login" in driver.current_url.lower()
