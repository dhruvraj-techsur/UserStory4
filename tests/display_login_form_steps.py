"""Auto-generated step definitions from .feature files. Do not edit manually."""
from pytest_bdd import scenarios, given, when, then, parsers
import pytest
from selenium import webdriver
from config.locators import locators
from config.endpoints import endpoints

scenarios(r'../gherkin/display_login_form.feature')

@pytest.fixture
def browser():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

@given("the user is on the login page")
def given_the_user_is_on_the_login_page(browser):
    # TODO: navigate to login via mock_base_url + endpoints['login']['path']
    pass

@when("the user views the login form")
def when_the_user_views_the_login_form(browser):
    # TODO: wait for locators['form'] to appear
    pass

@then(parsers.parse('the form should contain "{field}" input field'))
def then_the_form_should_contain_field_input_field(browser, field):
    # TODO: use locators[field.lower()] to find and assert element presence
    pass

@when(parsers.parse('the user enters "{input}" in the "{field}" field'))
def when_the_user_enters_input_in_the_field_field(browser, input, field):
    # TODO: implement using Selenium and locators/endpoints
    pass

@when("clicks on the Login button")
def when_clicks_on_the_login_button(browser):
    # TODO: implement using Selenium and locators/endpoints
    pass

@then(parsers.parse('an error message should be displayed for "{field}"'))
def then_an_error_message_should_be_displayed_for_field(browser, field):
    # TODO: implement using Selenium and locators/endpoints
    pass
