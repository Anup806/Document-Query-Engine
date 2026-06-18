### About the project

This project runs as a FastAPI app in Docker and serves the web UI, chat endpoint, and voice chat endpoint from one container.

#### Run with Docker

1. Copy `.env.example` to `.env` and add your `GROQ_API_KEY` and `GOOGLE_API_KEY` values.
2. Build and start the app:

```bash
docker compose up --build
```

3. Open `http://localhost:8000` in your browser.

#### Optional CLI mode

If you want the terminal chat client inside Docker, run:

```bash
docker compose --profile cli run --rm cli
```
