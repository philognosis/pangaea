# Pangaea — Agentic Architecture
# How agents, tools, A2UI, and agentic workflows connect at every layer.
# Claude Code reads this alongside VISION.md and BUILDPLAN.md.

---

## The principle: right agency at the right layer

"Agentic" does not mean every part of the system uses an LLM.
It means the system can reason, plan, use tools, recover from partial
failures, and improve over time — at the layers where that adds value,
with hard deterministic boundaries at the layers where it would add risk.

The three-tier model:

  Tier 1 — Deterministic kernel          No LLM. Always fast. Enforces invariants.
  Tier 2 — Platform agents               LLM + tools. Agentic with guardrails.
  Tier 3 — Federated domain agents       Full autonomy. Team-owned. A2A protocol.

Each tier hands off to the next. Agency never flows backward —
a domain agent cannot override the trust fabric, and a platform
agent cannot write a confirmation card.

---

## Tier 1 — Deterministic kernel (no agency)

These components are intentionally not agentic. They are the
OS kernel — fast, predictable, provably correct.

### Trust fabric tools
Called by every other component. Never by a model directly.

  mint_obo_token(user_token, capability_id, required_scopes[])
    → access_token | error
    Invariant: scopes in returned token ⊆ scopes in manifest.
               TTL ≤ manifest.auth.token_ttl_seconds.
               Unknown capability_id → 404, not a guess.

  validate_scope(token, required_scope)
    → allowed | forbidden

  check_rbac(user_sub, capability_id, action_id)
    → permitted | denied | not_found
    Calls the capability's own PEP (policy enforcement point).
    Never makes the decision itself.

  write_receipt(intent, card_json, action, user_sub, idempotency_key)
    → receipt_id
    Invariant: called before any consequential action is dispatched.
               If write fails, action is not dispatched.

  verify_chain(receipt_id)
    → { valid: bool, chain_intact: bool }

### A2UI renderer tools
Maps structured JSON to catalog components. Never generates markup.

  render(component_id, props_json)
    → ReactElement | schema_error
    Invariant: component_id must exist in catalog.
               props_json must validate against component's Zod schema.
               Unknown component_id → hard error, never a fallback.

  build_confirm_card(action, resolved_entity_json, show_fields[])
    → ConfirmationCard (frozen — immutable after construction)
    Invariant: card is built from platform-fetched entity data.
               Model provides zero input to this function.

  stream_to_ws(session_id, a2ui_message)
    → delivered | session_not_found

### Hot-path router tools (deterministic path only)

  lookup_compiled(utterance_hash)
    → RouteResult | miss

  write_compiled(utterance_hash, route_result, slot_pattern)
    → stored
    Called by the Intent agent after a successful cold-path routing.
    This is how the system learns and gets faster over time.

  similarity_search(embedding, top_k)
    → [{ intent_id, capability_id, score }]
    pgvector cosine search. No model. Sub-200ms.

### Entity resolver tools (deterministic scoring)

  search_directory(entity_type, query, caller_context)
    → [EntityCandidate]

  rank_candidates(candidates[], disambiguators[], caller_context)
    → [RankedCandidate]
    Scoring: direct_report > reporting_line > same_team > recent_interaction
    Deterministic — same input always produces same ranking.

  build_disambig_card(candidates[], show_fields[])
    → EntityPicker (A2UI component)

---

## Tier 2 — Platform agents (LangGraph, agentic with guardrails)

Four agents. Each is a LangGraph graph with a defined tool set,
a model assignment, and explicit guardrails on what it can and
cannot do.

### Intent agent
Model: claude-3-5-haiku (fast, cheap — called on every cold path)
Trigger: hot-path miss in router
Purpose: classify intent, extract slots, route to the right capability

