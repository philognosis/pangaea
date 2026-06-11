# PANGAEA — Master Reference Document
# The single source of truth for Claude Code.
# Read this document completely before writing a single line of code.
# Every implementation decision traces back to something here.
#
# Version: 1.0  |  Status: Authoritative
# Synthesised from all design artifacts produced in the Pangaea design session.
# ─────────────────────────────────────────────────────────────────────────────

---

# PART 0 — HOW TO READ THIS DOCUMENT
# ─────────────────────────────────────────────────────────────────────────────

This document is structured in eight parts. Read them in order the first
time. After that, use the part headings as a reference index.

  PART 0  — How to read this document         (you are here)
  PART 1  — What Pangaea is. The northstar.   (read first, always)
  PART 2  — Architecture overview             (the whole system at a glance)
  PART 3  — The capability manifest           (the team contract — the driver)
  PART 4  — Agentic architecture              (where agency lives and why)
  PART 5  — Headless agents                   (background intelligence layer)
  PART 6  — The phased build plan             (what to build, in what order)
  PART 7  — Working rules for Claude Code     (how to behave while building)
  PART 8  — Reference manifests               (three complete worked examples)

When a conflict exists between any section and PART 1, PART 1 wins.
When a conflict exists between any section and PART 7's invariants,
the invariant wins. Raise the conflict as a code comment before proceeding.

---

# PART 1 — WHAT PANGAEA IS. THE NORTHSTAR.
# ─────────────────────────────────────────────────────────────────────────────

## 1.1 The one sentence that governs everything

> Any person in the organization can discover, access, and complete any work
> they are permitted to do — from one place, by expressing a human need,
> without knowing what systems exist.

Every line of code either moves toward this sentence or it doesn't.

## 1.2 What Pangaea is

Pangaea is the operating system of the organization.
Not a portal. Not a search engine. Not an integration platform. An OS.

Just as an OS provides applications with identity, storage, display, and
inter-process communication so that no application solves those problems
itself — Pangaea provides every internal capability team with intent
routing, identity delegation, trust, rendering, and push delivery, so
that no team ever builds a frontend, wires SSO, passes a security review,
or solves accessibility again.

The geological name is deliberate. Pangaea was one landmass before
continental drift fragmented it. Internal enterprise software drifted the
same way — one app per capability, each its own island. Pangaea reassembles
the landmass. The continents keep their terrain. The ocean disappears.

## 1.3 What Pangaea is NOT

Not enterprise search    — search finds the page; Pangaea finishes the task.
Not an iPaaS             — integration platforms wire systems to systems;
                           Pangaea wires humans to systems through intent.
Not a design system      — a design system still requires teams to build UIs;
                           Pangaea eliminates the frontend for federated teams.
Not a chatbot            — a chatbot is one system's conversational wrapper;
                           Pangaea's voice/chat is one of four entry points
                           to every system in the org.
Not an automation layer  — automation replaces humans; Pangaea surfaces the
                           right thing to the right human at the right moment.

The right comparison is iOS: it gave developers identity, push, rendering,
and payments once. Every app is better for it. Pangaea does this for
internal capabilities. Power compounds with every team that federates.

## 1.4 The end goal — what "done" looks like

An employee opens Pangaea on their phone. No URL. No install (PWA).
Home screen: pending work from every connected system, role-relevant
quick actions, a voice/search bar.

They say: "I want to recognise Maya for the platform work she did."

They do not know which system handles recognition. They do not know if
it is called "recognition," "rewards," "kudos," or a URL they've never
visited. They said what they want.

Pangaea's concept graph traverses the org's semantic map, finds that
acme.rewards claims the concept recognition → peer_acknowledgement,
routes to it, resolves "Maya" to Maya Chen (E-29183, Team Atlas) via
the entity spine, and streams back a guided form scoped to what the
caller is permitted to do.

Two fields. Tap Submit. A short-lived token is minted for exactly this
action. The rewards API is called. A provenance receipt is sealed. A push
notification lands on Maya's lock screen. Forty-five seconds. No URL.
No login. No documentation.

That is done.

## 1.5 The seven core architectural principles

These are the load-bearing walls. Never compromise them.

### P1 — System calls, not tool calls
When a user expresses a need, Pangaea resolves it through the concept
graph to the right system, then to the right operation within that system
— exactly like a kernel dispatching a syscall through the right driver.
The user never names a system. The platform discovers it.

Each syscall:
  - Carries a short-lived, scope-limited, per-user OBO token
  - Is recorded in the provenance ledger
  - Returns typed, schema-validated data (not free text)
  - Is invisible to the user unless they ask for the provenance footer

### P2 — Teams own the verbs. Pangaea owns distribution and trust.
A team's capability manifest is their driver registration. Once registered,
Pangaea handles discovery, routing, rendering, push, identity, and audit.
The team never loses ownership. Their API remains the policy enforcement
point. Their domain agent is a first-class participant, not a backend.
"Federate the experience, not the ownership."

### P3 — The concept graph is the PATH
Like Unix PATH letting you type `git` without knowing where it lives,
the concept graph is a semantic map of concepts → capabilities. Vague
or undirected needs find the right system through it. It is:
  - Auto-populated from manifests (no curation, no committee)
  - Queryable by semantic similarity (embeddings, not keywords)
  - Live-updated within seconds of xp publish
  - The authoritative answer to "what can Pangaea do?"

### P4 — Model proposes. Deterministic surface confirms. Human commits.
For any action above read risk, exactly one path to execution exists:
  model resolves intent
    → deterministic confirmation card built from resolved entity data
    → human commits with explicit tap
    → OBO token minted for exactly this action
    → domain API called
    → receipt sealed

The model never commits an action. Cards are never model-generated.

### P5 — Content plane and control plane never mix
Data from domain systems is typed payload bound to A2UI component
schemas. It is never interpreted as instructions. A field in a staffing
record cannot influence what the orchestrator does next. This is the
structural defense against prompt injection — architecture, not policy.

### P6 — Compiled paths are the performance contract
The LLM is in the cold path only. Once a route stabilises, it compiles
to a deterministic Redis entry. Second call: model not invoked, <50ms.
The system gets faster the more it is used. Heavy users get the best
experience, not the worst.

### P7 — The entity spine is mandatory
Every composite view, cross-system query, and disambiguation decision
anchors to the org's canonical entity spine (directory/IdP). Every domain
system references entities from the spine; none owns canonical identity.
No syscall is dispatched with an unresolved entity. Ever.

