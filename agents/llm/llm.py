from pathlib import Path
import requests
from dotenv import load_dotenv
import os

AGENT_DIR = Path(__file__).parent.parent
RULES_DIR = AGENT_DIR / "rules"
ROOT_DIR = AGENT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
DB_DIR = DATA_DIR / "db"


class get_rules:

    def __init__(self, rule_name: str):

        self.rule_name = rule_name
        self.rule_path = RULES_DIR / f"{self.rule_name}.txt"
        self.rules = self.load_rules()

    def load_rules(self) -> str:

        if not self.rule_path.exists():

            raise FileNotFoundError(f"Rule file not found: {self.rule_path}")

        return self.rule_path.read_text(encoding="utf-8")


class LLMClient:

    def __init__(self, api_key: str):

        if api_key == "use_local":

            load_dotenv()
            api_key = os.getenv("API_KEY", "")

        self.api_key = api_key
        self.api_url = "https://ai.hackclub.com/proxy/v1/chat/completions"
        self.model = "openai/gpt-5-mini"

    def load_rules():

        u = get_rules("user")
        s = get_rules("system")

        return s.rules, u.rules

    def request(self, story_format):

        system_rules, user_rules = self.load_rules()

        title = story_format.get("rep_title", "")
        
        articles = []

        for i in story_format.get("articles", []):
            articles.append(
                {
                    "title": i.get("title", ""),
                    "source": i.get("source", ""),
                }
            )


        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_rules},
                {
                    "role": "user",
                    "content": user_rules.format(title=title, articles=article_format),
                },
            ],
            "temperature": 0.7,
        }
