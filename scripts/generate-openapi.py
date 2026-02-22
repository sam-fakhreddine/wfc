#!/usr/bin/env python3
"""
Generate OpenAPI specification from FastAPI app.

Usage:
    uv run python scripts/generate-openapi.py > openapi.json
    uv run python scripts/generate-openapi.py --yaml > openapi.yaml
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from wfc.servers.rest_api.main import app  # noqa: E402


def main():
    """Generate and print OpenAPI spec."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate OpenAPI specification")
    parser.add_argument("--yaml", action="store_true", help="Output YAML instead of JSON")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)", default=None)
    args = parser.parse_args()

    openapi_schema = app.openapi()

    openapi_schema["info"]["x-logo"] = {
        "url": "https://wfc.example.com/logo.png",
        "altText": "WFC Logo",
    }

    openapi_schema["servers"] = [
        {
            "url": "https://api.wfc.example.com",
            "description": "Production",
        },
        {
            "url": "http://localhost:9950",
            "description": "Development",
        },
        {
            "url": "http://localhost:9951",
            "description": "Test",
        },
    ]

    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key",
            "description": "API key authentication. Include API key in Authorization header as 'Bearer <key>'",
        },
        "ProjectID": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Project-ID",
            "description": "Project identifier header required for all authenticated requests",
        },
    }

    if args.yaml:
        try:
            import yaml

            output = yaml.dump(openapi_schema, default_flow_style=False, sort_keys=False)
        except ImportError:
            print(
                "Error: PyYAML not installed. Install with: uv pip install pyyaml", file=sys.stderr
            )
            sys.exit(1)
    else:
        output = json.dumps(openapi_schema, indent=2)

    if args.output:
        Path(args.output).write_text(output)
        print(f"OpenAPI specification written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
