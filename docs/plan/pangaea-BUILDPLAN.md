# Pangaea — Claude Code Build Plan
**Status:** v0.1 · Ready for Claude Code execution
**Principle:** Build individual pieces → scaffold → integrate one by one.
Every phase is independently testable and demonstrates visible forward progress.

---

## Repository layout (target)

```
pangaea/
├── services/                   # Python/FastAPI microservices (uv workspaces)
│   ├── gateway/                # Session gateway (WebSocket)
│   ├── registry/               # Capability manifest registry
│   ├── router/                 # Intent router
│   ├── broker/                 # Token broker (OBO)
│   ├── orchestrator/           # LangGraph orchestrator
│   ├── entity-resolver/        # Cross-domain entity resolution
│   ├── concept-graph/          # Oxigraph JSON-LD graph service
│   └── telemetry/              # Intent analytics ingest
├── apps/
│   ├── pangaea-shell/          # Next.js 15 PWA (pnpm)
│   └── pangaea-dashboard/      # Grafana provisioning
├── packages/
│   ├── a2ui-catalog/           # React component catalog + Zod schemas
│   ├── manifest-schema/        # JSON Schema for capability.yaml
│   ├── xp-cli/                 # xp validate / xp publish CLI (Python/uv)
│   └── mock-domain-stubs/      # 3 fake domain services for dev/test
├── infra/
│   ├── docker-compose.yml      # Full local stack
│   ├── docker-compose.dev.yml  # Minimal dev subset
│   ├── k8s/                    # Helm charts (phase 4)
│   └── terraform/              # IaC (phase 4)
└── .github/
    └── workflows/
        ├── manifest-ci.yml     # xp validate on every PR
        └── test.yml            # pytest + jest per service
```

---

## PHASE 0 — Foundations (≈2 weeks)
**Goal:** Working monorepo, validated schema, fake domain teams, local stack running.
**Test gate:** `docker compose up` → all services healthy; `xp validate` passes and rejects correctly.

### 0.1 — Monorepo scaffold
```
Task: Initialise the monorepo with uv workspaces (services/*) and
      pnpm workspaces (apps/*, packages/a2ui-catalog).

Files to create:
  pyproject.toml                 # uv workspace root
  pnpm-workspace.yaml
  .env.example
  packages/manifest-schema/capability.schema.json
  packages/manifest-schema/README.md

Key pyproject.toml sections:
  [tool.uv.workspace]
  members = ["services/*", "packages/xp-cli"]

Test: uv sync --all-packages succeeds with zero packages installed yet.
```

### 0.2 — manifest-schema package
```
Task: Define the JSON Schema for capability.yaml v0.1.

Schema must enforce:
  - manifest version semver string
  - capability.id reverse-DNS format
  - lifecycle enum [draft|beta|ga|deprecated]
  - at least 1 fulfillment_mode
  - every action with risk=consequential has a confirmation block
  - every $ref resolves within the same document (lint only, not cross-validate)

Files:
  packages/manifest-schema/capability.schema.json
  packages/manifest-schema/tests/test_schema.py
    - valid manifests pass
    - missing confirmation on consequential action → fails
    - bad lifecycle value → fails
    - duplicate entity ownership → fails

Test: pytest packages/manifest-schema/tests/ → all pass
```

### 0.3 — xp CLI
```
Task: Build the xp validate and xp publish CLI tool.

Stack: Python/uv · click · jsonschema · openapi-core · httpx · rich

Commands:
  xp validate <path/to/capability.yaml>
    - loads YAML
    - validates against manifest-schema
    - resolves every operationId against the team's openapi.json URL
    - resolves every $ref entity type
    - prints rich ✓/✗ table per rule
    - exits 1 on any error

  xp publish <path/to/capability.yaml> --registry-url <url>
    - runs validate first; aborts if fails
    - POST /capabilities to registry
    - prints receipt

Files:
  packages/xp-cli/pyproject.toml
  packages/xp-cli/xp/cli.py
  packages/xp-cli/xp/validator.py
  packages/xp-cli/xp/publisher.py
  packages/xp-cli/tests/test_validator.py
  .github/workflows/manifest-ci.yml
    - on: pull_request paths: ['**/capability.yaml']
    - runs xp validate on changed manifests

Test: xp validate fixtures/valid.yaml → exit 0
      xp validate fixtures/missing-confirmation.yaml → exit 1 with clear error
```

