import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def test_login_and_check_element():

    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}/login")

        # Wait a little while to make sure the page has loaded completely
        time.sleep(4)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)

        # Wait a little while to ensure that the action has been completed
        time.sleep(4)

        try:

            driver.find_element(By.XPATH, "//h1[contains(@class, 'h2 mb-3') and contains(., 'Latest datasets')]")
            print("Test passed!")

        except NoSuchElementException:
            raise AssertionError("Test failed!")

    finally:

        # Close the browser
        close_driver(driver)


class TestInvalidcredentials1attempt():
  def setup_method(self, method):
    self.driver = initialize_driver()
    self.vars = {}
  
  def teardown_method(self, method):
    self.driver.quit()
  
  def test_invalid_credentials_shows_right_texts(self):
    self.driver.get("http://localhost:5000/")
    self.driver.set_window_size(954, 904)
    self.driver.find_element(By.LINK_TEXT, "Login").click()
    self.driver.find_element(By.ID, "email").click()
    self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
    self.driver.find_element(By.ID, "password").click()
    self.driver.find_element(By.ID, "password").send_keys("123")
    self.driver.find_element(By.ID, "submit").click()
    self.driver.find_element(By.CSS_SELECTOR, "span:nth-child(1)").click()
    assert self.driver.find_element(By.CSS_SELECTOR, "span:nth-child(1)").text == "Invalid credentials. 2 attempts remaining"
    self.driver.find_element(By.ID, "password").click()
    self.driver.find_element(By.ID, "password").send_keys("123")
    self.driver.find_element(By.ID, "submit").click()
    assert self.driver.find_element(By.CSS_SELECTOR, "span:nth-child(1)").text == "Invalid credentials. 1 attempt remaining"
    self.driver.find_element(By.ID, "password").click()
    self.driver.find_element(By.ID, "password").send_keys("123")
    self.driver.find_element(By.ID, "submit").click()
    assert self.driver.find_element(By.CSS_SELECTOR, "span:nth-child(1)").text == "Too many requests. Please wait 30 seconds"
