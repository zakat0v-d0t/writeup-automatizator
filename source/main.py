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
    output_path = os.path.join(output_dir, f"{safe_title}.md")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    console.print(f"\n[bold green]✔ Writeup сгенерирован:[/bold green] {output_path}")

@app.command()
def edit():
    """
    Edit an existing writeup. (Not implemented)
    """
    console.print("Not implemented yet.")

@app.command()
def generate():
    """
    Final generation of .md file. (Not implemented)
    """
    console.print("Not implemented yet.")

if __name__ == "__main__":
    app()
