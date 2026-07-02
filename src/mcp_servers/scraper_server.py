import os
import json
import requests
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("ReseAIrch-Scraper")

def load_cookies():
    """Loads session cookies from cookies.json for bypassing gated content."""
    cookies_path = os.path.join(os.getcwd(), "cookies.json")
    if os.path.exists(cookies_path):
        try:
            with open(cookies_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load cookies: {e}")
    return []

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

@mcp.tool()
async def scrape_url(url: str, method: str = "playwright") -> str:
    """
    Scrapes the given URL and extracts clean text/markdown.
    Supports bypassing captchas and paywalls using injected cookies and stealth headers.
    
    Args:
        url: The website to scrape.
        method: "playwright" (default, handles JS/captchas), "firecrawl" (premium markdown), or "bs4" (fast static).
    """
    if method == "firecrawl":
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            return "Error: FIRECRAWL_API_KEY not set. Fallback to playwright or bs4."
        
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {"url": url, "pageOptions": {"headers": get_headers()}}
            response = requests.post("https://api.firecrawl.dev/v1/scrape", headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json().get("data", {}).get("markdown", "")
        except Exception as e:
            return f"Firecrawl scraping failed: {str(e)}"

    elif method == "bs4":
        try:
            session = requests.Session()
            session.headers.update(get_headers())
            
            # Inject cookies
            for cookie in load_cookies():
                session.cookies.set(cookie.get('name'), cookie.get('value'), domain=cookie.get('domain'))
                
            response = session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # Basic cleanup
            for script in soup(["script", "style"]):
                script.extract()
            return soup.get_text(separator='\n', strip=True)
        except Exception as e:
            return f"BS4 scraping failed: {str(e)}"

    else:
        # Default to Playwright (best for Captcha bypass and dynamic JS)
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                # Context with custom headers and cookies
                context = await browser.new_context(
                    user_agent=get_headers()["User-Agent"],
                    viewport={'width': 1280, 'height': 720}
                )
                
                cookies = load_cookies()
                if cookies:
                    # Playwright expects url or domain in cookie dicts
                    await context.add_cookies(cookies)
                    
                page = await context.new_page()
                
                # Stealth plugins to evade bot detection
                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                await page.add_init_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]})")
                
                # Wait until network is mostly idle to bypass basic captchas/Cloudflare challenges
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Human-like macros (random mouse movements and scrolling) to bypass recaptcha
                import random
                for _ in range(3):
                    x = random.randint(100, 800)
                    y = random.randint(100, 800)
                    await page.mouse.move(x, y, steps=10)
                    await page.mouse.wheel(0, random.randint(100, 500))
                    await page.wait_for_timeout(random.randint(500, 1500))
                
                # Auto-solve basic Cloudflare Turnstile / Captcha clicks
                try:
                    cf_iframe = await page.query_selector("iframe[src*='cloudflare']")
                    if cf_iframe:
                        box = await cf_iframe.bounding_box()
                        if box:
                            await page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                            await page.wait_for_timeout(5000)
                except Exception:
                    pass

                # Take screenshot for debugging/captcha solving pipeline
                os.makedirs(os.path.join(os.getcwd(), "workspace", "debug"), exist_ok=True)
                await page.screenshot(path=os.path.join(os.getcwd(), "workspace", "debug", "last_scrape.png"))
                
                content = await page.content()
                await browser.close()
                
                soup = BeautifulSoup(content, 'html.parser')
                for script in soup(["script", "style"]):
                    script.extract()
                return soup.get_text(separator='\n', strip=True)
                
        except Exception as e:
            return f"Playwright scraping failed: {str(e)}"

if __name__ == "__main__":
    # Runs the MCP server locally over stdio so agents can connect to it
    print("Starting ReseAIrch-Scraper MCP Server...", flush=True)
    mcp.run()
