import json
import argparse

MSW_IMPORT = "import { rest } from 'msw';\n\n"
HANDLER_TEMPLATE = "rest.{method_lower}('{path}', (req, res, ctx) => res(ctx.status(200), ctx.json({ message: 'Mocked response' })))"


def main():
    parser = argparse.ArgumentParser(description="Generate MSW handlers.js from endpoints.json.")
    parser.add_argument('--endpoints', default='endpoints.json', help='Input endpoints.json file')
    parser.add_argument('--output', default='handlers.js', help='Output handlers.js file')
    args = parser.parse_args()

    with open(args.endpoints, 'r', encoding='utf-8') as f:
        endpoints = json.load(f)

    handlers = []
    for ep in endpoints:
        method = ep.get('method', 'GET').upper()
        path = ep.get('path', '/')
        # MSW supports get, post, put, delete, patch, options, head
        method_lower = method.lower() if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head'] else 'get'
        handlers.append(HANDLER_TEMPLATE.format(method_lower=method_lower, path=path))

    js = MSW_IMPORT
    js += "export const handlers = [\n  " + ",\n  ".join(handlers) + "\n];\n"

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(js)
    print(f"Generated {len(handlers)} MSW handlers in {args.output}")

if __name__ == "__main__":
    main() 