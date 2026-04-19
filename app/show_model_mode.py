from app.config import settings

print("Model mode:", settings.model_mode)
print("Selected Ollama model:", settings.ollama_model)
print("RAG model:", settings.ollama_model_rag)
print("Coder model:", settings.ollama_model_coder)
print("General model:", settings.ollama_model_general)