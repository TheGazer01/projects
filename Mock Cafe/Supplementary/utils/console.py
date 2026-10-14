from rich.console import Console
from rich.table import Table

console = Console()


def log_payment(number, result):
    console.print(f"[bold green]#{number}[/bold green] {result}")


def show_history(history):
    table = Table(title="Payment History")
    table.add_column("#", justify="right")
    table.add_column("Method", style="cyan")
    table.add_column("Result", style="green")
    for number, (method, amount, result) in enumerate(history, start=1):
        table.add_row(str(number), method, result)
    console.print(table)