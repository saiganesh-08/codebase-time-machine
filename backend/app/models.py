from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    local_path = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending | analyzing | ready | failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
    functions = relationship("Function", back_populates="repository", cascade="all, delete-orphan")


class Commit(Base):
    __tablename__ = "commits"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    sha = Column(String, index=True, nullable=False)
    author = Column(String)
    author_email = Column(String)
    message = Column(Text)
    committed_at = Column(DateTime)
    files_changed = Column(JSON)  # list of file paths
    insertions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    is_bugfix = Column(Integer, default=0)  # 1 if commit message looks like a bug fix

    repository = relationship("Repository", back_populates="commits")


class Function(Base):
    __tablename__ = "functions"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    name = Column(String, index=True, nullable=False)
    qualified_name = Column(String, index=True, nullable=False)  # module.Class.func
    file_path = Column(String, nullable=False)
    start_line = Column(Integer)
    end_line = Column(Integer)
    docstring = Column(Text, nullable=True)

    calls = Column(JSON, default=list)       # qualified names this function calls
    called_by = Column(JSON, default=list)   # qualified names that call this function

    change_count = Column(Integer, default=0)
    bugfix_count = Column(Integer, default=0)
    risk_score = Column(Float, default=0.0)

    repository = relationship("Repository", back_populates="functions")


class FunctionHistorySummary(Base):
    """Cached LLM-generated narrative for a function's evolution."""
    __tablename__ = "function_history_summaries"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    qualified_name = Column(String, index=True, nullable=False)
    summary = Column(Text)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
