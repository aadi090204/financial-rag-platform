import os
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException

from app.config import UPLOAD_DIR
from app.pdf_loader import extract_text_from_pdf
from app.text_splitter import split_text
from app.vector_store import store_chunks, search_relevant_chunks, reset_collection
from app.rag_pipeline import answer_question
from app.schemas import QuestionRequest, QuestionResponse, SearchResponse, SearchResult


app = FastAPI(
    title="Finance RAG Advisor",
    description="A RAG-based financial document assistant with source-grounded answers.",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Finance RAG Advisor backend is running"
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text = extract_text_from_pdf(file_path)

    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the PDF."
        )

    chunks = split_text(extracted_text)
    stored_count = store_chunks(chunks, file.filename)

    return {
        "message": "PDF uploaded and indexed successfully.",
        "filename": file.filename,
        "chunks_stored": stored_count
    }


@app.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    result = answer_question(request.question)

    return QuestionResponse(
        answer=result["answer"],
        sources=result["sources"]
    )

@app.post("/search", response_model=SearchResponse)
def search_documents(request: QuestionRequest):
    relevant_chunks = search_relevant_chunks(request.question)

    results = []

    for chunk in relevant_chunks:
        document_name = chunk["metadata"].get("document_name", "unknown")
        chunk_index = chunk["metadata"].get("chunk_index", "unknown")

        results.append(
            SearchResult(
                source=f"{document_name} - chunk {chunk_index}",
                text=chunk["text"][:700],
                distance=float(chunk["distance"])
            )
        )

    return SearchResponse(
        query=request.question,
        results=results
    )

@app.delete("/documents/reset")
def reset_documents():
    message = reset_collection()

    return {
        "message": message
    }