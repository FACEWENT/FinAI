from pydantic import BaseModel

class Query(BaseModel):
    question: str

class Answer(BaseModel):
    result: str


class ResearchQuery(BaseModel):
    question: str
    pdf_urls: list[str] = []
