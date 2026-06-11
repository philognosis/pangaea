# CLAUDE.md — Pangaea project instructions
# Claude Code reads this file automatically at the start of every session.

## First thing you do in every session

1. Read VISION.md completely. Every decision traces back to it.
2. Read BUILDPLAN.md and find the current phase + task.
3. Ask: what is the test gate for this phase?
   Do not write a single line of feature code until you could describe
   exactly what "passing" looks like.

---

## What we are building

Pangaea is the operating system of the organization. Not a portal, not an
integration platform, not an AI chatbot. An OS — where teams publish
capability manifests (drivers) and the platform handles routing, identity,
rendering, push, and trust on their behalf.

Northstar: any person in the org can discover, access, and complete any
work they are permitted to do — from one place, by expressing a human need,
without knowing what systems exist.

---

## How to work

**One task at a time. One phase at a time.**
Finish the current task's test gate before starting the next task.
Finish the current phase's test gate before starting the next phase.
The test gate is not a checkbox — it is a runnable test that proves the
northstar moved closer.

**Build → test → integrate. In that order.**
Build the piece in isolation first. Write its tests. Make them pass.
Then wire it into the larger system. Never wire first and test later.

**Every service gets /healthz and tests/ before anything else.**
No exceptions. A service without a health endpoint and a test directory
does not exist yet.

**Read the relevant section of BUILDPLAN.md before starting any task.**
The build plan has exact file paths, endpoint contracts, and test
assertions. Use them. Do not invent alternatives unless you've identified
a genuine conflict with VISION.md — in which case, document the conflict
as a code comment and resolve toward the vision.

---

## Stack and conventions

### Python services (all services/ directories)
- uv for package management. Always `uv add`, never `pip install`.
- pyproject.toml with [project] and [tool.uv] sections.
- FastAPI for all HTTP services. Pydantic v2 for models.
- pytest + pytest-asyncio for tests. Coverage target: 80% minimum.
- Every service has: main.py, models.py, routes/, tests/, .env.example
- Read .env via `from pydantic_settings import BaseSettings` in config.py
- All config documented in .env.example with description comments.
- Black + ruff for formatting. Run before committing.

### Next.js apps (all apps/ directories)
- Next.js 15, App Router, TypeScript strict mode.
- pnpm for package management.
- Tailwind CSS, dark theme default (background: #0B0F1A).
- shadcn/ui for base components.
- next.config.ts with `output: 'standalone'`.
- Build must pass (`pnpm build`) before a task is considered done.
- jest + React Testing Library for unit tests.
- playwright for e2e tests.

### Shared packages (packages/ directories)
- manifest-schema: JSON Schema, no runtime dependencies.
- xp-cli: Python/uv, click, rich, jsonschema, openapi-core.
- a2ui-catalog: React 19, TypeScript, Zod, no backend dependencies.
- mock-domain-stubs: FastAPI/uv, faker for seed data.

### Infrastructure
- docker-compose.yml is the local development truth.
- Every service referenced in compose has a healthcheck.
- Ports are documented in infra/PORTS.md (create if missing).
- Environment variables flow from .env → docker-compose → service.
  Never hardcode anything that differs between environments.

---

## The invariants (never violate)

These are from VISION.md. They are repeated here because they affect
code decisions every day:

1. **No standing credentials.** No persistent tokens to domain systems.
   Every token: minted per-request, single-operation scope, TTL ≤ 600s.

2. **No code in A2UI surfaces.** Component ID + Zod-validated props only.
   No JSX generation, no eval, no dangerouslySetInnerHTML. Ever.

3. **No unresolved entities before dispatch.** Ambiguous entity = 
   disambiguation card. Never guess. Never dispatch with a string name.

4. **No model-generated confirmation cards.** Cards are built from
   platform-fetched, platform-validated data. Model writes nothing
   that appears in a confirmation card.

5. **Every consequential action has a receipt.** Ledger write is not
   optional. Missing receipt = bug, stop immediately.

6. **Manifests are the contract.** If it's not in the manifest, the
   platform doesn't support it. No exceptions for "well it should work."

7. **Concept graph is auto-populated.** Never manually edit graph data.
   It comes from manifests, always.

---

## Naming conventions

Use these names everywhere — in code, comments, logs, error messages:

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

---

## Test conventions

### Unit tests
Location: services/{name}/tests/test_{module}.py
Run: `uv run pytest services/{name}/tests/ -v`
Every test function documents what invariant or northstar principle it
protects in a one-line docstring.

### Integration tests
Location: tests/integration/test_{scenario}.py
Require compose stack running: `docker compose up -d`
Run: `uv run pytest tests/integration/ -v --timeout=30`

### E2E / phase gate tests
Location: tests/e2e/test_phase{N}_{name}.py
These ARE the phase demos. Run them in front of stakeholders.
Run: `uv run pytest tests/e2e/test_phase1_push_approval.py -v`
Each assertion prints what happened in plain English.

### Test data
Never use production data. Always use faker-seeded fixtures.
Fixtures live in: tests/fixtures/ and mock-domain-stubs/data/seed.json
Employee IDs in tests always follow pattern: E-{5digits} (E-48291)
Test users: alice@acme.com (manager), bob@acme.com (engineer),
            carol@acme.com (HR), dave@acme.com (new employee)

---

## When you're stuck or uncertain

1. Re-read the relevant section of VISION.md.
2. Check if the uncertainty is about direction (vision wins) or
   implementation (use best judgment, document the choice).
3. If an approach would violate an invariant, do not proceed —
   document the blocker as a TODO with INVARIANT: prefix.
4. If two valid approaches exist, pick the one that makes the
   test gate easier to write. Testability is a design signal.

---

## What progress looks like

At the end of every work session, the repo should be in a state where:
- All existing tests still pass
- At least one new test passes that didn't before
- `docker compose up` still works
- The current phase's test gate is closer to passing than when you started

Progress is measured in passing tests, not in lines of code written.

---

## The phase we are currently in

**Set this when starting a session:**

Current phase: [ PHASE 0 ]
Current task:  [ 0.1 — Monorepo scaffold ]
Test gate:     [ uv sync succeeds · xp validate passes on stub manifests ]

Update this section at the start of each session based on what's passing.
