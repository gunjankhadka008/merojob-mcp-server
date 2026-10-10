import os
import secrets
from urllib.parse import urlparse, quote

from fastapi import FastAPI, Header, HTTPException, Depends
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

app = FastAPI(title="MeroJob MCP API")

API_KEY = os.environ.get("MEROJOB_API_KEY")
if not API_KEY:
    raise RuntimeError("MEROJOB_API_KEY environment variable is not set")


def verify_api_key(x_api_key: str = Header(...)):
    """Validate the API key for every request (constant-time comparison)."""
    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or expired API Key.")
    return x_api_key


def validate_merojob_url(url: str):
    """Only allow http(s) URLs whose host is merojob.com or a subdomain (SSRF protection)."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid URL protocol")
    if host != "merojob.com" and not host.endswith(".merojob.com"):
        raise HTTPException(status_code=400, detail="Invalid MeroJob URL")


@app.get("/api/search")
async def search_jobs(q: str, api_key: str = Depends(verify_api_key)):
    """Scrape MeroJob search by establishing a trusted session first."""
    html_content = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--disable-infobars"]
        )
        # Spoof a Mac/Chrome user agent for better trust scores
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            java_script_enabled=True
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page = await context.new_page()
        try:
            # STEP 1: Visit the homepage to establish a human session and clear Cloudflare
            await page.goto("https://merojob.com", wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(2000)

            # STEP 2: Navigate to the search page using our trusted session
            formatted_query = quote(q, safe="")
            url = f"https://merojob.com/search/?q={formatted_query}"
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)

            # STEP 3: Scroll down physically to trigger the lazy-loading AJAX requests
            await page.evaluate("window.scrollBy(0, 600)")
            await page.wait_for_timeout(2000)
            await page.evaluate("window.scrollBy(0, 600)")

            # Final wait for the network to paint the job cards to the DOM
            await page.wait_for_timeout(4000)

            html_content = await page.content()
        except Exception as e:
            await browser.close()
            return {"error": str(e)}

        await browser.close()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Strip garbage tags
    for element in soup(["script", "style", "svg", "img", "nav", "header", "footer"]):
        element.extract()

    main_content = soup.find('main') or soup.find('body')
    raw_text = main_content.get_text(separator='\n', strip=True) if main_content else ""

    links = []
    garbage_links = ['/login', '/register', '/blog', '/about', '/contact', '/search', '/faq', '/privacy', '/terms']

    for a in soup.find_all('a', href=True):
        href = a.get('href')
        if not href:
            continue

        text = a.get_text(separator=' ', strip=True)

        if not href.startswith(('javascript', 'mailto', 'tel')) and href != "#":
            full_url = f"https://merojob.com{href}" if href.startswith('/') else href

            # Strip out known navigation links to leave only job slugs
            if not any(nav in full_url.lower() for nav in garbage_links) and full_url != "https://merojob.com/":
                if {"link_text": text, "url": full_url} not in links:
                    links.append({"link_text": text, "url": full_url})

    return {
        "keyword": q,
        "raw_page_text": raw_text[:8000],
        "extracted_links": links
    }


@app.get("/api/details")
async def job_details(url: str, api_key: str = Depends(verify_api_key)):
    """Scrape the specific job description page with full anti-bot stealth."""
    validate_merojob_url(url)

    html_content = ""
    page_title = "Unknown"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            java_script_enabled=True
        )

        # Erase the webdriver flag
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=20000)
            html_content = await page.content()
            page_title = await page.title()
        except Exception as e:
            await browser.close()
            return {"error": f"Browser failed: {str(e)}"}

        await browser.close()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Destroy all menus, scripts, icons, and styling tags to reduce noise
    for element in soup(["script", "style", "nav", "header", "footer", "aside", "svg", "button", "iframe"]):
        element.extract()

    # Grab absolutely all remaining visible text from the page
    main_content = soup.find('main') or soup.find('body')

    if main_content:
        # Join all text with newlines so Claude can read it clearly
        text = main_content.get_text(separator='\n', strip=True)
    else:
        text = f"FAILED. The browser saw this page title: '{page_title}'"

    return {
        "url": url,
        "page_title": page_title,
        "full_description": text
    }