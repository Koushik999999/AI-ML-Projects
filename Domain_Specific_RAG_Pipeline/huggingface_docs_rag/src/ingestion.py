from typing import List, Dict
from datasets import load_dataset


def load_hf_docs(dataset_name: str, max_docs: int = None) -> List[Dict[str, str]]:
    dataset = load_dataset(dataset_name, split="train")
    documents = [{"text": item["text"], "source": item["source"]} for item in dataset]
    if max_docs:
        documents = documents[:max_docs]
    return documents


def chunk_document(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    step = chunk_size - chunk_overlap
    if step <= 0:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start : start + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
        start += step
    return chunks


def chunk_all_documents(
    documents: List[Dict[str, str]], 
    chunk_size: int = 1000, 
    chunk_overlap: int = 200
) -> List[Dict]:
    all_chunks = []
    chunk_id = 0
    for document in documents:
        chunks = chunk_document(
            document["text"], chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        for chunk in chunks:
            all_chunks.append({
                "chunk_id": chunk_id,
                "text": chunk,
                "source": document["source"],
            })
            chunk_id += 1
    return all_chunks