## 1.6 The four entry points (highest to lowest value per user-second)

  1. Push notifications + action cards
     Work arrives at the user. Tap Approve on the lock screen. Done.
     Highest leverage. Built first.

  2. Home surface
     Ambient state of the user's work world. Pending items, role-relevant
     capabilities, suggested actions. Shown when no intent is expressed.

  3. Voice and chat
     Natural language → routing → entity resolution → task → result.
     For intentional, initiated workflows.

  4. PWA shell
     Browsable, visual surface. Pinned layouts (spatial memory is a
     feature). Adapts only on explicit user request.

## 1.7 Naming conventions — use everywhere, without exception

  Use                  | Never use
  ─────────────────────┼──────────────────────────────────────
  Pangaea              | "the system", "the platform" alone
  capability manifest  | config, spec, schema (for the YAML)
  concept graph        | ontology, taxonomy, knowledge graph
  domain agent         | microservice, backend service
  routing              | searching, querying (for intent resolution)
  syscall              | tool call, API call (in user-facing copy)
  OBO token            | service token, API key
  provenance receipt   | audit log entry, event record
  A2UI surface         | generated UI, dynamic UI
  entity spine         | master data, golden record

## 1.8 Non-goals — never build these

  - Domain logic. Pangaea never decides who to evaluate or approve.
  - Domain data at rest. Platform caches for performance; never persists.
  - Domain schema governance. Manifests must be structurally valid;
    how a team models their domain is their business.
  - Cross-domain sagas before Phase 3 telemetry proves the need.
  - A formal OWL/RDF ontology with a standing committee.

---

# PART 2 — ARCHITECTURE OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────

## 2.1 System layers (top to bottom)

  ┌─────────────────────────────────────────────────────────────┐
  │  SURFACES (Phase 1+2)                                        │
  │  PWA Shell · Web Push · Voice · Chat                         │
  │  Next.js 15 · Serwist SW · WebRTC · VAPID                   │
  ├─────────────────────────────────────────────────────────────┤
  │  A2UI RENDERER (Phase 1)                                     │
  │  React 19 · shadcn/ui · Zod schema validation               │
  │  Catalog components only. No arbitrary code. Ever.          │
  ├─────────────────────────────────────────────────────────────┤
  │  PLATFORM AGENTS — TIER 2 (Phase 1–3)                       │
  │  Intent agent · Orchestrator · Discovery · Home surface      │
  │  LangGraph · Claude API · asyncio fan-out                   │
  ├─────────────────────────────────────────────────────────────┤
  │  DETERMINISTIC KERNEL — TIER 1 (Phase 1)                    │
  │  Trust fabric · Token broker · Entity resolver              │
  │  Hot-path router · Session gateway · Registry               │
  │  FastAPI · Redis · pgvector · OPA · Postgres ledger         │
  ├─────────────────────────────────────────────────────────────┤
  │  HEADLESS AGENTS (Phase 1–3)                                 │
  │  Concept graph ingestion · Proactive watch                  │
  │  Cross-domain watch · Failed-intent digest                  │
  │  NATS JetStream · sentence-transformers · ClickHouse        │
  ├─────────────────────────────────────────────────────────────┤
  │  DATA LAYER                                                   │
  │  Postgres · pgvector · Redis · Oxigraph · ClickHouse · MinIO│
  ├─────────────────────────────────────────────────────────────┤
  │  FEDERATED DOMAIN SYSTEMS (team-owned, dashed boundary)     │
  │  Domain agents (A2A) · Domain APIs (OpenAPI 3.1)            │
  │  capability.yaml · entity spine (directory/Keycloak)        │
  └─────────────────────────────────────────────────────────────┘

## 2.2 Repository structure

  pangaea/
  ├── services/                  # Python/FastAPI microservices (uv workspaces)
  │   ├── gateway/               # Session gateway · WebSocket · Redis sessions
  │   ├── registry/              # Manifest store · composition checks
  │   ├── router/                # Intent router · hot-paths · ASR
  │   ├── broker/                # Token broker · RFC 8693 OBO · Keycloak
  │   ├── orchestrator/          # LangGraph · A2A dispatch · fan-out
  │   ├── entity-resolver/       # Cross-domain entity resolution · pgvector
  │   ├── concept-graph/         # Oxigraph · JSON-LD · embeddings
  │   └── telemetry/             # ClickHouse ingest · intent analytics
  ├── apps/
  │   ├── pangaea-shell/         # Next.js 15 PWA · pnpm · Tailwind · dark theme
  │   └── pangaea-dashboard/     # Grafana provisioning
  ├── packages/
  │   ├── a2ui-catalog/          # React components · Zod schemas · Storybook
  │   ├── manifest-schema/       # JSON Schema v0.1 for capability.yaml
  │   ├── xp-cli/                # xp validate · xp publish · Python/uv/click
  │   └── mock-domain-stubs/     # 3 fake domain services for dev/test
  ├── infra/
  │   ├── docker-compose.yml     # Full local stack (source of truth)
  │   ├── k8s/                   # Helm charts (Phase 4)
  │   └── terraform/             # IaC (Phase 4)
  └── tests/
      ├── e2e/                   # Phase gate tests (these ARE the demos)
      └── integration/           # Cross-service integration tests

## 2.3 Full technology stack

  Layer                  | Technology
  ───────────────────────┼────────────────────────────────────────────────
  PWA shell              | Next.js 15 (App Router) · Tailwind · Serwist
  Component catalog      | React 19 · shadcn/ui · Zod · TypeScript strict
  Session gateway        | FastAPI · WebSockets · Redis · uvicorn
  Intent router          | FastAPI · Redis hot-paths · Claude API · pgvector
  Orchestrator           | LangGraph · python-a2a · asyncio · httpx
  Trust fabric / broker  | FastAPI · python-jose · Keycloak (dev) / Okta (prod)
  Policy engine          | OPA (open-policy-agent)
  Provenance ledger      | Postgres append-only table · KMS signing
  Registry               | FastAPI · Postgres · Alembic · jsonschema
  Concept graph          | Oxigraph (embedded RDF) · JSON-LD · pgvector
  Embeddings             | sentence-transformers (all-MiniLM-L6-v2)
  Voice / ASR            | WebRTC · faster-whisper · webrtcvad
  Event bus              | NATS JetStream
  Push notifications     | pywebpush · VAPID
  Telemetry              | OpenTelemetry → ClickHouse · Grafana · Prometheus
  Object storage         | MinIO (dev) / S3 (prod)
  CI / validation        | GitHub Actions · xp CLI · pytest · jest
  Infra (prod)           | k3s / Kubernetes · Terraform
  Local dev              | Docker Compose · .env files

