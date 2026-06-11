# Capability Manifest — v0 Specification

**Status:** Draft v0.1 · **Audience:** Domain teams federating into the Experience Graph · **Owners:** Platform team

---

## 1. Purpose

The Capability Manifest is the single contract between a domain team and the platform. A team that publishes a valid manifest receives, without writing any frontend code: voice, chat, push-notification, and PWA surfaces; SSO and on-behalf-of auth integration; deterministic confirmation flows for risky actions; signed audit provenance; WCAG-compliant rendering via the A2UI catalog; and intent-level usage analytics.

The manifest is declarative. It describes *what the capability is* — its entities, intents, actions, risk levels, and rendering bindings — never *how to render it* and never any executable code. The platform composes all published manifests into the org-wide supergraph.

### Design principles

1. **One file, in the team's repo, deployed like code.** The manifest lives next to the service it describes, is validated in CI against the platform JSON Schema, and is published to the registry on deploy. No portals, no tickets.
2. **The team's API remains the policy enforcement point.** The manifest declares scopes and risk tiers, but authorization decisions happen inside the team's service on every call. The platform can never grant access the team's own API would deny.
3. **Risk tiers drive interaction policy.** Every action is `read`, `reversible`, or `consequential`. The tier — not the team, not the model — determines whether the platform requires a deterministic confirmation card before commit.
4. **Two fulfillment modes, team's choice.** `direct` mode means the platform calls the team's API for simple reads/actions. `agent` mode delegates the whole task to the team's own domain agent over A2A. Teams can start `direct`-only and graduate to a federated agent without changing the contract shape.
5. **Reference, don't redefine.** Shared entities (Employee, Team, Role) are owned by exactly one capability and referenced by others (`acme.directory#Employee`). Composition fails if two manifests claim ownership of the same entity type. This is how we get federation without an enterprise ontology committee.

---

## 2. Top-level structure

```yaml
manifest: "0.1"        # spec version this manifest conforms to
capability: {...}      # identity, ownership, lifecycle
runtime: {...}         # endpoints, fulfillment modes, SLOs
auth: {...}            # IdP audience, OBO flow, scopes
entities: [...]        # domain objects, schemas, resolution hints
intents: [...]         # what users can ask for
actions: [...]         # what can be done, with risk tiers
surfaces: {...}        # A2UI bindings and layout policy
notifications: [...]   # push events and action cards
policy: {...}          # data classification, visibility, residency
observability: {...}   # telemetry and SLO reporting opt-ins
```

Every section below defines the fields, then Section 4 gives a complete worked example.

---

## 3. Section reference

### 3.1 `capability` — identity and ownership

| Field | Req | Notes |
|---|---|---|
| `id` | yes | Reverse-DNS, globally unique in the registry: `acme.evaluations`. Immutable. |
| `name`, `description` | yes | Human-readable. The description is used by the intent router as routing context — write it the way you'd explain the app to a new hire. |
| `owner.team` | yes | Org path. Drives registry ownership, paging, and review routing. |
| `owner.oncall`, `owner.slack` | yes | The platform routes runtime failures here, not to a central queue. |
| `lifecycle` | yes | `draft` \| `beta` \| `ga` \| `deprecated`. `draft` capabilities are visible only to the owning team. |
| `version` | yes | Semver. Breaking contract changes (removed intent, changed slot type, tightened scope) require a major bump; the registry serves old majors for 90 days. |

### 3.2 `runtime` — how the platform reaches you

| Field | Req | Notes |
|---|---|---|
| `fulfillment_modes` | yes | Any of `direct`, `agent`. At least one. |
| `api.openapi` | yes | URL of your OpenAPI 3.1 doc. Direct-mode operations and entity schemas are resolved against it by `operationId` and `$ref` — the manifest never duplicates schemas. |
| `api.base_url` | yes | Versioned base URL. |
| `agent.protocol`, `agent.endpoint`, `agent.card` | if `agent` mode | A2A protocol version, task endpoint, and agent card URL. See Section 5 for the registration handshake. |
| `health` | yes | The registry health-checks this; unhealthy capabilities are routed around with a graceful "Evaluations is unavailable" surface, never a spinner. |
| `slo.read_p95_ms`, `slo.action_p95_ms` | yes | Your declared latency budget. Published on the platform dashboard; the renderer uses it to choose between blocking and optimistic UI. |

### 3.3 `auth` — identity delegation

