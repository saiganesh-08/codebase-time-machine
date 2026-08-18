# Codebase Time Machine

**AI-powered codebase archaeology and change-impact analysis.**

Point it at a public GitHub repo. It mines git history, builds a real
function-level dependency graph from the code itself (via AST parsing —
not an LLM guess), and combines the two to answer questions engineers
actually ask before touching unfamiliar code:

- *"Why is this function written this way?"* → an AI-generated narrative,
  grounded in the actual commit messages that touched it.
- *"What breaks if I change this?"* → a computed blast radius from a
  real dependency graph.
- *"Is this risky to touch?"* → a risk score combining change frequency,
  bug-fix frequency, and fan-in (how many things depend on it).

The LLM is used to **explain** structured data, not to invent it. The
hard engineering — git mining and static analysis — happens first;
the AI layer sits on top of real facts.

## Architecture

```
┌─────────────┐      ┌────────────────┐      ┌─────────────┐
│   Next.js   │ ───▶|    FastAPI     │────▶ │  PostgreSQL │
│  (frontend) │      │   (backend)    │      │ (git history│
└─────────────┘      └────────┬───────┘      │  + graph)   │
                              │              └─────────────┘
                      ┌───────┴────────┐
                      │                │
                ┌─────▼─────┐    ┌─────▼──────┐
                │  Redis    │    │  Anthropic │
                │ (cache)   │    │  API (LLM) │
                └───────────┘    └────────────┘
```

**Pipeline, when a repo is submitted:**

1. `git_analyzer.py` clones the repo and mines commit history (author,
   message, files touched, insertion/deletion counts, bug-fix heuristic).
2. `ast_analyzer.py` walks every `.py` file with Python's `ast` module,
   extracts every function, and resolves function calls into a
   dependency graph (who calls whom).
3. `risk_score.py` merges both signals: change frequency × bug-fix
   frequency × fan-in → a 0–100 risk score per function.
4. `llm_service.py` takes a function's real commit history and asks
   Claude to summarize *why* it evolved the way it did — a narrative
   grounded entirely in the mined data.
5. Results are cached in Redis (parsing a large repo is expensive) and
   served via FastAPI to the Next.js frontend, which renders an
   interactive dependency graph, a risk leaderboard, and a detail panel
   per function.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | Next.js (React), React Flow |
| Database | PostgreSQL |
| Cache | Redis |
| AI | Anthropic API (Claude) |
| Containerization | Docker, Docker Compose |
| Orchestration | Kubernetes manifests (`/k8s`) |
| CI | GitHub Actions |

## Running locally

```bash
cp .env.example .env

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs

Paste a small-to-medium public GitHub repo URL (Python codebases work
best, since the AST analyzer currently targets Python) and watch it
analyze.

## Running on Kubernetes

```bash
kubectl apply -f k8s/configmap.yaml
kubectl create secret generic ctm-secrets --from-literal=ANTHROPIC_API_KEY=your_key_here
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

Update the `image:` fields in `backend-deployment.yaml` and
`frontend-deployment.yaml` to point at your own built images before
applying (see CI workflow for a build step you can extend to push to
a registry).

## API overview

| Endpoint | Purpose |
|---|---|
| `POST /repos` | Submit a repo URL, kicks off background analysis |
| `GET /repos/{id}` | Poll analysis status |
| `GET /repos/{id}/graph` | Full dependency graph (nodes + edges) |
| `GET /risk/{id}` | Top functions ranked by risk score |
| `GET /impact/{id}/{qualified_name}` | Blast radius for a function |
| `GET /history/{id}/{qualified_name}` | AI-generated evolution narrative |

## Project layout

```
backend/
  app/
    git_analyzer.py     # commit history mining
    ast_analyzer.py      # static dependency graph construction
    risk_score.py         # risk scoring + blast radius BFS
    llm_service.py         # Claude-powered history narratives
    routers/                # FastAPI route handlers
frontend/
  app/                        # Next.js app router pages
  components/                  # RepoForm, RiskTable, DependencyGraph, FunctionDetail
k8s/                              # Kubernetes manifests
.github/workflows/ci.yml           # lint/build/self-analysis CI
docker-compose.yml                  # one-command local stack
```

## Known limitations / next steps

- AST analysis currently supports Python only; extending to
  JavaScript/TypeScript via `tree-sitter` is a natural next step.
- Call resolution is name-based (not fully scope-aware), so it can
  over- or under-resolve calls in codebases with many same-named
  functions across modules.
- Bug-fix detection is a keyword heuristic on commit messages — good
  enough as a signal, not a ground truth.
