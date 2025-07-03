import os
import sys
import json
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv
import subprocess

from src.steps.step0_fetch_code import fetch_code_and_user_story
from src.steps.step1_generate_gherkin import step1_generate_gherkin
from src.steps.step2_generate_tests_with_ai import step2_generate_tests_with_ai


def load_config(config_path: str):
    with open(config_path, "r") as f:
        return json.load(f)

def setup_logging(log_config: dict):
    logging.basicConfig(
        level=getattr(logging, log_config.get("level", "INFO")),
        format=log_config.get("format", "%(asctime)s - %(levelname)s - %(message)s"),
        filename=log_config.get("file", None)
    )

def run_babel_instrumentation(input_dir, output_dir, plugin_path):
    env = os.environ.copy()
    env["PATH"] = "/Users/dhruv/.nvm/versions/node/v18.20.8/bin:" + env["PATH"]
    config_path = "./babel.config.cjs"
    cmd = [
        "/Users/dhruv/.nvm/versions/node/v18.20.8/bin/npx", "babel", input_dir,
        "--out-dir", output_dir,
        "--plugins", plugin_path,
        "--copy-files",
        "--config-file", config_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd="/Users/dhruv/Desktop/TechSur-Internship/latest_userStory4")
    if result.returncode != 0:
        print("Babel instrumentation failed:", result.stderr)
        raise RuntimeError("Babel instrumentation failed")
    print("Babel instrumentation complete:", result.stdout)

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Automated Test-Generation Pipeline")
    parser.add_argument("--github-branch", default=os.getenv("GITHUB_BRANCH"), help="GitHub branch URL to clone (e.g., https://github.com/user/repo/tree/branch)")
    parser.add_argument("--config", default="pipeline.config.json", help="Path to pipeline config file")
    args = parser.parse_args()

    config = load_config(args.config)
    setup_logging(config.get("logging", {}))

    # Override config with .env if present
    config["github"]["mcp_server_url"] = os.getenv("MCP_GITHUB_SERVER", config["github"].get("mcp_server_url"))
    config["github"]["auth_token"] = os.getenv("GITHUB_TOKEN", config["github"].get("auth_token"))

    # Step 0: Fetch code & user story
    step0_cfg = config["steps"]["step0_fetch_code"]
    if step0_cfg["enabled"]:
        print("[Step 0] Fetching code and user story...")
        ok = fetch_code_and_user_story(
            config,
            args.github_branch,
            output_dir=step0_cfg["output_dir"]
        )
        if not ok:
            print("[Step 0] Failed to fetch code and user story. See logs for details.")
            sys.exit(1)
        print(f"[Step 0] Code and user story fetched in '{step0_cfg['output_dir']}'")
    else:
        print("[Step 0] Skipped (disabled in config)")

    # Step 0.1: Inject data-testid attributes using jscodeshift
    print("[Step 0.1] Injecting data-testid attributes using jscodeshift...")
    result = subprocess.run([
        'jscodeshift',
        '-t', 'inject-data-testid.cjs',
        step0_cfg["output_dir"],
        '--parser=tsx'
    ], capture_output=True, text=True)
    if result.returncode != 0:
        print("[Step 0.1] jscodeshift injection failed:", result.stderr)
        sys.exit(1)
    print("[Step 0.1] jscodeshift injection complete:", result.stdout)

    # Step 1: Generate Gherkin feature from user story
    step1_cfg = config["steps"]["step1_parse_gherkin"]
    if step1_cfg["enabled"]:
        readme_path = os.path.join(step0_cfg["output_dir"], "README.md")
        print("[Step 1] Generating Gherkin feature from user story...")
        ok = step1_generate_gherkin(config, readme_path, output_dir=step1_cfg["output_dir"])
        if not ok:
            print("[Step 1] Failed to generate Gherkin feature. See logs for details.")
            sys.exit(1)
        print(f"[Step 1] Gherkin feature generated in '{step1_cfg['output_dir']}'")
        # Generate common_steps.py from feature files
        print("[Step 1b] Generating common_steps.py from feature files...")
        subprocess.run([sys.executable, 'scripts/overwrite_common_steps.py'], check=True)
        print("[Step 1b] common_steps.py generated.")
    else:
        print("[Step 1] Skipped (disabled in config)")

    # Step 2: Generate test files from Gherkin
    step2_cfg = config["steps"]["step2_generate_tests"]
    if step2_cfg["enabled"]:
        print("[Step 2] Generating test files from Gherkin feature(s) with AI...")
        step2_generate_tests_with_ai(config, feature_dir=step1_cfg["output_dir"], output_dir=step2_cfg["output_dir"])
        # Post-process generated test files to fix imports and scenario paths
        print("[Step 2b] Fixing generated test files (import pytest, scenario paths)...")
        subprocess.run([sys.executable, 'scripts/fix_generated_tests.py'], check=True)
        print("[Step 2b] Test files fixed.")
    else:
        print("[Step 2] Skipped (disabled in config)")

if __name__ == "__main__":
    main() 