import chromadb
from app.config import settings

client = chromadb.PersistentClient(path=str(settings.chroma_dir))

try:
    client.delete_collection("rag_test")
    print("Deleted collection: rag_test")
except Exception as exc:
    print(f"Skip: {exc}")