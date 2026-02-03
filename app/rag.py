from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from app.config import VECTOR_DB_PATH, RAG_SCORE_THRESHOLD, RAG_RELATIVE_MULTIPLIER, RAG_MIN_HITS

def search_db(query: str, k: int = 3) -> tuple[str, bool]:
    db = FAISS.load_local(
        VECTOR_DB_PATH,
        DashScopeEmbeddings(),
        allow_dangerous_deserialization=True
    )
    results = db.similarity_search_with_score(query, k=k)
    if not results:
        return "", False

    # FAISS returns distance scores (lower = more similar)
    top_score = results[0][1]
    dynamic_threshold = max(RAG_SCORE_THRESHOLD, top_score * RAG_RELATIVE_MULTIPLIER)
    filtered = [(doc, score) for doc, score in results if score <= dynamic_threshold]
    if len(filtered) < RAG_MIN_HITS:
        return "", False

    text = "\n".join([doc.page_content for doc, _ in filtered])
    return text, True