### 0.4 — Mock domain stubs
```
Task: Three fake domain services that behave like real federated systems.
      These are the "real" backends for all subsequent phases — never replaced,
      only supplemented by real systems later.

Services:
  mock-domain-stubs/staffing/   → port 8101
  mock-domain-stubs/evals/      → port 8102
  mock-domain-stubs/feedback/   → port 8103

Each service must:
  - Have a capability.yaml at root
  - Expose OpenAPI 3.1 at /openapi.json
  - Return realistic mock data (seeded faker)
  - Have /healthz endpoint
  - Support Idempotency-Key header on write operations
  - Validate Bearer tokens (mock Keycloak validation)

Key endpoints (staffing as example):
  GET  /staff/history?emp={id}        → StaffingHistory[]
  GET  /staff/search?q={query}        → Employee[]
  POST /staff/roles                   → RoleRequest
  GET  /healthz                       → {"status":"ok"}

Files:
  mock-domain-stubs/staffing/main.py
  mock-domain-stubs/staffing/capability.yaml
  mock-domain-stubs/staffing/models.py
  mock-domain-stubs/staffing/data/seed.json  (faker-generated)
  (repeat for evals, feedback)

Test: pytest mock-domain-stubs/tests/test_stubs.py
      - all /healthz return 200
      - all /openapi.json valid against OpenAPI 3.1 spec
      - xp validate passes on each capability.yaml
```

### 0.5 — Docker Compose base stack
```
Task: docker-compose.yml that boots the full local environment.

Services:
  postgres:16-alpine    ports: 5432
  redis:7-alpine        ports: 6379
  nats:2.10             ports: 4222, 8222 (monitoring)
  keycloak:24           ports: 8080  (dev IdP)
  staffing-stub         ports: 8101
  evals-stub            ports: 8102
  feedback-stub         ports: 8103

Keycloak realm bootstrap:
  infra/keycloak/realm-pangaea.json
    - realm: pangaea
    - client: pangaea-platform  (service account)
    - client: staffing-service  (audience)
    - client: evals-service
    - test user: alice@acme.com / password=dev

Health checks on all services.
.env.example with all required vars.

Test: docker compose up -d → docker compose ps → all "healthy"
      curl localhost:8101/healthz → {"status":"ok"}
      curl localhost:8080/realms/pangaea → Keycloak realm JSON
```

**Phase 0 demo:** `docker compose up` → terminal shows all green → `xp validate` 
runs on three stub manifests → all pass. Schema rejects a broken manifest with 
a clear error. Visible, concrete, zero handwaving.

---

## PHASE 1 — Push · Trust · Render (≈6 weeks)
**Goal:** Full end-to-end flow: push notification arrives → user taps Approve → 
stub API called with OBO token → receipt sealed. All trust guarantees proven.
**Test gate:** Automated e2e test drives the entire flow; receipt verifiable in DB.

### 1.1 — Registry service
```
Task: The manifest store — the canonical list of what's federated.

Stack: FastAPI · uv · SQLAlchemy · Postgres · Alembic · httpx

Endpoints:
  POST /capabilities                → publish / upsert manifest
  GET  /capabilities                → list all (with lifecycle filter)
  GET  /capabilities/{id}           → get one
  GET  /capabilities/{id}/openapi   → proxied/cached OpenAPI doc
  POST /capabilities/{id}/health    → force health check
  GET  /healthz

Data model:
  capabilities table:
    id, name, version, lifecycle, manifest_yaml,
    openapi_url, health_url, owner_team, owner_slack,
    fulfillment_modes, slo_read_p95, slo_action_p95,
    published_at, last_healthy_at

Composition checks on publish:
  - No two capabilities claim ownership of same entity type
  - All $ref entity types resolve to a published capability
  - OpenAPI doc is reachable and valid
  - Health endpoint responds 200

Files:
  services/registry/main.py
  services/registry/models.py
  services/registry/routes/capabilities.py
  services/registry/composition.py   (federation checks)
  services/registry/alembic/
  services/registry/tests/

Test: pytest services/registry/tests/
  - publish 3 stubs → listed
  - duplicate entity ownership → 409
  - dangling ref → 422
  - unpublish one → refs to it flagged
```

