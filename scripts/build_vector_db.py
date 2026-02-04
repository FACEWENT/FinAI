from dotenv import load_dotenv
import os

load_dotenv()  # 👈 这一行是关键！

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.document_loaders import TextLoader
import glob

# 可选：打印一下看看有没有读到 Key（调试用）
# print("KEY =", os.getenv("DASHSCOPE_API_KEY"))

docs = []
for path in sorted(glob.glob("data/*.txt")):
    loader = TextLoader(path, encoding="utf-8")
    docs.extend(loader.load())

db = FAISS.from_documents(docs, DashScopeEmbeddings())
db.save_local("vector_store")

print("向量库构建完成！")
