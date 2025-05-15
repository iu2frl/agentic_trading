# cli.py
import typer

app = typer.Typer(help="Agentic Trader CLI")

@app.command()
def run_simulation(strategy: str = typer.Argument(..., help="Strategy to use (e.g., momentum, value)")):
    """Run the simulation with the given strategy"""
    typer.echo(f"Running simulation with {strategy} strategy...")
    # Replace with your actual call
    from simulation.engine import run
    run(strategy)

@app.command()
def analyze(symbol: str):
    """Analyze a stock or portfolio"""
    typer.echo(f"Analyzing {symbol}...")
    # Add actual analysis logic here

if __name__ == "__main__":
    app()
