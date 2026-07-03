import os
import json
from litellm import completion

class PlannerAgent:
    """
    ADK Planner Agent.
    Responsible for analyzing user intent, data demands (JSON, markdown),
    and generating a DAG (Directed Acyclic Graph) of URLs and queries to scrape.
    """
    def __init__(self, model_source="ollama/mistral-nemo"):
        self.model = model_source
        self.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434") if "ollama" in model_source else None

    def plan_research(self, objective: str, max_depth: int = 1) -> dict:
        print(f"Planner Agent creating execution DAG for: {objective}")
        
        system_prompt = """
        You are the ADK Planner Agent. Your job is to orchestrate a deep, smart web scraping workflow.
        You must break down the user's objective into a JSON array of specific web queries AND specific URLs to investigate.
        If the objective is broad, your first task should be a search query (e.g., 'Google Dorks for SQLi' or a specific target URL).
        Subsequent tasks should represent the deep links that we expect to find and crawl. 
        You must also specify if cookies are needed for a specific target.
        
        CRITICAL RULES:
        1. When generating a "search" query, use PLAIN ENGLISH. Do NOT use regex, HTML, or raw DuckDuckGo URLs. (e.g., Use "top educational websites" NOT "https://duckduckgo.com/?q=...").
        2. When generating a "scrape" URL, you MUST ONLY use real, known URLs. Do NOT hallucinate placeholders like "example.com" or "example.edu". If you don't know a specific URL, just use a "search" task instead!
        
        Return ONLY valid JSON. Format:
        {
            "thought_process": "Write your step-by-step logic here on why you selected these search queries and URLs.",
            "tasks": [
                {"id": "t1", "query": "top educational websites", "type": "search"},
                {"id": "t2", "query": "https://en.wikipedia.org/wiki/List_of_educational_websites", "type": "scrape", "use_cookies": true}
            ]
        }
        """
        
        try:
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Objective: {objective}\nDepth: {max_depth}"}
                ],
                api_base=self.api_base,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"Planner Error: {e}")
            return {"tasks": []}
