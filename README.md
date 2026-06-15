<h1> <b> <span style = "color: red;"> Document Query Engine </span> </b> </h1> 
This is a terminal-based RAG chatbot for local Nepal knowledge.

It now:
- ingests `sample.txt`, or any `.txt` / `.md` files you add under `docs/` or `data/`
- persists the vector index in `.rag_storage`
- prints citations in the answer output
- includes a small retrieval evaluation set

<h3> <b> <span style = "color: cyan;"> To Run the system </span> </b> </h3> 
command: "python CLI.py"

<h3> <b> <span style = "color: cyan;"> Useful commands </span> </b> </h3>

Run the chatbot:

`python CLI.py`

Rebuild the vector index:

`python CLI.py --rebuild-index`

Run the retrieval evaluation:

`python CLI.py --eval`

<h3> <b> <span style = "color: cyan;"> File overview </span> </b> </h3>

This project is intentionally small, and each file has a specific role:

- `.env.example` - Template for the environment variables the app expects. Copy it to `.env` and add your actual API keys there.
- `CLI.py` - Command-line entry point. It starts the chat loop, supports `--eval`, and can rebuild the index with `--rebuild-index`.
- `evaluation_set.json` - Small evaluation dataset used to test whether retrieval returns the expected keywords and source files.
- `rag_engine.py` - Core RAG logic. It loads documents, builds or reloads the vector index, retrieves context, calls the LLM, and runs evaluation.
- `requirements.txt` - Python dependencies needed to run the project.
- `sample.txt` - Default knowledge-base source file used when no other document folder is configured.
- `__pycache__/` - Auto-generated Python bytecode cache created by Python for faster imports. It is safe to ignore and does not need to be edited.