### 1.2 — Token broker
```
Task: Mint short-lived, scoped, per-user OBO tokens. Never hold standing creds.

Stack: FastAPI · python-jose · httpx · Redis (TTL cache)

Keycloak token exchange (RFC 8693):
  POST /token/exchange
    body: { user_token, target_capability_id, required_scopes[] }
    1. validate user_token against Keycloak
    2. look up capability's audience + scopes from registry
    3. POST Keycloak /token with grant_type=urn:ietf:params:oauth:grant-type:token-exchange
    4. validate returned token has exactly required_scopes, no more
    5. cache in Redis with TTL = token expiry - 30s
    6. return { access_token, expires_in, capability_id, scopes }

Security invariants (tested):
  - broker cannot mint token for scopes not in manifest
  - broker cannot mint token for capability not in registry
  - TTL never exceeds manifest's token_ttl_seconds
  - no token stored longer than 600s

Files:
  services/broker/main.py
  services/broker/exchange.py
  services/broker/cache.py
  services/broker/tests/test_exchange.py
  services/broker/tests/test_invariants.py  ← security tests

Test: pytest services/broker/tests/
  - valid exchange → scoped token
  - over-scoped request → 403
  - unknown capability → 404
  - expired user token → 401
```

### 1.3 — Provenance ledger
```
Task: Append-only, hash-chained record of every consequential action.

Data model (Postgres):
  receipts table:
    id UUID PK,
    intent_text TEXT,           -- what the user said
    resolved_capability_id TEXT,
    resolved_entity_json JSONB, -- what was shown on the confirmation card
    action_id TEXT,
    user_sub TEXT,              -- from OBO token
    card_hash TEXT,             -- SHA256 of rendered confirmation card JSON
    committed_at TIMESTAMPTZ,
    idempotency_key TEXT UNIQUE,
    prev_hash TEXT,             -- chain link
    chain_hash TEXT,            -- SHA256(prev_hash + this record)
    signed_by TEXT              -- platform key fingerprint

Verification endpoint:
  GET /receipts/{id}/verify → { valid: bool, chain_intact: bool }

Files:
  services/gateway/ledger.py    (co-located with gateway for now)
  services/gateway/tests/test_ledger.py

Test: pytest test_ledger.py
  - 3 receipts written → chain_hash chain valid
  - tampered record detected by verify endpoint
  - idempotency_key prevents double-commit
```

### 1.4 — A2UI catalog v0
```
Task: The pre-approved component set. JSON in → rendered UI out.
      This is the structural defense: no arbitrary code, ever.

Stack: React 19 · TypeScript · Zod · shadcn/ui · Tailwind (dark theme)
Location: packages/a2ui-catalog/

Components to build (10):
  ActionCard         - push notification expandable card with action buttons
  ConfirmationCard   - deterministic pre-commit display for consequential actions
  EntityCard         - single entity summary (name, key fields, status badge)
  EntityPicker       - disambiguation selector (shows disambiguators)
  DataTable          - paginated table bound to array schema
  FormFlow           - multi-step guided form
  StatusBadge        - risk/status indicator
  SectionHeader      - labeled section with owning-system provenance tag
  CompositeLayout    - multi-section collated view (the mentee view)
  ReceiptView        - provenance receipt display

Each component:
  - Zod schema defining its JSON input (this IS the A2UI contract)
  - React component that renders from validated props
  - Storybook story
  - Accessibility: keyboard nav, ARIA labels, focus management

Renderer:
  packages/a2ui-catalog/src/renderer.tsx
    renderFromJSON(componentId: string, props: unknown): ReactElement
    - validates props against component's Zod schema
    - throws if componentId not in catalog (no escape hatch)

Files:
  packages/a2ui-catalog/src/components/
  packages/a2ui-catalog/src/schemas/
  packages/a2ui-catalog/src/renderer.tsx
  packages/a2ui-catalog/src/catalog.ts   (registry of all components)
  packages/a2ui-catalog/.storybook/

Test: jest packages/a2ui-catalog/
  - each component renders from valid JSON
  - renderer throws on unknown component ID
  - renderer throws on schema-invalid props
  - ConfirmationCard: props are frozen after render (no mutation)
```

