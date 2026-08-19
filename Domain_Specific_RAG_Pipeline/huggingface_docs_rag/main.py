from config import settings
from src.embeddings import EmbeddingService
from src.vector_store import MilvusVectorStore
from src.generator import LLMGenerator
from src.pipeline import RAGPipeline

def main():
    embedding_svc = EmbeddingService(settings.EMBEDDING_MODEL_NAME)
    vector_store = MilvusVectorStore(settings.MILVUS_DB_PATH, settings.COLLECTION_NAME)
    generator = LLMGenerator(settings.LLM_MODEL_NAME, settings.PROMPT_TEMPLATE)

    rag = RAGPipeline(
        embedding_service=embedding_svc,
        vector_store=vector_store,
        generator=generator,
    )

    sample_queries = [
        "What is the Trainer class in transformers?",
        "How do I load a dataset from HuggingFace?",
        "What is Gradio used for?",
    ]

    for q in sample_queries:
        print(f"\n{'='*60}\nQ: {q}")
        res = rag.run(q, top_k=3)
        print(f"A: {res['answer']}")

if __name__ == "__main__":
    main()