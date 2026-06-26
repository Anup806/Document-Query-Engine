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
    {"question": "Who is an AI Engineer?", "expected_keyword": "AI Engineer"},
    {"question": "Which programming languages are important for AI engineers?", "expected_keyword": "Python"},
    {"question": "Which ML libraries do AI engineers use?", "expected_keyword": "TensorFlow"},
    {"question": "What is the role of MLOps in AI engineering?", "expected_keyword": "MLOps"},
    {"question": "Which cloud platforms are used by AI engineers?", "expected_keyword": "AWS"},
    {"question": "What tools help with containerization?", "expected_keyword": "Docker"},
    {"question": "What orchestration system is commonly used?", "expected_keyword": "Kubernetes"},
    {"question": "How do AI engineers ensure fairness and transparency?", "expected_keyword": "ethics"},
    {"question": "Which industries employ AI engineers?", "expected_keyword": "healthcare"},
    {"question": "What is the difference between AI engineers and data scientists?", "expected_keyword": "deployment"},
    {"question": "How do AI engineers handle large datasets?", "expected_keyword": "SQL"},
    {"question": "What is the role of AI engineers in RAG pipelines?", "expected_keyword": "RAG"},
    {"question": "Why is explainability important in AI engineering?", "expected_keyword": "explainability"},
    {"question": "What career opportunities exist for AI engineers?", "expected_keyword": "career"},
    {"question": "Why is continuous learning important for AI engineers?", "expected_keyword": "learning"},
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
