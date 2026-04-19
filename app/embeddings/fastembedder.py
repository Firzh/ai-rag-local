import warnings

from fastembed import TextEmbedding
from app.config import settings


warnings.filterwarnings(
    "ignore",
    message=r"The model .* now uses mean pooling instead of CLS embedding.*",
    category=UserWarning,
)


class FastEmbedder:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embed_model
        self.model = TextEmbedding(model_name=self.model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = list(self.model.embed(texts))
        return [v.tolist() for v in vectors]

    def embed_query(self, text: str) -> list[float]:
        vector = list(self.model.embed([text]))[0]
        return vector.tolist()