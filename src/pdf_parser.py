from pathlib import Path

def extract_text_pymupdf(pdf_path: Path, max_pages: int = 12) -> str:
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf_path))
    pages = min(len(doc), max_pages)

    texts = []
    for i in range(pages):
        page = doc[i]
        texts.append(page.get_text("text"))

    doc.close()
    text = "\n".join(texts)

    # Basic cleanup
    text = text.replace("\x00", " ")
    return " ".join(text.split())