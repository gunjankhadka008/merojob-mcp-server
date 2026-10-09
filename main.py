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
    
    # Ultra-Generic Search: Look for ANY heading that contains a link
    headings = soup.find_all(['h1', 'h2', 'h3'])
    
    for heading in headings:
        link_elem = heading.find('a')
        # If the heading itself isn't a link, check its parent
        if not link_elem:
            parent_link = heading.find_parent('a')
            if parent_link:
                link_elem = parent_link
                
        if not link_elem or 'href' not in link_elem.attrs:
            continue
            
        href = link_elem['href']
        # MeroJob job URLs usually contain '/job/' or are relative paths
        if href == "#" or "javascript" in href:
            continue
            
        title = heading.text.strip()
        if not title:
            continue
            
        full_url = f"https://merojob.com{href}" if href.startswith('/') else href

        # Attempt to find the company name nearby
        parent_container = heading.find_parent(['div', 'li', 'article'])
        company = "Unknown Company"
        if parent_container:
            for tag in parent_container.find_all(['h2', 'h3', 'h4', 'span']):
                text = tag.text.strip()
                if text and text != title and len(text) > 2:
                    company = text
                    break

        # Prevent duplicates
        if not any(j['url'] == full_url for j in jobs):
            jobs.append({
                "title": title,
                "company": company,
                "url": full_url
            })
        
        if len(jobs) >= 15:
            break
            
    return {
        "keyword": q, 
        "total_found": len(jobs), 
        "debug_page_title": page_title, 
        "jobs": jobs
    }

@app.get("/api/details")
async def job_details(url: str, api_key: str = Depends(verify_api_key)):
    """Scrape the specific job description page using Playwright."""
    if "merojob.com" not in url:
        raise HTTPException(status_code=400, detail="Invalid MeroJob URL")
        
    html_content = ""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=15000)
            html_content = await page.content()
        except Exception as e:
            await browser.close()
            return {"error": str(e)}
            
        await browser.close()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    desc_div = soup.find('div', itemprop='description')
    if desc_div:
        text = desc_div.get_text(separator='\n', strip=True)
    else:
        card_body = soup.find('div', class_='card-body')
        text = card_body.get_text(separator='\n', strip=True) if card_body else "Description not found."
        
    return {"url": url, "full_description": text}