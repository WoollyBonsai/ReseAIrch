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
        You are the Planner Agent. Your job is to break down a research objective into a JSON array of specific web queries or URLs to investigate.
        Return ONLY valid JSON. Format:
        {
            "format_demand": "JSON-L | Markdown | CSV",
            "tasks": [
                {"id": "t1", "query": "specific search or URL", "type": "scrape|search"}
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
            return {"format_demand": "Markdown", "tasks": []}
