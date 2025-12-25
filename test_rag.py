from services.pdf_loader import extract_text
from services.text_chunker import chunk_text
from services.gemini_client import get_embedding
from services.vector_store import store_chunks
from services.rag_pipeline import ask_question

with open("sample.pdf", "rb") as f:
    text = extract_text(f)

chunks = chunk_text(text)
embeddings = [get_embedding(chunk) for chunk in chunks]
store_chunks(chunks, embeddings)

answer = ask_question("What is this document about?")
print(answer)
