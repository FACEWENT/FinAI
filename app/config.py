import os
from dotenv import load_dotenv

load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
VECTOR_DB_PATH = "vector_store"
RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.6"))
RAG_RELATIVE_MULTIPLIER = float(os.getenv("RAG_RELATIVE_MULTIPLIER", "1.6"))
RAG_MIN_HITS = int(os.getenv("RAG_MIN_HITS", "1"))
