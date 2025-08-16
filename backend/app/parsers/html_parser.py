from .base import BaseParser, ParseResult
from bs4 import BeautifulSoup

class HTMLParser(BaseParser):
    def parse(self, file_path: str) -> ParseResult:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
            
        text = soup.get_text(separator="\n", strip=True)
        title = soup.title.string if soup.title else None
        metadata = {"title": title}
        return ParseResult(text=text, metadata=metadata)