## 2.4 The syscall model (how intent becomes action)

  User: "Evaluate John Doe"
         │
         ▼
  1. Session gateway receives utterance (WebSocket or voice)
         │
         ▼
  2. Hot-path router: Redis lookup on utterance hash
     HIT  → deterministic route (<50ms, no model)
     MISS → Intent agent (LangGraph + Claude haiku)
              → query_concept_graph()
              → classify_intent() — structured JSON output
              → confidence < 0.85 → clarifying question
              → confidence ≥ 0.85 → RouteResult
              → compile_hot_path() — next call is a HIT
         │
         ▼
  3. Entity resolver: "John Doe" → search_directory()
     1 result   → auto-resolved (E-48291)
     2+ results → EntityPicker card (disambiguation)
     The wrong-John-Doe problem is solved here, before dispatch.
         │
         ▼
  4. Trust fabric: check_rbac(caller, capability, action)
     Token broker: mint_obo_token(user_token, evals, [evals.write])
     TTL ≤ 300s. Scopes ⊆ manifest.auth.scopes. No god tokens.
         │
         ▼
  5. Orchestrator (LangGraph): dispatch
     direct mode  → dispatch_direct(evals, authorFlow, params, token)
     agent mode   → dispatch_agent(evals, author_flow, context, token)
     composite    → fan_out_parallel([evals, staffing, learning])
         │
         ▼
  6. Domain system executes. Returns typed data.
         │
         ▼
  7. If consequential: build_confirm_card() → WAIT_FOR_HUMAN
     Card is frozen from resolved entity data. Model writes nothing in it.
     Human taps → confirmed signal
         │
         ▼
  8. write_receipt() → ledger (before dispatch, always)
         │
         ▼
  9. A2UI renderer: render(componentId, validated_props)
     stream_to_ws(session_id, a2ui_message)
         │
         ▼
  User sees the guided evaluation form on their screen.

## 2.5 The federated model — how teams join

  Team gives:      one capability.yaml · one afternoon · an OpenAPI doc
  Team receives:   voice + chat + push + PWA surfaces
                   SSO and delegated identity (OBO)
                   pre-certified security and accessibility
                   WCAG 2.2 AA across all surfaces
                   signed audit trail for every action
                   intent telemetry (what users ask for, including gaps)

  The team's API remains their policy enforcement point.
  The team's data never rests in Pangaea.
  The team's domain agent is a first-class A2A participant.

---

# PART 3 — THE CAPABILITY MANIFEST
# ─────────────────────────────────────────────────────────────────────────────

## 3.1 What the manifest is (and is not)

The capability manifest is the single contract between a domain team and
the platform. It is NOT:
  - Documentation (it is the contract, deployed like code)
  - A DSPy tool definition (it governs every layer, not just routing)
  - A configuration file (it drives trust, rendering, push, and auth)
  - An API spec (it references an OpenAPI doc; never duplicates schemas)

It IS:
  - A driver registration (OS layer) — declares existence to the kernel
  - A trust contract (security layer) — scopes, risk tiers, OBO config
  - A rendering contract (UX layer) — A2UI bindings, notification templates

## 3.2 Top-level structure

  manifest: "0.1"       # spec version
  capability: {...}     # id, name, description, owner, lifecycle, version
  runtime: {...}        # api endpoints, fulfillment modes, SLOs, health
  auth: {...}           # idp, audience, OBO flow, TTL, scopes
  entities: [...]       # owned entities + federated refs + enrichment refs
  intents: [...]        # what users can ask for, with utterances + slots
  actions: [...]        # what can be done, with risk tiers
  surfaces: {...}       # A2UI catalog version + component bindings
  notifications: [...]  # push events, templates, action buttons
  context_hints: [...]  # composite view enrichment from other capabilities
  watch_conditions: []  # proactive watch agent triggers (v0.2)
  policy: {...}         # authorization model, PII fields, visibility
  observability: {...}  # telemetry opt-in, SLO alerts, digest config

## 3.3 Risk tiers — the most important field in any action

  read          No token escalation. No receipt required.
                Enforced by team's API. Audit retention: 30–90 days.

  reversible    OBO token minted. Receipt written.
                Undo window may be declared. Audit retention: 365+ days.

  consequential OBO token minted. Receipt written BEFORE dispatch.
                Deterministic confirmation card mandatory.
                explicit_tap required. voice_blocked: true recommended.
                Audit retention: 2555+ days (7 years, HR compliance).

## 3.4 Entity ownership rules

  - Every entity type is owned by exactly one capability (owns: true)
  - All other capabilities reference it: ref: acme.directory#Employee
  - The registry rejects composition if two capabilities claim the same type
  - enrichment_only: true means read-only context, never stored
  - The entity spine (acme.directory) is the one mandatory federated capability
  - All Employee and Team refs resolve against it

## 3.5 Intents — the highest-leverage text in the manifest

The intent description and utterances[] are what the cold-path router
reads to classify user input. Write them the way a new employee would
describe the action. Be specific. Include variations. 3–10 utterances.

  description: >
    Start, resume, or complete a performance evaluation for a specific
    employee. Opens the guided evaluation authoring flow...

  utterances:
    - "evaluate {employee}"
    - "write {employee}'s evaluation"
    - "I need to evaluate {employee} for {cycle}"
    → seeded into LLM routing context AND compiled hot-path table

## 3.6 Confirmation block — mandatory for consequential

  confirmation:
    template: >
      Submit evaluation for {{subject.full_name}}
      ({{subject.employee_id}}, {{subject.team.name}}) — cycle {{cycle.name}}.
    show_fields: [subject.full_name, subject.employee_id, cycle.name, overall_rating]
    requires: [explicit_tap]
    voice_blocked: true

  The template is rendered from RESOLVED entity data.
  The model provides zero input. The card is frozen after construction.

## 3.7 Context hints — the composite view pattern

  context_hints:
    - for_entity: acme.directory#Employee
      enrich_from:
        - capability: acme.staffing
          fetch: staffing_history
          display_as: StaffingTimeline
          section_label: "Staffing history"

  When Pangaea assembles a composite view (e.g. mentee overview),
  it reads context_hints, fires parallel syscalls to each capability,
  and assembles the result into a CompositeLayout A2UI surface.
  No capability stores another's data at rest. Fetched in transit only.

