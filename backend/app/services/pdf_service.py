import fitz

def extract_pdf(file_bytes: bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        pages.append({"page": i + 1, "text": text.strip()})
    full = "\n\n".join(f"[Page {p['page']}]\n{p['text']}" for p in pages if p["text"])
    return full, len(doc), pages
