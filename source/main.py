import typer
from rich.console import Console
from rich.prompt import Prompt
import datetime
import os
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from typing import List, Optional

app = typer.Typer(help="writeup-automatizator")
console = Console()

class Step(BaseModel):
    title: str
    description: str
    commands: Optional[str] = ""
    language: Optional[str] = "bash"

def detect_language(code: str) -> str:
    if not code:
        return "bash"
    
    if any(kw in code for kw in ["import ", "def ", "print(", "sys.", "requests.", "from "]):
        return "python"
    
    if any(kw in code for kw in ["#include", "int main", "printf(", "std::"]):
        return "c"
        
    code_lower = code.lower()
    if any(kw in code_lower for kw in ["select ", "union ", "insert ", "drop ", "where "]):
        return "sql"
        
    if any(kw in code for kw in ["console.log", "const ", "let ", "=>", "function("]):
        return "javascript"
        
    if "<?php" in code or "$_GET" in code or "$_POST" in code or "echo $" in code:
        return "php"
        
    if code.strip().startswith("{") and code.strip().endswith("}"):
        return "json"
        
    if any(kw in code_lower for kw in ["mov ", "push ", "pop ", "xor ", "eax,", "rax,", "jmp ", "ret"]):
        return "asm"
        
    return "bash"

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
    Интерактивное создание нового writeup'а.
    """
    console.print("[bold green]writeup-automatizator - Создание нового writeup'a[/bold green]")
    
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
        cmds_formatted = step_cmds.replace("\\n", "\n")
        lang = detect_language(cmds_formatted)
        steps.append(Step(title=step_title, description=step_desc, commands=cmds_formatted, language=lang))
    
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
    Редактировать существующий файл (.json или .md).
    Используйте --editor или -e для выбора редактора.
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
    Генерация итогового .md файла из .json состояния.
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

@app.command(name="auth-telegraph")
def auth_telegraph(short_name: str):
    """
    Создать новый аккаунт в Telegraph и сохранить токен.
    """
    from telegraph import Telegraph
    try:
        tg = Telegraph()
        acc = tg.create_account(short_name=short_name)
        token_path = os.path.join(os.path.expanduser("~"), ".wup_telegraph_token")
        with open(token_path, "w") as f:
            f.write(acc['access_token'])
        console.print(f"[bold green]✔ Аккаунт '{short_name}' создан! Токен сохранен.[/bold green]")
        if 'auth_url' in acc:
            console.print(f"[bold cyan]URL для логина в браузере:[/bold cyan] {acc['auth_url']}")
    except Exception as e:
        console.print(f"[bold red]Ошибка создания аккаунта:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def publish(json_path: str):
    """
    Публикация райтапа в Telegraph.
    """
    if not os.path.exists(json_path) or not json_path.endswith(".json"):
        console.print(f"[bold red]Ожидается путь к .json файлу:[/bold red] {json_path}")
        raise typer.Exit(code=1)
    
    import json
    import markdown
    from telegraph import Telegraph

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

    md_content = template.render(**context.model_dump())
    html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
    
    # Telegraph supports only h3 and h4 headers, not h1 or h2
    html_content = html_content.replace("<h1>", "<h3>").replace("</h1>", "</h3>")
    html_content = html_content.replace("<h2>", "<h4>").replace("</h2>", "</h4>")

    try:
        token_path = os.path.join(os.path.expanduser("~"), ".wup_telegraph_token")
        if os.path.exists(token_path):
            with open(token_path, "r") as f:
                token = f.read().strip()
            tg = Telegraph(access_token=token)
        else:
            tg = Telegraph()
            acc = tg.create_account(short_name=context.team or "writeup-automatizator")
            with open(token_path, "w") as f:
                f.write(acc['access_token'])

        response = tg.create_page(
            context.title,
            html_content=html_content,
            author_name=context.team
        )
        url = response['url']
        console.print(f"[bold green]✔ Опубликовано в Telegraph:[/bold green] {url}")
    except Exception as e:
        console.print(f"[bold red]Ошибка публикации в Telegraph:[/bold red] {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()