#!/usr/bin/env python3
"""
Reverse Engineering Toolkit for Fustog API
Comprehensive tool for analyzing, documenting, and understanding API endpoints
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pathlib import Path
import httpx
from dotenv import load_dotenv
import pandas as pd
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, parse_qs

load_dotenv()


@dataclass
class Endpoint:
    """Represents an API endpoint"""
    method: str
    path: str
    base_url: str
    description: str = ""
    parameters: Dict[str, Any] = None
    request_headers: Dict[str, str] = None
    request_body: Any = None
    response_schema: Dict[str, Any] = None
    response_example: Any = None
    auth_required: bool = False
    auth_type: str = ""
    status_codes: List[int] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.request_headers is None:
            self.request_headers = {}
        if self.status_codes is None:
            self.status_codes = []


@dataclass
class APISchema:
    """Complete API schema documentation"""
    base_url: str
    endpoints: List[Endpoint]
    authentication: Dict[str, Any] = None
    common_headers: Dict[str, str] = None
    rate_limits: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.authentication is None:
            self.authentication = {}
        if self.common_headers is None:
            self.common_headers = {}
        if self.rate_limits is None:
            self.rate_limits = {}


class APIReverseEngineer:
    """Main reverse engineering class"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("FUSTOG_API_KEY")
        self.endpoints: List[Endpoint] = []
        self.discovered_paths: Set[str] = set()
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "Fustog-API-Reverse-Engineer/1.0"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.Client(
            headers=headers,
            timeout=30.0,
            follow_redirects=True
        )
    
    def analyze_har_file(self, har_path: str) -> List[Endpoint]:
        """Analyze HAR file to extract API endpoints"""
        print(f"Analyzing HAR file: {har_path}")
        
        with open(har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        endpoints = []
        entries = har_data.get('log', {}).get('entries', [])
        
        for entry in entries:
            req = entry.get('request', {})
            res = entry.get('response', {})
            
            url = req.get('url', '')
            method = req.get('method', 'GET')
            
            # Only analyze API endpoints
            if self.base_url not in url:
                continue
            
            path = url.replace(self.base_url, '')
            parsed = urlparse(url)
            
            # Extract parameters
            params = {}
            if parsed.query:
                params = parse_qs(parsed.query)
                params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
            
            # Extract headers
            headers = {}
            for h in req.get('headers', []):
                headers[h.get('name', '').lower()] = h.get('value', '')
            
            # Extract request body
            body = None
            post_data = req.get('postData', {})
            if post_data.get('text'):
                try:
                    body = json.loads(post_data['text'])
                except:
                    body = post_data['text']
            
            # Extract response
            response_data = None
            response_text = res.get('content', {}).get('text', '')
            if response_text:
                try:
                    response_data = json.loads(response_text)
                except:
                    response_data = response_text
            
            # Detect authentication
            auth_required = False
            auth_type = ""
            if 'authorization' in headers:
                auth_required = True
                if headers['authorization'].startswith('Bearer'):
                    auth_type = "Bearer Token"
                elif headers['authorization'].startswith('Basic'):
                    auth_type = "Basic Auth"
            
            endpoint = Endpoint(
                method=method,
                path=path,
                base_url=self.base_url,
                parameters=params,
                request_headers=headers,
                request_body=body,
                response_example=response_data,
                auth_required=auth_required,
                auth_type=auth_type,
                status_codes=[res.get('status', 0)]
            )
            
            endpoints.append(endpoint)
            self.discovered_paths.add(path)
        
        print(f"[OK] Found {len(endpoints)} API calls in HAR file")
        return endpoints
    
    def discover_endpoints_from_code(self, code_paths: List[str]) -> List[Endpoint]:
        """Discover API endpoints from codebase"""
        print(f"Scanning codebase for API endpoints...")
        
        endpoints = []
        api_patterns = [
            r'["\']([^"\']*api[^"\']*\/[^"\']+)["\']',  # String literals
            r'fetch\(["\']([^"\']+)["\']',  # Fetch calls
            r'\.get\(["\']([^"\']+)["\']',  # HTTP client get
            r'\.post\(["\']([^"\']+)["\']',  # HTTP client post
            r'api\.get_json\(["\']([^"\']+)["\']',  # Custom API client
        ]
        
        for code_path in code_paths:
            if not os.path.exists(code_path):
                continue
            
            with open(code_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern in api_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    url = match.group(1)
                    if self.base_url in url or url.startswith('/'):
                        path = url.replace(self.base_url, '') if self.base_url in url else url
                        if path not in self.discovered_paths:
                            endpoint = Endpoint(
                                method="GET",  # Default, could be improved
                                path=path,
                                base_url=self.base_url,
                                description=f"Discovered from {code_path}"
                            )
                            endpoints.append(endpoint)
                            self.discovered_paths.add(path)
        
        print(f"[OK] Discovered {len(endpoints)} endpoints from codebase")
        return endpoints
    
    def probe_endpoint(self, endpoint: Endpoint) -> Endpoint:
        """Probe an endpoint to gather more information"""
        url = f"{self.base_url}{endpoint.path}"
        
        try:
            # Try GET first
            if endpoint.method == "GET" or not endpoint.method:
                response = self.client.get(url, params=endpoint.parameters)
            else:
                response = self.client.request(
                    endpoint.method,
                    url,
                    params=endpoint.parameters,
                    json=endpoint.request_body
                )
            
            # Update status codes
            if response.status_code not in endpoint.status_codes:
                endpoint.status_codes.append(response.status_code)
            
            # Extract response schema
            try:
                data = response.json()
                endpoint.response_example = data
                endpoint.response_schema = self._infer_schema(data)
            except:
                endpoint.response_example = response.text[:500]
            
            # Extract response headers
            endpoint.request_headers.update(dict(response.headers))
            
        except Exception as e:
            print(f"[WARN] Error probing {endpoint.path}: {e}")
        
        return endpoint
    
    def _infer_schema(self, data: Any, depth: int = 0) -> Dict[str, Any]:
        """Infer JSON schema from data"""
        if depth > 5:  # Prevent infinite recursion
            return {"type": "object"}
        
        if isinstance(data, dict):
            schema = {"type": "object", "properties": {}}
            for key, value in data.items():
                schema["properties"][key] = self._infer_schema(value, depth + 1)
            return schema
        elif isinstance(data, list):
            if data:
                return {"type": "array", "items": self._infer_schema(data[0], depth + 1)}
            return {"type": "array"}
        elif isinstance(data, str):
            return {"type": "string"}
        elif isinstance(data, int):
            return {"type": "integer"}
        elif isinstance(data, float):
            return {"type": "number"}
        elif isinstance(data, bool):
            return {"type": "boolean"}
        elif data is None:
            return {"type": "null"}
        else:
            return {"type": "unknown"}
    
    def generate_documentation(self, output_path: str = "api_documentation.md"):
        """Generate Markdown documentation"""
        print(f"Generating API documentation...")
        
        doc = f"""# Fustog API Documentation

> Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> Base URL: `{self.base_url}`

## Overview

This documentation was automatically generated by reverse engineering the Fustog API.

## Endpoints

"""
        
        # Group by path prefix
        grouped = {}
        for endpoint in self.endpoints:
            prefix = endpoint.path.split('/')[1] if '/' in endpoint.path[1:] else 'root'
            if prefix not in grouped:
                grouped[prefix] = []
            grouped[prefix].append(endpoint)
        
        for prefix, endpoints in sorted(grouped.items()):
            doc += f"\n### {prefix.upper()}\n\n"
            
            for endpoint in endpoints:
                doc += f"#### `{endpoint.method} {endpoint.path}`\n\n"
                
                if endpoint.description:
                    doc += f"{endpoint.description}\n\n"
                
                if endpoint.parameters:
                    doc += "**Parameters:**\n\n"
                    for param, value in endpoint.parameters.items():
                        doc += f"- `{param}`: {type(value).__name__}\n"
                    doc += "\n"
                
                if endpoint.auth_required:
                    doc += f"**Authentication:** {endpoint.auth_type}\n\n"
                
                if endpoint.response_schema:
                    doc += "**Response Schema:**\n\n"
                    doc += f"```json\n{json.dumps(endpoint.response_schema, indent=2)}\n```\n\n"
                
                if endpoint.response_example:
                    doc += "**Example Response:**\n\n"
                    example_str = json.dumps(endpoint.response_example, indent=2)
                    if len(example_str) > 1000:
                        example_str = example_str[:1000] + "\n... (truncated)"
                    doc += f"```json\n{example_str}\n```\n\n"
                
                doc += "---\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(doc)
        
        print(f"[OK] Documentation saved to {output_path}")
    
    def export_openapi_spec(self, output_path: str = "openapi.json"):
        """Export OpenAPI 3.0 specification"""
        print(f"Generating OpenAPI specification...")
        
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Fustog API",
                "version": "1.0.0",
                "description": "Reverse engineered Fustog API specification"
            },
            "servers": [{"url": self.base_url}],
            "paths": {}
        }
        
        for endpoint in self.endpoints:
            path_item = spec["paths"].setdefault(endpoint.path, {})
            
            operation = {
                "summary": endpoint.description or f"{endpoint.method} {endpoint.path}",
                "responses": {}
            }
            
            # Add parameters
            if endpoint.parameters:
                operation["parameters"] = [
                    {
                        "name": name,
                        "in": "query",
                        "schema": {"type": "string"}
                    }
                    for name in endpoint.parameters.keys()
                ]
            
            # Add request body
            if endpoint.request_body:
                operation["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": endpoint.response_schema or {}
                        }
                    }
                }
            
            # Add responses
            for status in endpoint.status_codes:
                operation["responses"][str(status)] = {
                    "description": f"Status {status}",
                    "content": {
                        "application/json": {
                            "schema": endpoint.response_schema or {}
                        }
                    }
                }
            
            path_item[endpoint.method.lower()] = operation
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2)
        
        print(f"[OK] OpenAPI spec saved to {output_path}")
    
    def export_endpoints_json(self, output_path: str = "endpoints.json"):
        """Export endpoints as JSON"""
        data = {
            "base_url": self.base_url,
            "generated_at": datetime.now().isoformat(),
            "endpoints": [asdict(e) for e in self.endpoints]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"[OK] Endpoints exported to {output_path}")


