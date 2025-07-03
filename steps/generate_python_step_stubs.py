import re
import os
import argparse
from pathlib import Path

FEATURE_DIR = Path('gherkin')
STUBS_DIR   = Path('tests')


def slugify(text: str) -> str:
    """Convert arbitrary text into a valid Python identifier."""
    s = re.sub(r'[^0-9a-zA-Z_]', '_', text.strip().replace(' ', '_')).lower()
    return re.sub(r'_+', '_', s).strip('_')


def collect_features(feature_dir: Path):
    """
    Scan feature_dir for .feature files and extract steps.
    Returns list of (feature_path, feature_name, steps) where
    steps is [(keyword, raw_phrase), ...].
    """
    features = []
    for feature_path in feature_dir.glob('*.feature'):
        lines = feature_path.read_text().splitlines()
        feature_name = slugify(feature_path.stem)
        # override with Feature: header if present
        for l in lines:
            m = re.match(r'\s*Feature:\s*(.+)', l)
            if m:
                feature_name = slugify(m.group(1))
                break

        steps, prev_kw = [], None
        for l in lines:
            m = re.match(r'\s*(Given|When|Then|And)\s+(.+)', l)
            if not m:
                continue
            kw, phr = m.group(1), m.group(2).strip()
            # resolve "And"
            if kw == 'And' and prev_kw:
                kw = prev_kw
            else:
                prev_kw = kw
            steps.append((kw.lower(), phr))
        features.append((feature_path, feature_name, steps))
    return features


def generate_stub_file(feature_path: Path, feature_name: str, steps, output_dir: Path, mock_module: str=None):
    """
    Generate a pytest-bdd + Selenium stub file, preserving exact phrases
    and deduplicating repeated steps.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stub_path = output_dir / f"{feature_name}_steps.py"

    lines = [
        '"""Auto-generated step definitions from .feature files. Do not edit manually."""',
        'from pytest_bdd import scenarios, given, when, then, parsers',
        'import pytest',
        'from selenium import webdriver',
        'from selenium.webdriver.common.by import By',
        'from selenium.webdriver.support.ui import WebDriverWait',
        'from selenium.webdriver.support import expected_conditions as EC',
        'from config.locators import locators',
        'from config.endpoints import endpoints',
    ]
    if mock_module:
        lines.append(f'from {mock_module} import mock_api, base_url')
    lines.append('')

    # bind the feature
    rel = os.path.relpath(feature_path, output_dir)
    lines.append(f"scenarios(r'{rel}')")
    lines.append('')

    # browser fixture
    lines.extend([
        '@pytest.fixture',
        'def browser():',
        '    driver = webdriver.Chrome()',
    ])
    if mock_module:
        lines.extend([
            '    # Activate mock API server fixture',
            '    mock_api()',
        ])
    lines.extend([
        '    driver.maximize_window()',
        '    yield driver',
        '    driver.quit()',
        ''
    ])

    seen = set()
    for keyword, raw_phrase in steps:
        # use the raw phrase
        phrase = raw_phrase
        # prefix if needed
        if not phrase.lower().startswith('the user'):
            phrase = 'the user ' + phrase[0].lower() + phrase[1:]

        # dedupe
        key = (keyword, phrase)
        if key in seen:
            continue
        seen.add(key)

        # parameterize "<foo>" -> "{foo}"
        if '<' in phrase and '>' in phrase:
            pat = phrase.replace('<', '{').replace('>', '}')
            decorator = f"@{keyword}(parsers.parse(r'{pat}'))"
            args = ['browser'] + re.findall(r'\{(\w+)\}', pat)
        else:
            decorator = f"@{keyword}(\"{phrase}\")"
            args = ['browser']

        func_name = slugify(f"{keyword}_{raw_phrase}")

        lines.append(decorator)
        lines.append(f"def {func_name}({', '.join(args)}):")
        lines.append("    # TODO: implement this step using Selenium WebDriver, locators, and endpoints")
        lines.append("    pass")
        lines.append('')

    stub_path.write_text('\n'.join(lines))
    print(f"Generated stub: {stub_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate pytest-bdd Selenium stubs with exact Gherkin matching"
    )
    parser.add_argument('--features', type=Path, default=FEATURE_DIR)
    parser.add_argument('--stubs',    type=Path, default=STUBS_DIR)
    parser.add_argument('--mock',     type=str,  default='tests.conftest')
    args = parser.parse_args()

    for fp, fn, steps in collect_features(args.features):
        generate_stub_file(fp, fn, steps, args.stubs, args.mock)


if __name__ == '__main__':
    main() 