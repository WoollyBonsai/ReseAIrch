import os
import asyncio
from playwright.async_api import async_playwright
import bs4

async def versatile_scrape(url: str, use_stealth: bool = True) -> str:
    """
    A versatile, highly adaptable web scraper that avoids common bot detections.
    Can be used standalone or imported by ADK Agents.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            ignore_https_errors=True
        )
        page = await context.new_page()
        
        # Simple stealth properties to bypass basic bot detectors
        if use_stealth:
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            await page.add_init_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]})")

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Human-like macros (random mouse movements and scrolling)
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
            
            # Take screenshot of captcha if needed for debugging
            os.makedirs(os.path.join(os.getcwd(), "workspace", "debug"), exist_ok=True)
            await page.screenshot(path=os.path.join(os.getcwd(), "workspace", "debug", "last_scrape.png"))
            
            html = await page.content()
            soup = bs4.BeautifulSoup(html, 'html.parser')
            
            # Remove scripts and styles for clean text extraction
            for element in soup(["script", "style", "nav", "footer", "iframe"]):
                element.extract()
                
            text = soup.get_text(separator='\n', strip=True)
            return text
        except Exception as e:
            return f"Error scraping {url}: {e}"
        finally:
            await browser.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print(asyncio.run(versatile_scrape(target)))
    else:
        print("Usage: python versatile_scraper.py <URL>")