Tool set:
  query_concept_graph(utterance)
    → [ConceptMatch]  ranked concepts from Oxigraph + pgvector
    Used when utterance is vague or system is unknown.
    "I want to recognise someone" → concept: recognition →
    capability: acme.rewards

  get_capability_intents(capability_id)
    → [IntentDescription]  from registry manifest

  classify_intent(utterance, intent_candidates[])
    → { intent_id, capability_id, confidence, extracted_slots }
    This IS the LLM call. Structured output, Pydantic model.

  extract_slots(utterance, slot_definitions[])
    → { slot_name: raw_value }  raw — not yet resolved to entity IDs

  generate_clarification(utterance, low_confidence_reason)
    → ClarificationQuestion (string)
    Called when confidence < 0.85.
    Output rendered as inline chat message, not A2UI card.

  compile_hot_path(utterance_hash, route_result, slot_pattern)
    → calls Tier 1: write_compiled()
    Runs after every successful routing. System improves automatically.

LangGraph nodes:
  check_hot_path → [hit: return] → [miss: continue]
  check_similarity → [high confidence: return] → [low: continue]
  query_concept_graph
  classify_intent
  check_confidence → [low: generate_clarification] → [ok: continue]
  extract_slots
  compile_route
  return RouteResult

Guardrails:
  - Route only to capabilities in the registry (lifecycle: beta or ga)
  - Route only to capabilities discoverable_by the caller's roles
  - confidence < 0.85 → clarify, never guess
  - Max 3 clarification rounds before surfacing ExplorationCard
  - Model output is structured JSON only, never free-form routing

### Orchestrator agent
Model: claude-3-5-sonnet (more capable — handles complex multi-step tasks)
Trigger: RouteResult from Intent agent
Purpose: execute the work — dispatch syscalls, fan out, assemble results

Tool set (these ARE the syscalls):
  dispatch_direct(capability_id, operation_id, params, obo_token)
    → OperationResult
    Calls Tier 1: mint_obo_token() first, always.
    REST or GraphQL — speaks whatever protocol the manifest declares.

  dispatch_agent(capability_id, task_type, context, obo_token)
    → A2ATaskHandle
    Initiates an A2A task to a domain agent (Tier 3).
    Returns a handle; results stream back asynchronously.

  fan_out_parallel(syscalls[])
    → [OperationResult]  (asyncio.gather)
    Used for composite views — fires 3 syscalls simultaneously.
    Partial failure returns degraded result, not an error.

  normalize_entities(results[], entity_spine_id)
    → NormalizedResults
    Reconciles entity references across systems.
    "alex-99" in staffing + "E-48291" in evals → same person.

  assemble_composite(sections[], layout_intent)
    → CompositeLayout params  (passed to A2UI renderer)

  request_confirmation(action_id, resolved_entity, show_fields)
    → calls Tier 1: build_confirm_card()
    Returns card to session gateway.
    Orchestrator waits for human_committed signal before continuing.

  handle_partial_failure(failed_capability_id, partial_results)
    → DegradedResult  (renders what succeeded, notes what failed)

LangGraph nodes (conditional, resumable):
  resolve_entity → check_permissions → [direct|agent] dispatch
  → [composite: fan_out_parallel] → assemble → [consequential: confirm_gate]
  → [confirmed: write_receipt + dispatch] → stream_result

Checkpoint: LangGraph checkpoints state at confirm_gate.
  The graph is resumable — if the user closes the app and comes back,
  the pending confirmation is restored from the checkpoint.

Guardrails:
  - dispatch_direct requires a valid OBO token (Tier 1 enforces this)
  - consequential actions: confirm_gate cannot be skipped
  - write_receipt must complete before action dispatch
  - domain agent responses: every A2UI message validated against
    catalog schema before forwarding (content/control plane separation)
  - partial failures surface gracefully; never silently drop data

### Discovery agent
Model: claude-3-5-haiku
Trigger: Tier 1+2 routing fails, OR utterance has no specific system intent
Purpose: help users find capabilities they didn't know existed

