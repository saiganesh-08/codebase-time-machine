import os
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, cache
from app.git_analyzer import clone_repository, mine_commit_history
from app.ast_analyzer import build_dependency_graph, build_called_by
from app.risk_score import compute_risk_scores

router = APIRouter(prefix="/repos", tags=["repos"])


def _repo_name_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1].replace(".git", "")


def run_analysis(repo_id: int):
    """Background job: clone, mine git history, run AST analysis, compute risk."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        repo = db.query(models.Repository).get(repo_id)
        repo.status = "analyzing"
        db.commit()

        local_path = clone_repository(repo.url, repo.name)
        repo.local_path = local_path
        db.commit()

        # --- Git history mining ---
        commit_records = mine_commit_history(local_path)
        for c in commit_records:
            db.add(models.Commit(
                repository_id=repo.id,
                sha=c["sha"], author=c["author"], author_email=c["author_email"],
                message=c["message"], committed_at=c["committed_at"],
                files_changed=c["files_changed"], insertions=c["insertions"],
                deletions=c["deletions"], is_bugfix=c["is_bugfix"],
            ))
        db.commit()

        # --- Static analysis: build function dependency graph ---
        functions = build_dependency_graph(local_path)
        called_by = build_called_by(functions)

        # --- Change / bugfix counts per file, approximated to functions in that file ---
        change_counts, bugfix_counts = {}, {}
        for qname, fn in functions.items():
            touching = [c for c in commit_records if fn.file_path in c["files_changed"]]
            change_counts[qname] = len(touching)
            bugfix_counts[qname] = sum(1 for c in touching if c["is_bugfix"])

        calls_map = {q: fn.calls for q, fn in functions.items()}
        risk_scores = compute_risk_scores(calls_map, called_by, change_counts, bugfix_counts)

        for qname, fn in functions.items():
            db.add(models.Function(
                repository_id=repo.id,
                name=fn.name, qualified_name=qname, file_path=fn.file_path,
                start_line=fn.start_line, end_line=fn.end_line, docstring=fn.docstring,
                calls=fn.calls, called_by=called_by.get(qname, []),
                change_count=change_counts.get(qname, 0),
                bugfix_count=bugfix_counts.get(qname, 0),
                risk_score=risk_scores.get(qname, 0.0),
            ))

        repo.status = "ready"
        db.commit()
        cache.invalidate(f"repo:{repo.id}:")
    except Exception as e:
        repo.status = "failed"
        db.commit()
        raise e
    finally:
        db.close()


@router.post("", response_model=schemas.RepoStatus)
def ingest_repo(req: schemas.RepoIngestRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    name = _repo_name_from_url(req.url)
    existing = db.query(models.Repository).filter_by(url=req.url).first()
    if existing:
        background_tasks.add_task(run_analysis, existing.id)
        existing.status = "pending"
        db.commit()
        return existing

    repo = models.Repository(url=req.url, name=name, local_path="", status="pending")
    db.add(repo)
    db.commit()
    db.refresh(repo)

    background_tasks.add_task(run_analysis, repo.id)
    return repo


@router.get("/{repo_id}", response_model=schemas.RepoStatus)
def get_repo_status(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(models.Repository).get(repo_id)
    if not repo:
        raise HTTPException(404, "Repository not found")
    return repo


@router.get("/{repo_id}/graph")
def get_dependency_graph(repo_id: int, db: Session = Depends(get_db)):
    cache_key = f"repo:{repo_id}:graph"
    cached = cache.get_json(cache_key)
    if cached:
        return cached

    functions = db.query(models.Function).filter_by(repository_id=repo_id).all()
    nodes = [{"id": f.qualified_name, "file": f.file_path, "risk": f.risk_score} for f in functions]
    edges = [
        {"source": f.qualified_name, "target": callee}
        for f in functions for callee in (f.calls or [])
    ]
    result = {"nodes": nodes, "edges": edges}
    cache.set_json(cache_key, result)
    return result
