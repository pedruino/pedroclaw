# Pedroclaw 🦀

AI-powered GitLab pipeline automation with pluggable review engines and knowledge base.

Similar to CodeRabbit, but adapted to PM-driven workflows with issue triage, workflow state management, and a knowledge base that learns from past issues.

## Features

- **Squad XI** multi-agent review (Aratu, Coral, Nautilo, Baiacu)
- **Pluggable Review Engine** builtin (Squad XI) ou CodeRabbit
- **Issue Triage Agent** classifica issues, sugere labels, busca issues similares
- **Knowledge Base** RAG sobre issues/MRs passados usando pgvector
- **Interactive Commands** `@pedroclaw review`, `@pedroclaw triage` via GitLab comments
- **Skills em runtime** carrega regras do projeto frontend automaticamente
- **LLM Agnostic** Claude, GPT, DeepSeek, Gemini, ou modelos locais via config

## Stack

Python 3.12 · FastAPI · Celery · Redis · PostgreSQL/pgvector · LiteLLM

## Quick Start

### 1. Configure

```bash
cp .env.example .env
```

Copy and edit `.env` (see [`.env.example`](.env.example) for every variable, including Langfuse):

```env
# GitLab — Settings > Access Tokens (scope: api)
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=glpat-xxxx
GITLAB_WEBHOOK_SECRET=pick-a-secret

# LLM (any provider via LiteLLM)
LLM_REVIEW_MODEL=claude-sonnet-4-6   # or: deepseek/deepseek-chat, gpt-4o, gemini/gemini-2.5-pro
LLM_REVIEW_API_KEY=sk-ant-xxxx

# Review engine
REVIEW_ENGINE=builtin               # builtin | squad-xi | coderabbit | pr_agent

# Embedding (for knowledge base) — optional
# LLM_KB_MODEL=text-embedding-3-small
# LLM_KB_API_KEY=sk-xxxx

# DB and Redis — no changes needed if using docker-compose
DATABASE_URL=postgresql+asyncpg://pedroclaw:pedroclaw@localhost:5432/pedroclaw
REDIS_URL=redis://localhost:6379/0
```

### 2. Run

```bash
docker compose up -d
```

