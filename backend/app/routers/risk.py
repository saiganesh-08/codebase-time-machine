from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/{repo_id}")
def get_top_risk_functions(repo_id: int, limit: int = Query(20, le=100), db: Session = Depends(get_db)):
    functions = (
        db.query(models.Function)
        .filter_by(repository_id=repo_id)
        .order_by(models.Function.risk_score.desc())
        .limit(limit)
        .all()
    )
    return [schemas.FunctionOut.model_validate(f) for f in functions]


@router.get("/{repo_id}/file", response_model=schemas.RiskResponse)
def get_file_risk(repo_id: int, file_path: str, db: Session = Depends(get_db)):
    functions = db.query(models.Function).filter_by(
        repository_id=repo_id, file_path=file_path
    ).all()
    avg = round(sum(f.risk_score for f in functions) / len(functions), 2) if functions else 0.0
    return {
        "file_path": file_path,
        "functions": [schemas.FunctionOut.model_validate(f) for f in functions],
        "average_risk": avg,
    }
