import re
import os
import argparse
from pathlib import Path

FEATURE_DIR = Path('gherkin')
STUBS_OUT = Path('ai_prompts/available_step_stubs.txt')
STUBS_DIR = Path('tests')

HEADER = '''"""
Auto-generated step definitions from .feature files. Do not edit manually.
"""
from pytest_bdd import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
'''

def slugify(text: str) -> str:
    """Convert text to a valid Python identifier fragment."""
    return re.sub(r'[^0-9a-zA-Z_]', '_', text.strip().replace(' ', '_')).lower()

def collect_features(feature_dir: Path):
    """
    Scan feature_dir for .feature files and extract title + steps.
    Returns list of tuples: (feature_path, feature_name, steps)
    where steps is a list of (keyword, phrase) tuples.
    """
    features = []
    for feature_path in feature_dir.glob('*.feature'):
        lines = feature_path.read_text().splitlines()
        # Derive feature name from filename or Feature: header
        feature_name = slugify(feature_path.stem)
        for line in lines:
            m = re.match(r'\s*Feature:\s*(.+)', line)
            if m:
                feature_name = slugify(m.group(1))
                break
        # Collect steps
        steps = []
        prev_keyword = None
        for line in lines:
            m = re.match(r'\s*(Given|When|Then|And)\s+(.+)', line)
            if m:
                kw, phrase = m.group(1), m.group(2).strip()
                if kw == 'And' and prev_keyword:
                    kw = prev_keyword
                else:
                    prev_keyword = kw
                steps.append((kw.lower(), phrase))
        features.append((feature_path, feature_name, steps))
    return features

def generate_stub_file(feature_path: Path, feature_name: str, steps: list, output_dir: Path, mock_module: str = None):
    """
    Generate a pytest-bdd + selenium stub for one feature.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stub_path = output_dir / f"{feature_name}_steps.py"
    lines = []
    # Header imports
    lines.append('"""Auto-generated step definitions from .feature files. Do not edit manually."""')
    lines.append('from pytest_bdd import scenarios, given, when, then, parsers')
    lines.append('import pytest')
    lines.append('from selenium import webdriver')
    lines.append('from config.locators import locators')
    lines.append('from config.endpoints import endpoints')
    if mock_module:
        lines.append(f'from {mock_module} import mock_api')
    lines.append('')
    # scenarios() binding
    rel_path = os.path.relpath(feature_path, output_dir)
    lines.append(f"scenarios(r'{rel_path}')")
    lines.append('')
    # Browser fixture
    lines.append('@pytest.fixture')
    lines.append('def browser():')
    lines.append('    driver = webdriver.Chrome()')
    lines.append('    driver.maximize_window()')
    if mock_module:
        lines.append('    # Activate mock API server')
        lines.append('    mock_api()')
    lines.append('    yield driver')
    lines.append('    driver.quit()')
    lines.append('')
    # Step definitions
    for keyword, phrase in steps:
        # Parameterize placeholders
        if '<' in phrase and '>' in phrase:
            # Fix: Use single quotes and proper placeholder format
            pattern = re.sub(r'<([^>]+)>', r'{\1}', phrase)
            decorator = f"@{keyword}(parsers.parse('{pattern}'))"
            args = ['browser'] + re.findall(r'\{(\w+)\}', pattern)
        else:
            decorator = f"@{keyword}(\"{phrase}\")"
            args = ['browser']
        
        # Fix: Create cleaner function names
        func_name = slugify(f"{keyword}_{phrase}")
        # Remove extra underscores and limit length
        func_name = re.sub(r'_+', '_', func_name)[:60]
        if func_name.endswith('_'):
            func_name = func_name[:-1]
        
        lines.append(decorator)
        lines.append(f"def {func_name}({', '.join(args)}):")
        
        # Add specific TODO comments based on the step type
        if keyword == 'given' and 'login page' in phrase.lower():
            lines.append('    # TODO: navigate to login via mock_base_url + endpoints[\'login\'][\'path\']')
        elif keyword == 'when' and 'views' in phrase.lower():
            lines.append('    # TODO: wait for locators[\'form\'] to appear')
        elif keyword == 'then' and 'contain' in phrase.lower() and 'field' in phrase.lower():
            lines.append('    # TODO: use locators[field.lower()] to find and assert element presence')
        elif keyword == 'then' and 'contain' in phrase.lower() and 'button' in phrase.lower():
            lines.append('    # TODO: use locators[button.lower()] to find and assert element presence')
        elif keyword == 'then' and 'input' in phrase.lower():
            lines.append('    # TODO: clear & send_keys on locators[field.lower()]')
        elif keyword == 'then' and 'click' in phrase.lower():
            lines.append('    # TODO: find locators[button.lower()] and click')
        else:
            lines.append('    # TODO: implement using Selenium and locators/endpoints')
        lines.append('    pass')
        lines.append('')
    # Write file
    stub_path.write_text('\n'.join(lines))
    print(f"Generated stub: {stub_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate pytest-bdd Selenium stubs from .feature files")
    parser.add_argument('--features', type=Path, default=Path('gherkin'),
                        help="Directory containing .feature files")
    parser.add_argument('--stubs', type=Path, default=Path('tests'),
                        help="Output directory for generated stubs")
    parser.add_argument('--mock', type=str, default=None,
                        help="Python module path for mock server fixture (e.g. 'tests.conftest')")
    args = parser.parse_args()

    features = collect_features(args.features)
    for feature_path, feature_name, steps in features:
        generate_stub_file(
            feature_path, feature_name, steps,
            args.stubs, args.mock
        )

if __name__ == '__main__':
    main() 