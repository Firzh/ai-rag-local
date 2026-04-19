from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.config import settings
from app.embeddings.fastembedder import FastEmbedder
from app.db.chroma_store import ChromaStore
from app.db.fts_store import FTSStore
from app.graph.mini_graph import MiniGraphStore
from app.reranker import CandidateChunk, HeuristicReranker


class HybridRetriever:
    def __init__(self) -> None:
        self.embedder = FastEmbedder()
        self.chroma = ChromaStore()
        self.fts = FTSStore() if settings.enable_fts else None
        self.graph_store = MiniGraphStore()
        self.reranker = HeuristicReranker()

        self.nodes = self.graph_store.load_nodes()
        self.edges = self.graph_store.load_edges()

        self.node_by_id = {node["id"]: node for node in self.nodes}
        self.edges_by_node = defaultdict(list)

        for edge in self.edges:
            self.edges_by_node[edge["source"]].append(edge)
            self.edges_by_node[edge["target"]].append(edge)

    def vector_search(self, query: str, top_k: int | None = None) -> list[CandidateChunk]:
        query_embedding = self.embedder.embed_query(query)

        result = self.chroma.query(
            query_embedding=query_embedding,
            top_k=top_k or settings.vector_top_k,
        )

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        chunks = []

        for chroma_id, doc, meta, dist in zip(ids, documents, metadatas, distances):
            chunks.append(
                CandidateChunk(
                    chroma_id=chroma_id,
                    document=doc,
                    metadata=meta or {},
                    distance=float(dist),
                    source="vector",
                )
            )

        return chunks

    def fts_search(self, query: str, top_k: int | None = None) -> list[CandidateChunk]:
        if self.fts is None:
            return []

        rows = self.fts.search(query, top_k=top_k or settings.fts_top_k)

        return [
            CandidateChunk(
                chroma_id=row["chroma_id"],
                document=row["document"],
                metadata=row["metadata"],
                bm25_score=row["bm25_score"],
                source="fts",
            )
            for row in rows
        ]

    def _graph_chunk_neighbors(self, chroma_id: str, hops: int = 1) -> set[str]:
        seed_node_id = f"chunk:{chroma_id}"

        if seed_node_id not in self.node_by_id:
            return set()

        found_chunk_node_ids = set()
        frontier = {seed_node_id}
        visited = set()

        for _ in range(max(hops, 0)):
            next_frontier = set()

            for node_id in frontier:
                if node_id in visited:
                    continue

                visited.add(node_id)

                for edge in self.edges_by_node.get(node_id, []):
                    for candidate in [edge["source"], edge["target"]]:
                        if candidate.startswith("chunk:"):
                            found_chunk_node_ids.add(candidate)
                        if candidate not in visited:
                            next_frontier.add(candidate)

            frontier = next_frontier

        return {
            node_id.replace("chunk:", "", 1)
            for node_id in found_chunk_node_ids
            if node_id.startswith("chunk:")
        }

    def graph_expand(self, seed_chunks: list[CandidateChunk], hops: int | None = None) -> list[CandidateChunk]:
        hops = hops if hops is not None else settings.graph_hops

        graph_ids = set()

        for chunk in seed_chunks:
            graph_ids.update(
                self._graph_chunk_neighbors(chunk.chroma_id, hops=hops)
            )

        seed_ids = {chunk.chroma_id for chunk in seed_chunks}
        graph_ids = graph_ids - seed_ids

        if not graph_ids:
            return []

        result = self.chroma.get_by_ids(sorted(graph_ids))

        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])

        return [
            CandidateChunk(
                chroma_id=chroma_id,
                document=doc,
                metadata=meta or {},
                source="graph",
            )
            for chroma_id, doc, meta in zip(ids, documents, metadatas)
        ]

    def retrieve_candidates(self, query: str) -> list[CandidateChunk]:
        vector_chunks = self.vector_search(query)
        fts_chunks = self.fts_search(query)

        # Graph expand hanya dari kandidat kuat, bukan semua kandidat.
        seed_for_graph = vector_chunks[:3] + fts_chunks[:3]
        graph_chunks = self.graph_expand(seed_for_graph)

        return vector_chunks + fts_chunks + graph_chunks

    def retrieve(self, query: str) -> list[CandidateChunk]:
        candidates = self.retrieve_candidates(query)

        return self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=settings.rerank_top_k,
            distance_cutoff=settings.distance_cutoff,
            score_cutoff=settings.score_cutoff,
        )

    def build_context(self, query: str) -> str:
        chunks = self.retrieve(query)

        context_parts = []
        total_chars = 0

        for i, chunk in enumerate(chunks, start=1):
            source_name = chunk.metadata.get("source_name", "unknown")
            parser = chunk.metadata.get("parser", "unknown")
            chunk_index = chunk.metadata.get("chunk_index", "unknown")

            header = (
                f"[Context {i} | source={source_name} | parser={parser} | "
                f"chunk={chunk_index} | retrieval={chunk.source} | score={chunk.score:.4f}"
            )

            if chunk.distance is not None:
                header += f" | distance={chunk.distance:.4f}"

            if chunk.bm25_score is not None:
                header += f" | bm25={chunk.bm25_score:.4f}"

            header += "]"

            part = f"{header}\n{chunk.document.strip()}\n"

            if total_chars + len(part) > settings.max_context_chars:
                remaining = settings.max_context_chars - total_chars
                if remaining > 300:
                    context_parts.append(part[:remaining])
                break

            context_parts.append(part)
            total_chars += len(part)

        return "\n---\n".join(context_parts)