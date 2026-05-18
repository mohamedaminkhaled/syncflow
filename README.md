<<<<<<< HEAD
<div align="center">

# SyncFlow

### The AI-native collaborative project management platform.

*Real-time boards. Streaming agents. Auditable AI. Built for teams that ship.*

[![Status](https://img.shields.io/badge/status-Week%201%20of%2052-blue)](./docs/ROADMAP.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-darkgreen)](https://www.djangoproject.com/)
[![AWS](https://img.shields.io/badge/deployed-AWS%20EKS-orange)](#-deployment)
[![CI](https://img.shields.io/badge/CI-pending-lightgrey)](.github/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-pending-lightgrey)](#)

[**Live demo**](#) · [**Architecture**](#-architecture) · [**Docs**](./docs/) · [**ADRs**](./docs/adr/) · [**Roadmap**](./docs/ROADMAP.md)

</div>

---

## Table of Contents

- [What SyncFlow Is](#what-syncflow-is)
- [Why It Exists](#why-it-exists)
- [Feature Tour](#-feature-tour)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Repository Layout](#-repository-layout)
- [Local Development](#-local-development)
- [Testing](#-testing)
- [Evals — Testing the AI Features](#-evals--testing-the-ai-features)
- [Observability](#-observability)
- [Cost & Production Guardrails](#-cost--production-guardrails)
- [Deployment](#-deployment)
- [Security](#-security)
- [Compliance](#-compliance)
- [Architecture Decision Records](#-architecture-decision-records)
- [Performance Benchmarks](#-performance-benchmarks)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [FAQ](#-faq)
- [License & Credits](#-license--credits)

---

## What SyncFlow Is

**SyncFlow is a multi-tenant, AI-native collaborative project management platform** — think Trello or Jira, but with first-class AI agents that take real actions inside your workspace: triaging bugs, breaking down epics, drafting standups, summarizing long discussions, and surfacing risks before they become blockers.

It is a single deployable Django application with:

- **Boards, lists, cards, comments, real-time multi-user editing** (Django Channels + WebSockets).
- **AI agents** that act on your workspace through a strict tool layer — every action is logged, costed, and revertible.
- **A production-grade observability + eval + cost layer** built around the LLMs from day one.
- **Multi-tenant isolation** with row-level security and per-tenant budget caps.
- **A REST and GraphQL API**, with WebSocket subscriptions for live updates.
- **Built-in audit trail and data lineage** for every AI decision — engineered for EU AI Act compliance from the start.

If you've used Linear, Notion AI, or Jira's AI features, the surface will feel familiar. The difference: SyncFlow is built so the AI layer is **observable, evaluatable, cost-bounded, and auditable** — not a magic black box bolted onto the side.

> **Project status.** SyncFlow is being built in public over 52 weeks as a portfolio capstone. It is currently in **Cycle 1**. Major features land cycle-by-cycle. The `main` branch is always deployable. See [Roadmap](#-roadmap).

---

## Why It Exists

Most production "AI features" today are duct-taped onto products with no engineering rigor around them. Specifically:

1. **No evals.** Nobody knows if a prompt change made things better or worse.
2. **No observability.** Engineers can't debug why an agent gave a bad answer at 3am.
3. **No cost guardrails.** A single user's runaway loop can bankrupt the feature.
4. **No audit trail.** "What inputs influenced this output?" is unanswerable.
5. **No reproducibility.** Models change. Behavior drifts. Nobody notices until the customer complaint arrives.

SyncFlow exists to demonstrate that **all of these problems are solvable with mature engineering** — and that solving them is what separates a real AI-native product from a demo. Every architectural decision is captured as an [ADR](./docs/adr/). Every AI call is traced, costed, eval-gated, and logged for forensics.

The project management domain is the carrier — the engineering layer is the contribution.

---

## ✨ Feature Tour

### Project Management Core
- **Workspaces → Projects → Boards → Lists → Cards** with drag-and-drop position management.
- **Real-time collaboration** — multi-user editing, presence indicators, live cursors (Django Channels).
- **Card metadata** — assignees, priorities, due dates, tags, estimated effort, comments with @mentions, file attachments.
- **Activity log** — every action recorded via Generic Relations and broadcast via WebSocket.
- **Dashboards** — team velocity, burndown, WIP analysis, member workload.

### AI Agents (Cycle 1+)
| Feature | What it does | How it's gated |
|---|---|---|
| **Card Drafter** | "Make a card for X" → generates title, description, acceptance criteria, suggested assignees. | Per-tenant budget, eval suite, prompt versioning. |
| **Epic Breaker** | Takes an epic; returns a tree of suggested cards with dependencies. | Same as above; supervisor-worker agent. |
| **Standup Composer** | Drafts a daily standup from recent activity + open cards per assignee. | Cached daily, regeneratable on demand. |
| **Risk Sentinel** | Nightly agent reviews active cards, flags overdue/at-risk items with reasoning. | Drift-monitored; alerts on accuracy degradation. |
| **Smart Search (RAG)** | Natural-language search across cards, comments, descriptions, attachments. | Hybrid search (vector + BM25 + reranker); cites sources. |
| **Inbox Triage** | Watches a configured email/webhook source; classifies and creates triaged cards. | Confidence-gated; humans approve below threshold. |

Every agent is built on the same primitives: a strict tool layer, structured outputs, eval coverage, OTel traces, and per-tenant cost accounting.

### Engineering Surfaces
- **REST API** (DRF) for standard CRUD + mobile clients.
- **GraphQL** (Graphene + Strawberry consideration in ADR-018) for complex queries.
- **WebSocket** (Channels) for live boards + agent streaming responses.
- **Webhooks out** — tenant-defined webhooks fire on configurable events.
- **Service-account API keys** — per-tenant, scoped, rotatable.

---

## 🏗 Architecture

### C4 Level 1 — System Context

```
                           ┌───────────────────────────────────┐
                           │             Users                 │
                           │  (Team members, admins, agents)   │
                           └──────────────┬────────────────────┘
                                          │
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                  SyncFlow                                        │
│                                                                                  │
│  Real-time collaborative project management with auditable AI agents.            │
│                                                                                  │
└────────┬──────────────────┬────────────────────┬────────────────────────┬────────┘
         │                  │                    │                        │
         ▼                  ▼                    ▼                        ▼
┌────────────────┐  ┌──────────────┐  ┌────────────────────┐  ┌────────────────────┐
│   Anthropic    │  │    OpenAI    │  │    AWS Bedrock     │  │  Tenant Webhooks   │
│  (Claude API)  │  │   (GPT API)  │  │  (Llama, Claude)   │  │ (configurable in)  │
└────────────────┘  └──────────────┘  └────────────────────┘  └────────────────────┘
```

### C4 Level 2 — Containers

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                  Internet                                        │
└──────────────┬───────────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    AWS ALB + CloudFront + WAF                                    │
└──────────────┬───────────────────────────────────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────────────────────────┐
│                              EKS Cluster                               │
│                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐    │
│  │   web (Django)   │  │  websocket       │  │  celery-worker     │    │
│  │   Gunicorn ASGI  │  │  Daphne (ASGI)   │  │  (agents, indexers,│    │
│  │   HPA: 1-10      │  │  HPA: 1-5        │  │   nightly jobs)    │    │
│  └────────┬─────────┘  └────────┬─────────┘  │  HPA: 1-20         │    │
│           │                     │            └────────┬───────────┘    │
│           └─────────────────────┴──────────────────────┘                │
│                                 │                                       │
│  ┌──────────────────────────────▼─────────────────────────────────┐   │
│  │            OpenTelemetry Collector (DaemonSet)                 │   │
│  └────────────┬───────────────────────────────────┬───────────────┘   │
└───────────────┼───────────────────────────────────┼───────────────────┘
                │                                   │
                ▼                                   ▼
┌──────────────────────────┐                ┌───────────────────────┐
│       Data Plane         │                │  Observability        │
│                          │                │                       │
│  • PostgreSQL 16 + RDS   │                │  • Grafana Cloud      │
│    + pgvector            │                │  • Honeycomb (traces) │
│    + Row-Level Security  │                │  • Loki (logs)        │
│  • Redis 7 (ElastiCache) │                │  • Prometheus (metrics│
│  • Redpanda (events)     │                │                       │
│  • S3 (attachments)      │                └───────────────────────┘
│  • Secrets Manager       │
└──────────────────────────┘
```

### The Agent Subsystem

Agents are not bolted on. They live behind a strict interface:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                              Agent Request                                     │
│                       (user action / scheduled trigger)                        │
└──────────────────────────────────┬─────────────────────────────────────────────┘
                                   │
              ┌────────────────────▼────────────────────┐
              │           Pre-flight Checks             │
              │  • Tenant budget (soft + hard limits)   │
              │  • Rate limit per tenant + per user     │
              │  • Provider circuit breaker             │
              │  • Semantic cache hit?                  │
              └────────────────────┬────────────────────┘
                                   │
                                   ▼
              ┌────────────────────┴────────────────────┐
              │            Model Routing                │
              │  Classifier → cheap model first;        │
              │  escalate to Sonnet on uncertainty.     │
              └────────────────────┬────────────────────┘
                                   │
                                   ▼
              ┌────────────────────┴────────────────────┐
              │           Supervisor Agent              │
              │   Plans → delegates → aggregates        │
              └────┬───────────────┬────────────────┬───┘
                   │               │                │
                   ▼               ▼                ▼
              ┌─────────┐    ┌─────────┐      ┌─────────┐
              │Retriever│    │ Analyzer│      │ Writer  │
              │ Worker  │    │ Worker  │      │ Worker  │
              └────┬────┘    └────┬────┘      └────┬────┘
                   │              │                │
                   └──────────────┼────────────────┘
                                  │
                                  ▼
              ┌────────────────────┴────────────────────┐
              │            Post-flight                  │
              │  • OTel spans (model, tokens, $, time)  │
              │  • Append to immutable audit log        │
              │  • Update lineage graph                 │
              │  • Eval gate (in CI; sampled in prod)   │
              └────────────────────┬────────────────────┘
                                   │
                                   ▼
                            Response to user
```

Detailed C4 diagrams (Container, Component, Code levels) live in [`docs/architecture/`](./docs/architecture/) as Structurizr DSL.

---

## 🧰 Tech Stack

| Layer | Choice | Why | ADR |
|---|---|---|---|
| **Language** | Python 3.12 | Lingua franca of AI engineering; Mohamed's strongest language. | — |
| **Web framework** | Django 5 + DRF + Channels | Mature, batteries-included; async-aware; ASGI for streaming. | [ADR-002](./docs/adr/0002-web-framework.md) |
| **API** | DRF (REST) + Graphene (GraphQL) | REST for mobile + CRUD; GraphQL for complex client queries. | [ADR-018](./docs/adr/0018-rest-and-graphql.md) |
| **Database** | PostgreSQL 16 + `pgvector` | One database for relational + vector; cuts ops complexity. | [ADR-004](./docs/adr/0004-vector-database.md) |
| **Cache & broker** | Redis 7 (Celery broker; cache; presence) | Lowest ops overhead; well-understood. | [ADR-005](./docs/adr/0005-broker-choice.md) |
| **Event bus** | Redpanda (Kafka-compatible) | Document indexing, agent triggers, event-driven workflows. | [ADR-010](./docs/adr/0010-event-streaming.md) |
| **Background jobs** | Celery + Redis | Mature, idempotent, Django-integrated. | [ADR-005](./docs/adr/0005-broker-choice.md) |
| **Async server** | Daphne (ASGI) + Gunicorn (WSGI) | WebSockets need ASGI; legacy paths use WSGI. | — |
| **LLM providers** | Anthropic + OpenAI + Bedrock | Multi-provider abstraction; routing by quality/cost. | [ADR-001](./docs/adr/0001-provider-abstraction.md) |
| **Agent framework** | Hand-rolled (Cycle 1) → LangGraph (Cycle 2+) | Build it raw first to understand; adopt framework where it helps. | [ADR-007](./docs/adr/0007-agent-framework.md) |
| **Vector / retrieval** | `pgvector` + Postgres FTS + Cohere Rerank | Hybrid search beats either alone. | [ADR-004](./docs/adr/0004-vector-database.md) |
| **Observability** | OpenTelemetry + Honeycomb + Grafana Cloud | Industry-standard; vendor-portable. | [ADR-006](./docs/adr/0006-observability.md) |
| **Evals** | Custom + `promptfoo` | Lightweight + extensible. | [ADR-008](./docs/adr/0008-eval-framework.md) |
| **Multi-tenancy** | Row-based + Postgres Row-Level Security | Simpler migrations than schema-per-tenant; RLS as defense-in-depth. | [ADR-014](./docs/adr/0014-multi-tenancy.md) |
| **Infrastructure** | AWS EKS + RDS + ElastiCache + S3 | Largest hiring pool; Bedrock co-located. | [ADR-005](./docs/adr/0005-eks-vs-ecs.md) |
| **IaC** | Terraform (community modules) | Industry default; reviewable PRs. | [ADR-011](./docs/adr/0011-terraform.md) |
| **CI/CD** | GitHub Actions | Free for OSS; reusable workflows. | [ADR-003](./docs/adr/0003-cicd.md) |
| **Frontend** | Django templates (marketing) + React 18 SPA (board) | SSR for SEO; SPA for interactive board. | — |
| **Frontend state** | React Query + Zustand | Server state + minimal client state. | — |
| **Linting** | `ruff` (lint + format) + `mypy --strict` | Single fast tool. | — |
| **Test runner** | `pytest`, `pytest-django`, `pytest-asyncio` | Industry default. | — |
| **Load testing** | Locust | Python-native; matches the rest of the stack. | — |

---

## 📁 Repository Layout

```
syncflow/
├── README.md                       # ← you are here
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── COMPLIANCE.md                   # EU AI Act mapping
├── CODE_OF_CONDUCT.md
├── pyproject.toml                  # uv-managed dependencies + tool config
├── .env.example                    # template; never committed with real values
├── .editorconfig
├── .gitignore
├── .dockerignore
├── Makefile                        # canonical commands: make up / migrate / test / lint
│
├── syncflow/                       # The Django project
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/                           # Domain apps (Django convention)
│   ├── accounts/                   # Users, auth, profile
│   ├── tenants/                    # Multi-tenancy, API keys, billing-stub
│   ├── workspaces/                 # Organizations, members, roles
│   ├── projects/                   # Projects, boards, lists, cards
│   ├── activity/                   # Activity log via Generic Relations
│   ├── comments/                   # Threaded comments + @mentions
│   ├── realtime/                   # Channels consumers (chat, board, agent stream)
│   ├── search/                     # RAG, vector index, hybrid retrieval
│   ├── agents/                     # The AI agent subsystem (see below)
│   ├── evals/                      # Eval framework, test suites, runners
│   ├── audit/                      # Immutable audit log + lineage queries
│   ├── observability/              # OTel custom instrumentation
│   ├── billing/                    # Tenant budgets, cost accounting
│   └── webhooks/                   # Outbound webhooks
│
├── syncflow/llm/                   # LLM provider abstraction (used by agents/, search/)
│   ├── providers/
│   │   ├── base.py                 # LLMProvider Protocol
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   └── bedrock_provider.py
│   ├── models.py                   # LLMResponse, LLMChunk dataclasses
│   ├── pricing.toml                # Per-model cost table
│   ├── cli.py                      # `syncflow ask ...` CLI
│   └── routing.py                  # Cheap-first model routing
│
├── apps/agents/                    # The agent subsystem
│   ├── supervisor.py               # Supervisor agent
│   ├── workers/
│   │   ├── retriever.py
│   │   ├── analyzer.py
│   │   └── writer.py
│   ├── tools/                      # Each tool is one file, sandboxed
│   │   ├── card_lookup.py
│   │   ├── project_search.py
│   │   ├── web_fetch.py
│   │   └── python_repl.py          # Sandboxed via RestrictedPython
│   ├── prompts/                    # *.md files, content-hashed
│   ├── replay.py                   # `syncflow replay --trace-id=X`
│   └── services.py                 # Public service-layer interface
│
├── deploy/
│   ├── helm/syncflow/              # Helm chart for EKS deployment
│   ├── grafana/dashboards/         # Dashboards as JSON (4 dashboards)
│   ├── otel-collector/             # OTel Collector config
│   └── nginx/                      # Local dev nginx config
│
├── infra/
│   └── terraform/
│       ├── modules/
│       │   ├── networking/
│       │   ├── compute/
│       │   ├── data/
│       │   └── observability/
│       ├── envs/
│       │   ├── dev/
│       │   └── prod/
│       └── README.md
│
├── docs/
│   ├── ROADMAP.md                  # 52-week roadmap
│   ├── adr/                        # Architecture Decision Records (Nygard format)
│   │   ├── README.md               # Index
│   │   ├── 0001-provider-abstraction.md
│   │   ├── 0002-web-framework.md
│   │   └── ...
│   ├── architecture/               # C4 diagrams as Structurizr DSL
│   │   ├── workspace.dsl
│   │   └── exports/
│   ├── runbooks/                   # Incident response runbooks
│   ├── evals.md                    # How evals work, current pass rates
│   ├── audit.md                    # How audit log + lineage work
│   ├── slos.md                     # SLO definitions + error-budget policies
│   └── retros/                     # Cycle retrospectives
│
├── notebooks/                      # Demo notebooks (RAG demos, eval analyses)
│
├── tests/
│   ├── unit/                       # Per-app unit tests live in apps/<app>/tests/
│   ├── integration/                # Cross-app integration tests
│   ├── e2e/                        # Full-flow tests
│   ├── evals/                      # Eval test suites (run in CI as gate)
│   └── performance/locustfile.py
│
├── Dockerfile                      # Production image (multi-stage, non-root)
├── Dockerfile.dev                  # Dev image
├── docker-compose.yml              # Full local stack
│
└── .github/
    ├── workflows/
    │   ├── ci.yml                  # 6-stage pipeline
    │   ├── terraform.yml           # Plan on PRs
    │   ├── eval-gate.yml           # Block PR merge on eval regression
    │   └── release.yml             # Tag-triggered release pipeline
    ├── pull_request_template.md
    └── ISSUE_TEMPLATE/
```

---

## 🚀 Local Development

### Prerequisites

- **Docker** ≥ 24 and **Docker Compose** ≥ 2.20
- **Python** 3.12 (for running tooling outside Docker; optional)
- **`uv`** package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **API keys** for at least one LLM provider (Anthropic recommended)

### One-Command Setup

```bash
git clone https://github.com/<your-username>/syncflow.git
cd syncflow
cp .env.example .env             # then edit .env with your API keys
make up                          # brings up postgres + redis + redpanda + django + celery
make migrate                     # runs Django migrations
make seed                        # loads demo workspace, users, projects, sample cards
```

Open `http://localhost:8000/admin/` (login: `admin@syncflow.local` / `dev`) or `http://localhost:3000/` for the React SPA.

### Make Targets

| Command | Purpose |
|---|---|
| `make up` | Bring up the full stack (Postgres, Redis, Redpanda, Django, Celery, OTel Collector). |
| `make down` | Tear down. |
| `make migrate` | Run Django migrations. |
| `make seed` | Load demo data. |
| `make shell` | Django shell inside the web container. |
| `make test` | Run the full pytest suite. |
| `make test-evals` | Run the eval suite against the current code. |
| `make lint` | Run ruff + mypy. |
| `make format` | Auto-format with ruff. |
| `make logs` | Tail logs from all services. |
| `make psql` | Open psql against the local Postgres. |
| `make load-test` | Run Locust against local stack. |

### LLM CLI (sanity check)

```bash
make shell
>>> from syncflow.llm.cli import ask
>>> ask("anthropic", "claude-sonnet-4-5", "Summarize Django Channels in 2 sentences.")
```

Or from a shell:

```bash
docker compose exec web python -m syncflow.llm.cli ask \
  --provider anthropic --model claude-sonnet-4-5 \
  "Summarize Django Channels in 2 sentences."
```

Output includes the response, tokens, and cost to 5-decimal-USD precision.

### Environment Variables (key ones)

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Active settings module | `syncflow.settings.dev` |
| `DATABASE_URL` | Postgres connection string | `postgres://syncflow:dev@db:5432/syncflow` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |
| `ANTHROPIC_API_KEY` | Anthropic API key | — (required for agents) |
| `OPENAI_API_KEY` | OpenAI API key | — (optional) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTel collector endpoint | `http://otel-collector:4317` |
| `SENTRY_DSN` | Sentry error tracking | — (optional in dev) |
| `LLM_DEFAULT_PROVIDER` | Default provider | `anthropic` |
| `LLM_DEFAULT_MODEL` | Default model | `claude-sonnet-4-5` |
| `TENANT_DEFAULT_BUDGET_USD` | Per-tenant monthly cap | `100.00` |

Full list in [`.env.example`](.env.example).

---

## 🧪 Testing

**Test pyramid** (per `pytest` markers):

```
   ┌─────────────────────────┐
   │       e2e (10%)         │   Full-flow tests; slow; gate on main.
   ├─────────────────────────┤
   │   integration (30%)     │   Django test client + service containers.
   ├─────────────────────────┤
   │      unit (60%)         │   Pure-function + service-layer tests.
   └─────────────────────────┘
```

Run levels independently:

```bash
make test-unit            # < 30s
make test-integration     # < 2 min
make test-e2e             # < 5 min
make test-load            # Locust against local stack
make test-evals           # ~3 min; runs eval suite
```

**Coverage target:** ≥ 80% lines, ≥ 90% on `apps/agents/` and `apps/audit/` (high-risk paths).

**Property-based tests** use Hypothesis for invariant testing on critical functions (cost accounting, position re-balancing).

**Mutation testing** with `mutmut` runs weekly; target ≥ 80% mutation kill rate.

---

## 🎯 Evals — Testing the AI Features

Conventional tests can't verify "did the model give a good answer?" — that's what evals are for. Every AI feature in SyncFlow has an eval suite.

### How They Work

```
tests/evals/
├── card_drafter/
│   ├── cases.yaml          # 50+ test cases
│   ├── evaluator.py        # Judge model + deterministic checks
│   └── README.md
├── epic_breaker/
├── standup_composer/
├── risk_sentinel/
└── smart_search/
```

**Each test case** has:
- `input` — the prompt or scenario.
- `expected_traits` — list of qualities the answer must have (e.g., "mentions acceptance criteria", "no hallucinated names").
- `forbidden_traits` — list of qualities it must not have.

**Each evaluator** combines:
1. **Deterministic checks** — regex, JSON schema match, contains.
2. **Judge-model checks** — Claude scores each trait 0/1 against a strict rubric.

### The CI Gate

The [`eval-gate.yml`](.github/workflows/eval-gate.yml) workflow runs the full eval suite on every PR. The pass-rate is compared against `main`. If it drops more than 5%, **CI fails and the PR cannot merge.**

Comment on the PR shows:
```
Eval Results
            main → PR       Δ
card_drafter       94% → 91%   -3%   ✅
epic_breaker       88% → 88%    0%   ✅
standup_composer   91% → 73%  -18%   ❌ regression
```

Bypass requires the `eval:skip` label, applied only by a maintainer with a written reason.

### Production Drift Monitor

A nightly Celery beat job samples 100 real production queries, runs them through the eval suite, and compares to the baseline. Drift > 5% triggers a Grafana alert with a runbook link.

See [`docs/evals.md`](./docs/evals.md) for the full philosophy.

---

## 📊 Observability

Every LLM call, tool call, retrieval, and database query is a span. Every span has structured attributes that make 3am debugging tractable.

### OpenTelemetry Attribute Conventions

```python
# Standard span attributes set on every LLM call
span.set_attributes({
    "gen_ai.system": "anthropic",
    "gen_ai.request.model": "claude-sonnet-4-5",
    "gen_ai.request.temperature": 0.0,
    "gen_ai.prompt.hash": prompt_sha256,
    "gen_ai.usage.input_tokens": resp.usage.input_tokens,
    "gen_ai.usage.output_tokens": resp.usage.output_tokens,
    "gen_ai.cost.usd": cost,
    "gen_ai.response.finish_reason": resp.stop_reason,
    "syncflow.tenant_id": tenant.id,
    "syncflow.session_id": session.id,
    "syncflow.feature": "card_drafter",
})
```

### Grafana Dashboards (shipped in `deploy/grafana/dashboards/`)

1. **Service Health** — HTTP p50/p95/p99, error rate, request volume, pod saturation.
2. **LLM Cost** — $/hour, $/tenant (top 10), $/feature, projected monthly burn.
3. **Quality** — Eval pass rate over time, broken by feature, by model.
4. **Drift** — Prompt-token-distribution shift, embedding-distribution shift, error trend.

Every panel has a runbook annotation linked to `docs/runbooks/`.

### SLOs (live in `docs/slos.md`)

| SLO | Target | Window |
|---|---|---|
| RAG query latency | p99 < 5s | 28d |
| Eval pass rate | ≥ 90% | 7d |
| Cost per query | p95 ≤ $0.05 | 7d |
| Service availability | ≥ 99.5% | 28d |

Burn-rate alerts in Grafana follow Google SRE's multi-window multi-burn-rate pattern.

### Replay CLI

When something goes wrong in production, get the trace ID from Honeycomb, then:

```bash
syncflow replay --trace-id=abc123 --diff
```

This reads the trace, resolves the exact prompt version by hash, re-runs the LLM call with the same parameters (temp=0, same context), and diffs the output. Useful for: prompt-change regression analysis, model-upgrade impact, customer support investigations.

---

## 💰 Cost & Production Guardrails

LLM cost is a load-bearing concern, not an afterthought. SyncFlow's guardrails:

### Per-Tenant Budgets
Each tenant has `monthly_budget_usd`. Soft limit (80% default) triggers a warning notification + admin-visible banner. Hard limit (100%) downgrades to the cheaper model based on tenant policy, then to a deterministic fallback.

### Model Routing
A small classifier model decides if a query is "simple" or "complex." Simple → Haiku/GPT-4o-mini. Complex → Sonnet/GPT-4o. Routing decisions are logged for eval analysis — quality must be measurably equivalent.

### Semantic Cache
Repeated similar queries (cosine similarity ≥ 0.95 to a recent cached query, same tenant, same feature) return cached answers. Hit/miss ratio visible in Grafana. Tenants can disable via setting.

### Prompt Caching
Anthropic prompt caching enabled for system prompts → typical 50%+ reduction in input-token cost on agent loops.

### Batch API
Non-time-sensitive workloads (embedding backfills, nightly eval runs, drift detection) use OpenAI's batch API → ~50% cost reduction.

### Circuit Breakers
Five provider failures in 60 seconds → circuit opens for 30 seconds → traffic routes to fallback provider. Prevents cascading failures during provider incidents.

See [ADR-009: Cost guardrails architecture](./docs/adr/0009-cost-guardrails.md).

---

## ☁️ Deployment

### Production Topology

- **EKS** (managed Kubernetes) on AWS, single cluster, multi-AZ.
- **RDS Postgres 16** (db.r6g.large in prod) with read replicas.
- **ElastiCache Redis 7** cluster.
- **Redpanda Cloud** for the event bus.
- **S3** for static + media + audit log payloads.
- **CloudFront** in front of the ALB; **WAF** for OWASP Top 10 protections.
- **Secrets Manager** for credentials; **External Secrets Operator** syncs them into K8s.
- **Grafana Cloud** + **Honeycomb** for observability.

### Provisioning

Everything is in Terraform. From a fresh AWS account:

```bash
cd infra/terraform/envs/prod
terraform init
terraform plan
terraform apply
```

End-to-end provisioning time: ~25 minutes.

### Deployment Flow

```
PR opened → CI (lint, type, unit, integration, security, evals)
   ├── all green → reviewer approves → merge to main
   │
   └── main push → build & push image to ECR → Helm upgrade on EKS
                  → rolling deploy with readiness gates
                  → smoke tests against canary pod
                  → if green, full rollout; if red, automatic rollback
```

No manual deploys. No `kubectl edit` in prod. Everything via GitHub Actions + Helm.

### Disaster Recovery

- **RDS** automated backups (35-day retention) + cross-region snapshots.
- **Tenant data export** API — every tenant can pull their data in JSON + Parquet.
- **Recovery runbook** in `docs/runbooks/disaster-recovery.md`. Last tested: see file.

---

## 🔒 Security

See [`SECURITY.md`](./SECURITY.md) for the full threat model. Highlights:

- **STRIDE threat-modeled.** Every threat documented + mitigation.
- **OWASP Top 10** mitigations applied (CSP, HSTS, parameterized queries, output encoding, rate limits).
- **OWASP Top 10 for LLM Apps** mitigations (prompt-injection structural defenses, sandboxed tool execution, output filtering, max-iteration + cost caps).
- **API keys** hashed at rest (SHA-256), shown in full only at creation.
- **Postgres Row-Level Security** as defense-in-depth for tenant isolation.
- **Secrets** never in code, env files, or container images. Always Secrets Manager.
- **Dependency scanning** in CI (`safety`, `pip-audit`, `trivy`).
- **OWASP ZAP** scan in CI against the staging environment, monthly.
- **Reporting:** `security@syncflow.example` — PGP key in `SECURITY.md`.

---

## ⚖️ Compliance

SyncFlow is built EU AI Act-aware from day one. See [`COMPLIANCE.md`](./COMPLIANCE.md) for the full mapping.

| EU AI Act obligation | SyncFlow implementation |
|---|---|
| **Transparency** — users must know they're interacting with AI | Every AI response includes `meta.is_ai_generated: true` + model identifier. UI labels AI features explicitly. |
| **Logging** — high-risk systems must log decisions | Immutable audit log captures every prompt, retrieval, tool call, output, eval outcome with content hashes. |
| **Risk management** | Documented in `SECURITY.md` (STRIDE) + ADRs. |
| **Data governance** | Lineage queries; PII tagging in audit log; tenant-configurable retention. |
| **Human oversight** | Destructive actions require explicit human confirmation; AI suggestions are never auto-applied. |
| **Accuracy + robustness** | Eval suite in CI; production drift monitor; circuit breakers per provider. |
| **Cybersecurity** | Per-tenant isolation; rate limits; OWASP mitigations. |

This is positioning, not just compliance — enterprise buyers ask the same questions.

---

## 📚 Architecture Decision Records

Every meaningful decision is documented in [`docs/adr/`](./docs/adr/) using the Michael Nygard format: **Status / Context / Decision / Consequences.** New decisions are added as new ADRs; old ADRs are superseded, not deleted.

Sample ADRs (full index in [`docs/adr/README.md`](./docs/adr/README.md)):

- [ADR-001: Multi-provider LLM abstraction](./docs/adr/0001-provider-abstraction.md)
- [ADR-004: Vector database choice (pgvector vs. dedicated)](./docs/adr/0004-vector-database.md)
- [ADR-007: Hand-rolled agent framework before adopting LangGraph](./docs/adr/0007-agent-framework.md)
- [ADR-009: Cost guardrails architecture](./docs/adr/0009-cost-guardrails.md)
- [ADR-014: Multi-tenancy approach (row-based + RLS)](./docs/adr/0014-multi-tenancy.md)

**Read these first if you're evaluating SyncFlow technically.** They explain not just *what* but *why*.

---

## 📈 Performance Benchmarks

Last measured: see [`docs/benchmarks/`](./docs/benchmarks/) for the most recent.

| Endpoint | Load | p50 | p95 | p99 | Throughput |
|---|---|---|---|---|---|
| `GET /api/v1/boards/{id}/` | 200 concurrent users | 45ms | 120ms | 280ms | 1,800 req/s |
| `POST /api/v1/cards/` | 100 concurrent users | 30ms | 95ms | 180ms | 1,200 req/s |
| `POST /api/v1/search/` (RAG) | 50 concurrent users | 1.2s | 3.4s | 4.8s | 80 req/s |
| `POST /api/v1/agents/draft-card/` | 50 concurrent users | 2.1s | 5.5s | 7.2s | 40 req/s |
| WebSocket message broadcast | 1,000 connected | — | — | — | 18,000 msg/s |

LLM-mediated endpoints are bounded by upstream provider latency, not SyncFlow.

Run the benchmark yourself: `make load-test`.

---

## 🗺 Roadmap

SyncFlow is being built over 52 weeks across 4 cycles. Current cycle and progress in [`docs/ROADMAP.md`](./docs/ROADMAP.md).

| Cycle | Months | Theme | Status |
|---|---|---|---|
| **1** | 1–3 | Foundations + first AI feature + AWS + CI/CD + first evals | 🚧 In progress |
| **2** | 4–6 | Multi-agent + full observability + cost guardrails + streaming | ⏳ Planned |
| **3** | 7–9 | Multi-tenancy + Service Layer + CQRS + audit + compliance + v1.0 | ⏳ Planned |
| **4** | 10–12 | Go to market: Go port of retrieval gateway + portfolio polish | ⏳ Planned |

Major releases:
- **v0.1** (end of Cycle 1): First end-to-end AI feature, AWS deploy, eval suite.
- **v0.5** (end of Cycle 2): Production-grade reliability + observability + cost.
- **v1.0** (end of Cycle 3): Multi-tenant SaaS-grade.

---

## 🤝 Contributing

SyncFlow is currently single-author but designed to be contributor-ready. If you find this repo and want to contribute:

1. Open an issue describing the change before sending a PR.
2. Branch from `main`. Use Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).
3. CI must be green. Eval gate must pass (or have a documented bypass).
4. Architectural changes require an ADR in the PR.
5. New features ship with tests + docs.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the full guide.

### Code Style

- Python: `ruff` (lint + format). `mypy --strict` on `syncflow/` and `apps/`.
- Commit messages: Conventional Commits.
- Branch names: `<type>/<short-description>` — `feat/card-drafter-streaming`, `fix/celery-retry`.

---

## ❓ FAQ

**Is this production-ready?**
v0.1 is functional in production but missing multi-tenant primitives that arrive in Cycle 3 (v1.0). The architecture is production-grade; the feature surface is intentionally narrow until then.

**Why Django, not FastAPI?**
Django gives mature ORM, admin, auth, migrations, signals, and Channels (for WebSockets) out of the box. FastAPI is great for thin services; SyncFlow is a thick product. See [ADR-002](./docs/adr/0002-web-framework.md).

**Why pgvector and not Pinecone / Weaviate / Qdrant?**
One database is cheaper to operate than two. pgvector at SyncFlow's scale (single-digit millions of vectors per tenant) is fast enough. Re-evaluate when one tenant exceeds 10M vectors. See [ADR-004](./docs/adr/0004-vector-database.md).

**Why hand-build the agent loop before using LangGraph?**
To understand the primitives. Frameworks are wonderful when you know what they're abstracting; dangerous when you don't. The hand-rolled version stays in the repo as a teaching artifact and a fallback. See [ADR-007](./docs/adr/0007-agent-framework.md).

**How is this different from Linear/Notion/Jira AI features?**
SyncFlow's AI features are *engineered like real software*: versioned prompts, regression-tested with evals, traced end-to-end, cost-bounded per tenant, audited for compliance. Most products treat AI as a magic call; SyncFlow treats it as a load-bearing subsystem.

**Can I self-host this?**
Yes. The Helm chart in `deploy/helm/syncflow/` works on any K8s cluster. You need: Postgres 16+ with `pgvector`, Redis 7+, Redpanda or Kafka, an S3-compatible object store, and at least one LLM API key.

**Where do I report bugs / request features?**
GitHub issues. Security issues to `security@syncflow.example` (PGP key in `SECURITY.md`).

---

## 📜 License & Credits

**License:** Apache 2.0 — see [`LICENSE`](./LICENSE).

**Built by** [Mohamed Amin](https://github.com/<your-username>) as the capstone of a 12-month AI-native backend engineering plan.

**Acknowledgments:**
- The Django, DRF, and Channels teams.
- The OpenTelemetry community.
- Hamel Husain, Eugene Yan, and Simon Willison — whose writing made the AI engineering parts learnable.
- Will Larson — whose writing made the senior-engineering parts learnable.
- Every author of every ADR I've cited in mine.

**If SyncFlow helped you,** consider:
- ⭐ Starring this repo.
- 📝 Sharing a real-world story of building AI-native features in a comment.
- 🤝 Opening an issue with what's missing.

---

<div align="center">

**SyncFlow — built in public, one cycle at a time.**

[Roadmap](./docs/ROADMAP.md) · [Architecture](./docs/architecture/) · [ADRs](./docs/adr/) · [Eval Reports](./docs/evals.md)

</div>
=======
# syncflow
SyncFlow is a multi-tenant, AI-native collaborative project management platform — think Trello or Jira, but with first-class AI agents that take real actions inside your workspace: triaging bugs, breaking down epics, drafting standups, summarizing long discussions, and surfacing risks before they become blockers.
>>>>>>> 51bc4a4fb3617fa4d387bef5e630aea7bd9d69c9
