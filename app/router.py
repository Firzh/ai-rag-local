from pathlib import Path
from dataclasses import dataclass
from magika import Magika


@dataclass
class RouteResult:
    path: Path
    label: str
    mime_type: str
    group: str
    is_text: bool
    route: str


class FileRouter:
    def __init__(self) -> None:
        self.magika = Magika()

    def route_file(self, file_path: str | Path) -> RouteResult:
        path = Path(file_path)
        result = self.magika.identify_path(path)

        output = result.output
        label = output.label
        mime_type = output.mime_type
        group = output.group
        is_text = output.is_text
        suffix = path.suffix.lower()

        route = "unsupported"

        if suffix == ".pdf" or mime_type == "application/pdf" or label == "pdf":
            route = "pdf"

        elif suffix in {
            ".txt", ".md", ".rst", ".log",
            ".py", ".js", ".ts", ".tsx", ".jsx",
            ".html", ".css", ".json", ".csv",
            ".yml", ".yaml", ".xml", ".sql",
            ".java", ".php", ".go", ".rs", ".cpp", ".c", ".h"
        }:
            route = "text"

        elif group == "text" or is_text:
            route = "text"

        return RouteResult(
            path=path,
            label=label,
            mime_type=mime_type,
            group=group,
            is_text=is_text,
            route=route,
        )