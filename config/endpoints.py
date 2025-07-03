import json
from pathlib import Path

endpoints_path = Path(__file__).parent / 'endpoints.json'
with open(endpoints_path, 'r', encoding='utf-8') as f:
    endpoints = json.load(f) 