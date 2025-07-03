@AutoGen
Feature: Display Login Form

  Background:
    Given the user is on the login page

  Scenario Outline: User sees the login form with required fields and validation
    When the user views the login form
    Then the form should contain "<field>" input field

    Examples:
      | field    |
      | Email    |
      | Password |
      | Login    |

  Scenario Outline: User enters invalid inputs in the login form
    When the user enters "<input>" in the "<field>" field
    And clicks on the Login button
    Then an error message should be displayed for "<field>"

    Examples:
      | field    | input          |
      | Email    | invalid_email  |
      | Password |              |
      | Email    | not_an_email   |