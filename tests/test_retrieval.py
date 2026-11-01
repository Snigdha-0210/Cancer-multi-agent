from backend.rag.retriever import SemanticRetriever

retriever = SemanticRetriever()

question = "What are the risk factors for melanoma?"
results = retriever.search(question, top_k=5)

print("\nTOP 5 RETRIEVAL RESULTS")
print("=" * 70)

for result in results:
    print(f"\nRank: {result['rank']}")
    print(f"Score: {result['score']:.4f}")
    print(f"Source: {result['document']}")
    print(f"Pages: {result['page_start']}-{result['page_end']}")
    print("Text:")
    print(result["text"][:350].replace("\n", " "))
    print("-" * 70)
