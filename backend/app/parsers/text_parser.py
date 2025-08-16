from .base import BaseParser, ParseResult

class TextParser(BaseParser):
    def parse(self, file_path: str) -> ParseResult:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return ParseResult(text=text, metadata={})