from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
class LoginIn(BaseModel):
    email: EmailStr
    password: str
class ChatIn(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[int] = None
class QuizIn(BaseModel):
    count: int = Field(default=5, ge=5, le=20)
    difficulty: str = Field(default="medium")
class CompareIn(BaseModel):
    paper_id: int
    other_paper_id: int

class Analysis(BaseModel):
    title: str = ""
    authors: List[str] = []
    abstract: str = ""
    research_problem: str = ""
    objective: str = ""
    methodology: Dict[str, Any] = {}
    key_findings: List[str] = []
    conclusion: str = ""
    limitations: List[str] = []
    future_work: List[str] = []
    sections: List[Dict[str, Any]] = []
    concepts: List[Dict[str, Any]] = []
    results: List[Dict[str, Any]] = []
    references: List[Dict[str, Any]] = []
    quick_summary: str = ""
    standard_summary: str = ""
    detailed_summary: str = ""
    beginner_explanation: str = ""
