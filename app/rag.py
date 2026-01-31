from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from app.config import VECTOR_DB_PATH

def search_db(query: str) -> str:
    db = FAISS.load_local(
        VECTOR_DB_PATH,
        DashScopeEmbeddings(),
        allow_dangerous_deserialization=True
    )
    docs = db.similarity_search(query, k=3)
    return "\n".join([d.page_content for d in docs])