| Field | Req | Notes |
|---|---|---|
| `idp` | yes | `okta` (only supported value in v0). |
| `audience` | yes | The token audience your API validates. |
| `flow` | yes | `on_behalf_of` is the only permitted value. The platform's token broker exchanges the user's session for a short-lived, audience-scoped, scope-limited token per call. **The platform holds no standing credentials to any domain system.** |
| `token_ttl_seconds` | yes | ≤ 600. |
| `scopes[]` | yes | Each scope: `id`, `description`. Actions reference scopes by id; the broker mints tokens with only the scopes the resolved action requires. |

### 3.4 `entities` — domain objects

Each entry is either an **owned entity** or a **federated reference**.

Owned entity fields: `type` (PascalCase, unique org-wide), `description`, `schema` (a `$ref` into your OpenAPI doc), `key` (primary identifier field), `display` (mustache templates for `title`/`subtitle` — used everywhere the entity is rendered, including confirmation cards, so make them disambiguating: include the employee ID, not just the name), and `resolution`:

```yaml
resolution:
  search_endpoint: /evaluations/search   # platform calls this to resolve "John Doe's eval"
  disambiguators: [subject.employee_id, cycle.name, due_date]
```

`disambiguators` are the fields shown side-by-side when resolution returns multiple candidates. **This is the field that prevents the wrong-John-Doe incident** — choose fields a human can tell apart at a glance.

Federated reference fields: `type`, `ref` (e.g. `acme.directory#Employee`), and `role_in_domain` (how your capability uses it, for routing context). The registry rejects composition if a `ref` points to an entity no GA capability owns.

### 3.5 `intents` — what users can ask for

| Field | Req | Notes |
|---|---|---|
| `id` | yes | snake_case, unique within the capability. |
| `description` | yes | Routing context for the LLM cold path. Precise descriptions are the highest-leverage text in the manifest. |
| `utterances[]` | yes | 3–10 examples with `{slot}` placeholders. These seed both the LLM router and, once an intent stabilizes, the **compiled hot path** — a deterministic pattern→route table that bypasses the model entirely for habitual phrasings. |
| `slots[]` | no | Each slot: `name`, `entity` (owned type or federated ref), `required`, optional `default`, and `disambiguation` (`strategy: card` forces a picker whenever resolution is ambiguous; `rank_by` orders candidates, e.g. `[same_team, reporting_line, recent_interaction]`). |
| `fulfillment` | yes | `mode: direct` + `operation` (OpenAPI operationId), or `mode: agent` + `task` (A2A task type your agent advertises). |
| `surface_hint` | no | `inline` (card in conversation), `focus` (full-screen flow), `ambient` (status only). A hint — the renderer may override for accessibility or device constraints. |
| `confidence.min_route` | no | Default 0.85. Below this the orchestrator asks a clarifying question rather than routing. **The router never guesses its way into an action; low confidence degrades to a question, not a wrong execution.** |

### 3.6 `actions` — what can be done, and how dangerous it is

| Field | Req | Notes |
|---|---|---|
| `id`, `operation` | yes | OperationId in your OpenAPI doc (direct) or task verb (agent). |
| `risk` | yes | `read` · `reversible` · `consequential`. |
| `scopes[]` | yes | Minimum scopes the broker must mint. |
| `idempotency` | yes for non-read | `required` means the platform sends an `Idempotency-Key` header and your API must honor it. This is what makes retries and double-taps safe. |
| `confirmation` | yes for `consequential` | See below. |
| `undo.window_seconds` | no | If > 0, the platform renders an undo affordance for that window after commit. An action with a meaningful undo window may qualify as `reversible`. |
| `audit.retention_days` | yes for non-read | Provenance receipt retention. |

**Confirmation block** (mandatory for `consequential`):

```yaml
confirmation:
  template: >
    Submit evaluation for {{subject.name}} ({{subject.employee_id}}, {{subject.team}})
    — cycle {{cycle.name}}. This finalizes the evaluation and notifies {{subject.manager.name}}.
  show_fields: [subject.name, subject.employee_id, cycle.name, overall_rating]
  requires: [explicit_tap]      # voice-only commit is never permitted for consequential actions
```

The confirmation card is rendered deterministically from **resolved** entity data — the model proposes, the card shows exactly what will happen, the human commits with a tap, and all three facts (proposal, displayed card, commit) are bound into one signed provenance receipt.