### 1.5 — Session gateway + push service
```
Task: Single bidirectional WebSocket pipe per device.
      Push notification dispatch via NATS → pywebpush.

Stack: FastAPI · WebSockets · Redis · NATS · pywebpush · VAPID

Gateway responsibilities:
  WS /ws/{session_id}
    - authenticate session from cookie/header
    - relay A2UI messages from platform to client
    - relay user actions (taps, form submits) to platform
    - prefetch: on notification publish, compose A2UI surface and
                cache it so tap opens instantly

Push service:
  POST /push/subscribe    → store VAPID subscription
  POST /push/send         → internal; called by other services via NATS
  NATS subscription: push.events.> → fan out to subscribed devices

NATS topic contract:
  push.events.{capability_id}  payload: PushEvent (see manifest spec)

Files:
  services/gateway/main.py
  services/gateway/ws.py
  services/gateway/push.py
  services/gateway/prefetch.py
  services/gateway/tests/test_push_flow.py

Test: pytest test_push_flow.py (async, uses aiohttp test client)
  - subscribe → publish event → push received in <500ms
  - prefetch cache hit on tap
  - expired session rejected
```

### 1.6 — Intent router v0
```
Task: Route a text intent to a registered capability + action.
      Phase 1 version: keyword matching + Claude fallback. Accuracy over speed.

Stack: FastAPI · Redis · anthropic SDK

Algorithm:
  1. Redis HGET compiled_routes:{utterance_hash}  →  hit: return cached route
  2. Load all GA capabilities from registry (cached 60s)
  3. Build routing context: capability descriptions + intent utterances
  4. Claude API call:
       system: "You are an intent router. Given an utterance and a list of
                registered capabilities with their intent descriptions and
                example utterances, return JSON: { capability_id, intent_id,
                confidence, slots: {} }. Confidence below 0.85 means unclear."
       user: utterance
  5. confidence < 0.85 → return { needs_clarification: true, question }
  6. confidence >= 0.85 → cache in Redis (compiled route) + return

Endpoint:
  POST /route
    body: { utterance, user_context: { sub, roles } }
    response: RouteResult | ClarificationNeeded

Files:
  services/router/main.py
  services/router/router.py
  services/router/hot_paths.py
  services/router/tests/test_routing.py

Test: pytest test_routing.py
  - "approve the extension" → staffing.approve_extension
  - "show my pending evals" → evals.view_pending (hot path on 2nd call)
  - "xyzzy foobar" → needs_clarification
  - second identical call uses Redis cache (mock Claude to verify not called)
```

### 1.7 — E2E integration test (Phase 1 gate)
```
Task: Automated test that proves the full trust chain works.

Scenario: "Staffing stub emits extension_requested event → 
           push arrives on simulated browser → 
           user taps Approve → 
           OBO token minted → 
           stub's approve endpoint called → 
           receipt written and verifiable"

Tools: pytest-asyncio · httpx · playwright (headless browser for push)

Steps in test:
  1. Start full compose stack (fixture)
  2. Subscribe test browser to push (playwright)
  3. POST staffing-stub /internal/emit {type: extension_requested, employee: alice}
  4. Assert push notification arrives in browser within 3s
  5. Playwright: tap Approve button
  6. Assert staffing-stub received POST /extensions/EXT-1/approve
     with correct Idempotency-Key and OBO token (stub validates token)
  7. Assert receipt row exists in ledger with correct card_hash
  8. GET /receipts/{id}/verify → { valid: true, chain_intact: true }

Files:
  tests/e2e/test_phase1_push_approval.py

This test IS the phase 1 demo. Run it in front of stakeholders.
```

