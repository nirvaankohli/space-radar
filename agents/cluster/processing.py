import re
from bs4 import BeautifulSoup
from html import unescape


class TextProcessor:

    def __init__(self, text):

        self.NAV_WORDS = [
            "more tips & guides",
            "faq",
            "explore this section",
            "science activation",
            "framework for heliophysics education",
            "big idea 1.1",
            "skywatching home",
            "more tips & guides",
            "skywatching faq",
            "night sky network",
            "explore this section",
            "science activation",
            "framework for heliophysics education",
            "helio big idea",
        ]

        self.CREDIT_KEYWORDS = [
            "credits:",
            "image credit:",
            "text credit:",
            "photo by",
        ]

        self.FOOTER_HEADINGS = [
            "keep exploring",
            "discover more topics",
            "related terms",
            "additional resources",
            "lesson plans & educator guides",
            "interactive resources",
            "webinars & slide decks",
            "share details",
            "last updated",
            "location",
        ]

        self.DATE_TOKEN_RE = re.compile(
            r"(\d{1,2}\.\d{1,2}\.\d{2,4})|" r"(\d{1,2}-\d{1,2}\.\d{2,4})|" r"(\d{4})"
        )

        self.text = text

    def clean_html(self):

        soup = BeautifulSoup(self.text, "html.parser")

        for script_or_style in soup(["script", "style"]):

            script_or_style.decompose()

        cleaned_text = soup.get_text(separator="\n")

        self.text = unescape(cleaned_text)

        self.text = re.sub(r"\n+", "\n", self.text).strip()

    def looks_like_nav_line(self, line: str) -> bool:

        l = line.lower()

        # if the line doesn't contain punctuation and is reasonably long
        if "." not in l and len(l.split()) >= 6:

            for kw in self.NAV_WORDS:

                if kw in l:

                    return True

        return False

    def looks_like_credit_line(self, line: str) -> bool:

        l = line.lower()

        if any(kw in l for kw in self.CREDIT_KEYWORDS):

            return True

        if line.count("/") >= 3 and ("nasa" in l or "esa" in l or "jpl" in l):

            return True

        if "©" in line:

            return True

        return False

    def looks_like_footer_heading(self, line: str) -> bool:

        l = line.lower()

        if any(h in l for h in self.FOOTER_HEADINGS):

            return True

        if "@" in line and any(c.isdigit() for c in line):

            return True

        return False

    def clean_text(self, text=None) -> str:

        if not text:

            text = self.text

        else:

            self.text = text

        text = self.text

        if not self.text:

            return ""

        self.clean_html()

        rough_lines = re.split(r"[ \t]*[\n\r]+[ \t]*", self.text)

        if len(rough_lines) == 1:

            rough_lines = re.split(r"\s{2,}", text)

        cleaned_lines = []
        cut_rest = False

        for raw_line in rough_lines:

            line = raw_line.strip()

            if not line:

                continue

            if self.looks_like_footer_heading(line):

                cut_rest = True
                break

            if self.looks_like_nav_line(line):

                continue

            if self.looks_like_credit_line(line):

                continue

            line = re.sub(r"\b\d+\s*min read\b", "", line, flags=re.I)
            line = re.sub(r"\b\d+\s*min read\b", "", line, flags=re.I)

            if len(line) < 3:

                continue

            cleaned_lines.append(line)

        if not cleaned_lines:

            return ""

        cleaned = " ".join(cleaned_lines)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned
