
from src.rag.retrieval import retrieve_documents


query = "How do stockouts affect retail demand forecasting?"

results = retrieve_documents(query, top_k=3)

print("\nQUESTION:", query)

for index, result in enumerate(results, start=1):

    print(f"\n===== RESULT {index} =====")
    print("Source:", result["source"])
    print("Page:", result["page"])
    print("Distance:", result["distance"])
    print("Text:", result["text"])
