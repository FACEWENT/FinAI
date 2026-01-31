from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.schemas import Query, Answer
from app.agent import run_agent

app = FastAPI(title="FinAI - 金融 AI Agent")

# 前端支持
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 👉 网页入口
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 👉 原来的 API 接口
@app.post("/analyze", response_model=Answer)
def analyze(q: Query):
    result = run_agent(q.question)
    return {"result": result}
