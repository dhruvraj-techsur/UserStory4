"""Auto-generated step definitions from .feature files. Do not edit manually."""
from pytest_bdd import scenarios, given, when, then, parsers
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config.locators import locators
from config.endpoints import endpoints
from tests.conftest import mock_api, base_url

scenarios(r'../gherkin/display_login_form.feature')

@pytest.fixture
def browser():
    driver = webdriver.Chrome()
    # Activate mock API server fixture
    mock_api()
    driver.maximize_window()
    yield driver
    driver.quit()

@given("the user is on the login page")
def given_the_user_is_on_the_login_page(browser):
    # TODO: implement this step using Selenium WebDriver, locators, and endpoints
    pass

@when(parsers.parse(r'the user fills in the {email} email field with a valid email'))
def when_the_user_fills_in_the_email_email_field_with_a_valid_email(browser, email):
    # TODO: implement this step using Selenium WebDriver, locators, and endpoints
    pass

@when(parsers.parse(r'the user fills in the {password} password field with a valid password'))
def when_the_user_fills_in_the_password_password_field_with_a_valid_password(browser, password):
    # TODO: implement this step using Selenium WebDriver, locators, and endpoints
    pass

@when("the user clicks on the login button")
def when_the_user_clicks_on_the_login_button(browser):
    # TODO: implement this step using Selenium WebDriver, locators, and endpoints
    pass

@then("the user should be logged in")
def then_the_user_should_be_logged_in(browser):
    # TODO: implement this step using Selenium WebDriver, locators, and endpoints
    pass

@when(parsers.parse(r'the user fills in the {email} email field with an invalid email'))
def when_the_user_fills_in_the_email_email_field_with_an_invalid_email(browser, email):
    # TODO: implement this step using Selenium WebDriver, locators, and endpoints
    pass

@when(parsers.parse(r'the user fills in the {password} password field with an invalid password'))
def when_the_user_fills_in_the_password_password_field_with_an_invalid_password(browser, password):
    # TODO: implement this step using Selenium WebDriver, locators, and endpoints
    pass

@then(parsers.parse(r'the user should see an error message next to the {field} field'))
def then_the_user_should_see_an_error_message_next_to_the_field_field(browser, field):
    # TODO: implement this step using Selenium WebDriver, locators, and endpoints
    pass

@when(parsers.parse(r'the user leaves the {field} field empty'))
def when_the_user_leaves_the_field_field_empty(browser, field):
    # TODO: implement this step using Selenium WebDriver, locators, and endpoints
    pass