**Phase 1 demo:** Run `pytest tests/e2e/test_phase1_push_approval.py -v` in a 
terminal on a screen. Every step prints. At the end, open the ledger and show 
the receipt row. Full trust chain in one script.

---

## PHASE 2 — Voice · Routing · Agents (≈8 weeks)
**Goal:** Say an intent → guided flow appears. Multi-system composite view works.
**Test gate:** Voice → transcript → intent → A2A task → composite UI assembled.

### 2.1 — Intent router v1 (pgvector + hot-path compiler)
```
Upgrade router to use semantic similarity for cold paths.

Changes:
  - Embed all intent utterances from all capabilities on registry publish
    → store in pgvector (services/router/embeddings.py)
  - Cold path: cosine similarity search first, Claude only for low-confidence
  - Hot-path compiler: after a route is used 3+ times with same slot pattern,
    write a compiled route entry to Redis with TTL=24h
  - Metrics: track cold/hot ratio, confidence distribution → Prometheus

Test additions:
  - synonym utterance routes correctly via embedding (not just keyword)
  - hot-path compilation triggers after threshold
  - new capability publish → its utterances embedded within 10s
```

### 2.2 — Orchestrator (LangGraph)
```
Task: The kernel's process scheduler. Takes a resolved route and executes it,
      handling fan-out, sequencing, and result assembly.

Stack: LangGraph · python-a2a · asyncio · httpx

LangGraph nodes:
  resolve_entity    → calls entity-resolver service
  check_permissions → calls broker (can this user do this?)
  dispatch_direct   → httpx call to team API with OBO token
  dispatch_agent    → A2A task to domain agent
  assemble_result   → normalize + bind to A2UI layout
  write_receipt     → ledger write for consequential actions
  handle_ambiguity  → generate disambiguation card

Graph edges:
  route_result → resolve_entity → check_permissions
               → [direct|agent] dispatch (parallel for composite)
               → assemble_result → write_receipt (if consequential)

Fan-out pattern (composite views):
  asyncio.gather(*[dispatch(cap) for cap in resolved_capabilities])
  results normalized against shared entity spine (acme.directory#Employee)

Files:
  services/orchestrator/main.py
  services/orchestrator/graph.py
  services/orchestrator/nodes/
  services/orchestrator/normalizer.py
  services/orchestrator/tests/test_graph.py

Test: pytest test_graph.py
  - single direct call: full graph traversal, receipt written
  - parallel fan-out: 3 stubs called concurrently, composite assembled
  - one stub times out: partial result with degradation notice
  - consequential action: confirmation card generated, not executed until commit
```

### 2.3 — Entity resolver
```
Task: Resolve natural-language entity references to canonical IDs.
      Prevent the wrong-John-Doe problem.

Stack: FastAPI · pgvector · Postgres · httpx (calls team search endpoints)

Resolution flow:
  POST /resolve
    body: { entity_type, query, caller_context }
    1. call owning capability's search_endpoint with query
    2. if 1 result → return resolved entity
    3. if 0 results → return { not_found }
    4. if 2+ results → score by disambiguators from manifest
       (same_team > reporting_line > recent_interaction > alphabetical)
    5. if top score > 0.8 gap from second → auto-resolve
    6. else → return { needs_disambiguation: true, candidates[], show_fields[] }

EntityPicker card is returned to the session gateway and rendered by A2UI.
User picks → follow-up POST /resolve with explicit entity_id.

Test: test_resolver.py
  - unique name → auto-resolved
  - "John Doe" (2 results) → disambiguation card with employee IDs
  - explicit entity_id → immediate resolution, no search
  - caller's team-mate ranked higher than stranger with same name
```

