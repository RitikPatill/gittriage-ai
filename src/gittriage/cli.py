import typer

app = typer.Typer()


@app.command()
def main():
    """GitTriage AI — placeholder. Implemented in M5."""
    typer.echo("GitTriage AI scaffold. Run with --help.")


if __name__ == "__main__":
    app()
