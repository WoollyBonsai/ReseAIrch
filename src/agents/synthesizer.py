import os
import json
from litellm import completion
from src.mcp_servers.memory_server import query_memory

class SynthesizerAgent:
    """
    ADK Synthesizer Agent.
    Responsible for fetching data from the Memory Server and converting it into
    full-scale categorized reports based on the user's demanded format.
    """
    def __init__(self, model_source="ollama/mistral-nemo"):
        self.model = model_source
        self.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434") if "ollama" in model_source else None
        os.makedirs(os.path.join(os.getcwd(), "workspace", "processed"), exist_ok=True)

    def apply_dynamic_formatting(self, raw_context: str, format_demand: str) -> dict:
        print(f"Synthesizer Agent applying dynamic formatting: {format_demand}")
        
        system_prompt = f"""
        You are the Synthesizer Agent. Your job is to format the raw data strictly as requested.
        The user has demanded format: {format_demand} AND requested full-scale reports categorized by different methods/topics as you understand them.
        Do NOT just write a short summary. Write extensive, comprehensive guides.
        
        You MUST output your response as a raw JSON object (and nothing else). 
        The keys of the JSON must be appropriate filenames (e.g., 'nmap_scanning_methods.md', 'owasp_testing_guide.md', 'training_data.jsonl').
        The values must be the full-scale string content for that file.
        Do not wrap the JSON in markdown code blocks.
        """
        
        try:
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Raw Context:\n{raw_context}"}
                ],
                api_base=self.api_base,
                response_format={ "type": "json_object" } if "ollama" not in self.model else None # Ollama handles json prompting via system prompt, OpenAI uses this
            )
            content = response.choices[0].message.content.strip()
            # Clean up if model wrapped in markdown anyway
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content.strip(), strict=False)
        except Exception as e:
            print(f"Synthesizer Error: {e}")
            return {"error_report.txt": str(e), "raw_fallback.txt": raw_context[:1000]}

    async def generate_output(self, objective: str, collection_name: str, format_demand: str):
        # Actual Call to Memory Server
        raw_context = query_memory(collection_name=collection_name, query=objective, n_results=10)
        
        if "Error" in raw_context or "No relevant information found" in raw_context:
            print("Warning: Could not retrieve robust context from memory.")
            
        file_map = self.apply_dynamic_formatting(raw_context, format_demand)
        
        # Save output
        print(f"Synthesizer extracted {len(file_map)} categorized reports.")
        for filename, content in file_map.items():
            filepath = os.path.join(os.getcwd(), "workspace", "processed", filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Generated report: workspace/processed/{filename}")
