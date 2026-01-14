import fitz  # PyMuPDF

def extract_pages(file):
    """
    Returns a list of dicts: [{"page": 1, "text": "..."}, ...]
    page is 1-based (Page 1, Page 2, ...)
    """
    doc = fitz.open(stream=file.read(), filetype="pdf")
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        pages.append({"page": i, "text": text})
    return pages


def extract_text(file):
    # kept for compatibility if any old code still uses it
    pages = extract_pages(file)
    return "\n".join([p["text"] for p in pages])
