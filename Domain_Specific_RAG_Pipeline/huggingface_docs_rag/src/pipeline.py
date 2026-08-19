from typing import Dict
from src.embeddings import EmbeddingService
from src.vector_store import MilvusVectorStore
from src.generator import LLMGenerator


class RAGPipeline:
    def __init__(
        self, 
        embedding_service: EmbeddingService, 
        vector_store: MilvusVectorStore, 
        generator: LLMGenerator
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.generator = generator

    def run(self, query: str, top_k: int = 3, max_new_tokens: int = 256) -> Dict:
        query_vector = self.embedding_service.embed_query(query)
        retrieved_docs = self.vector_store.search(query_vector, top_k=top_k)
        return self.generator.generate_answer(query, retrieved_docs, max_new_tokens=max_new_tokens)