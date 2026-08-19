from typing import List
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self.model.encode(
                batch, normalize_embeddings=True, show_progress_bar=False
            )
            all_embeddings.extend(embeddings.tolist())
        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        return self.model.encode([query], normalize_embeddings=True).tolist()[0]