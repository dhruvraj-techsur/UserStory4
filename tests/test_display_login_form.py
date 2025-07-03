# test_display_login_form.py

from pytest_bdd import scenarios, given, when, then, parsers
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import json
from pathlib import Path

# Load locators and endpoints
locators_path = Path(__file__).parent.parent / 'config' / 'locators.json'
with open(locators_path) as f:
    locators = json.load(f)

endpoints_path = Path(__file__).parent.parent / 'config' / 'endpoints.json'
with open(endpoints_path) as f:
    endpoints = json.load(f)

# Bind feature file
scenarios(r'gherkin/display_login_form.feature')

@pytest.fixture
def browser():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

@given('the user is on the login page')
def user_on_login_page(browser):
    browser.get(pytest.mock_base_url + endpoints['login']['path'])

@when('the user views the login form')
def user_views_login_form(browser):
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, locators['root']['selector']))
    )

@then(parsers.parse('the form should contain "{field}" input field'))
def form_contains_field(browser, field):
    locator_key = field.lower()
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, locators[locator_key]['selector']))
    )

@when(parsers.parse('the user enters "{input}" in the "{field}" field'))
def user_enters_input(browser, input, field):
    locator_key = field.lower()
    input_element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, locators[locator_key]['selector']))
    )
    input_element.clear()
    input_element.send_keys(input)

@when('clicks on the Login button')
def user_clicks_login_button(browser):
    login_button = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, locators['LoginForm-button-0']['selector']))
    )
    login_button.click()

@then(parsers.parse('an error message should be displayed for "{field}"'))
def error_message_displayed(browser, field):
    locator_key = field.lower()
    error_locator = (By.CSS_SELECTOR, f"#{locator_key}-error")
    WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located(error_locator)
    )