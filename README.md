# MeroJob Model Context Protocol (MCP) Server

A Model Context Protocol (MCP) server providing Claude Desktop with automated job search and job description extraction capabilities for the MeroJob portal.

The service addresses common data extraction challenges in modern Single-Page Applications (SPAs), including client-side rendering (CSR), Cloudflare bot mitigation, and layout shifts caused by atomic CSS frameworks such as Tailwind CSS.

---

## Architectural Overview

The connector employs a decoupled two-tier architecture:

### 1. MCP Tool Interface (`proxy_mcp.py`)

- Implements the FastMCP specification to expose callable tools directly to Claude Desktop.
- Handles local tool registration, input serialization, and error handling.
- Dispatches authenticated requests to the backend API using an `x-api-key` header.

### 2. Scraper Engine (`main.py`)

- Built using FastAPI and asynchronous Playwright.
- Configures browser properties, including a custom User-Agent and realistic viewport dimensions.
- Executes browser interactions, such as scrolling and execution delays, to allow dynamically rendered React components to load before DOM serialization.
- Cleans markup using BeautifulSoup, removing non-semantic elements such as `script`, `style`, `nav`, and `footer`.
- Returns extracted page text optimized for Large Language Model (LLM) processing.

### Network and IP Considerations

MeroJob may apply IP reputation filtering and automated traffic protection. Requests originating from cloud data center IP ranges can encounter HTTP 403 errors during page loading or API requests.

This project is designed to run locally using the loopback address (`127.0.0.1`), allowing browser traffic to use the machine's configured network connection. Local execution may reduce some network-related restrictions, but it does not guarantee that automated requests will bypass the platform's anti-bot protections.

---

## Tool Capabilities

### `search_merojob(keyword: str)`

- Searches MeroJob for job listings matching a specified keyword.
- Waits for dynamically rendered job cards to populate.
- Extracts absolute URLs for discovered job listings.
- Returns relevant page text and discovered links for further analysis.

### `get_job_description(job_url: str)`

- Opens a specific MeroJob job listing.
- Removes unnecessary navigational content and boilerplate markup.
- Extracts job requirements, responsibilities, qualifications, and available application details.
- Returns the extracted information for analysis.

---

## System Requirements

- Python 3.10 or higher
- Claude Desktop
- Git
- Supported operating systems:
  - macOS
  - Linux
  - Windows Subsystem for Linux (WSL)

---

## Installation and Setup

### 1. Clone the Repository

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/gunjankhadka08/merojob-mcp-server.git
cd merojob-mcp-server
```

### 2. Create a Virtual Environment

Create and activate an isolated Python virtual environment.

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

Install the required Python packages and Playwright's Chromium browser:

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configure Claude Desktop

Configure Claude Desktop to recognize the MCP server.

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

Add the following entry inside the `mcpServers` object in `claude_desktop_config.json`. Replace the placeholder paths with the absolute paths to your local project directory.

```json
{
  "mcpServers": {
    "merojob-pro": {
      "command": "/ABSOLUTE/PATH/TO/merojob-mcp-server/venv/bin/python",
      "args": [
        "/ABSOLUTE/PATH/TO/merojob-mcp-server/proxy_mcp.py"
      ]
    }
  }
}
```

**Important:** The `merojob-pro` value is the MCP server's configuration name. You can change it if desired, but it does not need to match the repository name.

Completely quit Claude Desktop and relaunch it after saving the configuration. On macOS, use `Cmd + Q` to quit the application.

### 5. Run the Backend API Server

Open a terminal in the project directory, activate the virtual environment, and start the FastAPI backend:

```bash
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000
```

Keep this terminal running while using the MCP tools.

If the backend requires an API key, ensure that the key is configured consistently between the backend and MCP client. The configuration above assumes that the MCP client can communicate with the local backend using the expected authentication mechanism.

### 6. Use the MCP Tools in Claude Desktop

Once the backend is running and Claude Desktop has loaded the MCP configuration, try prompts such as:

**Search for jobs**

> Search MeroJob for Data Analyst openings using the merojob-pro tool.

**Extract a job description**

> Retrieve the job requirements from this MeroJob listing: [paste the job listing URL] and summarize the responsibilities, qualifications, and required skills.

**Evaluate a job opportunity**

> Search MeroJob for entry-level Data Engineer positions and compare the requirements of relevant listings with my qualifications.

---

## Project Structure

```text
merojob-mcp-server/
├── proxy_mcp.py       # MCP tool interface for Claude Desktop
├── main.py            # FastAPI backend and Playwright scraper
├── requirements.txt   # Python dependencies
├── venv/              # Local virtual environment (not committed)
└── README.md          # Project documentation
```

---

## Troubleshooting

### Claude Desktop Does Not Detect the MCP Server

- Verify that `claude_desktop_config.json` contains valid JSON.
- Check that the Python interpreter and `proxy_mcp.py` paths are correct.
- Confirm that the required dependencies are installed in the configured virtual environment.
- Completely quit and relaunch Claude Desktop.
- Inspect Claude Desktop's logs for MCP startup errors.

### The Backend Returns HTTP 403 Errors

- Confirm that MeroJob is accessible through your browser.
- Check whether the website is blocking automated requests.
- Verify that the browser session and network connection are working correctly.
- Respect the website's access restrictions and avoid excessive request rates.

### Job Listings Are Missing or Incomplete

- Confirm that the backend is running and accessible on `127.0.0.1:8000`.
- Check whether the page requires additional loading time or browser interactions.
- Inspect the scraper's selectors and extraction logic if MeroJob has changed its page structure.
- Review the backend logs for Playwright timeouts or parsing errors.

---

## License and Compliance

This project is intended for personal research, educational analysis, and workflow automation.

Users should respect MeroJob's terms of service, applicable laws, robots.txt guidance where relevant, rate limits, and restrictions on automated access. Avoid excessive requests and do not attempt to circumvent access controls or security protections.

---

## Contributing

Contributions, bug reports, and suggestions for improving the scraper, MCP integration, and extraction reliability are welcome.

When proposing changes, please include a clear description of the issue, the expected behavior, and steps to reproduce it.

---

## Author

**Gunjan Khadka**

GitHub: [@gunjankhadka08](https://github.com/gunjankhadka08)