Tool set:
  semantic_search_concepts(utterance)
    → [Concept]  from pgvector

  traverse_concept_graph(concept_ids[], depth=2)
    → [Capability]  via Oxigraph SPARQL

  score_capability_fit(capabilities[], utterance, user_context)
    → [RankedCapability]

  generate_exploration_card(ranked_capabilities[])
    → ExplorationCard (A2UI component)
    "I found a few things that might help..."
    Lists 2-4 capabilities with one-line descriptions.
    Each tappable — tap fires that capability's primary intent.

  suggest_next_actions(current_surface, user_context)
    → [QuickAction]  for home surface
    Based on role, time of day, peer patterns.
    Never reads another user's PII — only anonymised pattern data.

Guardrails:
  - ExplorationCard is read-only — no actions executed at this stage
  - suggest_next_actions uses aggregate patterns, never individual data
  - capabilities shown must pass discoverable_by check for this user

### Home surface agent
Model: claude-3-5-haiku
Trigger: session open (runs in background, results cached 15 min)
Purpose: compose the ambient home screen — pending work + suggestions

Tool set:
  get_pending_actions(user_sub)
    → [PendingAction]  from push event store, filtered by user
    Sorted by: overdue → due today → upcoming → FYI

  get_role_capabilities(user_roles[])
    → [Capability]  from registry filtered by discoverable_by

  query_peer_patterns(user_role, anonymised: true)
    → [IntentPattern]  most-used intents by same-role users
    From ClickHouse. Aggregated, never individual.

  rank_suggestions(capabilities[], patterns[], user_history[])
    → [SuggestedAction]  top 3

  prefetch_surface(intent_id, entity_id)
    → cached A2UI surface  (stored in Redis, expires 5 min)
    Called for top suggestion so it opens instantly.

  personalise_layout(user_preferences, pending_count)
    → HomeSurface params  (A2UI component)

Output: HomeSurface A2UI component with three panels:
  - Pending (deterministic, from push store)
  - Your capabilities (deterministic, from registry)
  - Suggested (agentic, ranked by home surface agent)

---

## Tier 3 — Domain agents (team-owned, full autonomy)

Each domain agent is a team's intelligent participant in the platform.
They communicate via A2A protocol. They can use any tools that touch
their own domain. They can make cross-domain syscalls via the platform's
syscall interface (same OBO token model — they never get god tokens).

### What every domain agent must do

1. Expose an agent card at /.well-known/agent.json
   Declares: protocol version, supported task types, streaming capability

2. Accept A2A tasks at /a2a
   Each task arrives with: task_type, user_context, entity, obo_token

3. Stream responses as A2UI messages
   { component_id: "GuidedFormFlow", props: {...} }
   Never stream raw HTML, markdown, or code.
   Every message validated against catalog schema before forwarding.

4. Make cross-domain syscalls through the platform syscall interface
   Not by calling other teams' APIs directly.
   Syscall interface: POST /platform/syscall with capability_id + operation
   Platform mints a scoped OBO token for that specific call.
   This keeps the audit chain intact across domain boundaries.

### Evaluations domain agent
Task: author_flow
What it does autonomously:
  - Loads the right evaluation template for the cycle
  - Restores any existing draft
  - Streams the multi-section guided form via A2UI GuidedFormFlow
  - Validates completeness before enabling submit
  - Can suggest a rating range based on prior cycle patterns
    (model reasoning, but presented as a suggestion — human decides)

Tools:
  get_eval_template(cycle_id) → from own DB
  load_draft(eval_id, author_id) → from own DB
  save_section(eval_id, section_id, content) → to own DB
  validate_completeness(eval_id) → checks all required fields
  stream_a2ui(component_id, props) → to platform gateway
  suggest_rating(subject_history, comparable_evals) → model reasoning

Cross-domain syscalls this agent makes:
  None in the author flow — it has everything it needs.
  In future: fetch_staffing_context() for richer background.

### Staffing domain agent
Task: find_candidates
What it does autonomously:
  - Searches its own employee pool for availability and role match
  - Scores skill alignment from its own role/skill data
  - Makes cross-domain syscalls for enrichment context
  - Ranks candidates with a composite score
  - Streams results as CandidateRankingLayout with score breakdown

