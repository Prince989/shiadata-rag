from pipelines.retrieval_pipeline import RetrievalPipeline


def chat_with_bot():
    print("==================================================")
    print("🧠 SHIA-DATA AI ENGINE IS ONLINE (Type 'exit' to quit)")
    print("==================================================\n")

    # روشن کردن موتورِ جستجو
    pipeline = RetrievalPipeline()

    while True:
        question = input("\n👤 You: ")
        if question.lower() in ['exit', 'quit']:
            print("👋 Goodbye!")
            break

        if not question.strip():
            continue

        print("\n🤖 AI is thinking...\n")
        answer = pipeline.ask(question)
        print("--------------------------------------------------")
        print(f"💡 AI Answer:\n{answer}")
        print("--------------------------------------------------")


if __name__ == "__main__":
    chat_with_bot()