"""
benchmark_chat.py
------------------
Times response latency and checks rough answer accuracy for the
Document-Query-Engine /chat endpoint.

HOW TO RUN (Windows, PowerShell or cmd):
1. In your repo folder, start the app in one terminal:
       docker compose up --build
   (or, if running locally without Docker: uvicorn main:app --reload)
2. Open a SECOND terminal in the same folder and run:
       pip install requests
       python benchmark_chat.py
3. Read the printed summary, then open benchmark_results.csv and manually
   review the "correct" column -- keyword matching is a rough proxy, not
   ground truth. Fix any wrong grades by hand before using the numbers.
"""
import time
import csv
import requests

BASE_URL = "http://localhost:8000"

# Edit this list: mix of the 5 hardcoded facts in rag_engine.py AND
# questions about whatever content is in your sample.txt.

test_cases = [
    {"question": "What is RAG Pipeline?", "expected_keyword": "RAG"},
    {"question": "How does RAG differ from traditional LLMs?", "expected_keyword": "LLMs"},
    {"question": "What happens in the data ingestion phase?", "expected_keyword": "data ingestion"},
    {"question": "Why are documents divided into chunks?", "expected_keyword": "chunks"},
    {"question": "What are embeddings in RAG?", "expected_keyword": "embeddings"},
    {"question": "Where are embeddings stored?", "expected_keyword": "vector database"},
    {"question": "How is a user query processed in RAG?", "expected_keyword": "query"},
    {"question": "What does the retrieval component do?", "expected_keyword": "retrieval"},
    {"question": "What happens in the generation stage?", "expected_keyword": "generation"},
    {"question": "How does RAG improve factual accuracy?", "expected_keyword": "accuracy"},
    {"question": "How does RAG reduce hallucination?", "expected_keyword": "hallucination"},
    {"question": "What are some applications of RAG?", "expected_keyword": "applications"},
    {"question": "Where is RAG used in enterprise?", "expected_keyword": "enterprise search"},
    {"question": "How is RAG applied in customer support?", "expected_keyword": "customer support"},
    {"question": "Why is RAG useful for domain-specific knowledge?", "expected_keyword": "domain-specific"},
]


results = []
for case in test_cases:
    start = time.time()
    resp = requests.post(f"{BASE_URL}/chat", json={"message": case["question"]})
    elapsed = time.time() - start
    answer = resp.json().get("answer", "")
    correct = case["expected_keyword"].lower() in answer.lower()
    results.append({
        "question": case["question"],
        "answer": answer,
        "latency_sec": round(elapsed, 2),
        "correct": correct,
    })
    print(f"[{elapsed:.2f}s] Q: {case['question']}")
    print(f"A: {answer}")
    print(f"Keyword match: {correct}\n")

avg_latency = sum(r["latency_sec"] for r in results) / len(results)
accuracy = sum(r["correct"] for r in results) / len(results) * 100

print("--- SUMMARY ---")
print(f"Average latency: {avg_latency:.2f}s across {len(results)} queries")
print(f"Keyword-match accuracy: {accuracy:.0f}% "
      f"({sum(r['correct'] for r in results)}/{len(results)})")

with open("benchmark_results.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["question", "answer", "latency_sec", "correct"])
    writer.writeheader()
    writer.writerows(results)
print("Saved full details to benchmark_results.csv -- review before trusting the numbers.")
