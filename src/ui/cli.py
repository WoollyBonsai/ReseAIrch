import os
import sys
import asyncio
import typer
from rich.console import Console
from rich.panel import Panel

# Ensure imports work regardless of execution directory
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
from src.engine import ADKEngine

app = typer.Typer(help="ReseAIrch: Autonomous ADK Research Orchestrator")
console = Console()

@app.command()
def run(
    objective: str = typer.Argument(..., help="The research objective or data gathering request"),
    model: str = typer.Option("ollama/mistral-nemo", "--model", "-m", help="LLM to use (e.g., ollama/mistral-nemo, gemini)"),
    depth: int = typer.Option(1, "--depth", "-d", help="Depth level (1-3)"),
    collection: str = typer.Option("default_research", "--collection", "-c", help="ChromaDB Collection name")
):
    """
    Executes the ADK multi-agent pipeline for a single research objective.
    """
    console.print(Panel.fit(f"[bold blue]ReseAIrch ADK Engine[/bold blue]\nObjective: {objective}\nModel: {model}\nDepth: {depth}", border_style="blue"))
    
    engine = ADKEngine(model_source=model)
    
    with console.status("[bold green]ADK Agents executing pipeline... (Planner -> Harvester -> Synthesizer)"):
        result = asyncio.run(engine.run_research_pipeline(objective, max_depth=depth, collection_name=collection))
        
    console.print(f"\n[bold green]Pipeline Complete![/bold green]")
    console.print(f"Format Generated: [bold yellow]{result.get('format')}[/bold yellow]")
    console.print(f"Tasks Executed: {result.get('tasks_executed')}")
    console.print(f"\n[bold]Output Snippet:[/bold]")
    
    content = result.get('content', '')
    if len(content) > 500:
        console.print(content[:500] + "...\n[italic](See workspace/ directory for full output)[/italic]")
    else:
        console.print(content)

@app.command()
def interactive():
    """Starts the persistent interactive ADK CLI loop."""
    console.print(Panel.fit("[bold magenta]Welcome to ReseAIrch ADK Interactive Shell[/bold magenta]\nType 'exit' to quit.", border_style="magenta"))
    
    model = "ollama/mistral-nemo"
    depth = 1
    
    while True:
        try:
            cmd = console.input("\n[bold cyan]ReseAIrch>[/bold cyan] ").strip()
            if not cmd:
                continue
            if cmd.lower() in ['exit', 'quit']:
                break
                
            engine = ADKEngine(model_source=model)
            with console.status("[bold green]Agents are working..."):
                result = asyncio.run(engine.run_research_pipeline(cmd, max_depth=depth))
            
            console.print(f"\n[bold green]Finished![/bold green] Format: {result.get('format')}")
            content = result.get('content', '')
            if len(content) > 500:
                 console.print(content[:500] + "...\n[italic](Check workspace/ for full file)[/italic]")
            else:
                 console.print(content)
                 
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

@app.command()
def history(
    read: str = typer.Option(None, "--read", "-r", help="Read a specific file from raw or processed workspace"),
    delete_raw: bool = typer.Option(False, "--delete-raw", help="Delete all raw data dumps"),
    delete_processed: bool = typer.Option(False, "--delete-processed", help="Delete all processed reports")
):
    """Manage past operations, raw scrapes, and processed reports."""
    raw_dir = os.path.join(project_root, "workspace", "raw")
    processed_dir = os.path.join(project_root, "workspace", "processed")
    
    if delete_raw:
        for f in os.listdir(raw_dir):
            os.remove(os.path.join(raw_dir, f))
        console.print("[bold red]All raw data dumps deleted.[/bold red]")
        return
        
    if delete_processed:
        for f in os.listdir(processed_dir):
            os.remove(os.path.join(processed_dir, f))
        console.print("[bold red]All processed reports deleted.[/bold red]")
        return
        
    if read:
        raw_path = os.path.join(raw_dir, read)
        proc_path = os.path.join(processed_dir, read)
        if os.path.exists(proc_path):
            with open(proc_path, "r", encoding="utf-8") as f:
                console.print(Panel(f.read(), title=f"Processed: {read}"))
        elif os.path.exists(raw_path):
            with open(raw_path, "r", encoding="utf-8") as f:
                console.print(Panel(f.read()[:2000] + "\n...[TRUNCATED]", title=f"Raw: {read}"))
        else:
            console.print(f"[red]File '{read}' not found in raw or processed folders.[/red]")
        return
        
    # List files
    console.print(Panel.fit("[bold cyan]Past Operations History[/bold cyan]", border_style="cyan"))
    
    console.print("\n[bold yellow]Processed Reports:[/bold yellow]")
    if os.path.exists(processed_dir) and os.listdir(processed_dir):
        for f in os.listdir(processed_dir):
            console.print(f" - {f}")
    else:
        console.print(" (No processed reports found)")
        
    console.print("\n[bold magenta]Raw Data Dumps:[/bold magenta]")
    if os.path.exists(raw_dir) and os.listdir(raw_dir):
        for f in os.listdir(raw_dir):
            console.print(f" - {f}")
    else:
        console.print(" (No raw data found)")

if __name__ == "__main__":
    app()
