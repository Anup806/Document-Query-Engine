"""
This module exposes a single `RAGEngine` class that:
  - configures the embedding model (Gemini) and LLM (Groq via OpenAILike)
  - builds an in-memory vector index over the sample.txt file
  

Loading models and building the index is expensive, so create ONE
RAGEngine instance per process and reuse it.
"""

import os
from dotenv import load_dotenv

from openai import OpenAI

from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.openai_like import OpenAILike

load_dotenv()

SYSTEM_PROMPT = """
You are a production-grade RAG assistant.

RULES:
- Use the provided context to answer factual AI engineer.
- If the context does not contain the answer, respond: "I do not know from the knowledge base."
- Be concise, factual, and avoid speculation.
- Always prioritize retrieved context over pre-trained knowledge.
- Do not hallucinate or invent information outside the knowledge base.
- Format answers in clear, recruiter-friendly language when technical explanations are required.
"""




class RAGEngine:
    """Encapsulates embeddings, index, retriever, and the Groq chat client."""

    def __init__(self) -> None:
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

        self.index = self._build_index()
        self.retriever = self.index.as_retriever()

    @staticmethod
    def _build_index() -> VectorStoreIndex:
        with open("sample.txt", "r", encoding="utf-8") as f:
            content = f.read()
        documents = [Document(text=content)]
        return VectorStoreIndex.from_documents(documents)

    def retrieve_context(self, query: str) -> str:
        """Return concatenated text of the retrieved nodes for a query."""
        nodes = self.retriever.retrieve(query)
        if not nodes:
            return "No relevant information found."
        return "\n".join(n.node.text for n in nodes)

    def chat(self, user_input: str, history: list[dict] | None = None) -> str:
        """
        Run one RAG turn.

        `history` is a list of {"role": ..., "content": ...} dicts of
        PAST turns only (do not include the current user_input - it is
        added internally along with retrieved context).
        """
        history = history or []
        context = self.retrieve_context(user_input)

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

        return response.choices[0].message.content
