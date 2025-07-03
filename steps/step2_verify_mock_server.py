import json
import requests
import logging
from pathlib import Path
from pytest_httpserver import HTTPServer
from typing import Dict, Any

def verify_mock_server_config(config: Dict[str, Any], endpoints_path: str = "config/endpoints.json") -> bool:
    """
    Verify that the mock server configuration is working correctly by:
    1. Loading endpoints.json
    2. Starting a mock server
    3. Registering all endpoints
    4. Testing each endpoint with HTTP requests
    5. Asserting correct responses
    
    Returns True if all endpoints work correctly, False otherwise.
    """
    logger = logging.getLogger("step2_verify_mock_server")
    
    # Check if endpoints.json exists
    if not Path(endpoints_path).exists():
        logger.error(f"Endpoints file not found: {endpoints_path}")
        return False
    
    try:
        # 1) Load your endpoints spec
        with open(endpoints_path) as f:
            endpoints = json.load(f)
        
        if not endpoints:
            logger.warning("No endpoints found in endpoints.json")
            return True  # Empty config is valid
        
        logger.info(f"Loaded {len(endpoints)} endpoints from {endpoints_path}")
        
        # 2) Start the mock server on a random free port
        with HTTPServer(port=0) as httpserver:
            # 3) Register every endpoint from your JSON
            for name, info in endpoints.items():
                method = info["method"].upper()
                path = info["path"]
                status = info.get("mockStatus", 200)
                body = info.get("mockResponse", {})
                
                httpserver.expect_request(path, method=method) \
                          .respond_with_json(body, status=status)
                
                logger.debug(f"Registered endpoint: {method} {path} -> {status}")

            base_url = httpserver.url_for("")  # e.g. "http://127.0.0.1:45678/"
            logger.info(f"Mock server started at: {base_url}")

            # 4) Exercise each endpoint and assert the mock responses
            all_ok = True
            for name, info in endpoints.items():
                method = info["method"].upper()
                path = info["path"]
                expected_status = info.get("mockStatus", 200)
                expected_body = info.get("mockResponse", {})

                url = base_url.rstrip("/") + path
                
                try:
                    resp = requests.request(method, url, timeout=5)
                    
                    # Assert status code
                    if resp.status_code != expected_status:
                        logger.error(f"{name}: expected status {expected_status}, got {resp.status_code}")
                        all_ok = False
                        continue
                    
                    # Assert JSON body (if response is JSON)
                    try:
                        actual_body = resp.json()
                        if actual_body != expected_body:
                            logger.error(f"{name}: expected body {expected_body}, got {actual_body}")
                            all_ok = False
                            continue
                    except json.JSONDecodeError:
                        # If response is not JSON, check if expected body is empty
                        if expected_body and resp.text.strip():
                            logger.error(f"{name}: expected JSON body {expected_body}, got non-JSON response")
                            all_ok = False
                            continue
                    
                    logger.info(f"[OK]   {method} {path}")
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"{name}: Request failed - {e}")
                    all_ok = False

            if not all_ok:
                logger.error("🚨 Mock-server verification failed!")
                return False
            
            logger.info("✅ All mock endpoints are responding correctly.")
            return True
            
    except Exception as e:
        logger.error(f"Mock server verification failed with exception: {e}")
        return False

def main():
    """CLI entry point for testing mock server configuration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify mock server configuration")
    parser.add_argument("--endpoints", default="config/endpoints.json", 
                       help="Path to endpoints.json file")
    parser.add_argument("--config", default="pipeline.config.json", 
                       help="Path to pipeline config file")
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
    
    # Run verification
    success = verify_mock_server_config(config, args.endpoints)
    
    if success:
        print("✅ Mock server configuration verification passed!")
        exit(0)
    else:
        print("❌ Mock server configuration verification failed!")
        exit(1)

if __name__ == "__main__":
    main() 