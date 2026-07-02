import os
import asyncio
import hashlib
from src.mcp_servers.scraper_server import scrape_url
from src.mcp_servers.memory_server import store_document

class HarvesterAgent:
    """
    ADK Harvester Agent.
    Specialized in iterating over the Planner's DAG, dispatching commands to the Scraping Server,
    and pushing results to Memory, while saving raw data dumps.
    """
    def __init__(self):
        self.mcp_scraper = "ReseAIrch-Scraper"
        os.makedirs(os.path.join(os.getcwd(), "workspace", "raw"), exist_ok=True)

    def _sanitize_filename(self, url: str) -> str:
        safe_name = "".join(c if c.isalnum() else "_" for c in url)
        # truncate and append hash to avoid path length issues
        hash_suffix = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{safe_name[:50]}_{hash_suffix}.txt"

    async def execute_task(self, task: dict, collection_name: str):
        query = task.get("query", "")
        
        # If the planner generated a search term instead of a URL, format it as a duckduckgo search
        url = query if query.startswith("http") else f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        
        print(f"Harvester Agent fetching: {url}")
        
        # Execute actual scrape
        try:
            result = await scrape_url(url, method="playwright")
            
            if result and len(result) > 50:
                # Save Raw Unprocessed Data
                raw_filename = self._sanitize_filename(url)
                raw_filepath = os.path.join(os.getcwd(), "workspace", "raw", raw_filename)
                with open(raw_filepath, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"Raw data saved to {raw_filepath}")

                # Store in Memory
                store_document(collection_name=collection_name, content=result, source_url=url)
                return True
        except Exception as e:
            print(f"Scrape failed for {url}: {e}")
            
        return False

    async def run_dag(self, dag: dict, collection_name: str):
        tasks = dag.get("tasks", [])
        print(f"Harvester starting batch processing of {len(tasks)} tasks...")
        
        for task in tasks:
            success = await self.execute_task(task, collection_name)
            if not success:
                print(f"Task failed, retrying later: {task.get('id')}")
            await asyncio.sleep(2) # Polite delay
                
        print("Harvester run complete.")
