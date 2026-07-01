import os
import sys
import asyncio
import typer
from rich.console import Console
from rich.panel import Panel

# Ensure imports work regardless of execution directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

if __name__ == "__main__":
    app()
