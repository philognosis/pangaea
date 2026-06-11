# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Pangaea is the operating system of the organization — not a portal, not a search engine, not an integration platform. Teams publish **capability manifests** (YAML "drivers") and the platform handles routing, identity, rendering, push, and trust on their behalf.

**Northstar:** Any person in the organization can discover, access, and complete any work they are permitted to do — from one place, by expressing a human need, without knowing what systems exist.

## Before writing any code

1. Read `docs/vision/pangaea-VISION.md` and the future and evolved vision in `docs/vision/pangaea-vision-evolved.md` completely. Every decision traces back to it. A visual representation of the vision and what the future could hold is here `docs/vision/pangaea-vision-visual.svg`
2. Read `docs/plan/pangaea-BUILDPLAN.md` and find the current phase + task.
3. Identify the test gate for that phase. Do not write feature code until you can describe exactly what "passing" looks like.

**Current phase:** PHASE 0  
**Current task:** 0.1 — Monorepo scaffold  
**Test gate:** `uv sync` succeeds · `xp validate` passes on stub manifests

Update these three lines at the start of each session based on what's passing.

## Repo layout (target)

```
pangaea/
├── services/          # Python/FastAPI microservices (uv workspaces)
│   ├── gateway/       # Session gateway (WebSocket) + provenance ledger
│   ├── registry/      # Capability manifest registry
│   ├── router/        # Intent router + ASR service
│   ├── broker/        # Token broker (OBO, RFC 8693)
│   ├── orchestrator/  # LangGraph orchestrator
│   ├── entity-resolver/
│   ├── concept-graph/ # Oxigraph JSON-LD graph service
│   └── telemetry/
├── apps/
│   ├── pangaea-shell/     # Next.js 15 PWA
│   └── pangaea-dashboard/ # Grafana provisioning
├── packages/
│   ├── a2ui-catalog/      # React component catalog + Zod schemas
│   ├── manifest-schema/   # JSON Schema for capability.yaml
│   ├── xp-cli/            # xp validate / xp publish CLI
│   └── mock-domain-stubs/ # 3 fake domain services (ports 8101–8103)
├── infra/
│   ├── docker-compose.yml
│   └── keycloak/
└── tests/
    ├── integration/
    └── e2e/               # Phase gate tests — these ARE the demos
```

## Commands

### Python services (uv)
```bash
uv sync --all-packages               # install all workspace packages
uv run pytest services/{name}/tests/ -v          # run service tests
uv run pytest tests/e2e/test_phase1_push_approval.py -v  # phase gate demo
uv run pytest tests/integration/ -v --timeout=30  # needs compose running
uv add <package>                     # never pip install
```

### Next.js apps (pnpm)
```bash
pnpm install                         # install all workspace packages
pnpm --filter pangaea-shell build    # must pass before task is done
pnpm --filter pangaea-shell dev
pnpm --filter a2ui-catalog test      # jest
pnpm --filter pangaea-shell test:e2e # playwright
```

### Local stack
```bash
docker compose up -d
docker compose ps                    # all must be "healthy"
xp validate path/to/capability.yaml  # exit 0 = valid
xp publish path/to/capability.yaml --registry-url http://localhost:8200
```

## Stack and conventions

### Python services
- **uv** for package management. `pyproject.toml` with `[project]` and `[tool.uv]` sections.
- FastAPI + Pydantic v2. Config via `pydantic_settings.BaseSettings` reading from `.env`.
- Every service has: `main.py`, `models.py`, `routes/`, `tests/`, `.env.example`.
- Black + ruff before committing. pytest-asyncio for async tests. 80% coverage minimum.

### Next.js apps
- Next.js 15, App Router, TypeScript strict. pnpm. Tailwind dark theme (`#0B0F1A`).
- shadcn/ui for base components. `next.config.ts` must have `output: 'standalone'`.

### Infrastructure
- `docker-compose.yml` is local development truth. Every service has a healthcheck.
- Ports documented in `infra/PORTS.md`. Environment variables flow `.env` → `docker-compose` → service.

## The invariants — never violate

1. **No standing credentials.** Every token: minted per-request, single-operation scope, TTL ≤ 600s.
2. **No code in A2UI surfaces.** Component ID + Zod-validated props only. No JSX, no eval, no `dangerouslySetInnerHTML`.
3. **No unresolved entities before dispatch.** Ambiguous entity = disambiguation card. Never guess.
4. **No model-generated confirmation cards.** Cards built from platform-fetched, platform-validated data only.
5. **Every consequential action has a receipt.** Missing ledger write = bug; stop immediately.
6. **Manifests are the contract.** If it's not in the manifest, the platform doesn't support it.
7. **Concept graph is auto-populated.** Never manually edit graph data — it comes from manifests.

## Naming conventions

| Use | Never use |
|-----|-----------|
| capability manifest | config, spec, schema (for the YAML file) |
| concept graph | ontology, taxonomy, knowledge graph |
| domain agent | microservice, backend service |
| routing | searching, querying (for intent resolution) |
| syscall | tool call, API call (in user-facing contexts) |
| OBO token | service token, API key |
| provenance receipt | audit log entry, event record |
| A2UI surface | generated UI, dynamic UI |
| entity spine | master data, golden record |

## Test conventions

- **Unit:** `services/{name}/tests/test_{module}.py` — one-line docstring per function stating which invariant it protects.
- **Integration:** `tests/integration/` — requires compose stack running.
- **E2E / phase gate:** `tests/e2e/test_phase{N}_{name}.py` — these are the stakeholder demos; each assertion prints in plain English.
- Test users: `alice@acme.com` (manager), `bob@acme.com` (engineer), `carol@acme.com` (HR), `dave@acme.com` (new employee). Employee IDs: `E-{5digits}`.
- Fixtures in `tests/fixtures/` and `mock-domain-stubs/data/seed.json` (faker-seeded, never production data).
- Ensure it adhreres to the goal and show the new capabilities built or bugs fixed and a visual way of the state of the system after each of the above

## Work rules

- One task at a time, one phase at a time. Finish the test gate before moving on.
- Build → test → integrate. Never wire first and test later.
- Every service gets `/healthz` and `tests/` before anything else.
- `xp validate` must pass on every `capability.yaml` before any service uses it.
- If an approach violates an invariant, document the blocker with `# INVARIANT:` prefix and do not proceed.
- When two valid approaches exist, pick the one that makes the test gate easier to write.

At the end of every session: all existing tests pass, at least one new test passes, `docker compose up` still works.
