from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import repos, history, impact, risk

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Codebase Time Machine",
    description="AI-powered codebase archaeology & change-impact analysis",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repos.router)
app.include_router(history.router)
app.include_router(impact.router)
app.include_router(risk.router)


@app.get("/health")
def health():
    return {"status": "ok"}
