from config import settings
from src.ingestion import load_hf_docs, chunk_all_documents
from src.embeddings import EmbeddingService
from src.vector_store import MilvusVectorStore

def main():
    print("Loading documents...")
    docs = load_hf_docs(settings.DATASET_NAME, max_docs=settings.MAX_DOCS)
    
    print(f"Chunking {len(docs)} documents...")
    chunks = chunk_all_documents(
        docs, 
        chunk_size=settings.CHUNK_SIZE, 
        chunk_overlap=settings.CHUNK_OVERLAP
    )

    print(f"Generating embeddings for {len(chunks)} chunks...")
    embedding_svc = EmbeddingService(settings.EMBEDDING_MODEL_NAME)
    chunk_texts = [c["text"] for c in chunks]
    embeddings = embedding_svc.generate_embeddings(chunk_texts)

    print("Storing in Milvus...")
    vector_store = MilvusVectorStore(settings.MILVUS_DB_PATH, settings.COLLECTION_NAME)
    vector_store.setup_collection(settings.EMBEDDING_DIM, drop_existing=True)
    inserted = vector_store.insert_chunks(chunks, embeddings)
    print(f"Successfully indexed {inserted} records.")

if __name__ == "__main__":
    main()