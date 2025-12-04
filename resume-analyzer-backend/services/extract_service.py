import tempfile
import os
from docx import Document
import pdfplumber

class ResumeExtractor:
    """Service to extract text from PDF or DOCX resumes."""

    def extract_from_file(self, upload_file) -> str:
        # Reset pointer in case framework already read something
        upload_file.file.seek(0)

        file_bytes = upload_file.file.read()
        if not file_bytes:
            raise ValueError("Uploaded file is empty or not received.")

        suffix = os.path.splitext(upload_file.filename)[1].lower()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            if suffix == ".pdf":
                return self._extract_pdf(tmp_path)
            elif suffix in (".docx", ".doc"):
                return self._extract_docx(tmp_path)
            else:
                with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
        finally:
            os.remove(tmp_path)

    def _extract_pdf(self, path: str) -> str:
        text = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                content = page.extract_text()
                if content:
                    text.append(content)
        return "\n".join(text)

    def _extract_docx(self, path: str) -> str:
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
