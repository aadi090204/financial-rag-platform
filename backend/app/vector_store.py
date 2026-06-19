import chromadb
from sentence_transformers import SentenceTransformer

from app.config import CHROMA_DB_DIR, COLLECTION_NAME


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)


def generate_embedding(text: str) -> list[float]:
    embedding = embedding_model.encode(text)
    return embedding.tolist()


def store_chunks(chunks: list[str], document_name: str) -> int:
    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        chunk_id = f"{document_name}_{index}"

        ids.append(chunk_id)
        documents.append(chunk)
        embeddings.append(generate_embedding(chunk))
        metadatas.append(
            {
                "document_name": document_name,
                "chunk_index": index
            }
        )

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(chunks)


def search_relevant_chunks(question: str, top_k: int = 4) -> list[dict]:
    question_embedding = generate_embedding(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )

    relevant_chunks = []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, metadata, distance in zip(documents, metadatas, distances):
        relevant_chunks.append(
            {
                "text": doc,
                "metadata": metadata,
                "distance": distance
            }
        )

    return relevant_chunks

def reset_collection() -> str:
    global collection

    client.delete_collection(name=COLLECTION_NAME)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    return "Vector database collection reset successfully."