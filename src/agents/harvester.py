import os
import asyncio
from src.mcp_servers.scraper_server import scrape_url
from src.mcp_servers.memory_server import store_document

class HarvesterAgent:
    """
    ADK Harvester Agent.
    Specialized in iterating over the Planner's DAG, dispatching commands to the Scraping Server,
    and pushing results to Memory.
    """
    def __init__(self):
        self.mcp_scraper = "ReseAIrch-Scraper"

    async def execute_task(self, task: dict, collection_name: str):
        query = task.get("query", "")
        
        # If the planner generated a search term instead of a URL, format it as a duckduckgo search
        url = query if query.startswith("http") else f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        
        print(f"Harvester Agent fetching: {url}")
        
        # Execute actual scrape
        try:
            result = await scrape_url(url, method="bs4")
            
            if result and len(result) > 50:
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
