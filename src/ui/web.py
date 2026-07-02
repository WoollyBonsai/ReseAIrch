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

# Serve static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))
