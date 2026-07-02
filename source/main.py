import typer
from rich.console import Console
from rich.prompt import Prompt
import datetime
import os
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from typing import List, Optional

app = typer.Typer(help="Writeup Automator")
console = Console()

class Step(BaseModel):
    title: str
    description: str
    commands: Optional[str] = ""

class WriteupContext(BaseModel):
    title: str
    category: str
    difficulty: str
    flag: str
    description: str
    link: Optional[str] = ""
    team: str
    date: str
    steps: List[Step] = []

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

@app.command()
def init():
    """
    Initialize a new writeup interactively.
    """
    console.print("[bold green]Writeup Automator - Создание нового writeup'a[/bold green]")
    
    title = Prompt.ask("Название таска")
    category = Prompt.ask("Категория", choices=["forensics", "web", "crypto", "pwn", "reverse", "misc", "osint"], default="pwn")
    difficulty = Prompt.ask("Сложность", choices=["easy", "medium", "hard"], default="easy")
    flag = Prompt.ask("Флаг", default="ctf{...}")
    description = Prompt.ask("Краткое описание таска", default="")
    link = Prompt.ask("Ссылка на таск (опционально)", default="")
    team = Prompt.ask("Команда/Автор", default="r007s")
    

    steps = []
    console.print("\n[bold cyan]Шаги решения[/bold cyan]")
    while True:
        step_title = Prompt.ask("Заголовок шага (оставьте пустым для завершения)", default="")
        if not step_title:
            break
        step_desc = Prompt.ask("Описание того, что делал", default="")
        step_cmds = Prompt.ask("Команды (опционально, используйте \\n для переносов)", default="")
        steps.append(Step(title=step_title, description=step_desc, commands=step_cmds.replace("\\n", "\n")))
    
    date_str = datetime.date.today().isoformat()
    
    context = WriteupContext(
        title=title,
        category=category,
        difficulty=difficulty,
        flag=flag,
        description=description,
        link=link,
        team=team,
        date=date_str,
        steps=steps
    )
    

    template_name = "default.md"
    try:
        template = env.get_template(template_name)
    except Exception as e:
        console.print(f"[bold red]Ошибка загрузки шаблона:[/bold red] {e}")
        return

    content = template.render(**context.model_dump())
    

    safe_title = title.lower().replace(" ", "_").replace("'", "").replace('"', '')
    output_dir = os.path.join(os.getcwd(), "writeups", str(datetime.date.today().year), category)
    os.makedirs(output_dir, exist_ok=True)
    
    json_path = os.path.join(output_dir, f"{safe_title}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(context.model_dump_json(indent=4))
        
    output_path = os.path.join(output_dir, f"{safe_title}.md")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    console.print(f"\n[bold green]✔ Writeup сгенерирован:[/bold green] {output_path}")

@app.command()
def edit(
    filepath: str,
    editor: Optional[str] = typer.Option(None, "--editor", "-e", help="Редактор для использования (nano, vim, code и т.д.)")
):
    """
    Edit an existing writeup state (.json) or markdown file.
    """
    if not os.path.exists(filepath):
        console.print(f"[bold red]Файл не найден:[/bold red] {filepath}")
        raise typer.Exit(code=1)
    
    import click
    click.edit(filename=filepath, editor=editor)
    console.print(f"[bold green]✔ Файл сохранен:[/bold green] {filepath}")
    
    if filepath.endswith(".json"):
        console.print("[bold cyan]Запустите `writeup generate <путь_к_json>` для обновления .md файла.[/bold cyan]")

@app.command()
def generate(json_path: str):
    """
    Generate the final .md file from a .json state file.
    """
    if not os.path.exists(json_path) or not json_path.endswith(".json"):
        console.print(f"[bold red]Ожидается путь к .json файлу:[/bold red] {json_path}")
        raise typer.Exit(code=1)
    
    import json
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        context = WriteupContext(**data)
    except Exception as e:
        console.print(f"[bold red]Ошибка чтения JSON:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    template_name = "default.md"
    try:
        template = env.get_template(template_name)
    except Exception as e:
        console.print(f"[bold red]Ошибка загрузки шаблона:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    content = template.render(**context.model_dump())
    
    output_path = json_path.replace(".json", ".md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    console.print(f"[bold green]✔ Writeup обновлен:[/bold green] {output_path}")

if __name__ == "__main__":
    app()
