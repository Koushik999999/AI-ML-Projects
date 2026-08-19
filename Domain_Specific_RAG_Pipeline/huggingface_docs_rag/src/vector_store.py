from typing import List, Dict
from pymilvus import MilvusClient


class MilvusVectorStore:
    def __init__(self, uri: str, collection_name: str):
        self.client = MilvusClient(uri=uri)
        self.collection_name = collection_name

    def setup_collection(self, embedding_dim: int, drop_existing: bool = False):
        if self.client.has_collection(self.collection_name):
            if drop_existing:
                self.client.drop_collection(self.collection_name)
            else:
                return

        self.client.create_collection(
            collection_name=self.collection_name,
            dimension=embedding_dim,
            metric_type="IP",
            consistency_level="Strong",
        )

    def insert_chunks(self, chunks: List[Dict], embeddings: List[List[float]], batch_size: int = 100) -> int:
        total_inserted = 0
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_embeddings = embeddings[i : i + batch_size]
            
            batch_data = [
                {
                    "id": chunk["chunk_id"],
                    "vector": emb,
                    "text": chunk["text"],
                    "source": chunk["source"],
                }
                for chunk, emb in zip(batch_chunks, batch_embeddings)
            ]
            res = self.client.insert(collection_name=self.collection_name, data=batch_data)
            total_inserted += res.get("insert_count", 0)
        return total_inserted

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=top_k,
            search_params={"metric_type": "IP", "params": {}},
            output_fields=["text", "source"],
        )
        retrieved_docs = []
        search_results = results[0] if results and isinstance(results[0], list) else results
        for r in search_results:
            retrieved_docs.append({
                "text": r["entity"]["text"],
                "source": r["entity"]["source"],
                "score": r["distance"],
            })
        return retrieved_docs