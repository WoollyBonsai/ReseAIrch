import os
import sys
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
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

@app.get("/api/history")
def get_history():
    raw_dir = os.path.join(project_root, "workspace", "raw")
    processed_dir = os.path.join(project_root, "workspace", "processed")
    raws = os.listdir(raw_dir) if os.path.exists(raw_dir) else []
    processed = os.listdir(processed_dir) if os.path.exists(processed_dir) else []
    return JSONResponse(content={"raw": raws, "processed": processed})

@app.get("/api/history/read/{filename}")
def read_history(filename: str):
    raw_path = os.path.join(project_root, "workspace", "raw", filename)
    proc_path = os.path.join(project_root, "workspace", "processed", filename)
    
    if os.path.exists(proc_path):
        with open(proc_path, "r", encoding="utf-8") as f:
            return JSONResponse(content={"content": f.read()})
    elif os.path.exists(raw_path):
        with open(raw_path, "r", encoding="utf-8") as f:
            return JSONResponse(content={"content": f.read()[:5000] + "\n...[TRUNCATED]"})
    return JSONResponse(status_code=404, content={"message": "File not found"})

@app.delete("/api/history/delete/raw")
def delete_raw():
    raw_dir = os.path.join(project_root, "workspace", "raw")
    if os.path.exists(raw_dir):
        for f in os.listdir(raw_dir):
            os.remove(os.path.join(raw_dir, f))
    return JSONResponse(content={"status": "success"})

@app.delete("/api/history/delete/processed")
def delete_processed():
    processed_dir = os.path.join(project_root, "workspace", "processed")
    if os.path.exists(processed_dir):
        for f in os.listdir(processed_dir):
            os.remove(os.path.join(processed_dir, f))
    return JSONResponse(content={"status": "success"})

class MemoryQuery(BaseModel):
    query: str
    collection_name: str = "default_research"

@app.post("/api/memory/query")
def query_memory_db(req: MemoryQuery):
    try:
        from src.mcp_servers.memory_server import query_memory
        results = query_memory(req.collection_name, req.query, n_results=5)
        return JSONResponse(content={"status": "success", "results": results})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# Serve static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))
