import os
import re
import openai
import dotenv
from pathlib import Path

def extract_selector_map(component_code):
    # Extract all data-testid attributes from the component code
    regex = r'data-testid=["\]([a-zA-Z0-9-_]+)["\]'
    return {match: match for match in re.findall(regex, component_code)}

def parse_feature_file(feature_path):
    # Simple line-based Gherkin parser
    with open(feature_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f]
    feature_name = ''
    scenarios = []
    current_scenario = None
    for line in lines:
        if line.startswith('Feature:'):
            feature_name = line[len('Feature:'):].strip()
        elif line.startswith('Scenario:'):
            if current_scenario:
                scenarios.append(current_scenario)
            current_scenario = {'name': line[len('Scenario:'):].strip(), 'steps': []}
        elif current_scenario and re.match(r'^(Given|When|Then)\b', line):
            keyword, *rest = line.split(' ', 1)
            current_scenario['steps'].append({'keyword': keyword, 'text': rest[0] if rest else ''})
    if current_scenario:
        scenarios.append(current_scenario)
    return feature_name, scenarios

def build_prompt(component_code, scenario, selector_map, framework):
    if framework == 'jest':
        prompt = f"""
You are a test-code generator.
Given this React component:

```jsx
{component_code}
```

And this Gherkin scenario:

```
Scenario: {scenario['name']}
{chr(10).join(f"{s['keyword']} {s['text']}" for s in scenario['steps'])}
```

And this selector map (data-testids):

```
{chr(10).join(f"{k} -> {v}" for k, v in selector_map.items())}
```

Write a complete Jest test file using @testing-library/react that:
1. Renders the component
2. Mocks the network call to /api/login
3. Executes each step in order (fireEvent or userEvent)
4. Asserts the expected outcomes (loading spinner, redirect, error message)
5. Has no TODOs, just working code.

Begin and end your answer with only the code, wrapped in triple backticks with a 'js' language tag.
"""
    elif framework == 'selenium':
        prompt = f"""
You are a test-code generator.
Given this React component (for reference):

```jsx
{component_code}
```

And this Gherkin scenario:

```
Scenario: {scenario['name']}
{chr(10).join(f"{s['keyword']} {s['text']}" for s in scenario['steps'])}
```

And this selector map (data-testids):

```
{chr(10).join(f"{k} -> {v}" for k, v in selector_map.items())}
```

Write a complete Python test file using pytest-bdd and Selenium that:
1. Uses pytest-bdd scenario/step decorators
2. Uses Selenium to interact with the UI using the data-testids
3. **Do NOT use any Python-side network mocking (no patch, no requests, no unittest.mock).**
4. **Do NOT use webdriver_manager; assume chromedriver is in PATH.**
5. Only use browser-side mocking (MSW or fetch patch) and UI interactions.
6. Use a simple browser fixture with webdriver.Chrome().
7. Asserts the expected outcomes (loading spinner, redirect, error message)
8. Has no TODOs, just working code.

Begin and end your answer with only the code, wrapped in triple backticks with a 'python' language tag.
"""
    else:
        raise ValueError(f"Unknown framework: {framework}")
    return prompt

def call_openai(prompt, model='gpt-4o', temperature=0.2, max_tokens=2048):
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
    match = re.search(r'```[a-zA-Z]*\n([\s\S]*?)```', content)
    return match.group(1).strip() if match else content.strip()

def step2_generate_tests_with_ai(config, feature_dir, output_dir):
    dotenv.load_dotenv()
    openai.api_key = os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        raise RuntimeError('OPENAI_API_KEY not found in environment or .env')

    test_frameworks = config["steps"]["step2_generate_tests"]["test_frameworks"]
    feature_files = [f for f in os.listdir(feature_dir) if f.endswith('.feature')]
    test_build_dir = Path('test_build')
    component_files = list(test_build_dir.glob('*.js'))
    if not component_files:
        raise RuntimeError('No instrumented component found in test_build/')
    component_code = component_files[0].read_text(encoding='utf-8')
    selector_map = extract_selector_map(component_code)
    os.makedirs(output_dir, exist_ok=True)

    for feature_file in feature_files:
        feature_path = os.path.join(feature_dir, feature_file)
        feature_name, scenarios = parse_feature_file(feature_path)
        for scenario in scenarios:
            safe_title = re.sub(r'\W+', '_', scenario['name']).lower()
            for fw, fw_cfg in test_frameworks.items():
                if not fw_cfg.get("enabled"):
                    continue
                prompt = build_prompt(component_code, scenario, selector_map, fw)
                try:
                    print(f"[AI] Generating {fw} test for scenario: {scenario['name']}")
                    code = call_openai(prompt)
                    if fw == "jest":
                        out_file = os.path.join(output_dir, f"{feature_name.replace(' ', '_').lower()}-{safe_title}.test.js")
                    elif fw == "selenium":
                        # Replace any scenarios('login.feature') or scenarios("login.feature") with the correct path
                        code = re.sub(
                            r"scenarios\(['\"]login\.feature['\"]\)",
                            f"scenarios('../gherkin/{feature_file}')",
                            code
                        )
                        # Replace any scenarios('...feature') with @scenario for the specific scenario
                        scenario_name = scenario['name']
                        code = re.sub(
                            r"scenarios\(['\"].*?\.feature['\"]\)",
                            f"from pytest_bdd import scenario\n\n@scenario('../gherkin/{feature_file}', '{scenario_name}')\ndef test_{safe_title}():\n    pass\n",
                            code
                        )
                        out_file = os.path.join(output_dir, f"test_{feature_name.replace(' ', '_').lower()}_{safe_title}_selenium.py")
                    else:
                        continue
                    with open(out_file, 'w', encoding='utf-8') as f:
                        f.write(code)
                    print(f"[Generated] {fw} test file: {out_file}")
                except Exception as e:
                    print(f"[Error] Failed to generate {fw} test for scenario '{scenario['name']}': {e}")
    print("\n[AI Test file generation complete]") 