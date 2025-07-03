import os
import re
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from dotenv import load_dotenv
import requests

def extract_title_and_criteria(user_story_text: str, criteria_headers=None):
    # Extract title from 'Title:' line if present, else first non-empty line
    title = "feature"
    for line in user_story_text.splitlines():
        if line.strip().lower().startswith("title:"):
            title = line.strip()[len("Title:"):].strip()
            break
        elif line.strip():
            title = line.strip()
            break
    # Find acceptance criteria section
    criteria = []
    if not criteria_headers:
        criteria_headers = ["acceptance criteria", "acceptance criteria:", "acceptance criteria -", "## Acceptance Criteria"]
    lines = user_story_text.splitlines()
    start_idx = -1
    for idx, line in enumerate(lines):
        if any(h.lower() in line.lower() for h in criteria_headers):
            start_idx = idx
            break
    if start_idx != -1:
        # Collect everything after the header until the next section or end of file
        for line in lines[start_idx+1:]:
            if line.strip().startswith("#") and not line.strip().lower().startswith("# acceptance criteria"):
                break
            criteria.append(line)
    criteria_text = '\n'.join(criteria).strip()
    return title, criteria_text

def strip_markdown_code_fence(text):
    # Remove ```gherkin or ``` and matching closing ```
    return re.sub(r'^```[a-zA-Z]*\n|```$', '', text, flags=re.MULTILINE).strip()

