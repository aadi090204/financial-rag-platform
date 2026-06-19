import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

UPLOAD_DIR = "uploads"
CHROMA_DB_DIR = "chroma_db"
COLLECTION_NAME = "finance_documents"