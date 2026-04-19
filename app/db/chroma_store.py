import chromadb
from app.config import settings


class ChromaStore:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={
                "hnsw:space": "cosine",
                "embedding_model": settings.embed_model,
                "description": "Local RAG collection using FastEmbed multilingual MiniLM",
            },
        )
    
    def get_by_ids(self, ids: list[str]) -> dict:
        if not ids:
            return {"ids": [], "documents": [], "metadatas": []}

        return self.collection.get(
            ids=ids,
            include=["documents", "metadatas"],
        )

    def upsert_chunks(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
    ) -> dict:
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k or settings.top_k,
            include=["documents", "metadatas", "distances"],
        )

    def delete_by_document_hash(self, document_hash: str) -> None:
        self.collection.delete(
            where={"document_hash": document_hash}
        )

    def delete_by_source_path(self, source_path: str) -> None:
        self.collection.delete(
            where={"source_path": source_path}
        )

    def count(self) -> int:
        return self.collection.count()