# test_display_login_form.py

from pytest_bdd import scenarios, given, when, then, parsers
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.locators import locators
from config.endpoints import endpoints
from tests.conftest import base_url

scenarios(r'../gherkin/display_login_form.feature')

@given('the user is on the login page')
def user_on_login_page(browser, base_url):
    browser.get(f"{base_url}{endpoints['login']['path']}")

@when(parsers.parse('the user fills in the {email} email field with a valid email'))
def user_fills_in_email_field(browser, email):
    email_field = browser.find_element(By.ID, locators['email']['value'])
    email_field.clear()
    email_field.send_keys(email)

@when(parsers.parse('the user fills in the {password} password field with a valid password'))
def user_fills_in_password_field(browser, password):
    password_field = browser.find_element(By.ID, locators['password']['value'])
    password_field.clear()
    password_field.send_keys(password)

@when(parsers.parse('the user clicks on the login button'))
def user_clicks_login_button(browser):
    login_button = browser.find_element(By.CSS_SELECTOR, locators['login']['selector'])
    login_button.click()

@then('the user should be logged in')
def user_should_be_logged_in(browser):
    WebDriverWait(browser, 10).until(EC.url_contains("/dashboard"))
    assert "/dashboard" in browser.current_url

@when(parsers.parse('the user fills in the {email} email field with an invalid email'))
def user_fills_in_invalid_email_field(browser, email):
    email_field = browser.find_element(By.ID, locators['email']['value'])
    email_field.clear()
    email_field.send_keys(email)

@when(parsers.parse('the user fills in the {password} password field with an invalid password'))
def user_fills_in_invalid_password_field(browser, password):
    password_field = browser.find_element(By.ID, locators['password']['value'])
    password_field.clear()
    password_field.send_keys(password)

@then(parsers.parse('the user should see an error message next to the {field} field'))
def user_sees_error_message(browser, field):
    if field == "Email":
        error_locator = (By.CSS_SELECTOR, "[data-testid='email-error']")
    elif field == "Password":
        error_locator = (By.CSS_SELECTOR, "[data-testid='password-error']")
    error_message = WebDriverWait(browser, 10).until(EC.visibility_of_element_located(error_locator))
    assert error_message.is_displayed()

@when(parsers.parse('the user leaves the {field} field empty'))
def user_leaves_field_empty(browser, field):
    if field == "Email":
        email_field = browser.find_element(By.ID, locators['email']['value'])
        email_field.clear()
    elif field == "Password":
        password_field = browser.find_element(By.ID, locators['password']['value'])
        password_field.clear()