def fetch_jira_user_story():
    jira_url = os.getenv('JIRA_URL')
    jira_user = os.getenv('JIRA_USER')
    jira_token = os.getenv('JIRA_API_TOKEN')
    jira_ticket = os.getenv('JIRA_TICKET')
    print(f"[DEBUG] JIRA_URL={jira_url}, JIRA_USER={jira_user}, JIRA_TICKET={jira_ticket}")
    if not all([jira_url, jira_user, jira_token, jira_ticket]):
        print("[ERROR] Missing JIRA credentials or ticket in .env")
        raise ValueError("Missing JIRA credentials or ticket in .env")
    api_url = f"{jira_url}/rest/api/3/issue/{jira_ticket}"
    auth = (jira_user, jira_token)
    headers = {"Accept": "application/json"}
    print(f"[DEBUG] Fetching JIRA ticket from {api_url}")
    resp = requests.get(api_url, auth=auth, headers=headers)
    print(f"[DEBUG] JIRA API response status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"[ERROR] Failed to fetch JIRA ticket: {resp.status_code} {resp.text}")
        raise RuntimeError(f"Failed to fetch JIRA ticket: {resp.status_code} {resp.text}")
    data = resp.json()
    # Try to extract summary, description, and acceptance criteria (if present)
    summary = data['fields'].get('summary', '')
    description = data['fields'].get('description', '')
    # JIRA Cloud uses Atlassian Document Format for description; try to extract plain text
    if isinstance(description, dict) and 'content' in description:
        def extract_text(adf, level=0):
            # Recursively extract text, preserving newlines and indentation for nested lists
            indent = '    ' * level
            if isinstance(adf, dict):
                t = adf.get('type')
                if t == 'text':
                    return adf.get('text', '')
                elif t in ('paragraph', 'heading', 'blockquote'):
                    return ''.join(extract_text(c, level) for c in adf.get('content', [])) + '\n'
                elif t in ('bulletList', 'orderedList'):
                    return ''.join(extract_text(c, level+1) for c in adf.get('content', []))
                elif t == 'listItem':
                    # List item: add bullet and indent, then recurse for content
                    item_text = ''.join(extract_text(c, level) for c in adf.get('content', []))
                    # Only add bullet if not already a bullet (for nested lists)
                    lines = item_text.splitlines()
                    if lines:
                        first_line = lines[0].strip()
                        rest = '\n'.join(lines[1:])
                        bullet = f"{indent}- {first_line}\n"
                        # If there is a nested list, it will be in the rest
                        if rest.strip():
                            bullet += rest + '\n'
                        return bullet
                    else:
                        return f"{indent}- \n"
                elif 'content' in adf:
                    return ''.join(extract_text(c, level) for c in adf['content'])
            elif isinstance(adf, list):
                return ''.join(extract_text(c, level) for c in adf)
            return ''
        description = extract_text(description).strip()
    # Try to find acceptance criteria in custom fields or in description
    acceptance_criteria = ''
    found_custom_field = False
    for k, v in data['fields'].items():
        if 'acceptance' in k.lower() and isinstance(v, str) and v.strip():
            acceptance_criteria = v.strip()
            found_custom_field = True
            break
    if not acceptance_criteria and 'Acceptance Criteria' in description:
        # Try to extract from description
        lines = description.splitlines()
        start = None
        for i, line in enumerate(lines):
            if 'acceptance criteria' in line.lower():
                start = i
                break
        if start is not None:
            # Only take lines after the header, stop at next section or end
            acc_lines = []
            for line in lines[start+1:]:
                if line.strip().startswith('#') or (line.strip().endswith(':') and not line.strip().lower().startswith('acceptance criteria')):
                    break
                acc_lines.append(line)
            acceptance_criteria = '\n'.join(acc_lines).strip()
    # Remove acceptance criteria from description if it was extracted from there
    if acceptance_criteria and not found_custom_field:
        desc_lines = description.splitlines()
        cleaned_desc = []
        in_acc = False
        for line in desc_lines:
            if 'acceptance criteria' in line.lower():
                in_acc = True
                continue
            if in_acc:
                # Stop at next section or end
                if line.strip().startswith('#') or (line.strip().endswith(':') and not line.strip().lower().startswith('acceptance criteria')):
                    in_acc = False
            if not in_acc:
                cleaned_desc.append(line)
        description = '\n'.join(cleaned_desc).strip()
    # Remove orphaned 'Acceptance Criteria:' heading at the end of description
    desc_lines = description.splitlines()
    while desc_lines and desc_lines[-1].strip().lower() == 'acceptance criteria:':
        desc_lines.pop()
    description = '\n'.join(desc_lines).strip()
    # Compose user story text
    if acceptance_criteria:
        user_story = f"Title: {summary}\n\nDescription:\n{description}\n\nAcceptance Criteria:\n{acceptance_criteria}"
    else:
        user_story = f"Title: {summary}\n\nDescription:\n{description}"
    # Clean up multiple consecutive blank lines and blank lines between list items
    user_story = re.sub(r'(?m)^\s*\n', '', user_story)  # Remove lines that are just whitespace
    user_story = re.sub(r'\n{3,}', '\n\n', user_story)  # Collapse 3+ newlines to 2
    user_story = re.sub(r'(?m)\n{2,}(- )', '\n\1', user_story)  # No blank lines before list items
    user_story = user_story.strip() + '\n'
    print(f"[DEBUG] Extracted user story summary: {summary}")
    print(f"[DEBUG] Acceptance criteria found: {bool(acceptance_criteria)}")
    return user_story

async def step1_generate_gherkin_async(config: Dict[str, Any], output_dir: str = "gherkin") -> bool:
    logger = logging.getLogger("step1_generate_gherkin")
    os.makedirs(output_dir, exist_ok=True)
    try:
        print("[DEBUG] Fetching user story from JIRA...")
        user_story = fetch_jira_user_story()
        user_story_path = os.path.join("github_code", "user_story.txt")
        print(f"[DEBUG] Writing user story to {user_story_path}")
        with open(user_story_path, "w", encoding="utf-8") as f:
            f.write(user_story)
        print(f"[DEBUG] User story written to {user_story_path}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch or write user story: {e}")
        return False
    # Use this file for Gherkin generation
    try:
        title, criteria_text = extract_title_and_criteria(user_story, config["steps"]["step1_parse_gherkin"].get("acceptance_criteria_sections"))
        if not criteria_text:
            print("[ERROR] No acceptance criteria found in JIRA user story.")
            logger.error("No acceptance criteria found in JIRA user story.")
            return False
        # Prepare user story text for OpenAI
        user_story_for_ai = f"Title: {title}\nAcceptance Criteria:\n{criteria_text}"
        server_params = StdioServerParameters(
            command="python",
            args=["server.py"]
        )
        print(f"[DEBUG] Calling generate_gherkin with user story title: {title}")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("generate_gherkin", {"user_story": user_story_for_ai})
                if hasattr(result, 'content') and result.content:
                    gherkin_text = result.content[0].text
                elif isinstance(result, str):
                    gherkin_text = result
                else:
                    print(f"[ERROR] Unexpected result from MCP server: {type(result)}")
                    logger.error("Unexpected result from MCP server: %s", type(result))
                    return False
                # Strip markdown code fences if present
                gherkin_text = strip_markdown_code_fence(gherkin_text)
    except Exception as e:
        print(f"[ERROR] Failed to generate Gherkin: {e}")
        logger.error(f"Failed to generate Gherkin via MCP: {e}")
        return False
    # Sanitize title for filename
    file_title = re.sub(r'[^a-zA-Z0-9]+', '_', title.strip().lower())
    feature_path = os.path.join(output_dir, f"{file_title}.feature")
    try:
        print(f"[DEBUG] Writing Gherkin feature to {feature_path}")
        with open(feature_path, "w", encoding="utf-8") as f:
            f.write(gherkin_text)
        print(f"[DEBUG] Gherkin feature written to {feature_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write Gherkin feature: {e}")
        logger.error(f"Failed to write Gherkin feature: {e}")
        return False
    logger.info(f"Generated Gherkin feature: {feature_path}")
    return True

def step1_generate_gherkin(config: Dict[str, Any], output_dir: str = "gherkin") -> bool:
    load_dotenv()
    return asyncio.run(step1_generate_gherkin_async(config, output_dir))

if __name__ == "__main__":
    import json
    import argparse
    load_dotenv()
    parser = argparse.ArgumentParser(description="Step 1: Generate Gherkin from JIRA user story")
    parser.add_argument("--config", default="pipeline.config.json", help="Path to pipeline config file")
    parser.add_argument("--output-dir", default="gherkin", help="Output directory for Gherkin feature")
    args = parser.parse_args()
    with open(args.config, "r") as f:
        config = json.load(f)
    step1_generate_gherkin(config, output_dir=args.output_dir) 