Tools:
  search_available_employees(role_id, skills_required[]) → from own DB
  score_skill_match(employee_id, role_id) → own scoring model
  fetch_eval_summary(employee_id)
    → platform syscall → acme.evaluations (read, evals.read scope)
    Returns: last cycle rating summary, not full eval text
  fetch_learning_profile(employee_id)
    → platform syscall → acme.learning (read, learning.read scope)
    Returns: certifications + skill tags
  rank_candidates(candidates[], weights) → composite scoring
  stream_a2ui("CandidateRankingLayout", ranked_candidates)

Note: the agent calls platform syscall interface, not evals/learning APIs
directly. The platform mints the scoped OBO tokens and maintains the
audit trail. The staffing agent never holds tokens to other systems.

### Learning domain agent
Task: development_plan_flow
What it does autonomously:
  - Loads the employee's current profile and any existing plan
  - Optionally pulls evaluation competency gaps as input context
  - Optionally pulls target role skill requirements from staffing
  - Recommends courses and paths to close the gaps
  - Streams a multi-step guided form for the manager/employee to confirm
  - Never decides what the plan should be — it recommends, human approves

Tools:
  get_learner_profile(employee_id) → from own DB
  fetch_eval_gaps(employee_id)
    → platform syscall → acme.evaluations
    Returns: competency areas marked as development needed
  fetch_role_skills(role_id)
    → platform syscall → acme.staffing
    Returns: required skill tags for the target role
  recommend_courses(skill_gaps[], learner_history[])
    → model reasoning over own catalogue
  build_milestone_plan(goals[], recommended_courses[])
    → structured plan draft
  stream_a2ui("GuidedFormFlow", plan_draft)

---

## A2UI as the agentic output contract

Every agent — platform or domain — outputs A2UI messages, not text.

This is not a rendering convenience. It is the content/control plane
separation that makes the system safe for agentic use:

  WRONG (never):  agent streams "Please approve the extension"
                  + button markup in free text
  CORRECT:        agent streams {
                    component_id: "ActionCard",
                    props: {
                      title: "Extension request",
                      entity: { ... resolved entity ... },
                      actions: ["open:approve_extension", "dismiss"]
                    }
                  }

The platform validates every A2UI message from every domain agent
against the catalog's Zod schema before forwarding to the client.
A message with an unknown component_id is rejected and logged.
A message with schema-invalid props is rejected and logged.
This makes prompt injection through domain agent responses
structurally impossible — there is no code path from agent text
to executed code in the client.

---

## How the system evolves (the agentic growth loop)

Pangaea gets smarter over time through three automatic feedback loops:

### Loop 1 — Hot-path compilation
Every time the Intent agent successfully routes a cold-path utterance,
write_compiled() stores it in Redis. The second identical phrasing is
deterministic (<50ms). The system learns from every interaction.
No model retraining required.

### Loop 2 — Concept graph enrichment
Every time a new manifest is published (xp publish), the concept graph
ingestion pipeline fires:
  manifest → extract concepts → embed → write to Oxigraph + pgvector
New capabilities are semantically discoverable within seconds.
Intent patterns from telemetry feed back as concept weights.
Popular intents strengthen their concept graph connections.

### Loop 3 — Failed intent → roadmap signal
Every utterance that reaches Tier 2 without routing successfully is
recorded in ClickHouse as a failed intent with the anonymised utterance,
user role, and tier reached. Weekly digest clusters these and delivers
them to capability teams via NATS → Slack:
  "47 users this week asked for something related to 'recognition'
   and we had no capability to serve them."
Teams respond by building new capabilities and publishing manifests.
The system's coverage of human needs grows over time, driven by evidence.

---

## Agentic workflow patterns in the codebase

