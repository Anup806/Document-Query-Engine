# Document-Query-Engine 

This project is a FastAPI RAG demo with a web chat UI, a browser voice-chat endpoint, and a separate terminal voice agent.

## Prerequisites

- Docker Desktop
- Python 3.11 or newer, for running `voice-agent.py` locally
- A Groq API key
- A Google API key

## Environment setup

Create a `.env` file from the example file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and add your keys:

```env
GROQ_API_KEY="your_groq_api_key"
GOOGLE_API_KEY="your_google_api_key"
```

## Run with Docker

Build and start the FastAPI app:

```powershell
docker compose up --build
```

Open the app in your browser:

```text
http://localhost:8012
```

Stop the app:

```powershell
docker compose down
```

Run the optional terminal chat client inside Docker:

```powershell
docker compose --profile cli run --rm cli
```

## Run the voice agent in terminal

The terminal voice agent uses your local microphone and speakers, so run it on your host machine instead of Docker.

Create and activate a virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start the voice agent:

```powershell
python .\voice-agent.py
```

Press `ENTER` to record a question. Type `exit` and press `ENTER` to quit.

## Useful commands

View Docker logs:

```powershell
docker compose logs -f app
```

Run the FastAPI app locally without Docker:

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
