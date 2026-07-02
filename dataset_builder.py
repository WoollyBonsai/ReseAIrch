import asyncio
import os
from src.engine import ADKEngine

async def main():
    engine = ADKEngine(model_source="ollama/llama3.1")
    
    objective = """
    Search the web for a massive variety of informational websites, reference sites, educational domains, and general sites. 
    Catalog them into a large dataset table. 
    The final output MUST be a Markdown table with exactly these columns:
    | Link | Name | Usage Category |
    """
    
    print("=== Starting Massive Dataset Scraping Operation ===")
    print("This will take some time as it crawls multiple depths.")
    
    # We set max_depth to 2 to allow the engine to crawl search results -> lists of sites
    result = await engine.run_research_pipeline(objective=objective, max_depth=2, base_collection_name="massive_dataset")
    
    print("\n\n=== FINAL RESULT ===")
    print("Status:", result["status"])
    print("Tasks Executed:", result["tasks_executed"])
    print("\nCONTENT:\n")
    print(result["content"])
    
if __name__ == "__main__":
    asyncio.run(main())
