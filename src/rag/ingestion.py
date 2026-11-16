
from pathlib import Path
from src.rag.download_documents import download_documents
import chromadb
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


ROOT_DIR = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = ROOT_DIR / "data" / "documents"
CHROMA_PATH = ROOT_DIR / "chroma_db"

COLLECTION_NAME = "retail_knowledge"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def load_documents():
    """Extract text from all PDF documents."""

    documents = []

    for pdf_path in sorted(DOCUMENTS_DIR.glob("*.pdf")):

        reader = PdfReader(pdf_path)

        print(f"Reading: {pdf_path.name}")

        for page_number, page in enumerate(reader.pages, start=1):

            text = page.extract_text()

            if text and text.strip():
                documents.append({
                    "text": text,
                    "source": pdf_path.name,
                    "page": page_number
                })

    return documents


def create_chunks(documents):
    """Split documents into smaller passages."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = []

    for document in documents:

        texts = splitter.split_text(document["text"])

        for index, text in enumerate(texts):

            chunks.append({
                "id": (
                    f"{document['source']}"
                    f"_p{document['page']}"
                    f"_c{index}"
                ),
                "text": text,
                "source": document["source"],
                "page": document["page"]
            })

    return chunks


def ingest_documents():
    """Build the persistent vector database."""
    download_documents()

    documents = load_documents()

    if not documents:
        raise ValueError("No readable PDF documents found.")

    chunks = create_chunks(documents)

    if not chunks:
        raise ValueError("No document chunks created.")

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH)
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        configuration={"hnsw": {"space": "cosine"}}
    )

    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[
            {
                "source": chunk["source"],
                "page": chunk["page"]
            }
            for chunk in chunks
        ]
    )

    print("\n===== INGESTION COMPLETE =====")
    print("Pages processed:", len(documents))
    print("Chunks created:", len(chunks))
    print("Chunks stored:", collection.count())
    print("Database location:", CHROMA_PATH)


if __name__ == "__main__":
    ingest_documents()
