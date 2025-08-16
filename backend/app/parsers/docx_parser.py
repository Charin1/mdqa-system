from .base import BaseParser, ParseResult
import docx

class DOCXParser(BaseParser):
    def parse(self, file_path: str) -> ParseResult:
        doc = docx.Document(file_path)
        full_text = "\n".join([para.text for para in doc.paragraphs if para.text])
        
        metadata = {
            "author": doc.core_properties.author,
            "title": doc.core_properties.title,
            "created": doc.core_properties.created.isoformat() if doc.core_properties.created else None,
            "modified": doc.core_properties.modified.isoformat() if doc.core_properties.modified else None,
        }
        return ParseResult(text=full_text, metadata=metadata)