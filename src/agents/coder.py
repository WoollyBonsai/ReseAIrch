import os
import subprocess
import hashlib
from litellm import completion
from src.mcp_servers.memory_server import store_document

class CoderAgent:
    """
    ADK Coder Agent (Execution Environment).
    Dynamically writes, executes, and iterates on custom Python scraping scripts
    if the standard Harvester is blocked (e.g. Captcha, 403 Forbidden).
    """
    def __init__(self, model_source="ollama/mistral-nemo"):
        self.model = model_source
        self.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434") if "ollama" in model_source else None
        self.scripts_dir = os.path.join(os.getcwd(), "workspace", "scripts")
        os.makedirs(self.scripts_dir, exist_ok=True)

    def _sanitize_filename(self, url: str) -> str:
        safe_name = "".join(c if c.isalnum() else "_" for c in url)
        hash_suffix = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"scraper_{safe_name[:30]}_{hash_suffix}.py"

    def write_and_execute(self, url: str, collection_name: str, objective: str, max_retries: int = 2) -> bool:
        print(f"\n[Coder Agent] Standard harvesting failed. Deploying custom script for: {url}")
        
        system_prompt = f"""
            You are an elite Python Coder Agent for the ADK Engine.
            The Harvester Agent failed to extract data from {url}.
            Your task is to write a dynamic, custom Python script to extract data from it.
            
            CRITICAL RULES:
            1. You MUST use the `versatile_scrape` function from our utils to bypass Cloudflare/Captchas.
            2. The function signature is `async def versatile_scrape(url: str, use_stealth: bool = True) -> str`.
            3. The function returns raw text or HTML from the page after bypassing captchas.
            4. You must write the asyncio boilerplate and parse the returned text.
            5. Print your final extracted data so the engine can capture stdout.
            6. Do NOT use standard `requests` or `urllib` because they will be blocked.
            
            Example Format:
            import asyncio
            from src.utils.versatile_scraper import versatile_scrape
            
            async def main():
                html = await versatile_scrape("{url}")
                # Parse data from html string here if needed
                print(html[:5000]) # Example output
                
            asyncio.run(main())
            
            Do NOT include markdown code blocks. Output raw Python ONLY.
            """
        
        for attempt in range(max_retries):
            print(f"[Coder Agent] Attempt {attempt+1}/{max_retries} to generate and run script...")
            try:
                response = completion(
                    model=self.model,
                    messages=[{"role": "system", "content": system_prompt}],
                    api_base=self.api_base
                )
                
                script_code = response.choices[0].message.content.strip()
                
                # Robust extraction for chatty models
                if "```python" in script_code:
                    script_code = script_code.split("```python")[1].split("```")[0].strip()
                elif "```" in script_code:
                    script_code = script_code.split("```")[1].strip()
                    
                script_path = os.path.join(self.scripts_dir, self._sanitize_filename(url))
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(script_code)
                    
                print(f"[Coder Agent] Executing generated script: {script_path}")
                
                # Execute in the venv environment
                result = subprocess.run(["python", script_path], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and len(result.stdout) > 50:
                    print(f"[Coder Agent] Execution Successful! Storing {len(result.stdout)} bytes to memory.")
                    store_document(collection_name=collection_name, content=result.stdout, source_url=url)
                    return True
                else:
                    print(f"[Coder Agent] Execution failed or no data. Stderr: {result.stderr[:200]}")
                    system_prompt += f"\nPrevious attempt failed with error:\n{result.stderr}\nFix the code and output raw Python only."
                    
            except Exception as e:
                print(f"[Coder Agent] Error during generation/execution: {e}")
                
        return False