## 3.8 Watch conditions — proactive headless triggers (v0.2)

  watch_conditions:
    - id: placement_ending_soon
      poll_endpoint: /watch/placements/ending-soon
      poll_interval_minutes: 60
      threshold_field: days_remaining
      threshold_value: 30
      cooldown_hours: 24
      notify_intent: approve_extension
      notify_roles: [manager_of_subject]

  Declares to the Proactive watch agent what to poll and when to push.
  No agent code required from the team. Manifest is sufficient.

## 3.9 The xp CLI

  xp validate capability.yaml
    - JSON Schema validation against manifest-schema
    - Resolves every operationId against the team's openapi.json
    - Resolves every $ref entity against registry
    - Checks consequential actions have confirmation blocks
    - Exits 1 on any error with precise messages

  xp publish capability.yaml --registry-url <url>
    - Runs validate first; aborts on failure
    - POST /capabilities to registry
    - Registry runs composition checks (no duplicate entity ownership,
      no dangling refs, health endpoint reachable)
    - On success: NATS event fires, concept graph updates within ~5s

---

# PART 4 — AGENTIC ARCHITECTURE
# ─────────────────────────────────────────────────────────────────────────────

## 4.1 The three-tier model

  Tier 1 — Deterministic kernel    No LLM. Always fast. Enforces invariants.
  Tier 2 — Platform agents         LLM + tools. Agentic with guardrails.
  Tier 3 — Domain agents           Full autonomy. Team-owned. A2A protocol.

Agency never flows backward. A domain agent cannot override the trust
fabric. A platform agent cannot write a confirmation card.

## 4.2 Tier 1 — Deterministic kernel

### Trust fabric tools (called by everything, never by a model directly)
  mint_obo_token(user_token, capability_id, required_scopes[]) → token
  validate_scope(token, required_scope) → allowed | forbidden
  check_rbac(user_sub, capability_id, action_id) → permitted | denied
  write_receipt(intent, card_hash, action, user_sub, idempotency_key) → id
  verify_chain(receipt_id) → { valid, chain_intact }

### A2UI renderer tools (catalog components only, never arbitrary markup)
  render(component_id, props_json) → ReactElement | schema_error
  build_confirm_card(action, resolved_entity_json, show_fields[]) → card
  stream_to_ws(session_id, a2ui_message) → delivered

### Hot-path router tools (deterministic, Redis-backed)
  lookup_compiled(utterance_hash) → RouteResult | miss
  write_compiled(utterance_hash, route_result) → stored
  similarity_search(embedding, top_k) → [{ intent_id, capability_id, score }]

### Entity resolver tools (deterministic scoring, never guesses)
  search_directory(entity_type, query, caller_context) → [EntityCandidate]
  rank_candidates(candidates[], disambiguators[], caller_context) → ranked
  build_disambig_card(candidates[], show_fields[]) → EntityPicker

## 4.3 Tier 2 — Platform agents

### Intent agent
  Model:    claude-3-5-haiku (fast, high frequency)
  Trigger:  hot-path miss
  Tools:    query_concept_graph() · get_capability_intents()
            classify_intent() · extract_slots()
            generate_clarification() · compile_hot_path()
  Guardrails:
    - Route only to registry capabilities (lifecycle: beta | ga)
    - Route only to capabilities discoverable_by caller's roles
    - confidence < 0.85 → clarify (never guess)
    - Max 3 clarification rounds → ExplorationCard
    - Output is structured JSON only, never free-form

  LangGraph graph:
    check_hot_path → [HIT: return] → [MISS:]
    → check_similarity → [high confidence: return] → [low:]
    → query_concept_graph → classify_intent
    → check_confidence → [low: generate_clarification]
    → extract_slots → compile_route → RouteResult

### Orchestrator agent
  Model:    claude-3-5-sonnet (complex multi-step, lower frequency)
  Trigger:  RouteResult from Intent agent
  Tools:    dispatch_direct() · dispatch_agent() · fan_out_parallel()
            normalize_entities() · assemble_composite()
            request_confirmation() · handle_partial_failure()
  Guardrails:
    - dispatch_direct always calls mint_obo_token first
    - consequential actions: confirm_gate cannot be skipped
    - write_receipt must complete before action dispatch
    - domain agent A2UI messages validated against catalog schema
    - partial failures → degraded render, never silent drop

  LangGraph graph (checkpointed, resumable across sessions):
    resolve_entity → check_permissions
    → [direct: dispatch_direct] | [agent: dispatch_agent]
    → [composite: fan_out_parallel]
    → assemble_composite
    → [consequential: request_confirmation → CHECKPOINT → WAIT_FOR_HUMAN]
    → write_receipt → dispatch → stream_result

### Discovery agent
  Model:    claude-3-5-haiku
  Trigger:  tier 1+2 routing fails OR undirected utterance
  Tools:    semantic_search_concepts() · traverse_concept_graph()
            get_related_capabilities() · score_capability_fit()
            generate_exploration_card() · suggest_next_actions()
  Output:   ExplorationCard A2UI component
  Guardrails:
    - ExplorationCard is read-only; no actions executed at this stage
    - suggest_next_actions uses aggregate patterns, never individual PII
    - capabilities shown must pass discoverable_by for this user

### Home surface agent
  Model:    claude-3-5-haiku
  Trigger:  session open (runs in background, cached 15 min)
  Tools:    get_pending_actions() · get_role_capabilities()
            query_peer_patterns() · rank_suggestions()
            prefetch_surface() · personalise_layout()
  Output:   HomeSurface A2UI component (3 panels: Pending, Context, Suggested)

## 4.4 Tier 3 — Domain agents (team-owned)

Every domain agent MUST:
  1. Expose /.well-known/agent.json (agent card)
  2. Accept A2A tasks at /a2a
  3. Stream responses as A2UI messages only
     { component_id: "GuidedFormFlow", props: {...} }
     Never stream raw HTML, markdown, or code.
  4. Make cross-domain reads via platform syscall interface
     (POST /platform/syscall with capability_id + operation)
     Never call other teams' APIs directly.
     The platform mints scoped OBO tokens and maintains audit chain.

### Evaluations domain agent
  Task:   author_flow
  Tools:  get_eval_template() · load_draft() · save_section()
          validate_completeness() · stream_a2ui() · suggest_rating()
  Note:   suggest_rating is model reasoning but presented as suggestion.
          Human decides. Model never submits.

### Staffing domain agent
  Task:   find_candidates
  Tools:  search_available_employees() · score_skill_match()
          fetch_eval_summary() [syscall → evals]
          fetch_learning_profile() [syscall → learning]
          rank_candidates() · stream_a2ui()
  Note:   cross-domain reads via platform syscall. Never direct API calls.

