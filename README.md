# MeroJob Model Context Protocol (MCP) Server

A Model Context Protocol (MCP) server providing Claude Desktop with automated job search and description extraction capabilities for the MeroJob portal.

The service resolves data extraction challenges common to modern Single-Page Applications (SPAs), specifically client-side rendering (CSR), Cloudflare bot mitigation, and layout shifts from atomic CSS frameworks such as Tailwind CSS.

---

## Architectural Overview

The connector employs a decoupled two-tier architecture:

1. **MCP Tool Interface (`proxy_mcp.py`):**
   * Implements the FastMCP specification to expose callable tools directly to Claude Desktop.
   * Handles local tool registration, input serialization, and error handling.
   * Dispatches authenticated requests with an `x-api-key` header to the backend API.

2. **Scraper Engine (`main.py`):**
   * Built on FastAPI and asynchronous Playwright.
   * Emulates a legitimate browser fingerprint (`navigator.webdriver` masking, custom User-Agent, realistic viewport dimensions).
   * Executes synthetic interactions (e.g., scroll triggers and execution delays) to allow dynamic React components to mount before DOM serialization.
   * Cleans markup via BeautifulSoup, stripping non-semantic tags (`script`, `style`, `nav`, `footer`) and returning raw unstructured body text optimized for Large Language Model (LLM) parsing.

### Network and IP Considerations

MeroJob applies strict IP reputation filtering. Cloud data center IP ranges (such as AWS, Google Cloud, and Render) frequently encounter automated 403 blocks during asynchronous API fetch cycles. This deployment operates locally via loopback (`127.0.0.1`), leveraging residential IP routing to bypass automated anti-scraping filters without requiring commercial proxy rotation.

---

## Tool Capabilities

* `search_merojob(keyword: str)`: Queries active listings for a target keyword, waits for client-side card population, extracts absolute URLs, and delivers trimmed raw text alongside discovered links.
* `get_job_description(job_url: str)`: Traverses a specific job listing page, purges boilerplate navigational chrome, and extracts comprehensive requirements, responsibilities, and application metadata.

---

## System Requirements

* Python 3.10 or higher
* Claude Desktop
* Supported Operating Systems: macOS, Linux, Windows Subsystem for Linux (WSL)

---

## Installation and Setup

### 1. Repository Configuration

Clone the repository and enter the project directory:

```bash
git clone [https://github.com/gunjankhadka08/merojob-api.git](https://github.com/gunjankhadka08/merojob-api.git)
cd merojob-api

### 2. Environment Initialization

Create and activate an isolated Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
(On Windows: venv\Scripts\activate)

### 3. Dependency Installation

Install required Python packages and headless Chromium binaries:

```bash
pip install -r requirements.txt
playwright install chromium

### Claude Desktop Configuration
Configure Claude Desktop to recognize the MCP server:
1. Locate the configuration file:

macOS: ~/Library/Application Support/Claude/claude_desktop_config.json

Windows: %APPDATA%\Claude\claude_desktop_config.json

2. Add the merojob-pro entry inside mcpServers, replacing the placeholder paths with your absolute local directory paths:

JSON

{
  "mcpServers": 
  {
    "merojob-pro": 
    {
      "command": "/ABSOLUTE/PATH/TO/merojob-api/venv/bin/python",
      "args": [
        "/ABSOLUTE/PATH/TO/merojob-api/proxy_mcp.py"
      ]
    }
  }
}
#Completely quit and relaunch Claude Desktop (Command + Q on macOS).

### 4. Execution
1. Start the API Server
Run the backend scraper service locally:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000

2. Querying via Claude
Once the server is running, invoke the tool within Claude Desktop prompts:

"Search MeroJob for <Specify the Job Role> openings using the merojob-pro tool."

"Retrieve the job requirements from https://merojob.com/ and evaluate them against my qualifications."

### 5. License and Compliance
This implementation is intended for personal research, educational analysis, and workflow automation. Automated requests should respect platform stability, rate limits, and service terms.

### How to apply and save it in VS Code:
1. In your `README.md` tab, find the lines for Step 1:
   ````markdown
   ### 1. Repository Configuration

   Clone the repository and enter the project directory:

   ```bash
   git clone https://github.com/gunjankhadka08/merojob-api.git
   cd merojob-api

2. Place your cursor right on the blank line underneath ```` ``` ````.
3. Paste the text block above.
4. Press **`Cmd + S`** to save.