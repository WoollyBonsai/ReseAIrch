import os
import sys
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.engine import ADKEngine

app = FastAPI(title="ReseAIrch Web UI")

class ResearchRequest(BaseModel):
    objective: str
    depth: int = 1
    model: str = "ollama/mistral-nemo"

@app.post("/api/run")
async def run_pipeline(req: ResearchRequest):
    try:
        engine = ADKEngine(model_source=req.model)
        result = await engine.run_research_pipeline(req.objective, max_depth=req.depth)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# A simple html response for root just to prove it works
@app.get("/")
def read_root():
    html_content = """
    <html>
        <head><title>ReseAIrch Web Interface</title></head>
        <body style="font-family: sans-serif; padding: 2rem; background: #0f172a; color: white;">
            <h1>ReseAIrch ADK Web Interface</h1>
            <p>API is running. Send POST requests to /api/run</p>
        </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)
