from fastapi import FastAPI, Header, HTTPException, Depends
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# This is the line that was missing! It defines 'app'.
app = FastAPI(title="MeroJob MCP API")

VALID_API_KEYS = {
    "sk_test_12345": "PremiumUser"
}

def verify_api_key(x_api_key: str = Header(...)):
    """Middleware to validate the API key for every request."""
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or expired API Key.")
    return x_api_key

@app.get("/api/search")
async def search_jobs(q: str, api_key: str = Depends(verify_api_key)):
    """Scrape the MeroJob search page with anti-bot stealth and hard-waits."""
    formatted_query = q.replace(" ", "+")
    url = f"https://merojob.com/search/?q={formatted_query}"
    
    html_content = ""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--disable-infobars"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            java_script_enabled=True
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=20000)
            # HARD WAIT: Give the client-side React/Tailwind components 4 seconds to mount the job cards
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
        
    # Dump the raw visible text for Claude to read the job requirements
    main_content = soup.find('main') or soup.find('body')
    raw_text = main_content.get_text(separator='\n', strip=True) if main_content else ""
    
    # Dump all valid URLs so Claude has the links to pass to the get_job_description tool
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(separator=' ', strip=True)
        if not href.startswith(('javascript', 'mailto', 'tel')) and href != "#":
            full_url = f"https://merojob.com{href}" if href.startswith('/') else href
            # Filter out standard site navigation links
            if not any(nav in full_url.lower() for nav in ['/login', '/register', '/blog', '/about', '/contact', '/employer/']):
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
    if "merojob.com" not in url:
        raise HTTPException(status_code=400, detail="Invalid MeroJob URL")
        
    html_content = ""
    page_title = "Unknown"
    
    async with async_playwright() as p:
        # 1. Apply the exact same stealth arguments used in the search endpoint
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
    await browser.close()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Destroy all menus, scripts, icons, and styling tags to reduce noise
    for element in soup(["script", "style", "nav", "header", "footer", "aside", "svg", "button", "iframe"]):
        element.extract()

    # 2. Grab absolutely all remaining visible text from the page
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