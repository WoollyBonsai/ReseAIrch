import os
import asyncio
from typing import Dict, Any

from src.agents.planner import PlannerAgent
from src.agents.harvester import HarvesterAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.reviewer import ReviewerAgent
from src.agents.coder import CoderAgent

class ADKEngine:
    """
    The Core ADK Engine (Agent Development Kit).
    This class orchestrates the Multi-Agent System. It initializes the
    Planner, Harvester, and Synthesizer agents and routes the state between them.
    """
    def __init__(self, model_source: str = "ollama/mistral-nemo"):
        print(f"Initializing ADK Engine with {model_source}...")
        self.planner = PlannerAgent(model_source=model_source)
        self.harvester = HarvesterAgent()
        self.synthesizer = SynthesizerAgent(model_source=model_source)
        self.reviewer = ReviewerAgent(model_source=model_source)
        self.coder = CoderAgent(model_source=model_source)

    async def run_research_pipeline(self, objective: str, max_depth: int = 1, base_collection_name: str = "default_research") -> Dict[str, Any]:
        """
        Executes the full multi-agent pipeline.
        1. Planner: Breaks down the objective into a DAG and determines formatting demand.
        2. Harvester: Executes the scraping jobs against the DAG.
        3. Synthesizer: Pulls from memory and formats the output.
        """
        import time
        collection_name = f"{base_collection_name}_{int(time.time())}"
        
        print("\n--- [Phase 1: Planning] ---")
        dag = self.planner.plan_research(objective, max_depth)
        format_demand = "Markdown" # Hardcoded to simple markdown to prevent LLM confusion
        print(f"Planned {len(dag.get('tasks', []))} tasks. Demanded format: {format_demand}")

        print("\n--- [Phase 2: Harvesting] ---")
        await self.harvester.run_dag(dag, collection_name)

        print("\n--- [Phase 3: Review & Reflection] ---")
        failed_urls = self.reviewer.evaluate_harvest(collection_name, dag)
        
        if failed_urls:
            print(f"\n--- [Phase 3b: Coder Execution (Fallback)] ---")
            print(f"Deploying dynamic Coder Agent for {len(failed_urls)} blocked targets...")
            for url in failed_urls:
                self.coder.write_and_execute(url, collection_name, objective)

        print("\n--- [Phase 4: Synthesizing] ---")
        # Pulls data from Memory Server and formats it
        await self.synthesizer.generate_output(objective, collection_name, format_demand)
        
        processed_dir = os.path.join(os.getcwd(), "workspace", "processed")
        final_content = "Error: Output file not generated."
        
        if os.path.exists(processed_dir):
            files = [f for f in os.listdir(processed_dir) if not f.startswith("error")]
            if files:
                # Read the first successful processed file for the CLI snippet
                output_path = os.path.join(processed_dir, files[0])
                try:
                    with open(output_path, "r", encoding="utf-8") as f:
                        final_content = f"File: {files[0]}\n\n" + f.read()
                except Exception as e:
                    final_content = f"Error reading generated report: {e}"
            else:
                # If only error fallback exists
                error_path = os.path.join(processed_dir, "error_report.txt")
                if os.path.exists(error_path):
                    with open(error_path, "r", encoding="utf-8") as f:
                        final_content = "Synthesizer Error Fallback:\n" + f.read()

        return {
            "status": "success",
            "format": format_demand,
            "content": final_content,
            "tasks_executed": len(dag.get("tasks", []))
        }

# For simple testing
if __name__ == "__main__":
    engine = ADKEngine()
    asyncio.run(engine.run_research_pipeline("Analyze recent advancements in local LLMs", max_depth=1))
