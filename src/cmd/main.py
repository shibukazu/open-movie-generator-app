import generate
import typer
import upload

app = typer.Typer()
app.add_typer(upload.app, name="upload")
app.add_typer(generate.app, name="generate")


if __name__ == "__main__":
    app()
