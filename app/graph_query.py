import sys
from rich.console import Console
from rich.table import Table

from app.graph.mini_graph import MiniGraphQuery


console = Console()


def main() -> None:
    if len(sys.argv) < 2:
        console.print('[yellow]Gunakan:[/yellow] python -m app.graph_query "parser pdf"')
        return

    query = " ".join(sys.argv[1:])
    graph = MiniGraphQuery()
    result = graph.search(query, hops=1)

    console.print(f"\n[bold]Graph query:[/bold] {query}\n")

    seed_table = Table(title="Seed Nodes")
    seed_table.add_column("Type")
    seed_table.add_column("Label")
    seed_table.add_column("ID")

    for node in result["seed_nodes"]:
        seed_table.add_row(
            node.get("type", ""),
            node.get("label", ""),
            node.get("id", "")[:48],
        )

    console.print(seed_table)

    node_table = Table(title="Expanded Nodes")
    node_table.add_column("Type")
    node_table.add_column("Label")

    for node in result["nodes"][:30]:
        node_table.add_row(
            node.get("type", ""),
            node.get("label", ""),
        )

    console.print(node_table)

    edge_table = Table(title="Expanded Edges")
    edge_table.add_column("Type")
    edge_table.add_column("Source")
    edge_table.add_column("Target")

    for edge in result["edges"][:30]:
        edge_table.add_row(
            edge.get("type", ""),
            edge.get("source", "")[:36],
            edge.get("target", "")[:36],
        )

    console.print(edge_table)


if __name__ == "__main__":
    main()