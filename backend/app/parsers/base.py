from typing import Dict, Any

class ParseResult:
    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata

class BaseParser:
    def parse(self, file_path: str) -> ParseResult:
        raise NotImplementedError