### Pattern 1 — Sequential with confirmation gate (LangGraph)
Used by: Orchestrator agent for consequential actions

  graph TD
    resolve_entity --> check_permissions
    check_permissions --> dispatch
    dispatch --> build_confirmation_card
    build_confirmation_card --> WAIT_FOR_HUMAN
    WAIT_FOR_HUMAN --> write_receipt
    write_receipt --> execute_action
    execute_action --> stream_result

  LangGraph checkpoint at WAIT_FOR_HUMAN.
  State persisted across sessions — user can close app and return.

### Pattern 2 — Parallel fan-out with degraded assembly
Used by: Orchestrator agent for composite views

  graph TD
    resolve_entity --> fan_out_parallel
    fan_out_parallel --> syscall_1 & syscall_2 & syscall_3
    syscall_1 & syscall_2 & syscall_3 --> collect_results
    collect_results --> normalize_entities
    normalize_entities --> assemble_composite
    assemble_composite --> stream_result

  asyncio.gather with timeout per syscall.
  Failed syscall → section marked "unavailable" in composite.
  Never blocks the whole view for one failing system.

### Pattern 3 — Streaming multi-step flow (A2A)
Used by: Domain agents (evals, staffing, learning)

  Platform → A2A task → Domain agent
  Domain agent streams A2UI messages back:
    { component_id: "ProgressStepper", props: { current: 1, total: 4 }}
    { component_id: "FormSection", props: { section_id: "goals", ... }}
    { component_id: "FormSection", props: { section_id: "ratings", ... }}
    { component_id: "SubmitButton", props: { action_id: "submit_evaluation" }}

  Each message forwarded to client WebSocket after schema validation.
  Platform never buffers the full response — it's always streaming.

### Pattern 4 — Concept graph traversal (Discovery agent)
Used by: Discovery agent for undirected needs

  utterance → embed → pgvector similarity → concept candidates
  concept candidates → Oxigraph SPARQL traversal → related capabilities
  related capabilities → score_capability_fit (model)
  → generate_exploration_card (A2UI) → stream to client

  The model's job here is scoring and ranking, not deciding.
  ExplorationCard renders options; user chooses; platform routes.

---

## Model assignments and why

  Intent agent         claude-3-5-haiku
    High frequency (every cold-path call), low complexity task
    (classify + extract). Haiku: fast, cheap, good enough.

  Orchestrator agent   claude-3-5-sonnet
    Lower frequency, higher complexity (multi-step planning,
    partial failure handling, composite assembly). Sonnet: worth it.

  Discovery agent      claude-3-5-haiku
    Concept scoring is pattern matching, not deep reasoning.
    Haiku handles it well.

  Home surface agent   claude-3-5-haiku
    Ranking and personalisation, not reasoning. Haiku.

  Domain agents        team's choice
    Teams pick their own model for their domain agent.
    They declare it in the agent card.
    Platform is model-agnostic at the A2A boundary.

Rule: choose the cheapest model that passes the relevant test gate.
      Upgrade only when a test gate fails on model quality, not before.

---

## What this means for Claude Code

When building any agent in this system, verify before writing:

1. Which tier is this? If tier 1, there must be NO model calls.

2. What is the tool set? List every tool the agent can call.
   If a tool crosses a tier boundary upward (e.g. an agent
   calling mint_obo_token), verify it goes through the right interface.

3. What is the A2UI output contract? Every agent output that
   reaches a client must be a component_id + props pair, validated
   against the catalog schema. No exceptions.

4. Where is the guardrail? Every agent has at least one hard
   guardrail encoded in the LangGraph graph structure —
   a node that checks something deterministically before
   the graph can proceed. Name it explicitly in the code.

5. Where does this fit in the growth loops? Does this agent
   write to the hot-path cache? Feed the concept graph?
   Generate telemetry events? If not, is that intentional?

The system is agentic because it reasons, plans, and improves.
It is safe because the trust fabric, confirmation surface, and
content/control plane separation are deterministic and unskippable.
Both things must be true. Neither compromises the other.
