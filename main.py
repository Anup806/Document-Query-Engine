import os
import time
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from openai import BadRequestError
from pydantic import BaseModel

from rag_engine import RAGEngine

# -------------------------
# SETUP
# -------------------------
app = FastAPI(title="Document Query Engine")

# Build the index / load models ONCE at startup.
engine = RAGEngine()

# Simple in-memory, single-session history (fine for a demo / single user).
# For multiple concurrent users, key this dict by a session id instead.
conversation_history: list[dict] = []

# Where the latest TTS reply is written so /audio-response can serve it.
TTS_OUTPUT_PATH = os.path.join(tempfile.gettempdir(), "sherpa_response.wav")

STT_MODEL = "whisper-large-v3"
TTS_MODEL = "canopylabs/orpheus-v1-english"
TTS_VOICE = "troy"
TTS_TERMS_URL = "https://console.groq.com/playground?model=canopylabs%2Forpheus-v1-english"

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_TEXT_PATH = BASE_DIR / "sample.txt"
if not SAMPLE_TEXT_PATH.exists():
    SAMPLE_TEXT_PATH = BASE_DIR / "sample_text.txt"

STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = BASE_DIR / "index.html"

SAMPLE_TEXT = SAMPLE_TEXT_PATH.read_text(encoding="utf-8").strip()

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# -------------------------
# SCHEMAS
# -------------------------
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


def build_rag_input(user_input: str) -> str:
    """
    Constructs the RAG (Retrieval-Augmented Generation) input by combining
    the user's question with reference text from sample.txt.

    Args:
        user_input (str): The user's question or message.

    Returns:
        str: The formatted RAG input with question and reference text, or
        just the user input if no reference text exists.
    """
    if not SAMPLE_TEXT:
        return user_input
    return f"""User question:
{user_input}

Reference text from sample.txt:
{SAMPLE_TEXT}"""


# -------------------------
# ROUTES
# -------------------------
@app.get("/", response_class=HTMLResponse)
def serve_frontend() -> str:
    """
    Serves the frontend HTML page at the root endpoint.

    Returns:
        str: The HTML content of index.html.
    """
    return INDEX_HTML.read_text(encoding="utf-8")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Handles text-based chat requests using RAG-enhanced conversation.

    Args:
        request (ChatRequest): The user's chat message.

    Returns:
        ChatResponse: The assistant's answer.
    """
    answer = engine.chat(build_rag_input(request.message), conversation_history)
    conversation_history.append({"role": "user", "content": request.message})
    conversation_history.append({"role": "assistant", "content": answer})
    return ChatResponse(answer=answer)


@app.post("/voice-chat")
async def voice_chat(audio: UploadFile = File(...)):
    """
    Handles voice-based chat with full audio processing pipeline.

    Process flow:
    1. Converts uploaded audio to text using Groq Whisper (STT - Speech-to-Text)
    2. Generates RAG-enhanced answer using the transcribed text
    3. Converts the answer back to speech using Groq Orpheus (TTS - Text-to-Speech)

    Each stage is timed and printed to the console as [TIMING] lines, so you
    can read off STT / RAG+LLM / TTS latency separately for benchmarking.

    Args:
        audio (UploadFile): Audio file uploaded by the user.

    Returns:
        dict: Contains transcript, answer text, and audio_url for the response.
    """
    # Persist the upload with its original extension (e.g. .webm, .wav)
    suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
        tmp_in.write(await audio.read())
        input_path = tmp_in.name

    try:
        # 1) Speech -> text (Groq Whisper)
        stt_start = time.time()
        with open(input_path, "rb") as f:
            transcription = engine.client.audio.transcriptions.create(
                file=f,
                model=STT_MODEL,
            )
        user_text = transcription.text.strip()
        stt_elapsed = time.time() - stt_start
        print(f"[TIMING] STT (Whisper):  {stt_elapsed:.2f}s")
    finally:
        os.remove(input_path)

    if not user_text:
        return {"transcript": "", "answer": "I didn't catch any speech, please try again.", "audio_url": None}

    # 2) Text -> RAG answer
    llm_start = time.time()
    answer = engine.chat(build_rag_input(user_text), conversation_history)
    llm_elapsed = time.time() - llm_start
    print(f"[TIMING] RAG + LLM:      {llm_elapsed:.2f}s")

    conversation_history.append({"role": "user", "content": user_text})
    conversation_history.append({"role": "assistant", "content": answer})

    # 3) Text -> speech (Groq Orpheus)
    tts_start = time.time()
    audio_url = "/audio-response"
    try:
        speech = engine.client.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input=answer,
            response_format="wav",
        )
        speech.write_to_file(TTS_OUTPUT_PATH)
        tts_elapsed = time.time() - tts_start
        print(f"[TIMING] TTS (Orpheus):  {tts_elapsed:.2f}s")
    except BadRequestError as exc:
        tts_elapsed = time.time() - tts_start
        if getattr(exc, "code", None) == "model_terms_required":
            print("[TIMING] TTS (Orpheus):  unavailable (terms not accepted)")
            print(f"[TTS] Accept terms here: {TTS_TERMS_URL}")
            audio_url = None
        else:
            raise

    total_elapsed = stt_elapsed + llm_elapsed + tts_elapsed
    print(f"[TIMING] TOTAL:          {total_elapsed:.2f}s\n")

    return {"transcript": user_text, "answer": answer, "audio_url": audio_url}


@app.get("/audio-response")
def audio_response():
    """
    Serves the most recently generated TTS (Text-to-Speech) audio response.

    Returns:
        FileResponse: The audio file if it exists, otherwise an error message.
    """
    if not os.path.exists(TTS_OUTPUT_PATH):
        return {"error": "No audio response generated yet."}
    return FileResponse(TTS_OUTPUT_PATH, media_type="audio/wav")


@app.post("/reset")
def reset():
    """
    Clears the conversation history, allowing a fresh start for the next session.

    Returns:
        dict: Status confirmation message.
    """
    conversation_history.clear()
    return {"status": "conversation reset"}