# MeroJob Model Context Protocol (MCP) Server

A Model Context Protocol (MCP) server that gives Claude Desktop automated job search and job description extraction for the MeroJob portal.

The service handles common scraping challenges in modern Single-Page Applications (SPAs), including client-side rendering, Cloudflare bot mitigation, and layout shifts caused by atomic CSS frameworks such as Tailwind CSS.

---

## Architectural Overview

The connector uses a decoupled two-tier architecture:

### 1. MCP Tool Interface (`proxy_mcp.py`)

- Implements the FastMCP specification to expose callable tools to Claude Desktop.
- Handles tool registration, input serialization, and error handling.
- Sends authenticated requests to the backend API using an `x-api-key` header, read from the `MEROJOB_API_KEY` environment variable.

### 2. Scraper Engine (`main.py`)

- Built with FastAPI and asynchronous Playwright.
- Configures browser properties, including a custom User-Agent and realistic viewport dimensions.
- Scrolls and waits so dynamically rendered React components can load before the page is read.
- Cleans markup with BeautifulSoup, removing non-semantic elements such as `script`, `style`, `nav`, and `footer`.
- Returns page text optimized for Large Language Model (LLM) processing.
- Requires a valid API key on every request and only accepts `merojob.com` URLs (see Security).

### Network and IP Considerations

MeroJob may apply IP reputation filtering and automated traffic protection. Requests from cloud data center IP ranges can hit HTTP 403 errors.

This project is designed to run locally on the loopback address (`127.0.0.1`), so browser traffic uses your machine's own network connection. This may reduce some network-related restrictions, but it does not guarantee that automated requests will get past the site's anti-bot protections.

---

## Tool Capabilities

### `search_merojob(keyword: str)`

- Searches MeroJob for job listings matching a keyword.
- Waits for dynamically rendered job cards to load.
- Extracts absolute URLs for discovered listings.
- Returns page text and discovered links for further analysis.

### `get_job_description(job_url: str)`

- Opens a specific MeroJob job listing.
- Removes navigation and boilerplate markup.
- Extracts requirements, responsibilities, qualifications, and application details.
- Returns the extracted text for analysis.

---

## System Requirements

