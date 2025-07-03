import json
import pytest
from pytest_httpserver import HTTPServer
from pathlib import Path

@pytest.fixture(autouse=True)
def mock_api(httpserver: HTTPServer, request):
    # 1) Load endpoints.json
    endpoints_path = Path(__file__).parent.parent / 'config' / 'endpoints.json'
    with open(endpoints_path) as f:
        endpoints = json.load(f)

    # 2) Register each endpoint on the HTTPServer
    for name, info in endpoints.items():
        method = info['method'].upper()
        path   = info['path']
        status = info.get('mockStatus', 200)
        body   = info.get('mockResponse', {})

        httpserver.expect_request(path, method=method) \
                  .respond_with_json(body, status=status)

    # 3) Start server & expose its base URL
    httpserver.start()
    # Make the base URL available in tests
    pytest.mock_base_url = httpserver.url_for('/')
    yield
    httpserver.stop() 