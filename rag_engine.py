import json
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from openai import OpenAI

from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.openai_like import OpenAILike

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE_FILE = BASE_DIR / "sample.txt"
DEFAULT_STORAGE_DIR = BASE_DIR / ".rag_storage"
DEFAULT_EVALUATION_FILE = BASE_DIR / "evaluation_set.json"
SUPPORTED_SOURCE_SUFFIXES = {".txt", ".md"}

SYSTEM_PROMPT = """
You are a production-grade RAG assistant.

RULES:
- Use the provided context to answer factual Nepal-related questions.
- If the context does not contain the answer, say you do not know from the knowledge base.
- Be concise and factual.
- Include a brief source note when possible.
"""

DEFAULT_EVALUATION_SET = [
    {
        "question": "What country is Nepal?",
        "expected_keywords": ["South Asia", "country"],
        "expected_sources": ["sample.txt"],
    },
    {
        "question": "What is the capital of Nepal?",
        "expected_keywords": ["Kathmandu"],
        "expected_sources": ["sample.txt"],
    },
    {
        "question": "Where is Mount Everest located?",
        "expected_keywords": ["Mount Everest", "Nepal"],
        "expected_sources": ["sample.txt"],
    },
    {
        "question": "What is Pokhara known for?",
        "expected_keywords": ["Pokhara", "tourist destination"],
        "expected_sources": ["sample.txt"],
    },
    {
        "question": "How many provinces does Nepal have?",
        "expected_keywords": ["7 provinces"],
        "expected_sources": ["sample.txt"],
    },
]


class RAGEngine:
    """Encapsulates embeddings, index, retriever, and the Groq chat client."""

    def __init__(self, rebuild_index: bool = False) -> None:
        self.groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")

        if not self.groq_api_key:
            raise ValueError("Missing GROQ_API_KEY in environment")
        if not self.google_api_key:
            raise ValueError("Missing GOOGLE_API_KEY in environment")

        # Groq client (OpenAI-compatible). Also used for Whisper STT and
        # Orpheus TTS in the voice agent / FastAPI app.
        self.client = OpenAI(
            api_key=self.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

        # Embeddings (Gemini)
        Settings.embed_model = GoogleGenAIEmbedding(
            model_name="models/gemini-embedding-2",
            api_key=self.google_api_key,
        )

        # LLM (Groq, via OpenAI-compatible endpoint)
        Settings.llm = OpenAILike(
            model="llama-3.3-70b-versatile",
            api_base="https://api.groq.com/openai/v1",
            api_key=self.groq_api_key,
            is_chat_model=True,
        )

        self.storage_dir = DEFAULT_STORAGE_DIR
        self.source_files = self._discover_source_files()
        self.index = self._load_or_build_index(rebuild_index=rebuild_index)
        self.retriever = self.index.as_retriever(similarity_top_k=3)

    def _discover_source_files(self) -> list[Path]:
        configured_source = os.getenv("RAG_SOURCE_PATH")
        if configured_source:
            source_path = Path(configured_source)
            if source_path.is_file() and source_path.suffix.lower() in SUPPORTED_SOURCE_SUFFIXES:
                return [source_path]
            if source_path.is_dir():
                files = [
                    path
                    for path in sorted(source_path.rglob("*"))
                    if path.is_file() and path.suffix.lower() in SUPPORTED_SOURCE_SUFFIXES
                ]
                if files:
                    return files
            raise FileNotFoundError(f"No supported source files found at {source_path}")

        candidates: list[Path] = []
        for folder_name in ("docs", "data"):
            folder = BASE_DIR / folder_name
            if folder.exists() and folder.is_dir():
                candidates.extend(
                    path
                    for path in sorted(folder.rglob("*"))
                    if path.is_file() and path.suffix.lower() in SUPPORTED_SOURCE_SUFFIXES
                )

        if candidates:
            return candidates

        return [DEFAULT_SOURCE_FILE]

    def _load_documents(self) -> list[Document]:
        documents: list[Document] = []
        for file_path in self.source_files:
            content = file_path.read_text(encoding="utf-8")
            documents.append(
                Document(
                    text=content,
                    metadata={"source": file_path.name, "path": str(file_path)},
                )
            )
        return documents

    def _load_or_build_index(self, rebuild_index: bool = False) -> VectorStoreIndex:
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        has_persisted_index = any(self.storage_dir.iterdir())
        if has_persisted_index and not rebuild_index:
            storage_context = StorageContext.from_defaults(persist_dir=str(self.storage_dir))
            return load_index_from_storage(storage_context)

        documents = self._load_documents()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=str(self.storage_dir))
        return index

    def retrieve_context(self, query: str) -> tuple[str, list[dict[str, str]]]:
        """Return concatenated text of the retrieved nodes and citations."""
        nodes = self.retriever.retrieve(query)
        if not nodes:
            return "No relevant information found.", []

        context_parts: list[str] = []
        citations: list[dict[str, str]] = []
        seen_sources: set[str] = set()

        for node_with_score in nodes:
            node = node_with_score.node
            source = node.metadata.get("source") or node.metadata.get("path") or "unknown source"
            snippet = " ".join(node.get_content().split())
            context_parts.append(f"[{source}] {snippet}")

            if source not in seen_sources:
                citations.append({"source": source, "snippet": snippet[:180]})
                seen_sources.add(source)

        return "\n".join(context_parts), citations

    @staticmethod
    def _append_sources(answer: str, citations: list[dict[str, str]]) -> str:
        if not citations:
            return answer

        source_lines = ["", "Sources:"]
        for citation in citations:
            source_lines.append(f"- {citation['source']}: {citation['snippet']}")
        return answer.rstrip() + "\n" + "\n".join(source_lines)

    def chat(self, user_input: str, history: list[dict] | None = None) -> str:
        """
        Run one RAG turn.

        `history` is a list of {"role": ..., "content": ...} dicts of
        PAST turns only (do not include the current user_input - it is
        added internally along with retrieved context).
        """
        history = history or []
        context, citations = self.retrieve_context(user_input)

        prompt = f"""Context from knowledge base:
{context}

User question:
{user_input}"""

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
        )

        answer = response.choices[0].message.content or ""
        return self._append_sources(answer, citations)

    def run_evaluation(self, evaluation_file: Path | None = None) -> list[dict[str, Any]]:
        evaluation_path = evaluation_file or DEFAULT_EVALUATION_FILE
        if evaluation_path.exists():
            evaluation_set = json.loads(evaluation_path.read_text(encoding="utf-8"))
        else:
            evaluation_set = DEFAULT_EVALUATION_SET

        results: list[dict[str, Any]] = []
        for case in evaluation_set:
            context, citations = self.retrieve_context(case["question"])
            context_lower = context.lower()
            citation_sources = {citation["source"].lower() for citation in citations}

            expected_keywords = [keyword.lower() for keyword in case.get("expected_keywords", [])]
            expected_sources = [source.lower() for source in case.get("expected_sources", [])]

            keyword_hits = [keyword for keyword in expected_keywords if keyword in context_lower]
            source_hits = [source for source in expected_sources if source in citation_sources]

            results.append(
                {
                    "question": case["question"],
                    "keyword_hits": keyword_hits,
                    "source_hits": source_hits,
                    "passed": bool(keyword_hits) and bool(source_hits),
                }
            )

        return results
