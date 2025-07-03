"""
Researched: https://github.com/modelcontextprotocol/python-sdk, https://gofastmcp.com/clients
Implements step 0: Fetch code & user story via MCP GitHub integration (real MCP client).
"""
import os
import shutil
import logging
import asyncio
import zipfile
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from dotenv import load_dotenv
import json


def parse_github_branch_url(github_branch_url: str):
    # Example: https://github.com/user/repo/tree/branch
    import re
    m = re.match(r"https://github.com/([^/]+)/([^/]+)/tree/(.+)", github_branch_url)
    if not m:
        raise ValueError(f"Invalid github_branch URL: {github_branch_url}")
    user, repo, branch = m.groups()
    repo_url = f"https://github.com/{user}/{repo}.git"
    return repo_url, branch

def extract_zip_to_dir_flat(zip_bytes, output_dir):
    import io
    import os
    import shutil
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(output_dir)
    # Flatten if there's a single top-level folder
    entries = [e for e in os.listdir(output_dir) if not e.startswith('.')]
    if len(entries) == 1 and os.path.isdir(os.path.join(output_dir, entries[0])):
        top_dir = os.path.join(output_dir, entries[0])
        for item in os.listdir(top_dir):
            shutil.move(os.path.join(top_dir, item), output_dir)
        shutil.rmtree(top_dir)

def has_any_code_files(output_dir):
    # Recursively check for .js, .ts, .jsx, .tsx, .py files
    exts = ('.js', '.ts', '.jsx', '.tsx', '.py')
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith(exts):
                return True
    return False

async def fetch_code_and_user_story_async(config: Dict[str, Any], github_branch: str, output_dir: str = "github_code") -> bool:
    logger = logging.getLogger("step0_fetch_code")
    os.makedirs(output_dir, exist_ok=True)

    # Idempotency: check if README.md and at least one code file exist
    readme_path = Path(output_dir) / "README.md"
    if readme_path.exists() and has_any_code_files(output_dir):
        logger.info(f"Step 0 already completed: {output_dir} contains README.md and code files.")
        return True

    # Clean up output_dir if incomplete
    for item in Path(output_dir).iterdir():
        if item.is_file() or item.is_dir():
            if item.name != ".gitkeep":
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

    # Parse github_branch URL
    repo_url, branch = parse_github_branch_url(github_branch)

    # Use stdio transport to launch the MCP server as a subprocess
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )
    tool_args = {"repo_url": repo_url, "branch": branch}
    try:
        print("Connecting to MCP server via stdio...")
        print("Calling clone_repo with:", tool_args)
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("clone_repo", tool_args)
                # Expect base64-encoded zip string
                if hasattr(result, 'content') and result.content:
                    b64_zip = result.content[0].text
                elif isinstance(result, str):
                    b64_zip = result
                else:
                    logger.error("Unexpected result from MCP server: %s", type(result))
                    return False
                zip_bytes = base64.b64decode(b64_zip)
                extract_zip_to_dir_flat(zip_bytes, output_dir)
    except Exception as e:
        logger.error(f"Failed to fetch repo via MCP: {e}")
        return False

    # Confirm presence of README.md and code files
    readme_path = Path(output_dir) / "README.md"
    if not readme_path.exists():
        logger.error("README.md not found in repo.")
        return False
    if not has_any_code_files(output_dir):
        logger.error("No code files found in repo.")
        return False
    logger.info(f"Fetched code and user story to {output_dir}")
    return True

# Synchronous wrapper for CLI/main.py
def fetch_code_and_user_story(config: Dict[str, Any], github_branch: str, output_dir: str = "github_code") -> bool:
    load_dotenv()
    return asyncio.run(fetch_code_and_user_story_async(config, github_branch, output_dir))

if __name__ == "__main__":
    import argparse
    load_dotenv()
    parser = argparse.ArgumentParser(description="Step 0: Fetch code & user story from GitHub branch")
    parser.add_argument("--github-branch", required=False, help="GitHub branch URL to clone (e.g., https://github.com/user/repo/tree/branch)")
    parser.add_argument("--config", default="pipeline.config.json", help="Path to pipeline config file")
    parser.add_argument("--output-dir", default="github_code", help="Output directory for fetched code")
    args = parser.parse_args()
    github_branch = args.github_branch or os.getenv("GITHUB_BRANCH")
    if not github_branch:
        raise ValueError("You must provide --github-branch or set GITHUB_BRANCH in your .env file.")
    with open(args.config, "r") as f:
        config = json.load(f)
    ok = fetch_code_and_user_story(config, github_branch, output_dir=args.output_dir)
    if ok:
        print(f"[Step 0] Code and user story fetched in '{args.output_dir}'")
    else:
        print("[Step 0] Failed to fetch code and user story. See logs for details.") 