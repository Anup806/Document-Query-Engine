<h1> <b> <span style = "color: red;"> RAG </span> </b> </h1> 
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