- Python 3.10 or higher
- Claude Desktop
- Git
- Supported operating systems: macOS, Linux, Windows Subsystem for Linux (WSL)

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/gunjankhadka008/merojob-mcp-server.git
cd merojob-mcp-server
```

### 2. Create a Virtual Environment

**macOS / Linux / WSL**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Generate Your API Key

The backend will not start without an API key. Generate a long random one:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Keep this value private. Never commit it to git or paste it into source files.

### 5. Configure Claude Desktop

#### Locate the Configuration File

**macOS**

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows**

```text
%APPDATA%\Claude\claude_desktop_config.json
```

#### Add the MCP Server Configuration

Add this entry inside the `mcpServers` object. Replace the placeholder paths with the absolute paths to your project, and paste in your API key:

```json
{
  "mcpServers": {
    "merojob-pro": {
      "command": "/ABSOLUTE/PATH/TO/merojob-mcp-server/venv/bin/python",
      "args": [
        "/ABSOLUTE/PATH/TO/merojob-mcp-server/proxy_mcp.py"
      ],
      "env": {
        "MEROJOB_API_KEY": "paste-your-generated-key-here"
      }
    }
  }
}
```

The name `merojob-pro` is just the configuration label. You can change it.

Completely quit Claude Desktop and relaunch it after saving. On macOS, use `Cmd + Q`.

### 6. Run the Backend API Server

In a terminal in the project directory, activate the virtual environment, set the same key, and start the backend:

**macOS / Linux / WSL**

```bash
source venv/bin/activate
export MEROJOB_API_KEY="paste-your-generated-key-here"
uvicorn main:app --host 127.0.0.1 --port 8000
```

**Windows (PowerShell)**

```powershell
venv\Scripts\activate
$env:MEROJOB_API_KEY="paste-your-generated-key-here"
uvicorn main:app --host 127.0.0.1 --port 8000
```

The key must be identical in the backend terminal and in the Claude Desktop config. If `MEROJOB_API_KEY` is not set, the backend refuses to start. Keep this terminal running while using the tools.

### 7. Use the Tools in Claude Desktop

Once the backend is running and Claude Desktop has loaded the config, try prompts like:

**Search for jobs**
> Search MeroJob for Data Analyst openings using the merojob-pro tool.

**Extract a job description**
> Retrieve the job requirements from this MeroJob listing: [paste the job listing URL] and summarize the responsibilities, qualifications, and required skills.

**Evaluate a job opportunity**
> Search MeroJob for entry-level Data Engineer positions and compare the requirements of relevant listings with my qualifications.

---

## Security

- **Authentication:** every API request needs a valid `x-api-key` header. The key comes from the `MEROJOB_API_KEY` environment variable and is compared in constant time. No keys are stored in the code.
- **URL validation:** `/api/details` only accepts `http`/`https` URLs whose host is exactly `merojob.com` or a subdomain of it. This prevents the backend from being used to open arbitrary or internal addresses (SSRF).
- **Run locally:** bind the backend to `127.0.0.1` as shown above. Do not expose it on a public port or bind it to `0.0.0.0` unless you understand the risks. A headless browser behind a public endpoint is a powerful tool for attackers.
- **Secrets:** never commit your API key or a `.env` file. `.env` is listed in `.gitignore`.

---

## Project Structure

```text
merojob-mcp-server/
├── proxy_mcp.py       # MCP tool interface for Claude Desktop
├── main.py            # FastAPI backend and Playwright scraper
├── requirements.txt   # Python dependencies
├── Dockerfile         # Container build (see Security before deploying publicly)
├── .gitignore         # Excludes venv/, __pycache__/, .env
└── README.md          # Project documentation
```

---

## Troubleshooting

### Claude Desktop Does Not Detect the MCP Server

- Verify that `claude_desktop_config.json` contains valid JSON.
- Check that the Python interpreter and `proxy_mcp.py` paths are correct and absolute.
- Confirm the dependencies are installed in the configured virtual environment.
- Completely quit and relaunch Claude Desktop.
- Inspect Claude Desktop's logs for MCP startup errors.

### The Backend Will Not Start

- If you see `MEROJOB_API_KEY environment variable is not set`, export the key in the same terminal before running `uvicorn`.

### Requests Return HTTP 401

- The key in `claude_desktop_config.json` does not match the key the backend was started with. Make sure both use the same value, then restart both.

### Requests Return HTTP 400

- The URL was rejected. Only `merojob.com` listing URLs are allowed.

### The Backend Returns HTTP 403 Errors

- Confirm that MeroJob is accessible in your normal browser.
- Check whether the website is blocking automated requests.
- Verify your network connection.
- Respect the site's access restrictions and avoid excessive request rates.

### Job Listings Are Missing or Incomplete

- Confirm the backend is running on `127.0.0.1:8000`.
- The page may need more loading time or extra browser interactions.
- Inspect the scraper's extraction logic if MeroJob changed its page structure.
- Review the backend logs for Playwright timeouts or parsing errors.

---

## License and Compliance

This project is intended for personal research, educational analysis, and workflow automation.

Respect MeroJob's terms of service, applicable laws, robots.txt guidance where relevant, rate limits, and restrictions on automated access. Avoid excessive requests and do not attempt to circumvent access controls or security protections.

---

## Contributing

Contributions, bug reports, and suggestions for improving the scraper, MCP integration, and extraction reliability are welcome.

When proposing changes, please include a clear description of the issue, the expected behavior, and steps to reproduce it.

---

## Author

**Gunjan Khadka**

GitHub: [@gunjankhadka008](https://github.com/gunjankhadka008)