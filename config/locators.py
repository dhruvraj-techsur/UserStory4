import json
from pathlib import Path

locators_path = Path(__file__).parent / 'locators.json'
with open(locators_path, 'r', encoding='utf-8') as f:
    locators = json.load(f) 