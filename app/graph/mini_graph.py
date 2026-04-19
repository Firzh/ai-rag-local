from __future__ import annotations

import json
import re
import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import settings


STOPWORDS = {
    "yang", "dan", "atau", "dari", "dengan", "untuk", "pada", "dalam", "adalah",
    "ini", "itu", "ke", "di", "sebagai", "oleh", "karena", "maka", "akan",
    "the", "and", "or", "from", "with", "for", "this", "that", "into", "are",
    "was", "were", "been", "have", "has", "had", "not", "but", "can", "could",
    "lorem", "ipsum", "dolor", "sit", "amet", "nulla", "sed", "quam", "erat",
    "consectetuer", "adipiscing", "phasellus", "curabitur", "vestibulum",
"pellentesque", "suspendisse", "vivamus", "maecenas", "morbi",
"natoque", "penatibus", "magnis", "parturient", "montes", "nascetur",
"ridiculus", "scelerisque", "condimentum", "commodo", "convallis",
}


@dataclass
class GraphNode:
    id: str
    type: str
    label: str
    properties: dict[str, Any]


@dataclass
class GraphEdge:
    id: str
    source: str
    target: str
    type: str
    properties: dict[str, Any]


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def normalize_term(term: str) -> str:
    term = term.strip().lower()
    term = re.sub(r"[^a-zA-Z0-9_\- ]+", "", term)
    term = re.sub(r"\s+", " ", term)
    return term.strip()


def make_node_id(node_type: str, raw: str) -> str:
    return f"{node_type}:{stable_hash(raw)[:24]}"


def make_edge_id(source: str, edge_type: str, target: str) -> str:
    return f"edge:{stable_hash(source + '|' + edge_type + '|' + target)[:32]}"


def extract_terms(text: str, max_terms: int = 12) -> list[str]:
    # Cocok untuk teks biasa dan kode sederhana.
    raw_terms = re.findall(r"[A-Za-z_][A-Za-z0-9_\-]{3,}", text)

    cleaned_terms = []
    for term in raw_terms:
        term = normalize_term(term)
        if not term:
            continue
        if term in STOPWORDS:
            continue
        if len(term) < 4:
            continue
        if term.isdigit():
            continue
        cleaned_terms.append(term)

    counter = Counter(cleaned_terms)
    return [term for term, _ in counter.most_common(max_terms)]


def detect_page_from_chunk(text: str) -> str | None:
    match = re.search(r"--- PAGE\s+(\d+)\s+---", text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1)


class MiniGraphStore:
    def __init__(self) -> None:
        self.graph_dir = settings.graph_dir
        self.graph_dir.mkdir(parents=True, exist_ok=True)

        self.nodes_path = self.graph_dir / "nodes.jsonl"
        self.edges_path = self.graph_dir / "edges.jsonl"
        self.summary_path = self.graph_dir / "graph_summary.json"

    def save(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> dict[str, Any]:
        unique_nodes = {}
        for node in nodes:
            unique_nodes[node.id] = node

        unique_edges = {}
        for edge in edges:
            unique_edges[edge.id] = edge

        final_nodes = list(unique_nodes.values())
        final_edges = list(unique_edges.values())

        with self.nodes_path.open("w", encoding="utf-8") as f:
            for node in final_nodes:
                f.write(json.dumps(node.__dict__, ensure_ascii=False) + "\n")

        with self.edges_path.open("w", encoding="utf-8") as f:
            for edge in final_edges:
                f.write(json.dumps(edge.__dict__, ensure_ascii=False) + "\n")

        summary = self._build_summary(final_nodes, final_edges)

        with self.summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return summary

    def load_nodes(self) -> list[dict[str, Any]]:
        if not self.nodes_path.exists():
            return []

        nodes = []
        with self.nodes_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    nodes.append(json.loads(line))
        return nodes

    def load_edges(self) -> list[dict[str, Any]]:
        if not self.edges_path.exists():
            return []

        edges = []
        with self.edges_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    edges.append(json.loads(line))
        return edges

    def _build_summary(
        self,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
    ) -> dict[str, Any]:
        node_types = Counter(node.type for node in nodes)
        edge_types = Counter(edge.type for edge in edges)

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": dict(node_types),
            "edge_types": dict(edge_types),
            "nodes_path": str(self.nodes_path),
            "edges_path": str(self.edges_path),
        }


