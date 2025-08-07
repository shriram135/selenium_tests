import time
import uuid
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")  # Remove this line to see the browser
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def wait_and_click(driver, by, value, timeout=10):
    wait = WebDriverWait(driver, timeout)
    element = wait.until(EC.element_to_be_clickable((by, value)))
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    driver.execute_script("arguments[0].click();", element)

def test_todo_app(driver):
    base_url = "http://localhost/todo-app/public/index.php"
    category = "weekly"
    unique_task = f"Test Task Selenium {uuid.uuid4().hex[:6]}"

    driver.get(base_url)
    wait = WebDriverWait(driver, 10)

    # Add a new task
    wait.until(EC.presence_of_element_located((By.NAME, "title"))).send_keys(unique_task)
    Select(driver.find_element(By.NAME, "category")).select_by_value(category)
    wait_and_click(driver, By.CSS_SELECTOR, "button[type='submit']")
    time.sleep(1)

    # Navigate to category tab
    driver.get(f"{base_url}?category={category}")
    time.sleep(1)

    # Confirm task is added
    row = wait.until(EC.presence_of_element_located((By.XPATH, f"//td[contains(text(), '{unique_task}')]/..")))

    # Mark as complete
    checkbox = row.find_element(By.XPATH, ".//input[@type='checkbox']")
    driver.execute_script("arguments[0].click();", checkbox)

    # Click update
    wait_and_click(driver, By.NAME, "update_tasks")
    time.sleep(1)

    # Reload and delete the task
    driver.get(f"{base_url}?category={category}")
    time.sleep(1)

    row = wait.until(EC.presence_of_element_located((By.XPATH, f"//td[contains(text(), '{unique_task}')]/..")))
    delete_link = row.find_element(By.LINK_TEXT, "Delete")
    driver.execute_script("arguments[0].click();", delete_link)

    # Final check: ensure task is deleted
    driver.get(f"{base_url}?category={category}")
    time.sleep(1)
    matches = driver.find_elements(By.XPATH, f"//td[contains(text(), '{unique_task}')]")
    assert len(matches) == 0, "❌ Task was not deleted"
