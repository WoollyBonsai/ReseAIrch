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

    def apply_dynamic_formatting(self, raw_context: str, format_demand: str, objective: str) -> dict:
        print(f"Synthesizer Agent applying dynamic formatting: {format_demand}")
        
        system_prompt = f"""
        You are the Synthesizer Agent. Your job is to analyze the Raw Context and fulfill the user's objective.
        
        USER OBJECTIVE:
        {objective}
        
        REQUESTED FORMAT: {format_demand}
        
        You MUST output your response as a raw JSON object (and nothing else). 
        The keys of the JSON must be appropriate filenames (e.g., 'report.md', 'data.json', 'summary.txt') that fit the objective.
        The values must be the full string content for that file.
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
            try:
                # Some models might wrap JSON inside ```json
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].strip()
                else:
                    json_str = content
                    
                return json.loads(json_str, strict=False)
            except Exception:
                # If it's completely not JSON, assume the model generated a single raw markdown report
                print("Synthesizer could not parse JSON, falling back to raw markdown dump.")
                return {"final_report_fallback.md": content}
                
        except Exception as e:
            print(f"Synthesizer Error: {e}")
            return {"error_report.txt": str(e), "raw_fallback.txt": raw_context[:1000]}

    async def generate_output(self, objective: str, collection_name: str, format_demand: str):
        # Actual Call to Memory Server
        raw_context = query_memory(collection_name=collection_name, query=objective, n_results=10)
        
        if "Error" in raw_context or "No relevant information found" in raw_context:
            print("Warning: Could not retrieve robust context from memory.")
            
        file_map = self.apply_dynamic_formatting(raw_context, format_demand, objective)
        
        # Save output
        print(f"Synthesizer extracted {len(file_map)} categorized reports.")
        for filename, content in file_map.items():
            filepath = os.path.join(os.getcwd(), "workspace", "processed", filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Generated report: workspace/processed/{filename}")
