# Pangaea — Headless Agents
# Background intelligence layer. Reads alongside AGENTIC.md.

---

## What headless means in Pangaea

A headless agent runs without an active user session.
It is triggered by events, schedules, or other agents.
Its output is always one of:
  - A push notification (user gets a card on their lock screen)
  - A NATS event (triggers another agent downstream)
  - A cached A2UI surface (prefetched for instant open)
  - A Slack/webhook digest (to a team, not a user)
  - An A2A task handoff (passes work to a domain agent)

A headless agent NEVER:
  - Commits a consequential action without human confirmation
  - Writes to a domain system (it can read; writes go through
    the orchestrator's confirm_gate like any other action)
  - Access another user's PII to personalise for this user
    (aggregate/anonymised patterns only)

---

## Existing headless agents (already in architecture)

### 1. Concept graph ingestion pipeline
Type: event-driven pipeline (no model)
Trigger: NATS capability.published
Runtime: services/concept-graph/ingestion.py

What it does:
  On every xp publish, this pipeline fires automatically:
  1. Fetch the new manifest from registry
  2. Extract concept signals:
     - capability.description → embed with sentence-transformers
     - intent[].description fields → embed each
     - entity type names + descriptions → embed
     - action descriptions → extract domain vocabulary
  3. Write JSON-LD triples to Oxigraph
     { capability_id } --claims--> { concept }
     { concept } --related-to--> { concept }
  4. Store concept embeddings in pgvector
  5. Emit concept-graph.updated to NATS

Result: new capability discoverable by Discovery agent within ~5 seconds
        of xp publish. No human curation. No committee.

### 2. Home surface agent
Type: haiku agent (session-triggered)
Trigger: user session open
Runtime: services/orchestrator/agents/home_surface.py

Already specified in AGENTIC.md. Headless classification: it runs
before the user has typed or said anything. The "head" hasn't formed yet.
Output is cached so the session open feels instant.

### 3. Hot-path compiler
Type: deterministic pipeline (no model)
Trigger: successful cold-path routing in intent agent
Runtime: services/router/hot_paths.py

After every successful cold-path route, write_compiled() fires.
Pure function. No model. Makes the system faster on every interaction.

### 4. Failed intent telemetry agent
Type: haiku agent (scheduled)
Trigger: cron Monday 08:00 UTC
Runtime: services/telemetry/weekly_digest.py

What it does:
  1. Query ClickHouse: failed intents in last 7 days
     SELECT utterance, user_role, tier_reached, COUNT(*)
     FROM intent_failed
     WHERE ts > now() - interval 7 day
     GROUP BY cluster_id
     ORDER BY count DESC
  2. Model clusters utterances by concept similarity
     (haiku: "group these failed utterances into themes")
  3. For each cluster, find nearest registered capability
     (or flag if no capability serves it → roadmap signal)
  4. Compose per-team digest and POST to each team's
     manifest.observability.failed_intent_webhook

Output example to #evals-eng:
  "This week: 47 users asked about something we don't handle.
   Top unserved themes:
   - 'skip level feedback' (23 requests) — not in your intents
   - 'bulk eval status' (14 requests) — view_team_evals exists but
     not being found (check your utterance examples)
   - '360 review' (10 requests) — no capability owns this yet"

---

## New headless agents (add to BUILDPLAN.md Phase 3)

### 5. Proactive watch agent ★
Type: haiku agent (scheduled + threshold)
Trigger:
  - cron every 15 minutes (scans all registered watch conditions)
  - OR threshold event from a domain system (immediate path)
Runtime: services/orchestrator/agents/proactive_watch.py

Purpose:
  Monitor declared watch conditions across federated systems and
  emit push notifications before users have to go looking.
  This is what makes Pangaea feel like it's working for you,
  not waiting for you.

Watch conditions are declared in domain manifests
(add watch_conditions[] section to manifest spec v0.2):

  # Example from staffing manifest:
  watch_conditions:
    - id: placement_ending_soon
      poll_endpoint: /watch/placements/ending-soon
      poll_interval_minutes: 60
      threshold_field: days_remaining
      threshold_value: 30
      notify_intent: approve_extension
      notify_roles: [manager_of_subject]

    - id: role_open_with_no_action
      poll_endpoint: /watch/roles/stale
      poll_interval_minutes: 240
      threshold_field: days_open_without_action
      threshold_value: 7
      notify_intent: find_candidate_for_role
      notify_roles: [role_requester]

  # Example from learning manifest:
  watch_conditions:
    - id: certification_expiring
      poll_endpoint: /watch/certifications/expiring
      poll_interval_minutes: 1440   # daily
      threshold_field: days_to_expiry
      threshold_value: 60
      notify_intent: find_course
      notify_roles: [cert_holder, manager_of_cert_holder]

Agent algorithm:
  1. Load all watch_conditions from registry (manifests with watch_conditions[])
  2. For each condition due for poll (last_polled + interval < now):
     a. Mint read-scoped OBO token for the polling user context
        (system service account — read only, cannot write anything)
     b. GET capability's poll_endpoint with token
     c. Parse threshold field against threshold value
     d. If threshold crossed AND not already notified in cooldown window:
        → emit push.events.{capability_id} to NATS
        → record notification sent (prevent duplicate spam)
  3. Model step (haiku): evaluate ambiguous threshold cases
     "Days remaining is 28, threshold is 30 — is this worth notifying
      given this user already dismissed a reminder 2 days ago?"
     Most cases are deterministic; model handles edge cases only.

Guardrails:
  - Can only call poll_endpoints declared in manifests (read-only)
  - Cannot trigger consequential actions directly
  - Respects user quiet hours for push dispatch
  - Cooldown: max one notification per condition per user per 24h
  - If poll_endpoint returns 5xx 3× in a row → pause + alert team

### 6. Cross-domain watch agent ★
Type: sonnet agent (event-triggered)
Trigger:
  - NATS events: eval.submitted, placement.changed, cert.completed,
                 staffing_request.created
  - OR cron daily at 09:00 for full sweep
Runtime: services/orchestrator/agents/cross_domain_watch.py

Purpose:
  Detect meaningful signals that span multiple systems and surface
  them as proactive suggestions. This is the agent that makes
  Pangaea feel like it understands the whole picture, not just
  individual systems.

Why this needs a model (sonnet):
  Cross-domain signal detection requires reasoning about relationships
  between data from different systems. It's not threshold checking.
  Example: "an evaluation just completed showing growth areas in
  technical leadership, AND there's an open engineering lead role on
  Team Atlas, AND this person has been on the same team for 18 months"
  → that's a staffing + evals + time signal that no single threshold
  rule can encode.

Tool set:
  get_event_context(event_type, entity_id)
    → fetches the triggering entity's context from the source capability

  fetch_related_context(entity_id, capability_ids[])
    → parallel syscalls to named capabilities for related context
    Uses the same OBO/trust chain as any other syscall.
    Only reads — never writes.

  detect_signal(contexts[])
    → model reasoning: "is there a meaningful cross-domain signal here?"
    Returns: { signal_detected: bool, signal_type, confidence,
               suggested_action_intent, suggested_capability,
               explanation }
    confidence < 0.75 → do not notify (better to miss one than spam)

  compose_insight_notification(signal, entity, suggested_intent)
    → PushEvent  (A2UI ActionCard)
    Rendered exactly like any other notification.
    User can act on the suggestion or dismiss.

  emit_to_nats(push_event)
    → to push.events.{capability_id}

Example flows:

  FLOW 1: eval → learning suggestion
    Trigger: eval.submitted (NATS)
    Agent fetches: eval result + learner profile from learning
    Detects: "overall_rating good but technical_skills marked as
              growth area + no relevant course in learner history"
    Signal type: development_opportunity
    Emits: push to employee + manager
    Card: "Based on Alex's Q4 evaluation, these courses address
           the identified growth areas: [Kubernetes Fundamentals,
           System Design]. [View courses] [Dismiss]"

  FLOW 2: placement ending + no backfill started
    Trigger: placement.changed (NATS) OR cron daily
    Agent fetches: placement end date + any open roles on that team
    Detects: "placement ends in 45 days AND no open role for this
              position AND no pending staffing request"
    Signal type: staffing_gap_risk
    Emits: push to team manager
    Card: "Alex's placement on Team Supernova ends Nov 15 and there's
           no backfill started. Open a role now? [Open role] [Dismiss]"

  FLOW 3: skill gap + available training
    Trigger: cron daily
    Agent fetches: team skill coverage from learning +
                   open roles from staffing
    Detects: "Team Atlas has an open Backend Engineer role requiring
              Kubernetes + the whole team is uncertified in Kubernetes"
    Signal type: team_skill_gap_blocks_hiring
    Emits: push to manager
    Card: "Team Atlas has a skill gap in Kubernetes that affects
           your open engineer role. 3 team members could complete
           the cert in 2 weeks. [View course] [View role] [Dismiss]"

Guardrails:
  - confidence < 0.75 → do not notify
  - max 1 cross-domain insight per entity per day
  - user can opt out of cross-domain insights per capability pair
    (stored in user preferences, checked before emit)
  - all fetched context is read-only; never stored in this service
  - model prompt explicitly forbids recommendations outside
    the user's permitted capabilities

---

## The headless → headed handoff pattern

This is the key pattern that ties headless and headed agents together.
Every headless agent that surfaces something actionable follows it:

  Step 1 (headless): detect condition, decide to notify
  Step 2 (headless): prefetch the A2UI surface for the suggested intent
                     → store in Redis with key:
                       prefetch:{user_sub}:{intent_id}:{entity_id}
                       TTL: 10 minutes
  Step 3 (headless): emit push notification with action button
  Step 4 (human):    sees notification on lock screen, taps action
  Step 5 (headed):   session gateway checks Redis for prefetch hit
                     → surface loads instantly (<100ms)
                     → no LLM call needed; work already done
  Step 6 (human):    reviews, confirms or dismisses
  Step 7 (headed):   if confirmed → orchestrator confirm_gate →
                     receipt → action dispatched

The headless agent does all the thinking.
The human does all the deciding.
The prefetch makes the transition invisible.

---

## Adding watch_conditions to BUILDPLAN.md

These headless agents require a small addition to the manifest spec
(v0.2 — backwards compatible, watch_conditions is optional):

  # New section in capability manifest:
  watch_conditions:
    - id: string           # unique within capability
      poll_endpoint: path  # relative to api.base_url, GET, read-scoped
      poll_interval_minutes: int
      threshold_field: string   # dot-path into response JSON
      threshold_value: number | string
      comparison: gt | lt | eq | gte | lte | changed
      cooldown_hours: int       # min hours between notifications
      notify_intent: intent_id  # which intent to open on tap
      notify_roles: [role_expr] # who gets notified

Add to Phase 3 (concept graph phase) tasks:
  3.5 — Proactive watch agent
  3.6 — Cross-domain watch agent
  Both require the concept graph (for signal detection context)
  and the telemetry layer (for cooldown tracking).

---

## Summary: the full headless agent inventory

  Agent                      Trigger          Model      Output
  ─────────────────────────────────────────────────────────────────
  concept graph ingestion    NATS event       none       Oxigraph update
  hot-path compiler          routing success  none       Redis cache
  home surface agent         session open     haiku      A2UI HomeSurface
  failed intent digest       cron weekly      haiku      Slack digest
  proactive watch agent      cron + threshold haiku      NATS push event
  cross-domain watch agent   NATS + cron      sonnet     NATS push event

All six run without a user session.
All six improve the system or surface value proactively.
None can commit a consequential action.
All outputs flow through the same trust chain as any headed interaction.
