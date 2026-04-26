from rich.console import Console
from rich.table import Table

from app.config import settings
from app.db.chroma_store import ChromaStore
from app.graph.mini_graph import MiniGraphBuilder, MiniGraphStore


console = Console()


def main() -> None:
    if not settings.enable_graph:
        console.print("[yellow]Graph disabled. Set RAG_ENABLE_GRAPH=true in .env[/yellow]")
        return

    store = ChromaStore()
    graph_store = MiniGraphStore()
    builder = MiniGraphBuilder(store)

    nodes, edges = builder.build()
    summary = graph_store.save(nodes, edges)

    console.print("[bold green]Mini graph built.[/bold green]")
    console.print(f"Nodes: {summary['total_nodes']}")
    console.print(f"Edges: {summary['total_edges']}")
    console.print(f"Nodes path: {summary['nodes_path']}")
    console.print(f"Edges path: {summary['edges_path']}")

    node_table = Table(title="Node Types")
    node_table.add_column("Type")
    node_table.add_column("Count", justify="right")

    for node_type, count in summary["node_types"].items():
        node_table.add_row(node_type, str(count))

    console.print(node_table)

    edge_table = Table(title="Edge Types")
    edge_table.add_column("Type")
    edge_table.add_column("Count", justify="right")

    for edge_type, count in summary["edge_types"].items():
        edge_table.add_row(edge_type, str(count))

    console.print(edge_table)


if __name__ == "__main__":
    main()