### 3.7 `surfaces` — A2UI bindings

| Field | Req | Notes |
|---|---|---|
| `catalog` | yes | Pinned catalog version, e.g. `a2ui/core@2`. Bindings may only reference component IDs in that catalog — there is no escape hatch to arbitrary markup or code. This is the structural defense against both UI drift and prompt-injection-into-rendering. |
| `bindings[]` | yes | Map each entity to `card` / `detail` / `list` components, and optionally each intent to a `flow` component. Unmapped entities fall back to the generic record components — federation works on day one, polish later. |
| `layout.stability` | yes | `pinned` (default — same layout every time; adaptation only on explicit user request), `adaptive`, or `user_choice`. Default to `pinned`: spatial memory is a feature. |
| `accessibility.requires` | yes | Usually `none` — the catalog guarantees WCAG 2.2 AA. Declare anything extra (e.g. `audio_descriptions`) here. |

### 3.8 `notifications` — push entry points

Each entry: `id`, `trigger` (`webhook` — your service posts the event to your capability's platform inbox), `template` (mustache over the event payload), `actions[]` (each either a platform verb — `snooze`, `dismiss` — or `open:<intent_id>` which deep-links into a fully prefetched surface), `priority`, and `quiet_hours: respect_user`. Notification action buttons inherit the risk tier of the action they invoke: a `consequential` approve button in a notification still opens the confirmation card — it never one-tap-commits from a lock screen.

### 3.9 `policy`

`authorization: pep_local` (your API enforces; only supported value), `data_classification`, `pii[]` (fields the platform must mask in logs/telemetry), `residency`, and `visibility.discoverable_by` — a role expression controlling who even *sees* this capability in the registry and in "what can I do here" affordances. Undiscoverable capabilities also don't participate in intent routing for that user, so the router cannot leak existence through clarifying questions.

### 3.10 `observability`

`telemetry: opt_in_full | aggregate_only` and `failed_intent_reports: weekly | off`. Full opt-in gets the team the intent analytics dashboard: which intents fire, which utterances fail to route, which requested capabilities don't exist. Failed-intent reports are anonymized and PII-masked per `policy.pii`.

---

## 4. Complete worked example — `acme.evaluations`

```yaml
manifest: "0.1"

capability:
  id: acme.evaluations
  name: Evaluations
  description: >
    Performance evaluations: schedule, author, review, and submit
    evaluations of employees for a review cycle.
  owner:
    team: people-systems/evaluations
    slack: "#evals-eng"
    oncall: pagerduty:evaluations
  lifecycle: beta
  version: 1.4.0

runtime:
  fulfillment_modes: [agent, direct]
  agent:
    protocol: a2a/0.3
    endpoint: https://evals.internal.acme.com/a2a
    card: https://evals.internal.acme.com/.well-known/agent.json
  api:
    openapi: https://evals.internal.acme.com/openapi.json
    base_url: https://evals.internal.acme.com/api/v1
  health: https://evals.internal.acme.com/healthz
  slo:
    read_p95_ms: 400
    action_p95_ms: 800

auth:
  idp: okta
  audience: api://acme.evaluations
  flow: on_behalf_of
  token_ttl_seconds: 300
  scopes:
    - id: evals.read
      description: Read evaluations visible to the caller
    - id: evals.write
      description: Author or edit a draft evaluation
    - id: evals.submit
      description: Submit a final evaluation

entities:
  - type: Evaluation
    description: A single evaluation of an employee for a review cycle
    schema: "#/components/schemas/Evaluation"
    key: evaluation_id
    display:
      title: "{{subject.name}} — {{cycle.name}}"
      subtitle: "{{status}} · due {{due_date}}"
    resolution:
      search_endpoint: /evaluations/search
      disambiguators: [subject.employee_id, cycle.name, due_date]

  - type: Employee
    ref: acme.directory#Employee
    role_in_domain: [subject, reviewer]

intents:
  - id: evaluate_person
    description: Start or resume an evaluation of a specific employee
    utterances:
      - "evaluate {employee}"
      - "I want to review {employee}'s performance"
      - "start {employee}'s eval for {cycle}"
    slots:
      - name: employee
        entity: acme.directory#Employee
        required: true
        disambiguation:
          strategy: card
          rank_by: [same_team, reporting_line, recent_interaction]
      - name: cycle
        entity: Evaluation.cycle
        required: false
        default: current_open_cycle
    fulfillment:
      mode: agent
      task: evaluations.author_flow
    surface_hint: focus
    confidence:
      min_route: 0.85

  - id: view_my_pending_evals
    description: Show evaluations assigned to the caller that are not yet submitted
    utterances:
      - "my pending evals"
      - "what evaluations do I owe"
    fulfillment:
      mode: direct
      operation: listPendingEvaluations
    surface_hint: inline

actions:
  - id: save_draft
    operation: saveEvaluationDraft
    risk: reversible
    scopes: [evals.write]
    idempotency: required
    audit:
      retention_days: 365

  - id: submit_evaluation
    operation: submitEvaluation
    risk: consequential
    scopes: [evals.submit]
    idempotency: required
    confirmation:
      template: >
        Submit evaluation for {{subject.name}} ({{subject.employee_id}},
        {{subject.team}}) — cycle {{cycle.name}}. This finalizes the
        evaluation and notifies {{subject.manager.name}}.
      show_fields: [subject.name, subject.employee_id, cycle.name, overall_rating]
      requires: [explicit_tap]
    undo:
      window_seconds: 0
    audit:
      retention_days: 2555

surfaces:
  catalog: a2ui/core@2
  bindings:
    - entity: Evaluation
      card: EvaluationCard
      detail: EvaluationDetail
      list: EvaluationTable
    - intent: evaluate_person
      flow: GuidedFormFlow
  layout:
    stability: pinned
    density_default: comfortable
  accessibility:
    requires: none

notifications:
  - id: eval_due
    trigger: webhook
    template: "Time to evaluate {{subject.name}} — due {{due_date}}"
    actions: ["open:evaluate_person", snooze, dismiss]
    priority: normal
    quiet_hours: respect_user

  - id: eval_overdue
    trigger: webhook
    template: "{{subject.name}}'s evaluation is {{days_overdue}} days overdue"
    actions: ["open:evaluate_person", snooze]
    priority: high
    quiet_hours: respect_user

policy:
  authorization: pep_local
  data_classification: confidential-hr
  pii: [subject.name, ratings, comments]
  residency: us-only
  visibility:
    discoverable_by: "role:manager"

observability:
  telemetry: opt_in_full
  failed_intent_reports: weekly
```

---

## 5. Lifecycle: publish, compose, route

**Publish.** The manifest lives at the repo root (`capability.yaml`). CI runs `xp validate` (schema check, OpenAPI cross-reference check — every `operation` and `schema` ref must resolve — and confirmation-template lint for consequential actions). Deploy publishes the manifest to the registry alongside the service.

**Compose.** On every publish, the registry recomposes the supergraph and runs federation checks: entity ownership conflicts, dangling `ref`s, intent utterance collisions across capabilities (flagged, not blocked — the router disambiguates at runtime), and scope/audience consistency with the IdP. Composition failures block publish with a precise error, the same way a broken GraphQL subgraph blocks gateway rollout.

**Route.** At runtime, an utterance hits the intent router. Compiled hot paths resolve deterministically (<50ms, no model). Cold paths go to the LLM router with the supergraph's intent descriptions as context, filtered to capabilities the caller can discover. Slots resolve through entity `resolution` endpoints; ambiguity renders a disambiguation card. Fulfillment dispatches `direct` (platform → team API, with a freshly brokered OBO token) or `agent` (platform → team's A2A endpoint, token attached, results streamed back as A2UI messages bound to the declared catalog).

### A2A registration handshake (agent mode)

1. On publish, the registry fetches `agent.card` and verifies the advertised task types cover every `fulfillment.task` in the manifest.
2. The registry issues the agent a capability-scoped client registration; the agent authenticates to the platform with it, and the platform forwards user OBO tokens per task — the domain agent acts as the user, never as a service account.
3. Domain agent responses are **structured A2A messages containing data and A2UI component references only**. Free text from a domain agent is rendered as content, never interpreted as instructions to the orchestrator — control plane and content plane stay separate end to end.
4. Health and protocol-version checks run continuously; an agent that drops a task type it still advertises in a published manifest pages the owning team.

---

## 6. Non-goals for v0 (decide in v1)

Cross-capability transactions (sagas spanning two domains), user-defined automation over intents, manifest-declared SLAs with enforcement, multi-IdP support, and a formal ontology layer. Each should be added only when failed-intent telemetry proves demand — that's the point of shipping the telemetry first.
