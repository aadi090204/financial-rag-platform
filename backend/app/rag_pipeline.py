import google.generativeai as genai

from app.config import GEMINI_API_KEY
from app.vector_store import search_relevant_chunks


GEMINI_MODEL_NAME = "gemini-2.5-flash-lite"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def build_prompt(question: str, context_chunks: list[dict]) -> str:
    context_text = ""

    for index, chunk in enumerate(context_chunks, start=1):
        source = chunk["metadata"].get("document_name", "unknown")
        chunk_index = chunk["metadata"].get("chunk_index", "unknown")

        context_text += (
            f"\n[Source {index}: {source}, chunk {chunk_index}]\n"
            f"{chunk['text']}\n"
        )

    prompt = f"""
You are a careful financial document assistant.

Answer the user's question using ONLY the provided document context.

Rules:
1. Do not give investment advice.
2. Do not make up facts.
3. If the answer is not present in the context, say:
   "I could not find this information in the uploaded document."
4. Keep the answer clear and beginner-friendly.
5. Mention the relevant source chunks used.

Document context:
{context_text}

User question:
{question}

Answer:
"""

    return prompt


def fallback_retrieval_answer(relevant_chunks: list[dict]) -> dict:
    answer_parts = [
        "Gemini answer generation is currently unavailable, so I am returning the most relevant retrieved document context:",
        ""
    ]

    sources = []

    for index, chunk in enumerate(relevant_chunks, start=1):
        document_name = chunk["metadata"].get("document_name", "unknown")
        chunk_index = chunk["metadata"].get("chunk_index", "unknown")

        answer_parts.append(f"Source {index}: {document_name} - chunk {chunk_index}")
        answer_parts.append(chunk["text"][:700])
        answer_parts.append("")

        sources.append(f"{document_name} - chunk {chunk_index}")

    return {
        "answer": "\n".join(answer_parts),
        "sources": sources
    }


def answer_question(question: str) -> dict:
    relevant_chunks = search_relevant_chunks(question)

    if not relevant_chunks:
        return {
            "answer": "I could not find any relevant information in the uploaded document.",
            "sources": []
        }

    if not GEMINI_API_KEY:
        return fallback_retrieval_answer(relevant_chunks)

    prompt = build_prompt(question, relevant_chunks)

    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)

        sources = []

        for chunk in relevant_chunks:
            document_name = chunk["metadata"].get("document_name", "unknown")
            chunk_index = chunk["metadata"].get("chunk_index", "unknown")
            sources.append(f"{document_name} - chunk {chunk_index}")

        return {
            "answer": response.text,
            "sources": sources
        }

    except Exception as error:
        fallback = fallback_retrieval_answer(relevant_chunks)
        fallback["answer"] = (
            f"Gemini API error with model '{GEMINI_MODEL_NAME}': {str(error)}\n\n"
            + fallback["answer"]
        )
        return fallback