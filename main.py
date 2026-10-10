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
    """Scrape the MeroJob search page with anti-bot stealth."""
    formatted_query = q.replace(" ", "+")
    url = f"https://merojob.com/search/?q={formatted_query}"
    
    html_content = ""
    page_title = "Unknown"
    
    async with async_playwright() as p:
        # Launch with arguments that disable standard bot-detection flags
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
        
        # Erase the webdriver flag that gives away it's a bot
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        
        page = await context.new_page()
        
        try:
            # Wait longer for the network to settle in case of security redirects
            await page.goto(url, wait_until="networkidle", timeout=20000)
            
            # Wait specifically for the job container or at least 5 seconds
            try:
                await page.wait_for_selector("div.card, h1, h2", timeout=5000)
            except:
                pass # If it times out, we still try to scrape what we have
                
            html_content = await page.content()
            page_title = await page.title()
        except Exception as e:
            await browser.close()
            return {"error": f"Browser failed: {str(e)}"}
            
        await browser.close()

    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []
    
    # Strip out headers, footers, and navs to avoid grabbing menu links
    for element in soup(["nav", "header", "footer", "aside"]):
        element.extract()
        
    # Grab ALL links on the page
    links = soup.find_all('a', href=True)
    
    for a in links:
        href = a['href']
        title = a.get_text(separator=' ', strip=True)
        
        # Ignore empty links, javascript, hash links, or basic site navigation
        if not title or href in ["#", "/"] or "javascript" in href or "login" in href.lower() or "register" in href.lower():
            continue
            
        full_url = f"https://merojob.com{href}" if href.startswith('/') else href
        
        # Prevent duplicates
        if not any(j['url'] == full_url for j in jobs):
            jobs.append({
                "title": title,
                "company": "See URL for details", # We rely on Claude to read the title/URL context
                "url": full_url
            })
            
    return {
        "keyword": q, 
        "total_found": len(jobs), 
        "debug_page_title": page_title, 
        # Cap at 30 to avoid overwhelming Claude's context window
        "jobs": jobs[:30] 
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