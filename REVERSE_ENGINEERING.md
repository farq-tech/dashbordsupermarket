# Reverse Engineering Toolkit

This toolkit helps you reverse engineer and analyze the Fustog API.

## Tools Available

### 1. **API Reverse Engineer** (`scripts/reverse_engineer_api.py`)

Comprehensive tool for analyzing and documenting API endpoints.

**Features:**
- Analyze HAR files to extract API calls
- Discover endpoints from codebase
- Probe endpoints to gather information
- Generate Markdown documentation
- Export OpenAPI 3.0 specification
- Export endpoints as JSON

**Usage:**
```bash
python scripts/reverse_engineer_api.py
```

**Outputs:**
- `data/api_documentation.md` - Full API documentation
- `data/openapi.json` - OpenAPI 3.0 spec
- `data/endpoints.json` - Raw endpoint data

### 2. **API Analyzer** (`scripts/api_analyzer.py`)

Deep analysis of API responses for patterns and insights.

**Features:**
- Analyze response structures
- Find common field patterns
- Generate JSON schemas
- Calculate statistics (response times, status codes)
- Identify data types

**Usage:**
```bash
python scripts/api_analyzer.py
```

**Outputs:**
- `data/api_analysis_report.md` - Analysis report

### 3. **HTTP Interceptor** (Already set up)

Use mitmproxy to capture live API traffic:

```bash
# Windows
.\fustoog\sandbox\ingest\run_mitmproxy.ps1

# Or manually
mitmproxy -s fustoog/sandbox/ingest/send_to_ingest.py
```

### 4. **HAR File Viewer** (`fustoog/frontend/intercept/app.ts`)

View and analyze captured HAR files in a web interface.

## Workflow

### Step 1: Capture Traffic

1. **Using mitmproxy:**
   ```bash
   cd fustoog/sandbox/ingest
   .\run_mitmproxy.ps1
   ```

2. **Configure your browser/app** to use mitmproxy as proxy (usually `localhost:8080`)

3. **Use the app** - all HTTP traffic will be captured

4. **Export HAR file** from mitmproxy or browser DevTools

### Step 2: Analyze

```bash
# Run reverse engineering
python scripts/reverse_engineer_api.py

# Run deep analysis
python scripts/api_analyzer.py
```

### Step 3: Review Results

- Check `data/api_documentation.md` for full API docs
- Review `data/api_analysis_report.md` for insights
- Use `data/openapi.json` with API testing tools (Postman, Insomnia)

## What You Can Discover

### API Endpoints
- All available endpoints
- HTTP methods (GET, POST, etc.)
- Required parameters
- Query parameters
- Request/response formats

### Authentication
- Auth mechanisms (Bearer tokens, API keys, etc.)
- Required headers
- Token formats

### Data Structures
- Request body schemas
- Response schemas
- Field types and patterns
- Nested object structures

### API Patterns
- Common field names
- Response formats
- Error handling
- Rate limiting

## Advanced Usage

### Custom Analysis

```python
from scripts.reverse_engineer_api import APIReverseEngineer

engineer = APIReverseEngineer("https://api.fustog.app/api/v1")

# Analyze specific HAR file
endpoints = engineer.analyze_har_file("path/to/file.har")

# Probe specific endpoint
endpoint = engineer.probe_endpoint(endpoints[0])

# Generate documentation
engineer.generate_documentation("custom_docs.md")
```

### Batch Processing

```bash
# Process multiple HAR files
for har in har_files/*.har; do
    python scripts/reverse_engineer_api.py --har "$har"
done
```

## Tips

1. **Capture comprehensive traffic** - Use the app thoroughly to capture all endpoints
2. **Save multiple HAR files** - Different sessions may reveal different endpoints
3. **Check codebase** - The reverse engineer also scans your code for API calls
4. **Compare results** - Run analysis multiple times as you discover more endpoints
5. **Validate findings** - Use the generated OpenAPI spec to test endpoints

## Output Files

All outputs are saved in the `data/` directory:

- `api_documentation.md` - Human-readable API docs
- `openapi.json` - Machine-readable API spec
- `endpoints.json` - Raw endpoint data
- `api_analysis_report.md` - Analysis insights

## Next Steps

1. **Document your findings** - Update API documentation
2. **Create TypeScript types** - Generate types from discovered schemas
3. **Build API client** - Use OpenAPI spec to generate client code
4. **Test endpoints** - Use generated specs with testing tools
5. **Monitor changes** - Re-run analysis periodically to detect API changes
