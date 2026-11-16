
import chromadb

from src.rag.ingestion import (
    CHROMA_PATH,
    COLLECTION_NAME,
    ingest_documents
)


def retrieve_documents(query, top_k=3):
    """Retrieve relevant scientific passages."""

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be positive.")

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH)
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        configuration={"hnsw": {"space": "cosine"}}
    )

    # Automatically initialize the knowledge base
    # if no scientific passages are available.
    if collection.count() == 0:

        print("Initializing scientific knowledge base...")

        ingest_documents()

        collection = client.get_collection(
            name=COLLECTION_NAME
        )

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count())
    )

    passages = []

    for index, text in enumerate(results["documents"][0]):

        metadata = results["metadatas"][0][index]

        passages.append({
            "chunk_id": results["ids"][0][index],
            "text": text,
            "source": metadata["source"],
            "page": metadata["page"],
            "distance": round(
                float(results["distances"][0][index]), 4
            )
        })

    return passages
