import os
import re
import json
import argparse
import subprocess
from bs4 import BeautifulSoup
from pathlib import Path

# Helper: Extract locators using the improved AST-based extraction
def extract_locators_from_files(code_dir):
    """Extract locators using the Node.js AST-based script"""
    locators = {}
    
    # Check if the Node.js script exists
    script_path = Path('scripts/extract-locators.cjs')
    if not script_path.exists():
        print(f"Warning: {script_path} not found, falling back to regex extraction")
        return extract_locators_regex_fallback(code_dir)
    
    try:
        # Run the Node.js script to extract locators
        result = subprocess.run([
            'node', str(script_path)
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            # The script writes to config/locators.json, so read it
            locators_file = Path('config/locators.json')
            if locators_file.exists():
                with open(locators_file, 'r') as f:
                    locators = json.load(f)
                print(f"✅ AST-based extraction found {len(locators)} locators")
            else:
                print("Warning: locators.json not created, falling back to regex extraction")
                return extract_locators_regex_fallback(code_dir)
        else:
            print(f"Warning: Node.js script failed: {result.stderr}")
            return extract_locators_regex_fallback(code_dir)
            
    except Exception as e:
        print(f"Warning: AST extraction failed: {e}, falling back to regex extraction")
        return extract_locators_regex_fallback(code_dir)
    
    return locators

def extract_locators_regex_fallback(code_dir):
    """Fallback to regex-based extraction if AST extraction fails"""
    locators = {}
    for root, dirs, files in os.walk(code_dir):
        for file in files:
            if file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                # data-testid
                for m in re.finditer(r'data-testid=["\\\']([a-zA-Z0-9-_]+)["\\\']', code):
                    name = m.group(1)
                    normalized_key = name.lower().replace(' ', '-')
                    locators[normalized_key] = {"by": "data-testid", "selector": f"[data-testid='{name}']", "value": name}
                # id
                for m in re.finditer(r'id=["\\\']([a-zA-Z0-9-_]+)["\\\']', code):
                    name = m.group(1)
                    normalized_key = name.lower().replace(' ', '-')
                    if normalized_key not in locators:
                        locators[normalized_key] = {"by": "id", "selector": f"#{name}", "value": name}
            elif file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                for tag in soup.find_all(attrs={"data-testid": True}):
                    name = tag['data-testid']
                    normalized_key = name.lower().replace(' ', '-')
                    locators[normalized_key] = {"by": "data-testid", "selector": f"[data-testid='{name}']", "value": name}
                for tag in soup.find_all(id=True):
                    name = tag['id']
                    normalized_key = name.lower().replace(' ', '-')
                    if normalized_key not in locators:
                        locators[normalized_key] = {"by": "id", "selector": f"#{name}", "value": name}
    return locators

# Helper: Extract endpoints from JS/TS files
def extract_endpoints_from_file(filepath):
    endpoints = {}
    if filepath.endswith(('.js', '.jsx', '.ts', '.tsx')):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        # fetch('...') or fetch("...")
        for m in re.finditer(r'fetch\(["\\\']([^"\\\']+)["\\\']', code):
            url = m.group(1)
            name = url.strip('/').replace('/', '_').replace('-', '_')
            endpoints[name] = {"method": "GET/POST", "path": url, "mockStatus": 200, "mockResponse": {}}
        # axios.get/post/put/delete('...')
        for m in re.finditer(r'axios\.(get|post|put|delete)\(["\\\']([^"\\\']+)["\\\']', code):
            method, url = m.group(1).upper(), m.group(2)
            name = url.strip('/').replace('/', '_').replace('-', '_')
            endpoints[name] = {"method": method, "path": url, "mockStatus": 200, "mockResponse": {}}
    return endpoints

def main():
    parser = argparse.ArgumentParser(description="Extract locators and endpoints from codebase.")
    parser.add_argument('--code-dir', default='github_code', help='Directory to scan for code files')
    parser.add_argument('--locators', default='config/locators.json', help='Output file for locators')
    parser.add_argument('--endpoints', default='config/endpoints.json', help='Output file for endpoints')
    args = parser.parse_args()

    # Extract locators using improved AST-based extraction
    all_locators = extract_locators_from_files(args.code_dir)
    
    # Extract endpoints using existing regex-based extraction
    all_endpoints = {}
    for root, dirs, files in os.walk(args.code_dir):
        for file in files:
            if file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                path = os.path.join(root, file)
                eps = extract_endpoints_from_file(path)
                all_endpoints.update(eps)

    # Write locators (the AST script already wrote them, but we'll overwrite with our merged result)
    with open(args.locators, 'w', encoding='utf-8') as f:
        json.dump(all_locators, f, indent=2)
    
    # Write endpoints
    with open(args.endpoints, 'w', encoding='utf-8') as f:
        json.dump(all_endpoints, f, indent=2)
    
    print(f"Extracted {len(all_locators)} locators and {len(all_endpoints)} endpoints.")

if __name__ == "__main__":
    main() 