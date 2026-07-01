import os
from litellm import completion

class SynthesizerAgent:
    """
    ADK Synthesizer Agent.
    Responsible for fetching data from the Memory MCP Server and converting it into
    the user's demanded format (e.g., Markdown summary, JSON-L for training).
    """
    def __init__(self, model_source="ollama/mistral-nemo"):
        self.model = model_source
        self.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434") if "ollama" in model_source else None

    def apply_dynamic_formatting(self, raw_context: str, format_demand: str) -> str:
        print(f"Synthesizer Agent applying dynamic formatting: {format_demand}")
        
        system_prompt = f"""
        You are the Synthesizer Agent. Your job is to format the raw data strictly as requested.
        The user has demanded format: {format_demand}.
        If JSON-L, ensure each line is a valid JSON object suitable for model fine-tuning (e.g., {{"instruction": "...", "output": "..."}}).
        If Markdown, ensure it is a deeply researched academic summary.
        """
        
        try:
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Raw Context:\n{raw_context}"}
                ],
                api_base=self.api_base
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Synthesizer Error: {e}"

    async def generate_output(self, objective: str, collection_name: str, format_demand: str):
        # Simulated MCP Call to Memory Server
        # raw_context = await mcp_client.call_tool("query_memory", collection_name=collection_name, query=objective, n_results=10)
        
        raw_context = "[Simulated data retrieved from ChromaDB Memory MCP]"
        
        final_output = self.apply_dynamic_formatting(raw_context, format_demand)
        
        # Save output
        output_file = "training_data.jsonl" if "JSON" in format_demand else "research_summary.md"
        with open(os.path.join(os.getcwd(), "workspace", output_file), "w") as f:
            f.write(final_output)
            
        print(f"Output saved to workspace/{output_file}")
