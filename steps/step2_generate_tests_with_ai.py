import os
import re
import openai
import dotenv
import json
from pathlib import Path

def call_openai(prompt, model='gpt-4o', temperature=0.2, max_tokens=4096):
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Generate production-ready test code."},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )
    content = response.choices[0].message.content
    # Extract code block
    match = re.search(r'```python\s*([\s\S]*?)```', content)
    return match.group(1).strip() if match else content.strip()

def step2_generate_tests_with_ai(feature_dir, stubs_dir, locators_path, endpoints_path, mockserver_path, output_dir):
    dotenv.load_dotenv()
    openai.api_key = os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        raise RuntimeError('OPENAI_API_KEY not found in environment or .env')

    feature_files = [f for f in os.listdir(feature_dir) if f.endswith('.feature')]
    os.makedirs(output_dir, exist_ok=True)

    for feature_file in feature_files:
        feature_path = os.path.join(feature_dir, feature_file)
        feature_name_slug = Path(feature_file).stem.replace('-', '_').replace(' ', '_')
        stubs_path = os.path.join(stubs_dir, f"test_{feature_name_slug}_steps.py")
        output_path = os.path.join(output_dir, f"test_{feature_name_slug}.py")

        # Read all artifacts
        feature_text = Path(feature_path).read_text()
        stub_text = Path(stubs_path).read_text() if os.path.exists(stubs_path) else ''
        locators_json = Path(locators_path).read_text()
        endpoints_json = Path(endpoints_path).read_text()
        mockserver_code = Path(mockserver_path).read_text()

        prompt = f"""
You are a test-code generator that produces end-to-end front-end tests in Python using pytest-bdd and Selenium.  
Given the following artifacts, output **only** a single Python test module named `test_{feature_name_slug}.py` (wrapped in ```python blocks) that is fully working—no TODOs or explanations:

1) **Feature file** (`{feature_file}`)
```gherkin
{feature_text}
```

2. **Step-definition stubs** (`test_{feature_name_slug}_steps.py`)
```python
{stub_text}
```

3. **Locator map** (`locators.json`)
```json
{locators_json}
```

4. **Endpoint map** (`endpoints.json`)
```json
{endpoints_json}
```

5. **Mock-server fixture** (`tests/conftest.py`)
```python
{mockserver_code}
```

**Requirements**:

* At the top, `from pytest_bdd import scenarios, given, when, then, parsers` and import `pytest`, `selenium.webdriver`, your `locators`, `endpoints`, and the `browser` fixture from `tests/conftest`.
* Call `scenarios(r'{feature_path}')` to bind the feature.
* Implement **every** stub from the provided file:

  * Use `browser.get(pytest.mock_base_url + endpoints['<endpoint_key>']['path'])` for navigation or AJAX-driven flows.
  * Use `locators['<locator_key>']` (a `(By, selector)` tuple) with `WebDriverWait` and `find_element` to locate and interact with UI elements.
  * Map each `<…>` placeholder in your stubs via `parsers.parse()` so you receive them as function args.
* For any **Scenario Outline**, generate a parametrized test (you can loop over the Examples table).
* Assume `chromedriver` is on `PATH` and **do not** use any Python-side network mocking (patch, requests-mock); all API calls go through the provided mock fixture.
* No comments or TODOs—just runnable code with assertions for the expected behaviors.

Begin your answer with:

```python
# test_{feature_name_slug}.py
```

and then the full file contents.
"""

        print(f"[AI] Generating test for feature: {feature_file}")
        code = call_openai(prompt)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"[Generated] Test file: {output_path}")
    print("\n[AI Test file generation complete]")

if __name__ == "__main__":
    # Example usage with your pipeline's default paths
    step2_generate_tests_with_ai(
        feature_dir="gherkin",
        stubs_dir="tests",
        locators_path="config/locators.json",
        endpoints_path="config/endpoints.json",
        mockserver_path="tests/conftest.py",
        output_dir="tests"
    ) 