class MiniGraphBuilder:
    def __init__(self, chroma_store) -> None:
        self.store = chroma_store

    def build(self) -> tuple[list[GraphNode], list[GraphEdge]]:
        count = self.store.count()

        if count == 0:
            return [], []

        result = self.store.collection.get(
            include=["documents", "metadatas"],
            limit=count,
            offset=0,
        )

        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        chunks_by_doc: dict[str, list[tuple[int, str]]] = defaultdict(list)

        for chunk_id, text, metadata in zip(ids, documents, metadatas):
            metadata = metadata or {}

            source_name = metadata.get("source_name", "unknown")
            source_path = metadata.get("source_path", "")
            document_hash = metadata.get("document_hash", source_path or source_name)
            parser = metadata.get("parser", "unknown_parser")
            mime_type = metadata.get("mime_type", "unknown_mime")
            chunk_index = int(metadata.get("chunk_index", 0))

            doc_node_id = f"doc:{document_hash}"
            parser_node_id = make_node_id("parser", parser)
            type_node_id = make_node_id("filetype", mime_type)
            chunk_node_id = f"chunk:{chunk_id}"

            nodes.append(
                GraphNode(
                    id=doc_node_id,
                    type="document",
                    label=source_name,
                    properties={
                        "source_name": source_name,
                        "source_path": source_path,
                        "document_hash": document_hash,
                    },
                )
            )

            nodes.append(
                GraphNode(
                    id=parser_node_id,
                    type="parser",
                    label=parser,
                    properties={"parser": parser},
                )
            )

            nodes.append(
                GraphNode(
                    id=type_node_id,
                    type="filetype",
                    label=mime_type,
                    properties={"mime_type": mime_type},
                )
            )

            nodes.append(
                GraphNode(
                    id=chunk_node_id,
                    type="chunk",
                    label=f"{source_name}#chunk-{chunk_index}",
                    properties={
                        "source_name": source_name,
                        "source_path": source_path,
                        "document_hash": document_hash,
                        "chunk_index": chunk_index,
                        "text_preview": text[:500],
                    },
                )
            )

            edges.append(
                GraphEdge(
                    id=make_edge_id(doc_node_id, "PARSED_BY", parser_node_id),
                    source=doc_node_id,
                    target=parser_node_id,
                    type="PARSED_BY",
                    properties={},
                )
            )

            edges.append(
                GraphEdge(
                    id=make_edge_id(doc_node_id, "HAS_FILETYPE", type_node_id),
                    source=doc_node_id,
                    target=type_node_id,
                    type="HAS_FILETYPE",
                    properties={},
                )
            )

            edges.append(
                GraphEdge(
                    id=make_edge_id(doc_node_id, "CONTAINS", chunk_node_id),
                    source=doc_node_id,
                    target=chunk_node_id,
                    type="CONTAINS",
                    properties={"chunk_index": chunk_index},
                )
            )

            page_number = detect_page_from_chunk(text)

            if page_number:
                page_node_id = f"page:{document_hash}:{page_number}"

                nodes.append(
                    GraphNode(
                        id=page_node_id,
                        type="page",
                        label=f"{source_name} page {page_number}",
                        properties={
                            "source_name": source_name,
                            "document_hash": document_hash,
                            "page": page_number,
                        },
                    )
                )

                edges.append(
                    GraphEdge(
                        id=make_edge_id(doc_node_id, "HAS_PAGE", page_node_id),
                        source=doc_node_id,
                        target=page_node_id,
                        type="HAS_PAGE",
                        properties={"page": page_number},
                    )
                )

                edges.append(
                    GraphEdge(
                        id=make_edge_id(page_node_id, "CONTAINS", chunk_node_id),
                        source=page_node_id,
                        target=chunk_node_id,
                        type="CONTAINS",
                        properties={"chunk_index": chunk_index},
                    )
                )

            terms = extract_terms(text, max_terms=settings.graph_max_terms)

            for term in terms:
                term_node_id = make_node_id("term", term)

                nodes.append(
                    GraphNode(
                        id=term_node_id,
                        type="term",
                        label=term,
                        properties={"term": term},
                    )
                )

                edges.append(
                    GraphEdge(
                        id=make_edge_id(chunk_node_id, "MENTIONS", term_node_id),
                        source=chunk_node_id,
                        target=term_node_id,
                        type="MENTIONS",
                        properties={},
                    )
                )

            chunks_by_doc[document_hash].append((chunk_index, chunk_node_id))

        for document_hash, chunk_pairs in chunks_by_doc.items():
            sorted_chunks = sorted(chunk_pairs, key=lambda x: x[0])

            for (_, current_id), (_, next_id) in zip(sorted_chunks, sorted_chunks[1:]):
                edges.append(
                    GraphEdge(
                        id=make_edge_id(current_id, "NEXT_CHUNK", next_id),
                        source=current_id,
                        target=next_id,
                        type="NEXT_CHUNK",
                        properties={"document_hash": document_hash},
                    )
                )

        return nodes, edges


