#!/usr/bin/env python3
"""
Quick Reverse Engineering - Fast analysis of Fustog API
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.reverse_engineer_api import APIReverseEngineer
from scripts.api_analyzer import APIAnalyzer

def main():
    print("Quick Reverse Engineering Tool\n")
    
    # Setup
    base_url = os.getenv("VITE_API_BASE_URL") or os.getenv("API_BASE_URL") or "https://api.fustog.app/api/v1"
    har_path = "fustoog/sandbox/samples/fustog_categories.har"
    
    print(f"Base URL: {base_url}")
    print(f"HAR File: {har_path}\n")
    
    # Create output directory
    os.makedirs("data", exist_ok=True)
    
    # Step 1: Reverse Engineer
    print("=" * 60)
    print("STEP 1: Reverse Engineering API Endpoints")
    print("=" * 60)
    
    engineer = APIReverseEngineer(base_url)
    
    if Path(har_path).exists():
        endpoints = engineer.analyze_har_file(har_path)
        engineer.endpoints.extend(endpoints)
        print(f"[OK] Analyzed HAR file: {len(endpoints)} endpoints found")
    else:
        print(f"[WARN] HAR file not found: {har_path}")
        print("   Run mitmproxy to capture traffic first")
    
    # Discover from code
    code_paths = [
        "hooks/useFustogApi.ts",
        "scripts/scrape_products_prices_compare.py"
    ]
    discovered = engineer.discover_endpoints_from_code(code_paths)
    engineer.endpoints.extend(discovered)
    
    # Remove duplicates
    seen = set()
    unique = []
    for ep in engineer.endpoints:
        key = (ep.method, ep.path)
        if key not in seen:
            seen.add(key)
            unique.append(ep)
    engineer.endpoints = unique
    
    print(f"\nTotal unique endpoints: {len(engineer.endpoints)}\n")
    
    # Step 2: Deep Analysis
    print("=" * 60)
    print("STEP 2: Deep API Analysis")
    print("=" * 60)
    
    if Path(har_path).exists():
        analyzer = APIAnalyzer()
        analyzer.load_har_file(har_path)
        analyzer.export_analysis_report()
    else:
        print("[WARN] Skipping deep analysis (no HAR file)")
    
    # Step 3: Generate Documentation
    print("\n" + "=" * 60)
    print("STEP 3: Generating Documentation")
    print("=" * 60)
    
    engineer.generate_documentation("data/api_documentation.md")
    engineer.export_openapi_spec("data/openapi.json")
    engineer.export_endpoints_json("data/endpoints.json")
    
    # Summary
    print("\n" + "=" * 60)
    print("[OK] REVERSE ENGINEERING COMPLETE!")
    print("=" * 60)
    print("\nGenerated files:")
    print("  - data/api_documentation.md")
    print("  - data/openapi.json")
    print("  - data/endpoints.json")
    if Path(har_path).exists():
        print("  - data/api_analysis_report.md")
    print("\nNext steps:")
    print("  1. Review api_documentation.md")
    print("  2. Use openapi.json with API testing tools")
    print("  3. Generate TypeScript types from schemas")
    print("  4. Capture more traffic to discover additional endpoints")

if __name__ == "__main__":
    main()
