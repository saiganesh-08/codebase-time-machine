from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class RepoIngestRequest(BaseModel):
    url: str


class RepoStatus(BaseModel):
    id: int
    url: str
    name: str
    status: str

    class Config:
        from_attributes = True


class FunctionOut(BaseModel):
    qualified_name: str
    file_path: str
    start_line: int
    end_line: int
    change_count: int
    bugfix_count: int
    risk_score: float

    class Config:
        from_attributes = True


class ImpactResponse(BaseModel):
    target: str
    directly_depends_on: List[str]
    directly_depended_by: List[str]
    transitive_blast_radius: List[str]
    blast_radius_size: int


class RiskResponse(BaseModel):
    file_path: str
    functions: List[FunctionOut]
    average_risk: float


class HistoryResponse(BaseModel):
    qualified_name: str
    commit_count: int
    bugfix_count: int
    authors: List[str]
    narrative: str