class MiniGraphQuery:
    def __init__(self) -> None:
        self.store = MiniGraphStore()
        self.nodes = self.store.load_nodes()
        self.edges = self.store.load_edges()

        self.node_by_id = {node["id"]: node for node in self.nodes}
        self.adjacency = defaultdict(list)

        for edge in self.edges:
            self.adjacency[edge["source"]].append(edge)
            self.adjacency[edge["target"]].append(edge)

    def _score_node(self, node: dict[str, Any], query_terms: set[str], raw_query: str) -> int:
        label = normalize_term(str(node.get("label", "")))
        node_type = node.get("type", "")
        props = node.get("properties", {})
        preview = normalize_term(str(props.get("text_preview", "")))

        score = 0

        if not query_terms:
            return score

        # Exact label match paling kuat.
        if raw_query == label:
            score += 20

        # Semua term query muncul di label.
        if all(term in label for term in query_terms):
            score += 10

        # Sebagian term query muncul di label.
        for term in query_terms:
            if term == label:
                score += 8
            elif term in label:
                score += 4
            elif term in preview:
                score += 1

        # Prioritaskan node struktural dibanding term.
        type_weight = {
            "document": 5,
            "chunk": 4,
            "page": 3,
            "parser": 2,
            "filetype": 2,
            "term": 1,
        }

        score += type_weight.get(node_type, 0)

        # Hindari parser umum ikut menang hanya karena query mengandung "parser".
        if node_type == "parser" and "parser" in query_terms and len(query_terms) > 1:
            label_terms = set(label.split())
            if not (query_terms - {"parser"}) & label_terms:
                score -= 5

        return max(score, 0)

    def search(self, query: str, limit: int | None = None, hops: int = 1) -> dict[str, Any]:
        limit = limit or settings.graph_max_results
        raw_query = normalize_term(query)

        query_terms = {
            normalize_term(term)
            for term in re.findall(r"[A-Za-z_][A-Za-z0-9_\-]{2,}", query)
        }
        query_terms = {term for term in query_terms if term and term not in STOPWORDS}

        scored = []

        for node in self.nodes:
            score = self._score_node(node, query_terms, raw_query)
            if score > 0:
                scored.append((score, node))

        scored.sort(key=lambda x: x[0], reverse=True)
        seed_nodes = [node for _, node in scored[:limit]]

        expanded_node_ids = set()
        expanded_edge_ids = set()
        expanded_edges = []

        frontier = {node["id"] for node in seed_nodes}

        for _ in range(max(hops, 0)):
            next_frontier = set()

            for node_id in frontier:
                expanded_node_ids.add(node_id)

                for edge in self.adjacency.get(node_id, []):
                    edge_id = edge.get("id")

                    if edge_id not in expanded_edge_ids:
                        expanded_edges.append(edge)
                        expanded_edge_ids.add(edge_id)

                    expanded_node_ids.add(edge["source"])
                    expanded_node_ids.add(edge["target"])

                    if edge["source"] != node_id:
                        next_frontier.add(edge["source"])
                    if edge["target"] != node_id:
                        next_frontier.add(edge["target"])

            frontier = next_frontier

        expanded_nodes = [
            self.node_by_id[node_id]
            for node_id in expanded_node_ids
            if node_id in self.node_by_id
        ]

        return {
            "query": query,
            "seed_nodes": seed_nodes,
            "nodes": expanded_nodes,
            "edges": expanded_edges,
        }