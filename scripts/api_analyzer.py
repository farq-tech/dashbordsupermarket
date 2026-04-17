#!/usr/bin/env python3
"""
API Analyzer - Deep analysis of API responses and patterns
"""

import json
import sys
from typing import Dict, List, Any, Set
from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd


class APIAnalyzer:
    """Analyze API responses for patterns, schemas, and insights"""
    
    def __init__(self):
        self.endpoints: List[Dict[str, Any]] = []
        self.field_patterns: Dict[str, Set[str]] = defaultdict(set)
        self.data_types: Dict[str, Counter] = defaultdict(Counter)
        self.status_codes: Counter = Counter()
        self.response_times: List[float] = []
    
    def load_har_file(self, har_path: str):
        """Load and parse HAR file"""
        with open(har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        entries = har_data.get('log', {}).get('entries', [])
        
        for entry in entries:
            req = entry.get('request', {})
            res = entry.get('response', {})
            
            url = req.get('url', '')
            method = req.get('method', 'GET')
            status = res.get('status', 0)
            timing = entry.get('timings', {})
            
            # Extract response body
            content = res.get('content', {})
            text = content.get('text', '')
            
            try:
                data = json.loads(text) if text else None
            except:
                data = None
            
            self.endpoints.append({
                'method': method,
                'url': url,
                'status': status,
                'data': data,
                'content_type': content.get('mimeType', ''),
                'size': content.get('size', 0),
                'time': timing.get('wait', 0)
            })
            
            self.status_codes[status] += 1
            if timing.get('wait'):
                self.response_times.append(timing['wait'])
            
            # Analyze response structure
            if data:
                self._analyze_structure(data, url)
    
    def _analyze_structure(self, data: Any, context: str = "", depth: int = 0):
        """Recursively analyze data structure"""
        if depth > 10:  # Prevent infinite recursion
            return
        
        if isinstance(data, dict):
            for key, value in data.items():
                field_path = f"{context}.{key}" if context else key
                self.field_patterns[field_path].add(str(type(value).__name__))
                self.data_types[field_path][type(value).__name__] += 1
                self._analyze_structure(value, field_path, depth + 1)
        elif isinstance(data, list):
            for i, item in enumerate(data[:10]):  # Limit to first 10 items
                self._analyze_structure(item, f"{context}[{i}]", depth + 1)
    
    def find_common_patterns(self) -> Dict[str, Any]:
        """Find common patterns across endpoints"""
        patterns = {
            'common_fields': {},
            'data_types': {},
            'status_distribution': dict(self.status_codes),
            'avg_response_time': sum(self.response_times) / len(self.response_times) if self.response_times else 0
        }
        
        # Find fields that appear in multiple endpoints
        field_counts = Counter()
        for field in self.field_patterns.keys():
            field_counts[field] += 1
        
        patterns['common_fields'] = {
            field: {
                'count': count,
                'types': list(self.field_patterns[field]),
                'most_common_type': self.data_types[field].most_common(1)[0][0] if self.data_types[field] else None
            }
            for field, count in field_counts.most_common(20)
        }
        
        return patterns
    
    def generate_schema(self, endpoint_url: str) -> Dict[str, Any]:
        """Generate JSON schema for a specific endpoint"""
        endpoint_data = [e for e in self.endpoints if endpoint_url in e['url']]
        
        if not endpoint_data:
            return {}
        
        # Use the first response as base
        sample = endpoint_data[0]['data']
        if not sample:
            return {}
        
        return self._generate_json_schema(sample)
    
    def _generate_json_schema(self, data: Any, required: bool = True) -> Dict[str, Any]:
        """Generate JSON schema from data"""
        if isinstance(data, dict):
            schema = {
                "type": "object",
                "properties": {},
                "required": [] if not required else []
            }
            
            for key, value in data.items():
                schema["properties"][key] = self._generate_json_schema(value, False)
                if required and value is not None:
                    schema["required"].append(key)
            
            return schema
        
        elif isinstance(data, list):
            if data:
                return {
                    "type": "array",
                    "items": self._generate_json_schema(data[0], False)
                }
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
    
    def export_analysis_report(self, output_path: str = "data/api_analysis_report.md"):
        """Export comprehensive analysis report"""
        patterns = self.find_common_patterns()
        
        report = f"""# API Analysis Report

## Summary

- **Total Endpoints Analyzed**: {len(self.endpoints)}
- **Unique URLs**: {len(set(e['url'] for e in self.endpoints))}
- **Status Codes**: {dict(self.status_codes)}
- **Average Response Time**: {patterns['avg_response_time']:.2f}ms

## Common Fields

"""
        
        for field, info in patterns['common_fields'].items():
            report += f"### `{field}`\n"
            report += f"- Appears in {info['count']} endpoints\n"
            report += f"- Types: {', '.join(info['types'])}\n"
            report += f"- Most common: {info['most_common_type']}\n\n"
        
        report += "\n## Endpoint Details\n\n"
        
        # Group by base path
        grouped = defaultdict(list)
        for ep in self.endpoints:
            url = ep['url']
            base = '/'.join(url.split('/')[:4])  # Rough grouping
            grouped[base].append(ep)
        
        for base, endpoints in grouped.items():
            report += f"### {base}\n\n"
            for ep in endpoints[:5]:  # Limit to 5 per group
                report += f"- **{ep['method']}** {ep['url']}\n"
                report += f"  - Status: {ep['status']}\n"
                report += f"  - Size: {ep['size']} bytes\n"
                report += f"  - Time: {ep['time']}ms\n\n"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"[OK] Analysis report saved to {output_path}")


def main():
    har_path = "fustoog/sandbox/samples/fustog_categories.har"
    
    if not Path(har_path).exists():
        print(f"❌ HAR file not found: {har_path}")
        sys.exit(1)
    
    analyzer = APIAnalyzer()
    analyzer.load_har_file(har_path)
    analyzer.export_analysis_report()


if __name__ == "__main__":
    main()
