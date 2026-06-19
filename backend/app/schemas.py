from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    answer: str
    sources: list[str]


class SearchResult(BaseModel):
    source: str
    text: str
    distance: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]