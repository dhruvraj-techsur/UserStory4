@AutoGen
Feature: Display Login Form
  As a user
  I want to see a login form with email, password fields, and a login button
  So that I can log in to the system

Background:
  Given the user is on the login page

Scenario Outline: User fills in the login form with valid inputs
  When the user fills in the <email> email field with a valid email
    And the user fills in the <password> password field with a valid password
    And the user clicks on the login button
  Then the user should be logged in

  Examples:
    | email          | password |
    | test@test.com  | Password1 |

Scenario Outline: User fills in the login form with invalid inputs
  When the user fills in the <email> email field with an invalid email
    And the user fills in the <password> password field with an invalid password
    And the user clicks on the login button
  Then the user should see an error message next to the <field> field

  Examples:
    | email          | password   | field    |
    | invalidemail   | Password1  | Email    |
    | test@test.com  | pass       | Password |

Scenario Outline: User leaves the login form fields empty
  When the user leaves the <field> field empty
    And the user clicks on the login button
  Then the user should see an error message next to the <field> field

  Examples:
    | field    |
    | Email    |
    | Password |