def main():
    """Main entry point"""
    base_url = os.getenv("VITE_API_BASE_URL") or os.getenv("API_BASE_URL") or "https://api.fustog.app/api/v1"
    
    print("Fustog API Reverse Engineering Toolkit")
    print(f"Base URL: {base_url}\n")
    
    engineer = APIReverseEngineer(base_url)
    
    # Analyze HAR file
    har_path = "fustoog/sandbox/samples/fustog_categories.har"
    if os.path.exists(har_path):
        endpoints = engineer.analyze_har_file(har_path)
        engineer.endpoints.extend(endpoints)
    
    # Discover from codebase
    code_paths = [
        "hooks/useFustogApi.ts",
        "scripts/scrape_products_prices_compare.py",
        "fustoog/api/relay/server.ts"
    ]
    discovered = engineer.discover_endpoints_from_code(code_paths)
    engineer.endpoints.extend(discovered)
    
    # Remove duplicates
    seen = set()
    unique_endpoints = []
    for ep in engineer.endpoints:
        key = (ep.method, ep.path)
        if key not in seen:
            seen.add(key)
            unique_endpoints.append(ep)
    engineer.endpoints = unique_endpoints
    
    print(f"\nTotal unique endpoints: {len(engineer.endpoints)}\n")
    
    # Generate outputs
    os.makedirs("data", exist_ok=True)
    engineer.generate_documentation("data/api_documentation.md")
    engineer.export_openapi_spec("data/openapi.json")
    engineer.export_endpoints_json("data/endpoints.json")
    
    print("\n[OK] Reverse engineering complete!")
    print("\nGenerated files:")
    print("  - data/api_documentation.md")
    print("  - data/openapi.json")
    print("  - data/endpoints.json")


if __name__ == "__main__":
    main()
