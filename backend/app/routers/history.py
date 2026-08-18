from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, cache
from app.llm_service import summarize_function_history

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/{repo_id}/{qualified_name:path}", response_model=schemas.HistoryResponse)
def get_function_history(repo_id: int, qualified_name: str, db: Session = Depends(get_db)):
    cache_key = f"repo:{repo_id}:history:{qualified_name}"
    cached = cache.get_json(cache_key)
    if cached:
        return cached

    fn = db.query(models.Function).filter_by(
        repository_id=repo_id, qualified_name=qualified_name
    ).first()
    if not fn:
        raise HTTPException(404, "Function not found")

    commits = db.query(models.Commit).filter(
        models.Commit.repository_id == repo_id,
    ).all()
    touching = [c for c in commits if fn.file_path in (c.files_changed or [])]
    messages = [c.message for c in touching]
    authors = sorted(set(c.author for c in touching))

    narrative = summarize_function_history(qualified_name, messages, fn.bugfix_count)

    db.add(models.FunctionHistorySummary(
        repository_id=repo_id, qualified_name=qualified_name, summary=narrative,
    ))
    db.commit()

    result = {
        "qualified_name": qualified_name,
        "commit_count": len(touching),
        "bugfix_count": fn.bugfix_count,
        "authors": authors,
        "narrative": narrative,
    }
    cache.set_json(cache_key, result, ttl=60 * 60 * 6)
    return result
