import os
import json
from litellm import completion
from src.mcp_servers.memory_server import search_documents

class ReviewerAgent:
    """
    ADK Reviewer Agent (Reflection Loop).
    Checks the harvested memory for generic blocking errors, Captcha pages, or lack of data.
    If the standard harvest failed for specific URLs, it returns them so the Coder can take over.
    """
    def __init__(self, model_source="ollama/mistral-nemo"):
        self.model = model_source
        self.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434") if "ollama" in model_source else None

    def evaluate_harvest(self, collection_name: str, dag: dict) -> list:
        print("\n[Reviewer Agent] Evaluating harvest quality...")
        failed_urls = []
        
        # Check memory for each task's url
        for task in dag.get("tasks", []):
            if task.get("type") == "search":
                continue # Skip search tasks, focus on deep scrape tasks
                
            url = task.get("query", "")
            if not url.startswith("http"):
                continue
                
            docs = search_documents(collection_name, query=url, n_results=1)
            
            if not docs or not docs[0]:
                print(f"[Reviewer Agent] No data found in memory for {url}")
                failed_urls.append(url)
                continue
                
            content = docs[0]
            
            # Simple heuristic checks before calling LLM
            block_keywords = ["access denied", "403 forbidden", "captcha", "security check", "cloudflare", "verify you are human"]
            if any(k in content.lower()[:1000] for k in block_keywords):
                print(f"[Reviewer Agent] Detected block/captcha for {url}")
                failed_urls.append(url)
                continue
                
        return failed_urls
