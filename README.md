# Document Query Engine (RAG-updated)

A small Retrieval-Augmented Generation (RAG) example that demonstrates
how to combine a vector index + embeddings with an LLM to answer
questions from a knowledge base. The project includes both a
CLI chat agent and a voice-enabled agent (speech-to-text + text-to-speech).

## What the project does

- Builds an in-memory vector index over a small Nepal knowledge base.
- Uses embeddings (Gemini via Google GenAI) to retrieve relevant context.
- Calls an OpenAI-compatible Groq chat endpoint to generate answers
	using retrieved context (RAG-style).
- Offers two entry points:
	- `CLI.py`: interactive text chat in terminal.
	- `voice-agent.py`: record audio, transcribe (Whisper), run RAG, and
		optionally synthesize the response to audio (Orpheus TTS).

## Quickstart — install & run

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Set required environment variables (examples):

- `GROQ_API_KEY` or `XAI_API_KEY` — API key for Groq (OpenAI-compatible).
- `GOOGLE_API_KEY` — API key for Google GenAI embeddings.

You can put these into a `.env` file (the project uses `python-dotenv`).

3. Run the CLI chat agent:

```bash
python CLI.py
```

4. Run the voice agent (requires audio devices and `sounddevice` support):

```bash
python voice-agent.py
```

Notes:
- The voice agent records a short audio clip (default 5s), transcribes
	it using the Groq `whisper-large-v3` STT model, and synthesizes audio
	with `canopylabs/orpheus-v1-english` if Orpheus TTS terms are accepted.
- `sounddevice` may require additional OS-level audio libraries.

## Project structure and responsibilities

- `CLI.py`
	- Entry point for the text-based chat agent.
	- Function: `run_agent()` — starts an interactive loop, sends user
		input to `RAGEngine.chat()`, prints and tracks history.

- `rag_engine.py`
	- Core RAG implementation and configuration.
	- Class: `RAGEngine`
		- `__init__()` — reads environment variables, configures the
			Groq/OpenAI client, sets embedding and LLM settings, builds the
			in-memory `VectorStoreIndex`, and creates a retriever.
		- `_build_index()` (static) — constructs a small example index
			from `llama_index` `Document` objects (currently hard-coded
			Nepal facts). Replaceable with your own ingestion pipeline.
		- `retrieve_context(query: str) -> str` — performs a retrieval and
			concatenates the retrieved node texts into a context string.
		- `chat(user_input: str, history: list[dict] | None = None) -> str` —
			composes system/history/user messages, calls the Groq chat
			endpoint, and returns the assistant text.

- `voice-agent.py`
	- Voice-enabled wrapper around `RAGEngine` providing STT/TTS and
		audio playback.
	- Config: `RECORD_SECONDS`, `SAMPLE_RATE`, `STT_MODEL`, `TTS_MODEL`,
		`TTS_VOICE`, `TTS_TERMS_URL`.
	- Audio helpers:
		- `record_audio(filepath, duration, samplerate)` — records audio
			from the default input device and saves to file.
		- `play_audio(filepath)` — plays a WAV file to the default output.
	- Groq helpers:
		- `transcribe(client, filepath) -> str` — uploads file for STT.
		- `synthesize(client, text, filepath) -> bool` — requests TTS and
			writes WAV output (returns False if terms not accepted).
	- `run_voice_agent()` — main loop: records, transcribes, calls
		`RAGEngine.chat()`, optionally synthesizes and plays the response.

- `requirements.txt`
	- Python package dependencies used by the project (see file).

- `sample.txt`
	- Short explanation of what a RAG pipeline is (documentation/notes).

## Extending the project

- Replace `_build_index()` with a real ingestion pipeline that loads
	documents, chunks them, and builds a persistent vector store.
- Swap in other embedding or LLM providers by updating `Settings`
	configuration in `rag_engine.py`.
- Add batching, caching, or a web API layer (FastAPI) for production use.

## License & Notes

This repository is a small demo and starting point — adapt keys,
models, and index size for production. Keep API keys secure and follow
model provider terms of service.