### Learning domain agent
  Task:   development_plan_flow
  Tools:  get_learner_profile() · fetch_eval_gaps() [syscall → evals]
          fetch_role_skills() [syscall → staffing]
          recommend_courses() · build_milestone_plan() · stream_a2ui()
  Note:   recommends, never decides. Human approves the plan.

## 4.5 A2UI as the agentic output contract

Every agent output that reaches a client is a component_id + props pair.

  WRONG (never):  agent streams "Please approve the extension" + HTML
  CORRECT:        agent streams {
                    component_id: "ActionCard",
                    props: { title: "Extension request", entity: {...},
                             actions: ["open:approve_extension", "dismiss"] }
                  }

The platform validates every A2UI message from every domain agent against
the catalog Zod schema before forwarding. Unknown component_id → rejected.
Schema-invalid props → rejected. This makes prompt injection through
domain agent responses structurally impossible.

## 4.6 Model assignments

  Intent agent         claude-3-5-haiku   high freq, low complexity
  Orchestrator agent   claude-3-5-sonnet  lower freq, high complexity
  Discovery agent      claude-3-5-haiku   pattern matching, not reasoning
  Home surface agent   claude-3-5-haiku   ranking, not reasoning
  Domain agents        team's choice      declared in agent card

Rule: choose the cheapest model that passes the test gate.
      Upgrade only when a test gate fails on model quality.

## 4.7 The three agentic growth loops

  Loop 1 — Hot-path compilation
    Every cold-path success → write_compiled() → next identical call is
    deterministic (<50ms, no model). System improves with every interaction.

  Loop 2 — Concept graph enrichment
    Every xp publish → concept ingestion pipeline → new capability
    semantically discoverable within ~5 seconds. No human curation.
    Popular intents strengthen their concept graph connections over time.

  Loop 3 — Failed intent → roadmap signal
    Every unrouted utterance → ClickHouse failed_intents table →
    weekly digest clusters and delivers to capability teams →
    teams see what users need that doesn't exist yet →
    teams build it → manifests published → system coverage grows.

---

# PART 5 — HEADLESS AGENTS
# ─────────────────────────────────────────────────────────────────────────────

## 5.1 What headless means

A headless agent runs without an active user session. Triggered by
events, schedules, or other agents. No interactive frontend of its own.

Output is always one of:
  - Push notification (user gets action card on lock screen)
  - NATS event (triggers downstream agents)
  - Cached A2UI surface (prefetched for instant open)
  - Slack/webhook digest (to a team)
  - A2A task handoff (passes work to a domain agent)

A headless agent NEVER:
  - Commits a consequential action without human confirmation
  - Writes to a domain system directly
  - Reads one user's PII to personalise for another user

## 5.2 The complete headless agent inventory

  Agent                     Trigger            Model    Output
  ──────────────────────────────────────────────────────────────────
  Concept graph ingestion   NATS event         none     Oxigraph update
  Hot-path compiler         routing success    none     Redis cache
  Home surface agent        session open       haiku    A2UI HomeSurface
  Failed intent digest      cron weekly        haiku    Slack digest
  Proactive watch agent     cron + threshold   haiku    NATS push event
  Cross-domain watch agent  NATS + cron        sonnet   NATS push event

## 5.3 Proactive watch agent (Phase 3)

  Trigger:   cron every 15 minutes + threshold events from domain systems
  Model:     claude-3-5-haiku (for ambiguous threshold evaluation only)
  Runtime:   services/orchestrator/agents/proactive_watch.py

  Algorithm:
    1. Load all watch_conditions from registry manifests
    2. For each condition due for poll:
       a. Mint read-scoped OBO token (system service account, read only)
       b. GET capability's poll_endpoint
       c. Evaluate threshold (deterministic for most cases)
       d. Model handles edge cases: "days_remaining is 28, threshold 30,
          user dismissed a reminder 2 days ago — notify?"
       e. If threshold crossed + not in cooldown:
          → emit push.events.{capability_id} to NATS
          → record notification to prevent duplicate spam
    3. Respects user quiet_hours. Max 1 notification per condition per 24h.

