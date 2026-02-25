from fastapi import FastAPI, Request
import base64
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.schemas import Query, Answer, ResearchQuery
from app.agent import run_agent, run_agent_stream, run_report, run_research_report
from app.pdf_utils import build_report_pdf

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


# 👉 研究报告 PDF
@app.post("/report_pdf")
def report_pdf(q: Query):
    report_text = run_report(q.question)
    title = f"研究报告：{q.question}"
    pdf_buffer = build_report_pdf(title, report_text)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=research_report.pdf"},
    )


# 👉 研究报告文本 + PDF（一次生成）
@app.post("/report_bundle")
def report_bundle(q: Query):
    report_text = run_report(q.question)
    title = f"研究报告：{q.question}"
    pdf_buffer = build_report_pdf(title, report_text)
    pdf_b64 = base64.b64encode(pdf_buffer.getvalue()).decode("utf-8")
    return JSONResponse({"result": report_text, "pdf_base64": pdf_b64})


# 👉 研究助理（自动搜索 + PDF + 摘要 + 报告 + 可视化）
@app.post("/research")
def research(q: ResearchQuery):
    report_text, sources, chart = run_research_report(q.question, q.pdf_urls)
    return JSONResponse({"report": report_text, "sources": sources, "chart": chart})


@app.post("/research_pdf")
def research_pdf(q: ResearchQuery):
    report_text, _, _ = run_research_report(q.question, q.pdf_urls)
    title = f"研究报告：{q.question}"
    pdf_buffer = build_report_pdf(title, report_text)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=research_report.pdf"},
    )
