from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.schemas import Query, Answer
from app.agent import run_agent, run_agent_stream

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

# 👉 新的流式 API 接口
@app.post("/analyze_stream")
def analyze_stream(q: Query):
    return StreamingResponse(
        run_agent_stream(q.question),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache"},
    )


def _sse_event(data: str, event: str | None = None) -> str:
    # SSE requires each line to be prefixed with "data:"
    lines = data.splitlines() or [""]
    payload = ""
    if event:
        payload += f"event: {event}\n"
    for line in lines:
        payload += f"data: {line}\n"
    return payload + "\n"


# 👉 SSE 接口（推荐）
@app.get("/analyze_sse")
def analyze_sse(question: str):
    def gen():
        yield _sse_event("开始分析...", event="status")
        for chunk in run_agent_stream(question):
            yield _sse_event(chunk)
        yield _sse_event("[DONE]", event="done")

    return StreamingResponse(
        gen(),
        media_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache"},
    )
