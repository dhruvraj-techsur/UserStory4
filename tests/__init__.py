import pytest
import json
from pathlib import Path

# Load locators.json
locators_path = Path(__file__).parent.parent / 'locators.json'

with open(locators_path, 'r', encoding='utf-8') as f:
    locators = json.load(f)
 