This starts: API (port 8000) + Celery Worker + Celery Beat + PostgreSQL/pgvector + Redis + Langfuse (UI on port 3000) + ClickHouse + MinIO (see [Local development](#local-development)).

### 3. Verify

```bash
curl http://localhost:8000/health
# → {"status":"ok","version":"0.1.0"}
```

### 4. Configure GitLab Webhook

In your GitLab project: **Settings > Webhooks > Add webhook**

| Field | Value |
|-------|-------|
| URL | `https://your-domain.com/webhooks/gitlab` |
| Secret token | same as `GITLAB_WEBHOOK_SECRET` in `.env` |
| Triggers | ✅ Issues events, ✅ Merge request events, ✅ Comments |

> For local testing, use [ngrok](https://ngrok.com): `ngrok http 8000`

### 5. Test locally (without GitLab)

```bash
# Simulate an issue opened
curl -X POST http://localhost:8000/webhooks/gitlab \
  -H "Content-Type: application/json" \
  -H "X-Gitlab-Event: Issue Hook" \
  -d '{"object_attributes":{"action":"open","iid":1},"project":{"id":123,"path_with_namespace":"test/repo"}}'

# Simulate a merge request opened
curl -X POST http://localhost:8000/webhooks/gitlab \
  -H "Content-Type: application/json" \
  -H "X-Gitlab-Event: Merge Request Hook" \
  -d '{"object_attributes":{"action":"open","iid":1},"project":{"id":123,"path_with_namespace":"test/repo"}}'
```

## Local development

### What `docker compose` runs

| Service | Role |
|---------|------|
| `api` | FastAPI (`:8000`) |
| `worker` | Celery worker (MR review, triage, KB) |
| `beat` | Celery beat |
| `db` | PostgreSQL 17 + pgvector (`:5432`) |
| `redis` | Redis (`:6379`) |
| `langfuse-web` | Langfuse UI (`:3000`) |
| `langfuse-worker` | Langfuse async processing |
| `clickhouse` | Langfuse analytics backend |
| `minio` | S3-compatible storage for Langfuse events |

Convenience: `make run` runs `docker compose up -d --build`; `make stop` runs `docker compose down`.

### Langfuse (LLM observability)

Pedroclaw registers LiteLLM’s `langfuse_otel` callback so completions are sent to Langfuse via OpenTelemetry ([integration](https://langfuse.com/integrations/frameworks/litellm-sdk)).

1. **One-time Postgres database for Langfuse** (if the stack fails to migrate until `langfuse` exists):

   ```bash
   docker compose exec db psql -U pedroclaw -d postgres -c "CREATE DATABASE langfuse;"
   ```

2. **Secrets in `.env`** (see [`.env.example`](.env.example)):

   - `LANGFUSE_NEXTAUTH_SECRET` and `LANGFUSE_SALT` — long random strings you choose.
   - `LANGFUSE_ENABLED=true`
   - After the UI is up, create **API keys** in Langfuse and set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`.

3. **Hosts**:

   - With **Docker Compose as written**, `api` and `worker` already receive `LANGFUSE_OTEL_HOST=http://langfuse-web:3000` from `docker-compose.yml`. Your `.env` can keep the same values for consistency.
   - If you run **only** Postgres/Redis/Langfuse in Docker and run the API **on the host** with `uvicorn`, set `LANGFUSE_HOST` and `LANGFUSE_OTEL_HOST` to `http://localhost:3000`.

4. **UI**: open [http://localhost:3000](http://localhost:3000), sign up (local signup is enabled), then **Settings → API keys** and paste the keys into `.env`. Restart `api` / `worker` if they started before keys were set.

5. **Langfuse Cloud**: point `LANGFUSE_HOST` / `LANGFUSE_OTEL_HOST` to `https://cloud.langfuse.com` (or your region URL from their docs) and use project keys from the cloud UI. You can omit the self-hosted Langfuse services if you do not need them.

6. **Disable**: set `LANGFUSE_ENABLED=false`.

### Skills path (frontend rules)

The worker mounts the frontend repo so Squad XI can load project skills (e.g. `.claude/skills`). By default Compose uses `./frontend` → `/workspace/frontend` inside the worker. Override on the host:

```bash
export FRONTEND_PATH=/caminho/para/seu/frontend
docker compose up -d
```

`FRONTEND_PATH` in settings maps to `frontend_path` ([`config.py`](src/pedroclaw/config.py)).

### Run API and worker without full Compose (optional)

Use this when you want a local Python process while DB/Redis (and optionally Langfuse) still run in Docker:

```bash
pip install -e ".[dev]"
# or: uv sync && uv run …
export $(grep -v '^#' .env | xargs)   # load .env — adjust for your shell if needed
uvicorn pedroclaw.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
celery -A pedroclaw.tasks.worker:celery_app worker --loglevel=info
celery -A pedroclaw.tasks.worker:celery_app beat --loglevel=info   # if you need scheduled tasks
```

Point `DATABASE_URL` / `REDIS_URL` at `localhost` if those services publish ports from Compose.

### Agno AgentOS (separate from Pedroclaw core)

The production app is FastAPI + Celery + LiteLLM. **AgentOS** is Agno’s optional runtime with a web UI and APIs for agents ([Run your AgentOS](https://docs.agno.com/agent-os/run-your-os)). To try it locally alongside this repo:

1. Install the SDK (extras match what you need, e.g. LiteLLM-backed models):

   ```bash
   pip install "agno[agentos,litellm]"
   ```

2. Set the provider API key your agents use (for example `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` per Agno docs).

3. Follow the official guide to instantiate and serve an `AgentOS` — see [Agent OS](https://docs.agno.com/agent-os/run-your-os) and [configuration](https://docs.agno.com/agent-os/config).

4. For **traces** with AgentOS + OpenTelemetry, Agno’s docs recommend `opentelemetry-api`, `opentelemetry-sdk`, and `openinference-instrumentation-agno` ([example](https://docs.agno.com/examples/agent-os/tracing/basic-agent-tracing)); you can point OTLP at the same Langfuse or another backend you use for local experiments.

Pedroclaw does not embed AgentOS in the GitLab webhook path; use AgentOS when building or debugging Agno agents separately.

## Architecture

### Fluxograma geral

```mermaid
flowchart TD
    GL[GitLab Webhook] --> API[FastAPI receiver]
    API --> Redis[(Redis queue)]
    Redis --> Worker[Celery Worker]

    Worker --> Triage{Issue?}
    Worker --> Review{MR com<br/>workflow::in-review?}
    Worker --> KB[KB Sync]

    Triage -->|Sim| TriageAgent[Triage Agent]
    TriageAgent --> Labels[Aplica labels<br/>no GitLab]

    Review -->|Sim| Engine{Engine?}
    Review -->|Nao| Skip[Ignora]

    Engine -->|builtin| Squad[Squad XI]
    Engine -->|coderabbit| CR[CodeRabbit SaaS]

    Squad --> Aratu[🦀 Aratu<br/>Captain]
    Aratu --> Coral[🪸 Coral<br/>Researcher]
    Aratu --> Nautilo[🐚 Nautilo<br/>Logician]
    Aratu --> Baiacu[🐡 Baiacu<br/>Contrarian]
    Coral --> Consolidate[Aratu consolida]
    Nautilo --> Consolidate
    Baiacu --> Consolidate
    Consolidate --> RiskCheck{Risco alto?}
    RiskCheck -->|Sim| Specialists[Especialistas<br/>em paralelo]
    RiskCheck -->|Nao| Post[Posta comentarios<br/>inline no GitLab]
    Specialists --> Post

    KB --> pgvector[(pgvector)]
```

### Diagrama de sequencia: Review de MR

```mermaid
sequenceDiagram
    participant GL as GitLab
    participant API as FastAPI
    participant R as Redis
    participant W as Celery Worker
    participant A as 🦀 Aratu
    participant C as 🪸 Coral
    participant N as 🐚 Nautilo
    participant B as 🐡 Baiacu
    participant S as Especialistas
    participant LLM as LLM API

    GL->>API: POST /webhooks/gitlab (MR event)
    API->>API: Valida token
    API->>R: Enfileira task_review_mr
    API-->>GL: 200 OK (< 10s)

    R->>W: Dequeue task
    W->>GL: GET MR info + labels
    W->>W: Tem workflow::in-review?

    alt Sem label
        W-->>W: Skip review
    else Com label
        W->>GL: GET MR diff
        W->>A: Analisa diff

        A->>LLM: Classifica risco + areas
        LLM-->>A: risk_areas + specialists_needed

        A->>C: Pesquisa violacoes
        C->>C: Carrega skills do projeto
        C->>LLM: Diff + regras do projeto
        LLM-->>C: Lista de achados

        A->>N: Valida achados da Coral
        N->>LLM: Achados + diff
        LLM-->>N: Achados filtrados (sem falsos positivos)

        A->>B: Desafia achados
        B->>LLM: Achados validados + diff
        LLM-->>B: Pontos cegos encontrados

        opt Risco medio/alto
            A->>S: Chama especialistas em paralelo
            S->>LLM: Diff + skill especifica
            LLM-->>S: Achados especializados
        end

        A->>A: Consolida + deduplica

        loop Para cada achado
            W->>GL: POST inline comment 🦀
        end
    end
```

### Diagrama de sequencia: Triage de Issue

```mermaid
sequenceDiagram
    participant CL as Cliente
    participant GL as GitLab
    participant API as FastAPI
    participant R as Redis
    participant W as Celery Worker
    participant T as Triage Agent
    participant LLM as LLM API
    participant KB as Knowledge Base

    CL->>GL: Cria issue
    GL->>API: POST /webhooks/gitlab (Issue event)
    API->>R: Enfileira task_triage_issue
    API-->>GL: 200 OK

    R->>W: Dequeue task
    W->>GL: GET issue info
    W->>T: Triage issue

    opt KB habilitada
        T->>KB: Busca issues similares
        KB-->>T: Top-k similares
    end

    T->>LLM: Issue + contexto KB
    LLM-->>T: Classificacao + labels sugeridos

    W->>GL: Cria labels (se nao existem)
    W->>GL: Aplica labels na issue
    W->>GL: Posta comentario de triagem 🦀
```

### Workflow States

```mermaid
stateDiagram-v2
    [*] --> triagem: Issue criada

    triagem --> conceito: Feature identificada
    triagem --> in_dev: Bug vai direto pra dev
    triagem --> done: Duvida respondida

    conceito --> especificacao: PM escreve spec

    especificacao --> revisao_spec: Spec pronta
    especificacao --> conceito: Precisa repensar

    revisao_spec --> ready_for_dev: Spec + SDD aprovados
    revisao_spec --> especificacao: Spec precisa ajuste

    ready_for_dev --> in_dev: Dev inicia

    in_dev --> in_review: MR aberta
    in_dev --> ready_for_dev: Requirements mudaram

    in_review --> done: Aprovado + merged
    in_review --> in_dev: Precisa de changes

    done --> [*]

    state triagem {
        direction LR
        [*] --> analise: 🦀 Pedroclaw analisa
        analise --> classificacao: Consulta KB
        classificacao --> [*]: Aplica labels
    }

    state in_review {
        direction LR
        [*] --> ai_review: 🦀 Squad XI
        ai_review --> human_review: 2 devs + 1 maintainer
        human_review --> [*]: 2/3 aprovam
    }
```

## Workflow States (GitLab labels `workflow::*`)

| State | Quem | O que acontece |
|-------|------|---------------|
| `triagem` | Pedroclaw | Agente de triagem analisando issue |
| `conceito` | PM | Ideia registrada, ainda nao priorizada |
| `especificacao` | PM | PM escrevendo user stories e requisitos |
| `revisao-spec` | Arquiteto + PM | Revisando spec, Arquiteto escreve SDD |
| `ready-for-dev` | - | Spec + SDD aprovados, pode iniciar dev |
| `in-dev` | Dev | Em desenvolvimento |
| `in-review` | Pedroclaw + Devs | 🦀 AI review + revisao humana (2 devs + 1 maintainer) |
| `done` | - | Concluido |

## Configuration

All config lives in `config/default.yaml`. Key sections:

- **workflow** — states, transitions, initial/done states
- **labels** — nature, priority, app prefix, state prefix (~15 core labels)
- **review** — engine selection, model, prompts, max diff lines
- **triage** — auto-label, KB lookup, top-k similar issues
- **knowledge_base** — embedding model, chunk size, sync interval

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/

# Type check
mypy src/
```

## Cost Estimate

For a team of 5 devs, ~165 MRs/month:

| LLM | Review + Triage + KB | Per MR |
|-----|---------------------|--------|
| DeepSeek V3 | ~R$ 1/month | R$ 0.006 |
| Claude Sonnet | ~R$ 60/month | R$ 0.36 |
| GPT-4o | ~R$ 50/month | R$ 0.30 |

Infrastructure: R$ 50-130/month (VPS + DB + Redis)

## License

MIT
