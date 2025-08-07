# tests/test_pay.py
import time
import pytest
import mysql.connector
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost/minishop/customer/pay.php"
CART_URL = "http://localhost/minishop/customer/customer_home.php"

# ---------- DB CONFIG ----------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",       # adjust if needed
    "password": "",       # adjust if needed
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
        SELECT p.id, p.name, p.price, c.quantity, p.stock
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def seed_cart_if_empty(user_id):
    """Add a product to the cart if it's empty."""
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
def parse_currency(text):
    """Extract float value from currency string like '₹122,000.00'."""
    return float(text.replace("₹", "").replace(",", "").strip())

# ---------- TESTS ----------
@pytest.mark.usefixtures("login_customer")
class TestPaymentPage:

    def test_payment_page_loads(self, login_customer):
        driver = login_customer
        driver.get(BASE_URL)
        assert "Payment Summary" in driver.page_source

    def test_cart_summary_matches_db(self, login_customer):
        driver = login_customer
        username = "abc"  # ⚠️ update with your test user
        user_id = get_user_id(username)
        assert user_id, "⚠️ Test user not found in DB"

        seed_cart_if_empty(user_id)  # ✅ ensure cart has an item
        driver.get(BASE_URL)
        time.sleep(2)

        cart_items_db = get_cart_items(user_id)
        db_total = sum(price * qty for _, _, price, qty, _ in cart_items_db)

        total_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'Total Price')]"))
        ).text
        ui_total = parse_currency(total_text.split("₹")[1])

        print(f"📌 DB total: {db_total}, UI total: {ui_total}")
        assert round(ui_total, 2) == round(db_total, 2)

    def test_pay_button_and_purchase_flow(self, login_customer):
        driver = login_customer
        username = "abc"
        user_id = get_user_id(username)
        assert user_id, "⚠️ Test user not found in DB"

        seed_cart_if_empty(user_id)  # ✅ make sure cart isn’t empty
        driver.get(BASE_URL)
        time.sleep(2)

        cart_items_before = get_cart_items(user_id)
        assert cart_items_before, "⚠️ Cart is still empty after seeding."

        pay_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "button"))
        )
        driver.execute_script("arguments[0].click();", pay_button)
        time.sleep(3)

        # Verify cart is empty after payment
        cart_items_after = get_cart_items(user_id)
        print(f"📌 Cart items after payment: {cart_items_after}")
        assert not cart_items_after, "⚠️ Cart should be empty after payment"

        success_msg = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "message"))
        ).text
        print(f"📌 Success message: {success_msg}")
        assert "successfully bought" in success_msg.lower()

    def test_back_to_cart_button(self, login_customer):
        driver = login_customer
        driver.get(BASE_URL)

        # Locate and click the Back to Cart link
        back_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='back-btn']/a"))
        )
        back_btn.click()
        time.sleep(2)

        # Verify that we navigated to the customer_home.php page
        assert CART_URL in driver.current_url, f"⚠️ Expected to be at {CART_URL}, but got {driver.current_url}"
        assert "Cart" in driver.page_source or "Products" in driver.page_source, "⚠️ Back to Cart page did not load properly"