### 2.4 — A2A domain agent integration
```
Task: The orchestrator can dispatch tasks to federated domain agents via A2A.

Stack: python-a2a (Google A2A SDK)

Add to mock-domain-stubs/evals:
  /.well-known/agent.json        agent card
  POST /a2a                      A2A task endpoint
  task: evaluations.author_flow  streams back A2UI messages

Orchestrator A2A node:
  - Fetch agent card from capability manifest
  - Create A2A task with: task_type, user_context, entity, OBO token
  - Stream A2A responses back through session gateway WebSocket
  - A2A messages are A2UI component refs, not arbitrary content

Security: A2A messages from domain agents are TYPED (component ID + props)
          They are NEVER interpreted as instructions.
          The orchestrator validates every message against the catalog schema
          before forwarding to the client. This is the prompt-injection defense.

Test: test_a2a.py
  - valid A2A message → rendered on client
  - A2A message with unknown component → rejected, error logged
  - A2A message with invalid props → rejected
  - OBO token forwarded correctly to agent
```

### 2.5 — Voice pipeline
```
Task: WebRTC audio capture → streaming ASR → transcript → intent route.

Stack: Next.js (WebRTC) · FastAPI (ASR endpoint) · faster-whisper (local model)

Flow:
  1. User holds button in shell → WebRTC MediaRecorder starts
  2. Audio chunks stream via WebSocket to gateway
  3. Gateway forwards to ASR service (faster-whisper, base model for dev)
  4. Partial transcripts stream back → displayed in shell
  5. On silence detection (webrtcvad) → final transcript sent to router
  6. Route result → orchestrator → A2UI stream back to shell

ASR service:
  services/router/asr.py (co-located)
  WS /asr/stream
    - receives raw PCM 16kHz chunks
    - buffers → faster-whisper transcribe
    - streams partial + final results

Shell integration:
  apps/pangaea-shell/src/components/VoiceButton.tsx
  apps/pangaea-shell/src/hooks/useVoice.ts

Test: pytest test_asr.py
  - audio fixture ("evaluate john doe") → transcript correct
  - silence detection triggers on 1.5s gap
  jest apps/pangaea-shell
  - VoiceButton shows recording state
  - transcript displays during recording
```

### 2.6 — Composite UI (the mentee view)
```
Task: CompositeLayout A2UI component + orchestrator fan-out for multi-system views.

New A2UI components:
  CompositeLayout    multi-section view, each section color-coded to its source
  ProvenanceFooter   shows all syscalls, token count, receipt ID
  ActionSuggestor    derives contextual actions from assembled payload

Orchestrator: add composite_view intent type
  - resolves multiple capabilities from intent
  - parallel fan-out to all resolved capabilities
  - normalizes entity references against entity spine
  - assembles CompositeLayout JSON
  - each section tagged with source capability_id (for color coding + provenance)

Add to router: composite intent recognition
  "show me everything about {person}"
  "mentee overview for {person}"
  "what do I know about {person}"

Test: e2e test_composite_view.py
  "show me everything about alice" →
    - 3 parallel syscalls to stubs
    - composite JSON assembled with 3 sections
    - ProvenanceFooter shows 3 capability IDs
    - each section renders correct component
    - action buttons present and linked to correct capabilities
```

**Phase 2 demo:** Two demos run back to back:
1. Voice: speak "evaluate alice" → disambiguation card → pick → guided form flow 
2. Composite: type "show me everything about alice" → one screen, three sections, 
   provenance footer showing three syscalls.

---

## PHASE 3 — Concept Graph · Discovery · Home Surface (≈8 weeks)
**Goal:** Undirected discovery works. New systems are auto-discoverable. 
Home surface is ambient and context-aware. 
**Test gate:** Need-based query with no capability named routes correctly.

