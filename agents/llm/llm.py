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
            env_path = Path(ROOT_DIR) / ".env"
            load_dotenv(env_path)
            api_key = os.getenv("API_KEY", "")

            if not api_key:
                raise ValueError(
                    f"API_KEY not found in environment or .env file at {env_path}"
                )

        self.api_key = api_key
        self.api_url = "https://ai.hackclub.com/proxy/v1/chat/completions"
        self.model = "openai/gpt-5-mini"

    def load_rules(self):

        u = get_rules("user")
        s = get_rules("system")

        return s.rules, u.rules

    def request(self, story_format):

        system_rules, user_rules = self.load_rules()

        title = story_format.get("rep_title", "")

        articles_text = []
        for i, article in enumerate(story_format.get("articles", []), 1):
            article_info = f"Article {i}: {article.get('title', 'No title')} (Source: {article.get('source', 'Unknown')})"
            articles_text.append(article_info)

        articles_list = "\n".join(articles_text)
        rep_text = story_format.get("rep_text", "")[
            :2000
        ]  # Limit to avoid token limits

        user_content = f"""Primary Article Title: {title}
        
        Primary Article Text: {rep_text}

        Related Articles in this cluster:
        {articles_list}

        {user_rules}"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_rules},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.7,
        }

        try:
            r = requests.post(url=self.api_url, json=data, headers=headers, timeout=120)

            if r.status_code == 200:
                return r.json()
            else:
                print(f"API Error - Status: {r.status_code}")
                print(f"Response: {r.text}")
                raise Exception(
                    f"LLM request failed with status {r.status_code}: {r.text}"
                )

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise Exception(f"Request error: {e}")


if __name__ == "__main__":


    from pathlib import Path

    db_dir = Path(__file__).parent.parent.parent / "data" / "db"

    client = LLMClient("use_local")

    story_canidate_path = db_dir / "story_candidates.json"

    import json

    with open(story_canidate_path, "r", encoding="utf-8") as f:

        story_candidates = json.load(f)

    f = client.request(story_candidates[0])

    print(json.loads(f["choices"][0]["message"]["content"]))
