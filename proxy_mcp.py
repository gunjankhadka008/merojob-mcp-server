import os
import json
import requests
from fastmcp import FastMCP

# Backend URL and API key come from environment variables (never hardcode secrets)
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.environ["MEROJOB_API_KEY"]

# The backend drives a real browser, so allow generous time before giving up
REQUEST_TIMEOUT = 90

mcp = FastMCP("MeroJob-Pro")


@mcp.tool()
def search_merojob(keyword: str) -> str:
    """Search MeroJob for job postings based on a keyword. Returns job URLs."""
    try:
        res = requests.get(
            f"{API_BASE_URL}/api/search",
            params={"q": keyword},
            headers={"x-api-key": API_KEY},
            timeout=REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        return res.text
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_job_description(job_url: str) -> str:
    """Provide a MeroJob URL to read the full job description and requirements."""
    try:
        res = requests.get(
            f"{API_BASE_URL}/api/details",
            params={"url": job_url},
            headers={"x-api-key": API_KEY},
            timeout=REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        return res.text
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()