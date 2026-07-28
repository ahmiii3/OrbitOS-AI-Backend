import io
from fastapi import UploadFile
from pypdf import PdfReader
from docx import Document

class DocumentParser:
    """Service to parse raw files into text."""
    
    @staticmethod
    async def extract_text(file: UploadFile, content: bytes) -> str:
        """Extracts text from PDF, DOCX, or TXT."""
        filename = file.filename.lower()
        
        if filename.endswith(".pdf"):
            return DocumentParser._parse_pdf(content)
        elif filename.endswith(".docx"):
            return DocumentParser._parse_docx(content)
        elif filename.endswith(".txt") or filename.endswith(".md"):
            return content.decode("utf-8")
        else:
            raise ValueError("Unsupported file format. Please upload PDF, DOCX, or TXT.")

    @staticmethod
    def _parse_pdf(content: bytes) -> str:
        pdf = PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text

    @staticmethod
    def _parse_docx(content: bytes) -> str:
        doc = Document(io.BytesIO(content))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
