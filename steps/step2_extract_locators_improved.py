import os
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any

def run_locator_extraction(config: Dict[str, Any], code_dir: str = "github_code", output_dir: str = "config") -> bool:
    """
    Run the improved locator extraction using the Node.js script.
    This will extract all id and data-testid attributes from JSX/TSX files.
    """
    logger = logging.getLogger("step2_extract_locators_improved")
    
    # Check if Node.js dependencies are available
    try:
        # Check if required Node.js packages are installed
        result = subprocess.run(['npm', 'list', '@babel/parser', '@babel/traverse', 'glob'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode != 0:
            logger.info("Installing required Node.js dependencies...")
            install_result = subprocess.run(['npm', 'install', '@babel/parser', '@babel/traverse', 'glob'], 
                                          capture_output=True, text=True, cwd=os.getcwd())
            if install_result.returncode != 0:
                logger.error(f"Failed to install Node.js dependencies: {install_result.stderr}")
                return False
    except FileNotFoundError:
        logger.error("Node.js/npm not found. Please install Node.js to use the improved locator extraction.")
        return False
    
    # Ensure scripts directory exists
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    # Check if the extraction script exists
    extraction_script = scripts_dir / "extract-locators.cjs"
    if not extraction_script.exists():
        logger.error(f"Locator extraction script not found: {extraction_script}")
        return False
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    try:
        logger.info("Running improved locator extraction...")
        
        # Run the Node.js extraction script
        result = subprocess.run(['node', str(extraction_script)], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode != 0:
            logger.error(f"Locator extraction failed: {result.stderr}")
            return False
        
        logger.info("Locator extraction output:")
        logger.info(result.stdout)
        
        # Verify the output file was created
        locators_file = output_path / "locators.json"
        if not locators_file.exists():
            logger.error(f"Locators file not created: {locators_file}")
            return False
        
        # Load and validate the generated locators
        with open(locators_file, 'r') as f:
            locators = json.load(f)
        
        logger.info(f"Successfully extracted {len(locators)} locators")
        
        # Log the extracted locators for debugging
        for key, info in locators.items():
            logger.debug(f"  {key}: {info['selector']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Locator extraction failed with exception: {e}")
        return False

def validate_locators_with_gherkin(locators_path: str = "config/locators.json", gherkin_dir: str = "gherkin") -> bool:
    """
    Validate that all field names used in Gherkin scenarios have corresponding locators.
    """
    logger = logging.getLogger("validate_locators_with_gherkin")
    
    # Load locators
    if not Path(locators_path).exists():
        logger.error(f"Locators file not found: {locators_path}")
        return False
    
    with open(locators_path, 'r') as f:
        locators = json.load(f)
    
    # Find all feature files
    gherkin_path = Path(gherkin_dir)
    if not gherkin_path.exists():
        logger.warning(f"Gherkin directory not found: {gherkin_dir}")
        return True
    
    feature_files = list(gherkin_path.glob("*.feature"))
    if not feature_files:
        logger.warning(f"No feature files found in {gherkin_dir}")
        return True
    
    all_valid = True
    
    for feature_file in feature_files:
        logger.info(f"Validating locators for {feature_file.name}")
        
        with open(feature_file, 'r') as f:
            content = f.read()
        
        # Extract field names from Examples tables
        import re
        examples_matches = re.findall(r'Examples:\s*\n(.*?)(?=\n\s*\n|\Z)', content, re.DOTALL)
        
        for examples_block in examples_matches:
            # Parse the Examples table to find field names
            lines = examples_block.strip().split('\n')
            if len(lines) >= 2:  # Header + at least one data row
                header_line = lines[0].strip()
                field_names = [field.strip() for field in header_line.split('|')[1:-1]]  # Remove empty first/last
                
                for field_name in field_names:
                    normalized_key = field_name.lower().replace(' ', '-')
                    if normalized_key not in locators:
                        logger.warning(f"Missing locator for field '{field_name}' (normalized: '{normalized_key}') in {feature_file.name}")
                        all_valid = False
                    else:
                        logger.debug(f"✓ Found locator for field '{field_name}': {locators[normalized_key]['selector']}")
    
    if all_valid:
        logger.info("✅ All Gherkin field names have corresponding locators")
    else:
        logger.warning("⚠️  Some Gherkin field names are missing locators")
    
    return all_valid

def main():
    """CLI entry point for improved locator extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract locators using improved AST-based extraction")
    parser.add_argument("--code-dir", default="github_code", help="Directory containing source code")
    parser.add_argument("--output-dir", default="config", help="Output directory for locators.json")
    parser.add_argument("--config", default="pipeline.config.json", help="Path to pipeline config file")
    parser.add_argument("--validate-gherkin", action="store_true", help="Validate locators against Gherkin files")
    args = parser.parse_args()
    
    # Load config
    try:
        with open(args.config, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run extraction
    success = run_locator_extraction(config, args.code_dir, args.output_dir)
    
    if success and args.validate_gherkin:
        logger = logging.getLogger("main")
        logger.info("Validating locators against Gherkin files...")
        validate_locators_with_gherkin(f"{args.output_dir}/locators.json")
    
    if success:
        print("✅ Improved locator extraction completed successfully!")
        exit(0)
    else:
        print("❌ Improved locator extraction failed!")
        exit(1)

if __name__ == "__main__":
    main() 