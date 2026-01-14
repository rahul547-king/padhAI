def chunk_pages(pages, chunk_size=500, overlap=60):
    """
    pages: list of {"page": int, "text": str}

    Returns:
      chunks: [str, ...]
      metadatas: [{"page": int, "chunk_index": int}, ...]
    """
    chunks = []
    metadatas = []

    for p in pages:
        words = (p["text"] or "").split()
        if not words:
            continue

        page_no = p["page"]
        chunk_index = 0

        step = max(1, chunk_size - overlap)
        for i in range(0, len(words), step):
            chunk_words = words[i:i + chunk_size]
            if not chunk_words:
                continue

            chunk_text = " ".join(chunk_words).strip()
            if chunk_text:
                chunks.append(chunk_text)
                metadatas.append({
                    "page": int(page_no),
                    "chunk_index": int(chunk_index)
                })
                chunk_index += 1

    return chunks, metadatas
