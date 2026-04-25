from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import os


load_dotenv()


def env_str(key: str, default: str) -> str:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def env_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default

    try:
        return int(value.strip())
    except ValueError as exc:
        raise ValueError(f"Environment variable {key} harus berupa integer. Nilai saat ini: {value}") from exc


def env_float(key: str, default: float) -> float:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default

    try:
        return float(value.strip())
    except ValueError as exc:
        raise ValueError(f"Environment variable {key} harus berupa float. Nilai saat ini: {value}") from exc


def env_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_path(key: str, default: str) -> Path:
    return Path(env_str(key, default)).resolve()


@dataclass
class Settings:
    project_dir: Path
    inbox_dir: Path
    parsed_dir: Path
    chroma_dir: Path
    cache_dir: Path
    log_dir: Path
    graph_dir: Path
    indexes_dir: Path
    summaries_dir: Path
    memory_dir: Path
    evidence_dir: Path
    answers_dir: Path
    quality_dir: Path
    quality_db: Path

    models_base_dir: Path
    coder_model_dir: Path
    general_model_dir: Path

    collection_name: str
    embed_model: str

    chunk_size: int
    chunk_overlap: int
    top_k: int
    batch_size: int

    enable_graph: bool
    graph_max_terms: int
    graph_max_results: int
    graph_hops: int
    max_context_chars: int
    vector_weight: float
    graph_weight: float
    enable_fts: bool
    fts_top_k: int
    vector_top_k: int
    rerank_top_k: int
    compress_max_facts: int
    compress_max_quotes: int
    compress_max_quote_chars: int
    distance_cutoff: float
    score_cutoff: float

    model_mode: str
    ollama_model_rag: str
    ollama_model_coder: str
    ollama_model_general: str
    ollama_base_url: str
    ollama_model: str
    ollama_keep_alive: str

    openai_compat_base_url: str
    openai_compat_model: str
    openai_compat_api_key: str

    llm_provider: str
    llm_temperature: float
    llm_max_tokens: int
    save_prompts: bool

    answer_max_chars: int
    use_extractive_fallback: bool
    enable_quality_store: bool
    use_quality_examples: bool
    verification_audit_enabled: bool

    qwen_judge_enabled: bool
    qwen_judge_base_url: str
    qwen_judge_model: str
    qwen_judge_api_key: str
    qwen_judge_temperature: float
    qwen_judge_max_tokens: int
    qwen_judge_confidence_threshold: float

    def ensure_dirs(self) -> None:
        for path in [
            self.project_dir,
            self.inbox_dir,
            self.parsed_dir,
            self.chroma_dir,
            self.cache_dir,
            self.log_dir,
            self.graph_dir,
            self.indexes_dir,
            self.summaries_dir,
            self.memory_dir,
            self.evidence_dir,
            self.answers_dir,
            self.quality_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


settings = Settings(
    project_dir=env_path("RAG_PROJECT_DIR", "."),
    indexes_dir=env_path("RAG_INDEXES_DIR", "data/indexes"),
    summaries_dir=env_path("RAG_SUMMARIES_DIR", "data/summaries"),
    memory_dir=env_path("RAG_MEMORY_DIR", "data/memory"),
    evidence_dir=env_path("RAG_EVIDENCE_DIR", "data/evidence"),
    answers_dir=env_path("RAG_ANSWERS_DIR", "data/answers"),
    inbox_dir=env_path("RAG_INBOX_DIR", "data/inbox"),
    parsed_dir=env_path("RAG_PARSED_DIR", "data/parsed"),
    chroma_dir=env_path("RAG_CHROMA_DIR", "data/chroma"),
    cache_dir=env_path("RAG_CACHE_DIR", "data/cache"),
    log_dir=env_path("RAG_LOG_DIR", "data/logs"),
    graph_dir=env_path("RAG_GRAPH_DIR", "data/graph"),

    models_base_dir=env_path("RAG_MODELS_BASE_DIR", "models"),
    coder_model_dir=env_path("RAG_CODER_MODEL_DIR", ""),
    general_model_dir=env_path("RAG_GENERAL_MODEL_DIR", ""),

    collection_name=env_str(
        "RAG_COLLECTION",
        "rag_multilingual_minilm_l12_v2_384",
    ),
    embed_model=env_str(
        "RAG_EMBED_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ),

    chunk_size=env_int("RAG_CHUNK_SIZE", 900),
    chunk_overlap=env_int("RAG_CHUNK_OVERLAP", 120),
    top_k=env_int("RAG_TOP_K", 6),
    batch_size=env_int("RAG_BATCH_SIZE", 32),

    enable_graph=env_bool("RAG_ENABLE_GRAPH", True),
    graph_max_terms=env_int("RAG_GRAPH_MAX_TERMS", 12),
    graph_max_results=env_int("RAG_GRAPH_MAX_RESULTS", 10),
    graph_hops=env_int("RAG_GRAPH_HOPS", 1),
    max_context_chars=env_int("RAG_MAX_CONTEXT_CHARS", 6000),
    vector_weight=env_float("RAG_VECTOR_WEIGHT", 0.75),
    graph_weight=env_float("RAG_GRAPH_WEIGHT", 0.25),

    enable_fts=env_bool("RAG_ENABLE_FTS", True),
    fts_top_k=env_int("RAG_FTS_TOP_K", 8),
    vector_top_k=env_int("RAG_VECTOR_TOP_K", 6),
    rerank_top_k=env_int("RAG_RERANK_TOP_K", 5),
    compress_max_facts=env_int("RAG_COMPRESS_MAX_FACTS", 8),
    compress_max_quotes=env_int("RAG_COMPRESS_MAX_QUOTES", 5),
    compress_max_quote_chars=env_int("RAG_COMPRESS_MAX_QUOTE_CHARS", 450),
    distance_cutoff=env_float("RAG_DISTANCE_CUTOFF", 0.82),
    score_cutoff=env_float("RAG_SCORE_CUTOFF", 0.30),

    llm_provider=env_str("RAG_LLM_PROVIDER", "ollama"),
    model_mode=env_str("RAG_MODEL_MODE", "rag"),

    ollama_base_url=env_str("RAG_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
    ollama_model_rag=env_str("RAG_OLLAMA_MODEL_RAG", "qwen-rag-1.5b:latest"),
    ollama_model_coder=env_str("RAG_OLLAMA_MODEL_CODER", "qwen-coder-1.5b:latest"),
    ollama_model_general=env_str("RAG_OLLAMA_MODEL_GENERAL", "qwen-general:4b"),

    ollama_model=env_str("RAG_OLLAMA_MODEL", ""),
    ollama_keep_alive=env_str("RAG_OLLAMA_KEEP_ALIVE", "0"),

    openai_compat_base_url=env_str("RAG_OPENAI_COMPAT_BASE_URL", "http://127.0.0.1:8080/v1"),
    openai_compat_model=env_str("RAG_OPENAI_COMPAT_MODEL", "local-model"),
    openai_compat_api_key=env_str("RAG_OPENAI_COMPAT_API_KEY", "local"),

    llm_temperature=env_float("RAG_LLM_TEMPERATURE", 0.2),
    llm_max_tokens=env_int("RAG_LLM_MAX_TOKENS", 700),
    save_prompts=env_bool("RAG_SAVE_PROMPTS", True),
    answer_max_chars=env_int("RAG_ANSWER_MAX_CHARS", 1200),
    use_extractive_fallback=env_bool("RAG_USE_EXTRACTIVE_FALLBACK", True),
    quality_dir=env_path("RAG_QUALITY_DIR", "data/quality"),
    quality_db=env_path("RAG_QUALITY_DB", "data/quality/answer_quality.sqlite3"),
    enable_quality_store=env_bool("RAG_ENABLE_QUALITY_STORE", True),
    use_quality_examples=env_bool("RAG_USE_QUALITY_EXAMPLES", False),
    verification_audit_enabled=env_bool("RAG_VERIFICATION_AUDIT_ENABLED", True),

    qwen_judge_enabled=env_bool("RAG_QWEN_JUDGE_ENABLED", False),
    qwen_judge_base_url=env_str("RAG_QWEN_JUDGE_BASE_URL", env_str("RAG_OPENAI_COMPAT_BASE_URL", "http://127.0.0.1:8080/v1")),
    qwen_judge_model=env_str("RAG_QWEN_JUDGE_MODEL", "qwen2.5:4b-instruct"),
    qwen_judge_api_key=env_str("RAG_QWEN_JUDGE_API_KEY", env_str("RAG_OPENAI_COMPAT_API_KEY", "local")),
    qwen_judge_temperature=env_float("RAG_QWEN_JUDGE_TEMPERATURE", 0.0),
    qwen_judge_max_tokens=env_int("RAG_QWEN_JUDGE_MAX_TOKENS", 600),
    qwen_judge_confidence_threshold=env_float("RAG_QWEN_JUDGE_CONFIDENCE_THRESHOLD", 0.80),
)

if not settings.ollama_model:
    mode = settings.model_mode.lower().strip()

    if mode == "rag":
        settings.ollama_model = settings.ollama_model_rag
    elif mode == "coder":
        settings.ollama_model = settings.ollama_model_coder
    elif mode == "general":
        settings.ollama_model = settings.ollama_model_general
    else:
        raise ValueError(
            f"RAG_MODEL_MODE tidak dikenal: {settings.model_mode}. "
            "Gunakan: rag, coder, atau general."
        )

settings.ensure_dirs()
