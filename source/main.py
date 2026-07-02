import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
import datetime
import os
import click
from typing import Optional
import json

from .models import Step, WriteupContext
from .utils import detect_language
from .services import WriteupManager, TelegraphService

app = typer.Typer(help="writeup-automatizator")
console = Console()

@app.command()
def init(
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", "-o", help="Директория для сохранения райтапов"
    )
):
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
    console.print("\\n[bold cyan]Шаги решения[/bold cyan]")
    while True:
        step_title = Prompt.ask("Заголовок шага (оставьте пустым для завершения)", default="")
        if not step_title:
            break
        step_desc = Prompt.ask("Описание того, что делал", default="")
        step_cmds = Prompt.ask("Команды (опционально, используйте \\\\n для переносов)", default="")
        cmds_formatted = step_cmds.replace("\\\\n", "\\n")
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
    
    manager = WriteupManager(base_dir=output_dir)
    try:
        output_path = manager.save_writeup(context, str(datetime.date.today().year))
        console.print(f"\\n[bold green]✔ Writeup сгенерирован:[/bold green] {output_path}")
    except Exception as e:
        console.print(f"[bold red]Ошибка сохранения:[/bold red] {e}")

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
    
    click.edit(filename=filepath, editor=editor)
    console.print(f"[bold green]✔ Файл сохранен:[/bold green] {filepath}")
    
    if filepath.endswith(".json"):
        console.print("[bold cyan]Запустите `wup generate <путь_к_json>` для обновления .md файла.[/bold cyan]")

@app.command()
def generate(json_path: str):
    """
    Генерация итогового .md файла из .json состояния.
    """
    if not os.path.exists(json_path) or not json_path.endswith(".json"):
        console.print(f"[bold red]Ожидается путь к .json файлу:[/bold red] {json_path}")
        raise typer.Exit(code=1)
    
    manager = WriteupManager()
    try:
        output_path = manager.generate_markdown(json_path)
        console.print(f"[bold green]✔ Writeup обновлен:[/bold green] {output_path}")
    except Exception as e:
        console.print(f"[bold red]Ошибка генерации:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command(name="auth-telegraph")
def auth_telegraph(short_name: str):
    """
    Создать новый аккаунт в Telegraph и сохранить токен.
    """
    service = TelegraphService()
    try:
        acc = service.auth(short_name)
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
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        context = WriteupContext(**data)
    except Exception as e:
        console.print(f"[bold red]Ошибка чтения JSON:[/bold red] {e}")
        raise typer.Exit(code=1)

    service = TelegraphService()
    try:
        url = service.publish(context)
        console.print(f"[bold green]✔ Опубликовано в Telegraph:[/bold green] {url}")
    except Exception as e:
        console.print(f"[bold red]Ошибка публикации в Telegraph:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command(name="list")
def list_writeups(
    base_dir: Optional[str] = typer.Option(
        None, "--dir", "-d", help="Директория с райтапами (по умолчанию текущая)"
    )
):
    """
    Показать список всех локальных райтапов.
    """
    manager = WriteupManager(base_dir=base_dir)
    if not os.path.exists(manager.writeups_dir):
        console.print(f"[bold yellow]Папка writeups не найдена в {manager.base_dir}[/bold yellow]")
        raise typer.Exit()
        
    table = Table(title="Локальные райтапы", show_header=True, header_style="bold magenta")
    table.add_column("Категория", style="cyan")
    table.add_column("Название")
    table.add_column("Сложность")
    table.add_column("Дата")
    table.add_column("MD файл")

    results = manager.get_all_writeups()
    if not results:
        console.print("[bold yellow]Райтапы не найдены.[/bold yellow]")
        raise typer.Exit()
        
    for data, md_exists_bool in results:
        md_exists = "[green]Да[/green]" if md_exists_bool else "[red]Нет[/red]"
        cat = data.get("category", "-")
        title = data.get("title", "-")
        diff = data.get("difficulty", "-")
        date = data.get("date", "-")
        table.add_row(cat, title, diff, date, md_exists)
            
    console.print(table)

if __name__ == "__main__":
    app()