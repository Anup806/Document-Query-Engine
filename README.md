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

This project is intentionally small, and the file layout looks like this:

```text
README.md
requirements.txt
.env.example          # environment-driven configuration template
CLI.py                # terminal entrypoint for chat and evaluation
rag_engine.py         # retrieval, indexing, and answer generation logic
evaluation_set.json   # sample retrieval evaluation cases
sample.txt            # default local knowledge source
__pycache__/          # generated Python bytecode cache
```

What each file is responsible for:

- `README.md` - Project overview, setup steps, usage notes, and file layout.
- `requirements.txt` - Python dependencies required to run the project.
- `.env.example` - Environment variable template. Copy it to `.env` and add your API keys.
- `CLI.py` - Command-line entry point for the chatbot and the evaluation runner.
- `rag_engine.py` - Core RAG implementation that loads documents, builds or reuses the index, retrieves context, and calls the model.
- `evaluation_set.json` - Small JSON test set used to check retrieval quality.
- `sample.txt` - Default source document used when no custom document folder is configured.
- `__pycache__/` - Auto-generated Python cache directory created by the interpreter; it can be ignored.