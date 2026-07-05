import datetime
import re
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Header, Footer, Input, Select, Button, Label, TextArea, Static
from textual import on

from .models import WriteupContext, Step
from .storage import StorageService
from .markdown import MarkdownService
from .utils import detect_language

class StepInput(Static):
    def compose(self) -> ComposeResult:
        with Horizontal(classes="step-header"):
            yield Label("Заголовок шага", classes="step-label")
            yield Button("ⓧ", variant="error", classes="remove-step-btn")
        yield Input(classes="step-title")
        yield Label("Описание шага")
        yield TextArea(classes="step-desc")
        yield Label("Код/Команды")
        yield TextArea(classes="step-cmds")

    @on(Button.Pressed, ".remove-step-btn")
    def remove_self(self) -> None:
        self.remove()

class WriteupApp(App):
    CSS = """
    Input, Select { margin-bottom: 1; }
    TextArea { height: 5; margin-bottom: 1; }
    StepInput { margin-top: 1; padding: 1; border: solid green; }
    .step-header {
        height: 3;
    }
    .step-label {
        width: 1fr;
        padding-top: 1;
    }
    .remove-step-btn {
        width: 5;
        min-width: 5;
    }
    #buttons_container {
        dock: bottom;
        height: auto;
        padding: 1 0;
        align: center middle;
    }
    #buttons_container Button {
        width: 30;
        margin: 0 2;
    }
    """

    def __init__(self, cfg: dict, out_dir: str):
        super().__init__()
        self.cfg = cfg
        self.out_dir = out_dir

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="main_scroll"):
            yield Label("Название таска")
            yield Input(id="title")
            
            yield Label("Категория")
            yield Select(((c, c) for c in ["pwn", "web", "crypto", "forensics", "reverse", "misc", "osint"]), id="category", value="pwn")
            
            yield Label("Сложность")
            yield Select(((d, d) for d in ["easy", "medium", "hard"]), id="difficulty", value="easy")
            
            yield Label("Флаг")
            yield Input(value="ctf{...}", id="flag")
            
            yield Label("Краткое описание таска")
            yield TextArea(id="description")
            
            yield Label("Ссылка на таск (опционально)")
            yield Input(id="link")

        with Horizontal(id="buttons_container"):
            yield Button("+ Добавить шаг решения", id="add_step", variant="primary")
            yield Button("Сохранить и выйти", id="save", variant="success")
        yield Footer()

    @on(Button.Pressed, "#add_step")
    def add_step(self, event: Button.Pressed) -> None:
        self.query_one("#main_scroll").mount(StepInput())

    @on(Button.Pressed, "#save")
    def save_writeup(self, event: Button.Pressed) -> None:
        title = self.query_one("#title", Input).value or "Untitled"
        cat = self.query_one("#category", Select).value
        diff = self.query_one("#difficulty", Select).value
        flag = self.query_one("#flag", Input).value
        desc = self.query_one("#description", TextArea).text
        link = self.query_one("#link", Input).value
        
        steps = []
        for step_widget in self.query(StepInput):
            st_title = step_widget.query_one(".step-title", Input).value
            st_desc = step_widget.query_one(".step-desc", TextArea).text
            st_cmds = step_widget.query_one(".step-cmds", TextArea).text
            
            if st_title or st_desc or st_cmds:
                lang = detect_language(st_cmds)
                steps.append(Step(title=st_title, description=st_desc, commands=st_cmds, language=lang))
                
        context = WriteupContext(
            title=title,
            category=cat,
            difficulty=diff,
            flag=flag,
            description=desc,
            link=link,
            team=self.cfg.get("author", "r007s"),
            date=datetime.date.today().isoformat(),
            steps=steps
        )
        
        try:
            storage = StorageService(base_dir=self.out_dir)
            safe_title = re.sub(r'[^\w]+', '_', context.title.lower()).strip('_') or 'untitled'
            json_path = storage.save_json(context, str(datetime.date.today().year), safe_title)
            
            md_service = MarkdownService()
            output_path = md_service.generate(context, json_path)
            self.exit(output_path)
        except Exception as e:
            self.exit(e)    
