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
    tag_line = f' and {ticket_tag}' if ticket_tag else ''
    prompt = f"""
You are a Gherkin feature–writing assistant.  Given this user story / acceptance criteria:
{user_story}

Produce a single Gherkin `.feature` that meets these requirements:

1. **Feature header**  
   - Tag it with `@AutoGen`{tag_line}.  
   - Include a one-sentence description under the `Feature:` line summarizing the goal.

2. **Background**  
   - If there is a common starting state (e.g. "the user is on the X page"), put it in a `Background:`.

3. **Scenario Outlines**  
   - Group similar cases into `Scenario Outline:` blocks with clear titles.  
   - Use `<placeholder>` syntax for any dynamic values (fields, inputs, expected messages).

4. **Examples tables**  
   - Provide an `Examples:` table for each outline, listing every combination of placeholder values.

5. **Step phrasing**  
   - Start every step with **"the user ..."** (e.g. `When the user fills in ...`, `Then the user sees ...`).  
   - For validations, use patterns like  
     - `Then the user should see an error message next to the <field> field`  
     - `Then the user should see the <field> input field`

6. **Completeness**  
   - Cover both positive (presence, valid input) and negative (missing/invalid input) flows.  
   - Don't leave any loose ends or TODOs—only valid, runnable Gherkin.

7. **Output**  
   - Return _only_ the `.feature` text—no explanations or extra commentary.

End your response with the complete Gherkin feature text.
"""
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.2,
        )
        gherkin_text = response.choices[0].message.content.strip()
        return gherkin_text
    except Exception as e:
        print("Error in generate_gherkin:", e)
        return f"# Error: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio") 