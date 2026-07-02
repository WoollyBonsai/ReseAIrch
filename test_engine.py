import asyncio
import os
from src.engine import ADKEngine

async def main():
    engine = ADKEngine(model_source="ollama/mistral-nemo")
    
    # 1. Simple test first
    print("=== TEST 1: Simple Target ===")
    res1 = await engine.run_research_pipeline("Scrape https://news.ycombinator.com/ and summarize top 3 headlines.", max_depth=1)
    print("Test 1 Result:", res1)
    
    # 2. Hard target second
    print("\n=== TEST 2: Hard Target ===")
    res2 = await engine.run_research_pipeline("Search the web for NSE IPO data from moneycontrol.com over the past 12 months.", max_depth=1)
    print("Test 2 Result:", res2)

if __name__ == "__main__":
    asyncio.run(main())
