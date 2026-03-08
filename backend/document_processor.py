import io
from pypdf import PdfReader
from docx import Document
from fastapi import UploadFile

async def extract_text_from_upload(file: UploadFile) -> str:
    text = ""
    file_bytes = await file.read()
    
    # Process the file cleanly in-memory without Disk I/O bounds
    file_stream = io.BytesIO(file_bytes)
    
    if file.filename.endswith(".pdf"):
        reader = PdfReader(file_stream)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    elif file.filename.endswith(".docx"):
        doc = Document(file_stream)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file.filename.endswith(".txt"):
        text = file_bytes.decode("utf-8")
    else:
        raise ValueError("Unsupported file type")
            
    return text.strip()
