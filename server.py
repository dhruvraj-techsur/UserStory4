from mcp.server.fastmcp import FastMCP
import git
import shutil
import tempfile
import zipfile
import os
import io
import base64
import openai
from dotenv import load_dotenv
import re

mcp = FastMCP("Local GitHub MCP Server")

@mcp.tool()
def clone_repo(repo_url: str, branch: str = "main", pr_number: str = None, timeout: int = 300) -> str:
    """Clone a GitHub repo (optionally a PR) and return as base64-encoded zip string."""
    print("clone_repo called with:", repo_url, branch, pr_number)
    tmpdir = tempfile.mkdtemp()
    try:
        try:
            if pr_number:
                # For PR, fetch the PR branch
                pr_ref = f"pull/{pr_number}/head:pr_{pr_number}"
                repo = git.Repo.clone_from(repo_url, tmpdir)
                repo.git.fetch("origin", pr_ref)
                repo.git.checkout(f"pr_{pr_number}")
            else:
                repo = git.Repo.clone_from(repo_url, tmpdir, branch=branch)
            # Zip the contents
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(tmpdir):
                    for file in files:
                        abs_path = os.path.join(root, file)
                        rel_path = os.path.relpath(abs_path, tmpdir)
                        zf.write(abs_path, rel_path)
            # Return as base64 string
            return base64.b64encode(zip_buf.getvalue()).decode("utf-8")
        except Exception as e:
            print("Error in clone_repo:", e)
            raise
    finally:
        shutil.rmtree(tmpdir)

@mcp.tool()
def generate_gherkin(user_story: str) -> str:
    """Generate BDD Gherkin scenarios from user story text using OpenAI API."""
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # Try to extract ticket ID from user_story (e.g., PROJ-123)
    ticket_match = re.search(r'([A-Z][A-Z0-9]+-\d+)', user_story)
    ticket_tag = f'@{ticket_match.group(1)}' if ticket_match else ''
    prompt = f"""
Convert the following acceptance criteria or user story into a single Gherkin feature that:

  1. Uses a **Background** section for any common setup.
  2. **Groups similar test cases** into a **Scenario Outline** rather than separate Scenarios.
  3. Provides an **Examples** table to parameterize inputs and expected results.
  4. Adds a feature-level tag like `@AutoGen`{f' and {ticket_tag}' if ticket_tag else ''}.
  5. Outputs only valid, runnable Gherkin text.

Here's the user story / acceptance criteria:
{user_story}
"""
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.2,
        )
        gherkin_text = response.choices[0].message.content.strip()
        return gherkin_text
    except Exception as e:
        print("Error in generate_gherkin:", e)
        return f"# Error: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio") 