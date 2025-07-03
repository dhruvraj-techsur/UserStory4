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
***FILL-IN INSTRUCTIONS:***
- Never add or duplicate step functions—only fill in the bodies of the existing stubs.
- Do not generate any new @then (or any) decorators beyond what's in your stub file.
- Do **not** inline locators or endpoints. Instead:
    from config.locators import locators
    from config.endpoints import endpoints
- Any step that does `browser.get(...)` needs `base_url` in its signature:
    def user_on_X(browser, base_url):
- Use the same `scenarios(r'…')` path your stub declared—do **not** change it.
- Do **not** modify any imports, decorators, function names, or signatures in the stub file—treat it as immutable boilerplate.
- Only replace each `# TODO` line with working Selenium code.
- Use the imported `base_url` fixture (not `mock_base_url`) for all `browser.get(...)` calls.
- For navigation steps, use:
    browser.get(f"{{base_url}}{{endpoints['<endpoint_key>']['path']}}")
- `mock_api` is autouse—do not call it inside step functions.
- Do **not** reference `mock_base_url`.
- Do **not** add or remove any imports or definitions outside of `# TODO` replacements.
- Use the provided `locators` and `endpoints` dicts—do **not** reload JSON files.
- For placeholder steps (parsers.parse), preserve the existing pattern (`"{{placeholder}}"`) and inject `clear()`, `send_keys(...)`, or `click()` as appropriate.
- For assertion steps, use `WebDriverWait` + `EC` patterns and meaningful assertions (e.g. URL contains, element visibility).

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

* At the top, `from pytest_bdd import scenarios, given, when, then, parsers` plus `import pytest`, `selenium.webdriver`, your `locators`, `endpoints`, and the `base_url` fixture from `tests/conftest`.
* Call `scenarios(r'{feature_path}')` to bind the feature.
* Implement **every** stub by replacing its `# TODO` with the appropriate Selenium-driven code.
* For any **Scenario Outline**, generate a parametrized test (iterating over the Examples table).
* Assume `chromedriver` is on `PATH` and **do not** use Python-side network mocking—use the provided mock fixture instead.
* No extra commentary—just runnable code with real interactions and assertions.

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