### 3.1 — Concept graph service
```
Task: Semantic map of everything Pangaea can do.

Stack: FastAPI · Oxigraph (embedded RDF store) · JSON-LD · httpx

Graph schema (JSON-LD / lightweight OWL):
  Concept:   id, label, description, broader[], narrower[], related[]
  Capability: id, claims_concepts[], entity_types[]
  Intent:     id, capability, concepts[]

Population (automatic, on manifest publish):
  registry → emits NATS event capability.published
  concept-graph service subscribes → extracts concepts from:
    - capability.description (embed + cluster)
    - intent.description fields
    - entity type names
    - action descriptions
  → writes JSON-LD triples to Oxigraph

Query API:
  POST /concepts/resolve
    body: { utterance, top_k: 5 }
    1. embed utterance (sentence-transformers, all-MiniLM-L6-v2)
    2. cosine search in pgvector over concept embeddings
    3. for each matched concept → SPARQL: which capabilities claim it?
    4. return ranked capability candidates

  GET /concepts/{id}/related  → graph traversal
  GET /capabilities/{id}/concepts  → what does this capability cover?

Files:
  services/concept-graph/main.py
  services/concept-graph/graph.py       (Oxigraph wrapper)
  services/concept-graph/embedder.py    (sentence-transformers)
  services/concept-graph/ingestion.py   (manifest → triples)
  services/concept-graph/tests/

Test: pytest test_concept_graph.py
  - "recognize someone on my team" → rewards/HR capability ranked #1
  - "something is wrong with my pay" → HR/payroll capability found
  - new capability published → concepts appear in graph within 5s
  - graph traversal: staffing → related → skills → credentials
```

### 3.2 — Router v2: needs-based routing
```
Upgrade router to use concept graph for undirected queries.

New routing tiers (in order):
  1. Exact compiled hot-path (Redis)       → <50ms
  2. pgvector intent similarity             → <200ms
  3. Concept graph traversal               → <400ms
  4. Claude with full context               → <2000ms

Tier 3 is the new addition: when tiers 1+2 fail or low confidence,
query concept-graph service with utterance → get candidate capabilities
→ pass to Claude with just those candidates (smaller context → faster + cheaper)

If no tier resolves above 0.85: return exploration suggestions
  "I found a few things that might help: [capability cards]"
  This renders as an ExplorationCard A2UI component.

Test: test_routing_v2.py
  - tier 1: compiled route, no service calls beyond Redis
  - tier 2: synonym not in training data, embedding finds it
  - tier 3: vague need, concept graph surfaces candidates
  - tier 4: truly novel, Claude with small candidate set
  - performance: tier 1 p99 < 50ms, tier 3 p99 < 400ms (stub latencies)
```

### 3.3 — Home surface
```
Task: What Pangaea shows you when you open it with no intent.
      The lock screen + home screen of the org OS.

Three panels:
  Pending          actions awaiting the user (from push event store)
  Your context     role-relevant capabilities (from registry + user roles)
  Suggested        3 things Pangaea thinks you might want to do today
                   (based on role, time of day, peers' recent activity)

Data sources:
  Pending:    gateway's push event store, filtered by user.sub
  Context:    registry filtered by visibility.discoverable_by matching user roles
  Suggested:  simple heuristic v0: most-used intents by same-role users (ClickHouse)
              → displayed as quick-action chips

Shell changes:
  apps/pangaea-shell/src/app/page.tsx → HomeScreen
  New A2UI component: HomeSurface (layout + three panels)
  New A2UI component: QuickActionChip

Test: jest + playwright
  - user with 2 pending approvals → both shown in Pending panel
  - user with manager role → staffing + evals in Context panel
  - empty pending → "You're all caught up" invitation state
```

