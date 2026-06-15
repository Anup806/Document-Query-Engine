import argparse

from rag_engine import RAGEngine


def run_agent(rebuild_index: bool = False) -> None:
    engine = RAGEngine(rebuild_index=rebuild_index)
    history: list[dict] = []

    print("\n🚀 RAG Agent Started (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        answer = engine.chat(user_input, history)
        print("\nAssistant:", answer, "\n")

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": answer})


def run_evaluation(rebuild_index: bool = False) -> None:
    engine = RAGEngine(rebuild_index=rebuild_index)
    results = engine.run_evaluation()

    passed = sum(1 for result in results if result["passed"])
    print("\n📋 Retrieval evaluation results\n")
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[{status}] {result['question']}")
        if result["keyword_hits"]:
            print(f"  keyword hits: {', '.join(result['keyword_hits'])}")
        if result["source_hits"]:
            print(f"  source hits: {', '.join(result['source_hits'])}")
        print()

    print(f"Score: {passed}/{len(results)} passed\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Nepal RAG terminal assistant.")
    parser.add_argument("--eval", action="store_true", help="Run the retrieval evaluation set and exit.")
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Rebuild the local vector store before starting.",
    )
    args = parser.parse_args()

    if args.eval:
        run_evaluation(rebuild_index=args.rebuild_index)
    else:
        run_agent(rebuild_index=args.rebuild_index)