## 5.4 Cross-domain watch agent (Phase 3)

  Trigger:   NATS events (eval.submitted, placement.changed, cert.completed)
             + cron daily at 09:00
  Model:     claude-3-5-sonnet (cross-domain signal detection needs reasoning)
  Runtime:   services/orchestrator/agents/cross_domain_watch.py

  Tool set:
    get_event_context(event_type, entity_id)
    fetch_related_context(entity_id, capability_ids[])  — parallel syscalls
    detect_signal(contexts[]) → { signal_detected, type, confidence, ... }
    compose_insight_notification(signal, entity, suggested_intent)
    emit_to_nats(push_event)

  Guardrails:
    - confidence < 0.75 → do not notify (miss one, don't spam)
    - max 1 cross-domain insight per entity per day
    - user can opt out per capability pair
    - all context reads are read-only; never stored in this service

  Example flows:
    eval.submitted → fetch learning profile → detect dev gap →
    push to employee: "These courses address your growth areas"

    placement.changed → check for open backfill role → none found +
    end date < 45 days → push to manager: "No backfill started yet"

    cron daily → team skill coverage vs open roles →
    detect blocking gap → push: "Team Atlas needs Kubernetes cert to
    hire for the open engineer role"

## 5.5 The headless → headed handoff pattern

  Step 1  headless detects condition, decides to notify
  Step 2  headless prefetches A2UI surface for suggested intent
          → Redis: prefetch:{user_sub}:{intent_id}:{entity_id} (TTL 10m)
  Step 3  headless emits push notification with action button
  Step 4  human sees notification on lock screen, taps action
  Step 5  session gateway checks Redis → prefetch HIT → surface <100ms
          (no LLM call; work was already done)
  Step 6  human reviews, confirms or dismisses
  Step 7  if confirmed → orchestrator confirm_gate → receipt → dispatch

  The headless agent does all the thinking.
  The human does all the deciding.
  The prefetch makes the transition invisible.

---

# PART 6 — THE PHASED BUILD PLAN
# ─────────────────────────────────────────────────────────────────────────────

## 6.1 The guiding principle

  Build individual pieces → scaffold → integrate one by one.
  Every phase is independently testable and demonstrable.
  The test gate IS the demo.
  Do not start the next phase until the current gate passes.

## 6.2 Phase summary

  Phase 0  Foundations     ~2 weeks   Monorepo · schema · stubs · compose
  Phase 1  Push+Trust      ~6 weeks   First e2e flow · trust chain proven
  Phase 2  Voice+Routing   ~8 weeks   Voice demo · composite view · A2A
  Phase 3  Concept+OS      ~8 weeks   Undirected discovery · home surface
  Phase 4  Harden+Pilot    ongoing    Prod IdP · k8s · real teams · numbers

## 6.3 Phase 0 — Foundations

  Goal: monorepo running, schema validating, fake teams federated.

  0.1 — Monorepo scaffold
    pyproject.toml (uv workspace) · pnpm-workspace.yaml
    packages/manifest-schema/capability.schema.json
    .env.example
    Test: uv sync succeeds

  0.2 — manifest-schema package
    JSON Schema enforcing: id format, lifecycle enum, risk tiers,
    consequential actions require confirmation blocks
    Test: valid manifests pass · invalid fail with precise errors

  0.3 — xp CLI
    xp validate: schema + openapi ref resolution + CI action
    xp publish: validate first, then POST to registry
    Test: xp validate fixtures/valid.yaml → exit 0
          xp validate fixtures/missing-confirmation.yaml → exit 1

  0.4 — Mock domain stubs (×3: staffing · evals · feedback)
    FastAPI · OpenAPI 3.1 · faker seed data · capability.yaml
    /healthz · Idempotency-Key support · mock token validation
    Test: all /healthz 200 · all openapi.json valid · xp validate passes

  0.5 — Docker Compose base
    postgres:16 · redis:7 · nats:2.10 · keycloak:24 · 3 stubs
    Keycloak realm: pangaea · test users: alice, bob, carol, dave
    Test: docker compose up -d → all services healthy

  Phase 0 gate: compose up → all green · xp validate passes on 3 manifests
                · schema rejects broken manifest with clear error

## 6.4 Phase 1 — Push, Trust, Render

  Goal: end-to-end flow — push arrives → user taps Approve →
        stub called with OBO token → receipt sealed.

  1.1 — Registry service (FastAPI · Postgres · Alembic)
    POST /capabilities · GET /capabilities · composition checks
    Rejects: duplicate entity ownership · dangling refs · unreachable health
    Test: publish 3 stubs → listed · duplicate entity → 409

  1.2 — Token broker (FastAPI · python-jose · Keycloak RFC 8693)
    POST /token/exchange → scoped OBO token
    Security invariants: cannot mint beyond manifest scopes · TTL ≤ 600s
    Test: valid exchange → scoped token · over-scoped → 403

  1.3 — Provenance ledger (Postgres append-only · hash-chained)
    write_receipt() · verify_chain() · idempotency_key uniqueness
    Test: 3 receipts → chain valid · tampered record detected

  1.4 — A2UI catalog v0 (10 components)
    ActionCard · ConfirmationCard · EntityCard · EntityPicker
    DataTable · FormFlow · StatusBadge · SectionHeader
    CompositeLayout · ReceiptView
    Each: Zod schema · React component · Storybook story · a11y
    Test: renders from valid JSON · rejects unknown component ID

  1.5 — Session gateway + push service
    WebSocket /ws/{session_id} · pywebpush · NATS fan-out
    Prefetch: compose A2UI surface on notification publish, cache in Redis
    Test: subscribe → publish event → push <500ms · prefetch cache hit

  1.6 — Intent router v0
    Redis hot-path → Claude fallback (structured JSON output)
    confidence < 0.85 → clarification · successful route → compile
    Test: known utterance routes correctly · second call uses Redis

  1.7 — Minimal Next.js shell
    Push permission request · service worker · ActionCard render
    Test: push arrives in browser · Approve button present

  Phase 1 gate: pytest tests/e2e/test_phase1_push_approval.py -v
    PASSED  push notification arrived in browser
    PASSED  user tapped Approve
    PASSED  staffing stub received approved request
    PASSED  OBO token had correct scopes, no extras
    PASSED  receipt written to ledger
    PASSED  chain hash verified

## 6.5 Phase 2 — Voice, Routing, Agents

  Goal: voice demo works · composite mentee view works · A2A agents live.

  2.1 — Intent router v1 (pgvector + hot-path compiler)
    Embed all intent utterances on registry publish → pgvector
    Cold path: similarity search first, Claude only on low confidence
    Metrics: cold/hot ratio → Prometheus
    Test: synonym routes via embedding · hot-path fires after threshold

  2.2 — Orchestrator (LangGraph)
    Full graph: resolve → check_permissions → dispatch → assemble → confirm
    asyncio.gather for parallel fan-out · partial failure → degraded render
    LangGraph checkpoints at confirm_gate (resumable across sessions)
    Test: single call + receipt · parallel fan-out · timeout → degraded

  2.3 — Entity resolver
    POST /resolve · fuzzy match · disambiguation card
    Rank: direct_report > reporting_line > same_team > recent_interaction
    Test: unique → auto-resolved · "John Doe" × 2 → disambiguation card

  2.4 — A2A domain agent integration
    Add A2A endpoint to evals stub · streaming A2UI messages
    Orchestrator validates every A2A message against catalog schema
    Test: valid A2A message → client · unknown component → rejected

  2.5 — Voice pipeline
    WebRTC → faster-whisper → ASR → transcript → router
    webrtcvad silence detection · partial transcripts stream to shell
    Test: audio fixture → correct transcript · silence triggers at 1.5s

  2.6 — Composite UI (mentee view)
    CompositeLayout + ProvenanceFooter + ActionSuggestor
    "show me everything about alice" → 3 parallel syscalls → one screen
    Test: 3 sections rendered · provenance footer shows 3 capability IDs

  Phase 2 gate: two demos running back to back:
    Voice: speak "evaluate alice" → disambiguation → pick → guided flow
    Composite: type "show me everything about alice" → 3 sections

## 6.6 Phase 3 — Concept Graph, Discovery, OS

  Goal: undirected discovery works · new systems auto-discoverable ·
        home surface live · telemetry flowing.

  3.1 — Concept graph service (Oxigraph · JSON-LD · pgvector)
    NATS subscriber: capability.published → ingest → embed → store
    POST /concepts/resolve · GET /concepts/{id}/related
    Test: "recognise someone" → rewards cap · new cap discoverable < 5s

  3.2 — Router v2: needs-based routing
    Tier 1: compiled Redis (<50ms) · Tier 2: pgvector (<200ms)
    Tier 3: concept graph (<400ms) · Tier 4: Claude with small candidate set
    Ambiguous → ExplorationCard
    Test: tier 1 p99 < 50ms · tier 3 vague need → candidates surfaced

  3.3 — Home surface
    3 panels: Pending · Your capabilities · Suggested
    Suggested: anonymised peer patterns from ClickHouse (never PII)
    Test: 2 pending approvals → both shown · manager role → correct caps

  3.4 — Intent telemetry
    ClickHouse: intent_routed · intent_failed · action_committed events
    Grafana: routing dashboard · per-capability intent volume
    Weekly digest cron: clusters failed intents → NATS → Slack
    Test: 10 routed → ClickHouse count = 10 · digest produces correct payloads

  3.5 — Proactive watch agent
    Poll watch_conditions from manifests · threshold evaluation · push
    Test: condition crossed → push emitted < poll_interval · cooldown works

  3.6 — Cross-domain watch agent
    NATS event subscription · fetch_related_context · detect_signal
    confidence < 0.75 → no push · max 1/entity/day
    Test: eval.submitted → learning push composed · low confidence → no push

  Phase 3 gate: three demos:
    1. "I want to do something nice for my team" → ExplorationCard → 3 options
    2. xp publish new stub → ask about it → discovered immediately
    3. Open Pangaea → 2 pending approvals visible → tap → done

## 6.7 Phase 4 — Harden, Scale, Pilot

  Real IdP (Okta/Azure AD) · Kubernetes/Helm · k6 load test
  Pen test: no god tokens confirmed · WCAG 2.2 AA audit (axe-playwright)
  White-glove onboarding: 3 real teams · target: < 1 week to federate
  Before/after dashboard published: eng hours · approval time · review time
  Phase 4 gate: 3 real teams federated · actuals published

---

# PART 7 — WORKING RULES FOR CLAUDE CODE
# ─────────────────────────────────────────────────────────────────────────────

## 7.1 The seven invariants (never violate)

  INV-1  No standing credentials.
         The platform holds no persistent tokens to any domain system.
         Every token: minted per-request · single-operation scope · TTL ≤ 600s.

  INV-2  No code in A2UI surfaces.
         Component ID + Zod-validated props only.
         No JSX generation · no eval · no dangerouslySetInnerHTML.
         No script tags · no markdown-with-HTML. Ever.

  INV-3  No unresolved entities before dispatch.
         Ambiguous entity = disambiguation card, not a guess.
         No syscall dispatched with a string name instead of canonical ID.

  INV-4  No model-generated confirmation cards.
         Cards are built from platform-fetched, platform-validated data.
         The model provides zero input to build_confirm_card().

  INV-5  Every consequential action has a receipt.
         write_receipt() completes before dispatch_direct() is called.
         Missing receipt = bug. Stop and fix before continuing.

  INV-6  Manifests are the contract.
         If a capability's behavior is not in its manifest, the platform
         does not support it. No "well it should work" exceptions.

  INV-7  Concept graph is auto-populated.
         Never manually edit graph data.
         It comes from manifests, only from manifests, always.

## 7.2 How to work

  One task at a time. One phase at a time.
  Finish the current task's test gate before starting the next.
  The test gate is not a checkbox — it is a runnable test.

  Build → test → integrate. In that order. Never wire first, test later.

  Every service gets /healthz and tests/ before anything else.
  A service without both does not exist yet.

  Read the relevant Phase section of Part 6 before starting any task.
  The plan has exact file paths, endpoints, and test assertions. Use them.
  If a task conflicts with Part 1, Part 1 wins. Document the conflict.

## 7.3 Python service conventions

  - uv for packages. Always uv add, never pip install.
  - pyproject.toml with [project] and [tool.uv] sections.
  - FastAPI · Pydantic v2 · pytest + pytest-asyncio.
  - Config via pydantic_settings BaseSettings reading .env.
  - All vars documented in .env.example with description comments.
  - Black + ruff before committing.
  - Every service: main.py · models.py · routes/ · tests/ · .env.example

## 7.4 Next.js app conventions

  - Next.js 15 App Router · TypeScript strict · pnpm.
  - Tailwind dark theme default (background: #0B0F1A).
  - shadcn/ui base components.
  - next.config.ts: output: 'standalone'.
  - pnpm build must pass before task is considered done.
  - jest + React Testing Library · playwright for e2e.

## 7.5 Test conventions

  Unit tests:         services/{name}/tests/test_{module}.py
  Integration tests:  tests/integration/test_{scenario}.py
  Phase gate tests:   tests/e2e/test_phase{N}_{name}.py  ← these ARE the demos

  Test users: alice@acme.com (manager) · bob@acme.com (engineer)
              carol@acme.com (HR) · dave@acme.com (new employee)
  Employee IDs: always E-{5digits} pattern (e.g. E-48291)
  Never use real/production data. Faker-seeded fixtures only.

  Every test function has a one-line docstring stating which invariant
  or northstar principle it protects.

## 7.6 When building any agent

  Before writing a single line, answer these five questions:

  1. Which tier? If tier 1: zero model calls, full stop.

  2. What is the tool set? List every function the agent can call.
     If a tool crosses a tier boundary, verify it uses the right interface.

  3. What is the A2UI output contract?
     Every output that reaches a client is component_id + validated props.
     Name the component. Write the Zod schema. No exceptions.

  4. Where is the guardrail?
     Every Tier 2 agent has at least one hard check encoded in the
     LangGraph graph structure. Name it explicitly in the code.

  5. Where does this fit in the three growth loops?
     Does it write to hot-path cache? Feed the concept graph?
     Generate telemetry? If not, is that intentional?

## 7.7 Progress definition

  At the end of every session the repo must be in a state where:
    - All existing tests still pass
    - At least one new test passes that didn't before
    - docker compose up still works
    - The current phase gate is closer to passing

  Progress = passing tests. Not lines of code written.

## 7.8 Current phase tracker — update at start of every session

  Current phase:  [ PHASE 0 ]
  Current task:   [ 0.1 — Monorepo scaffold ]
  Gate status:    [ NOT STARTED ]

---

# PART 8 — REFERENCE MANIFESTS
# ─────────────────────────────────────────────────────────────────────────────

These three manifests are the reference implementation of the manifest spec.
They demonstrate federation in action: shared entity references, cross-system
enrichment, risk-tiered actions, and the complete field set.
Use them as the template when writing new capability manifests or test stubs.

## 8.1 Federation rules shown across the three manifests

  Entity ownership:
    acme.evaluations  owns  Evaluation · ReviewCycle
    acme.staffing     owns  Role · Placement · StaffingRequest
    acme.learning     owns  Course · LearningPath · Certification
                            LearnerProfile · Skill
    acme.directory    owns  Employee · Team  (entity spine — mandatory)

  All three manifests ref: acme.directory#Employee and acme.directory#Team.
  No two manifests claim the same owned entity type.
  Registry composition check enforces this on every xp publish.

  Cross-system enrichment (context_hints, read-only, in transit only):
    Evaluations enriches from → staffing (staffing_history)
                                learning (completed_courses)
    Staffing    enriches from → evaluations (eval_summary)
                                learning (skills_and_certifications)
    Learning    enriches from → evaluations (competency_gaps)
                                staffing (role_skill_requirements)

  The Skill entity owned by learning becomes the shared vocabulary:
    staffing roles reference skills · evaluations reference competencies
    learning paths target skills.
    The concept graph traverses: staffing#Role → skills → learning#Path.

## 8.2 Risk tier examples from the three manifests

  CONSEQUENTIAL (require confirmation card + explicit tap):
    evaluations  submit_evaluation     — finalises eval, notifies manager
    staffing     resolve_extension     — approves/denies extension request
    learning     record_certification  — updates official skill record

  REVERSIBLE (OBO token + receipt, undo window declared):
    evaluations  save_draft            — no undo window (re-edit freely)
    staffing     create_staffing_req   — 600s undo window
    learning     enrol_course          — 3600s undo window
    learning     nominate_employee     — 3600s undo window

  READ (no receipt, enforced by team API):
    evaluations  get_evaluation
    staffing     get_staffing_history
    learning     search_catalogue

## 8.3 Key manifest fields and their platform effect

  intent.description        → LLM routing context (write precisely)
  intent.utterances[]       → seeds both LLM routing AND compiled hot-paths
  intent.confidence.min_route → default 0.85; below this → clarify, not route
  entity.resolution.disambiguators → fields shown in EntityPicker card
  action.risk               → determines confirmation requirement and receipt
  action.confirmation.show_fields → exactly what appears in the confirmation card
  surfaces.layout.stability → pinned (default) · adaptive · user_choice
  policy.visibility.discoverable_by → who sees this capability in routing + registry
  watch_conditions[].poll_endpoint → what the proactive watch agent polls
  context_hints[].enrich_from → what gets fetched in a composite view

## 8.4 The composite view pattern (mentee overview example)

  User: "show me everything about my mentee Alex"

  1. Intent agent routes to: composite_profile intent (or equivalent)
  2. Entity resolver: "Alex" → disambiguation → E-48291
  3. Orchestrator reads context_hints for acme.directory#Employee
     from all registered capabilities
  4. fan_out_parallel([
       dispatch(evals, getEvaluationSummary, {employee: E-48291}),
       dispatch(staffing, getStaffingHistory, {employee: E-48291}),
       dispatch(learning, getLearnerProfile, {employee: E-48291})
     ])
  5. normalize_entities() reconciles cross-system entity refs
  6. assemble_composite() → CompositeLayout with 3 sections
     Each section color-coded to source capability
     Each section tagged with source capability_id (provenance)
  7. ProvenanceFooter: "syscalls: staffing.getHistory ·
     evals.getSummary · learning.getProfile · 3 OBO tokens · receipt #..."
  8. ActionSuggestor derives contextual actions from payload:
     "Write feedback" · "Suggest for staffing" · "Nominate certification"
     Each action button is a new syscall with its own confirm_gate.

---

# APPENDIX A — THE INVARIANT CHECKLIST
# Run this mentally before committing any code that touches trust, agents, or UI.

  □  Does any new code create a standing credential to a domain system?
     If yes: replace with per-request OBO token flow.

  □  Does any new code put executable content (HTML, JSX, eval, script)
     into a rendered surface?
     If yes: replace with component_id + props pattern.

  □  Does any new code dispatch a syscall before entity resolution completes?
     If yes: add resolution step before dispatch.

  □  Does any new code let the model write text that appears in a
     confirmation card?
     If yes: replace with build_confirm_card() from resolved entity data.

  □  Does any new consequential action complete without a receipt row?
     If yes: wire write_receipt() before dispatch_direct().

  □  Does any new capability behavior exist without a manifest declaration?
     If yes: add to the capability.yaml before wiring.

  □  Does any new code manually write to the concept graph?
     If yes: route the signal through the manifest ingestion pipeline instead.

# If all seven boxes are clear: the code is safe to commit.

---

# APPENDIX B — GLOSSARY

  A2A              Agent-to-Agent protocol. How Pangaea's orchestrator
                   communicates with domain agents. Streaming, typed messages.

  A2UI             Adaptive UI driven by structured JSON messages containing
                   component IDs and typed props. The platform's rendering
                   contract. No arbitrary code. Pre-approved catalog only.

  capability       A team's registered system. Published via capability.yaml.
                   The unit of federation. One manifest = one driver.

  capability manifest
                   The YAML file that is the contract between a team and
                   the platform. Declares entities, intents, actions, risk
                   tiers, A2UI bindings, notifications, and policy.

  compiled path    A deterministic Redis entry mapping an utterance hash to
                   a RouteResult. Written after every cold-path success.
                   The hot-path. <50ms. No model.

  concept graph    The platform's semantic map of concepts → capabilities.
                   Lightweight JSON-LD in Oxigraph + embeddings in pgvector.
                   Auto-populated from manifests. No human curation.

  confirmation card
                   A deterministic A2UI ConfirmationCard rendered from
                   resolved entity data before any consequential action.
                   Model-free. Frozen on construction. Human must tap.

  domain agent     A team's A2A-capable intelligent participant. Streams
                   A2UI messages. Uses platform syscall interface for
                   cross-domain reads. Full autonomy within its domain.

  entity spine     The org's canonical identity system (directory/IdP).
                   Every domain system references entities from it.
                   The mandatory federated capability.

  OBO token        On-behalf-of token. Short-lived, single-operation,
                   scoped to exactly the required permissions. Minted by
                   the token broker per request. TTL ≤ 600 seconds.

  provenance receipt
                   A hash-chained, KMS-signed Postgres row recording what
                   was asked, what was shown, what was committed, and by
                   whom. Written before dispatch. Tamper-evident.

  syscall          A call from the platform to a domain system carrying
                   a scoped OBO token. Analogous to a kernel syscall.
                   Returns typed data. Recorded in provenance ledger.

  xp CLI           The command-line tool for manifest validation and
                   publishing. xp validate · xp publish. Written in
                   Python/uv. Runs in CI on every capability.yaml change.
