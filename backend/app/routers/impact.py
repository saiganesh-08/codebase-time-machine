from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, cache
from app.risk_score import transitive_blast_radius

router = APIRouter(prefix="/impact", tags=["impact"])


@router.get("/{repo_id}/{qualified_name:path}", response_model=schemas.ImpactResponse)
def get_impact(repo_id: int, qualified_name: str, db: Session = Depends(get_db)):
    cache_key = f"repo:{repo_id}:impact:{qualified_name}"
    cached = cache.get_json(cache_key)
    if cached:
        return cached

    fn = db.query(models.Function).filter_by(
        repository_id=repo_id, qualified_name=qualified_name
    ).first()
    if not fn:
        raise HTTPException(404, "Function not found")

    all_functions = db.query(models.Function).filter_by(repository_id=repo_id).all()
    called_by_map = {f.qualified_name: (f.called_by or []) for f in all_functions}

    blast_radius = transitive_blast_radius(qualified_name, called_by_map)

    result = {
        "target": qualified_name,
        "directly_depends_on": fn.calls or [],
        "directly_depended_by": fn.called_by or [],
        "transitive_blast_radius": blast_radius,
        "blast_radius_size": len(blast_radius),
    }
    cache.set_json(cache_key, result)
    return result
