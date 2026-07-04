import os
import stat
import markdown
from bs4 import BeautifulSoup
from telegraph import Telegraph
from telegraph.exceptions import TelegraphException
from dotenv import load_dotenv, set_key
from deep_translator import GoogleTranslator

from .models import WriteupContext
from .exceptions import ApiAuthError, TranslationError
from .markdown import env

class TelegraphService:
    def __init__(self):
        self.token_path = os.path.join(os.path.expanduser("~"), ".writeup.env")

    def _get_token(self) -> str:
        load_dotenv(self.token_path)
        return os.environ.get("TELEGRAPH_TOKEN")

    def _save_token(self, token: str):
        if not os.path.exists(self.token_path):
            with open(self.token_path, "a"):
                pass
        set_key(self.token_path, "TELEGRAPH_TOKEN", token)
        os.chmod(self.token_path, stat.S_IRUSR | stat.S_IWUSR)

    def auth(self, short_name: str) -> dict:
        try:
            tg = Telegraph()
            acc = tg.create_account(short_name=short_name)
            self._save_token(acc['access_token'])
            return acc
        except TelegraphException as e:
            raise ApiAuthError(f"Ошибка авторизации Telegraph: {e}")

    def publish(self, context: WriteupContext) -> str:
        try:
            token = self._get_token()
            if token:
                tg = Telegraph(access_token=token)
            else:
                tg = Telegraph()
                acc = tg.create_account(short_name=context.team or "writeup-automatizator")
                self._save_token(acc['access_token'])

            template = env.get_template("default.md")
            md_content = template.render(**context.model_dump())
            html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
            
            soup = BeautifulSoup(html_content, "html.parser")
            for h1 in soup.find_all("h1"):
                h1.name = "h3"
            for h2 in soup.find_all("h2"):
                h2.name = "h4"
            html_content = str(soup)

            response = tg.create_page(
                context.title,
                html_content=html_content,
                author_name=context.team
            )
            return response['url']
        except TelegraphException as e:
            raise ApiAuthError(f"Ошибка публикации Telegraph: {e}")

class TranslationService:
    def translate_context(self, context_data: dict, target_lang: str) -> dict:
        try:
            translator = GoogleTranslator(source='auto', target=target_lang)
            
            if context_data.get("title"):
                context_data["title"] = translator.translate(context_data["title"])
            if context_data.get("description"):
                context_data["description"] = translator.translate(context_data["description"])
                
            if "steps" in context_data:
                for step in context_data["steps"]:
                    if step.get("title"):
                        step["title"] = translator.translate(step["title"])
                    if step.get("description"):
                        step["description"] = translator.translate(step["description"])
                        
            return context_data
        except Exception as e:
            raise TranslationError(f"Ошибка перевода: {e}")