### 3.4 — Intent telemetry + failed intent reports
```
Task: ClickHouse ingest + Grafana dashboard.
      Failed intents become the roadmap generator.

Events to capture:
  intent_routed    { utterance_hash, capability_id, intent_id, tier_used,
                     latency_ms, confidence, user_role, ts }
  intent_failed    { utterance, reason, tier_reached, user_role, ts }
  action_committed { capability_id, action_id, risk_tier, latency_ms, ts }

ClickHouse schema: one table per event type, MergeTree engine

Grafana dashboards:
  Intent routing   - volume, tier distribution, latency p50/p95/p99
  Per capability   - which intents fire, trending up/down
  Failed intents   - top unrouted utterances this week (these are feature requests)
  Actions          - approval cycle time: from push event to committed receipt

Weekly digest job (cron, every Monday):
  - Query ClickHouse for failed intents grouped by cluster
  - POST to NATS → each capability's team Slack webhook (configurable in manifest)
  - "These 47 users asked for X and we had nothing for them"

Test: pytest test_telemetry.py
  - 10 routed intents → ClickHouse row count = 10
  - 3 failed intents → appear in failed_intents table
  - weekly digest job produces correct Slack payloads
```

**Phase 3 demo:** Three demos:
1. Undirected: "I want to do something nice for my team" → ExplorationCard → 3 options
2. New capability: publish a new stub → `xp publish` → ask about it → discovered instantly
3. Home surface: open Pangaea → 2 pending approvals visible → tap one → done

---

## PHASE 4 — Harden · Scale · Pilot (ongoing)

### 4.1 — Production IdP (Okta / Azure AD)
Replace Keycloak dev setup with real IdP. OBO flow unchanged — only config changes.
Test: prod token round-trip in staging environment.

### 4.2 — k8s deploy
Helm charts for all services. Resource limits. HPA on gateway and router.
Liveness/readiness probes tied to existing /healthz.
Test: k6 load test → p95 latency within SLO under 10× baseline traffic.

### 4.3 — Security hardening
- Pen test: verify no god tokens exist anywhere in the system
- Verify OBO token cannot exceed manifest-declared scopes
- Verify A2A content plane isolation (injected text → never executed)
- Verify provenance chain tamper detection
All automated as pytest-security suite.

### 4.4 — Accessibility + i18n
- Catalog components: WCAG 2.2 AA audit (axe-playwright)
- All strings in i18n JSON files
- RTL layout support in CompositeLayout
- Screen reader testing: NVDA + VoiceOver fixtures

### 4.5 — First real team onboarding
White-glove with one real team:
1. Run `xp validate` on their existing OpenAPI doc → fix gaps
2. Write their capability.yaml together (1 day)
3. `xp publish` to staging registry
4. Test their intents route correctly
5. Wire one push notification
6. Go live
Measure: time-to-federation (target: <1 week end-to-end)

### 4.6 — Before/after dashboard
Publish publicly inside org:
- Engineering hours on frontend per team, per quarter (self-reported)
- Approval cycle time: before and after push notifications
- Security review duration: Pangaea inherits vs standalone app
- Failed intent rate: the gap between what people ask for and what exists

---

## Summary: what gets built in what order

```
P0  schema → CLI → stubs → compose          → everything validates, nothing integrates yet
P1  registry → broker → ledger → A2UI → push → first real flow; trust chain proven
P2  router++ → orchestrator → A2A → voice    → say it, see it; composite view works
P3  concept-graph → discovery → home → telem → OS-level; undirected need finds right system
P4  prod IdP → k8s → security → pilot teams → real usage, real numbers
```

Every phase ends with a demo that stakeholders can see and engineers can run.
Every phase produces artifacts that survive into production unchanged.
Nothing is thrown away.

---

## Claude Code instructions

When executing this plan:
1. Work phase by phase. Never start a phase until its test gate passes.
2. Within a phase, work task by task. Build → test → integrate.
3. Every service gets a `/healthz` endpoint and a `tests/` directory before anything else.
4. Every `.env` var gets a matching entry in `.env.example` with a description.
5. The docker-compose.yml is the source of truth for service topology.
6. `xp validate` must pass on every capability.yaml before any service uses it.
7. Never hardcode credentials; always read from environment.
8. Each service's README.md documents: purpose, endpoints, env vars, how to run, how to test.
