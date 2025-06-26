# 📝 Story: Secure Login API Integration

**Title:** Secure Login API Integration

**Description:**  
As a registered user, I want to submit my email and password to the login API endpoint so that, upon successful authentication, I’m redirected to my dashboard; otherwise I see an appropriate error.

**Acceptance Criteria:**

1. **Endpoint & Payload**  
   - **Endpoint:** `POST /api/login`  
   - **Request body:**  
     ```json
     {
       "email": "<user_email>",
       "password": "<user_password>"
     }
     ```

2. **Valid Credentials**  
   - A user exists with:
     - **email:** `user@example.com`
     - **password:** `Password123!`  
   - Submitting those credentials returns **200 OK** with body:
     ```json
     { "token": "<jwt_token>" }
     ```
   - The user is redirected to `/dashboard`.

3. **Invalid Credentials**  
   - No account matches:
     - **email:** `wrong@example.com`
     - **password:** `badpass`  
   - Submitting those credentials returns **401 Unauthorized** with body:
     ```json
     { "message": "Invalid email or password" }
     ```
   - The error message `"Invalid email or password"` is displayed.

4. **Loading State**  
   - While the login request is in flight, the **Login** button is disabled and shows `Logging in...`.

5. **Network Error**  
   - If the network is unreachable, submitting credentials shows:  
     ```
     "Network error. Please try again later."
     ```
