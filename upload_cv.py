from services.document_service import extract_pdf_text
from services.rag_service import save_document_to_db


# 🔹 YOUR PDF PATH
file_path = r".\uploads\Akila Abenayaka_Software Engineer_CV.pdf"


# 🔹 Extract text from PDF
text = extract_pdf_text(file_path)

print("[OK] PDF text extracted")


# 🔹 Save into PostgreSQL vector DB
save_document_to_db(text)

print("[OK] Document saved into database")