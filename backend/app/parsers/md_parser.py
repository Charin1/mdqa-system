from .base import BaseParser, ParseResult
import markdown
from bs4 import BeautifulSoup

class MDParser(BaseParser):
    def parse(self, file_path: str) -> ParseResult:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            md_text = f.read()
        
        html = markdown.markdown(md_text)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        
        # Markdown has no standard metadata, so we return an empty dict
        return ParseResult(text=text, metadata={})