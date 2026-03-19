# AI Code Review & Pipeline Automation Tools - Pricing Comparison (BRL)

> **Exchange Rate Used:** 1 USD = 5.33 BRL (March 13-14, 2026)
> **Research Date:** March 2026

---

## 1. AI Code Review Tools - Comprehensive Pricing

### 1.1 CodeRabbit

| Tier | USD/user/month | BRL/user/month | Billing | Key Limits |
|------|---------------|----------------|---------|------------|
| **Free** | $0 | R$ 0 | - | PR summaries only; 200 files/hr, 4 PR reviews/hr; 14-day Pro trial |
| **Lite** | $12 (annual) / $15 (monthly) | R$ 63,96 / R$ 79,95 | Per developer | Unlimited PRs, customizable learnings, web query, code graph |
| **Pro** | $24 (annual) / $30 (monthly) | R$ 127,92 / R$ 159,90 | Per developer | Unlimited reviews, all integrations incl. Jira |
| **Enterprise** | Custom (~$30/user for 500+) | ~R$ 159,90+ | Custom (min ~$15K/mo) | Self-hosted, compliance, dedicated support |

- **Billing model:** Per-seat, only active PR creators are charged
- **Self-hosted:** Enterprise tier only, custom pricing

---

### 1.2 Qodo (formerly CodiumAI) / PR-Agent

| Tier | USD/user/month | BRL/user/month | Key Limits |
|------|---------------|----------------|------------|
| **Developer (Free)** | $0 | R$ 0 | 30 free PRs/mo (promo); 250 credits/mo; IDE + CLI |
| **Teams** | $30 (~$38 regular, currently discounted) | R$ 159,90 | Unlimited PRs (promo, normally 20/user/mo); 2,500 credits/mo |
| **Enterprise** | Custom (contact sales) | Custom | Multi-repo context engine, SSO, analytics, on-prem/air-gapped |

- **Open Source:** PR-Agent is free and open-source (self-host with your own LLM keys)
- **Credit system:** Most operations = 1 credit; Claude Opus = 5 credits; Grok 4 = 4 credits
- **Self-hosted:** Enterprise tier supports SaaS, single/multi-tenant, on-prem, air-gapped

---

### 1.3 Sourcery

| Tier | USD/seat/month | BRL/seat/month | Key Limits |
|------|---------------|----------------|------------|
| **Free** | $0 | R$ 0 | Public repositories only |
| **Pro** | $12 | R$ 63,96 | Private repos, 30+ languages |
| **Team** | $24 | R$ 127,92 | Repo analytics, unlimited security scanning |
| **Enterprise** | Custom | Custom | Custom pricing, advanced features |

- Integrates with GitHub, GitLab, VS Code, PyCharm

---

### 1.4 What The Diff

| Tier | USD/month | BRL/month | Key Limits |
|------|----------|-----------|------------|
| **Free** | $0 | R$ 0 | 25,000 tokens/mo (~10 PRs); rate limited |
| **Pro 200k** | $19 | R$ 101,27 | 200,000 tokens/mo (~40 PRs); priority support |

- **Pricing model:** Per-organization (not per-user)
- Tokens do NOT roll over monthly
- Average PR ~2,300 tokens

---

### 1.5 Bito AI

| Tier | USD/user/month | BRL/user/month | Key Limits |
|------|---------------|----------------|------------|
| **Free Trial** | $0 (14 days) | R$ 0 | Limited trial period |
| **Team** | $15 | R$ 79,95 | Up to 25 seats; GPT-4o, Claude Sonnet access |
| **Professional** | $25 | R$ 133,25 | All Team features + premium features |
| **Enterprise** | Custom | Custom | Advanced enterprise features |

- Seat-based billing; monthly charges on 1st of each month

---

### 1.6 Tabnine

| Tier | USD/user/month | BRL/user/month | Key Limits |
|------|---------------|----------------|------------|
| **Free** | Discontinued (April 2025) | - | Was "Basic" tier; now 90-day Dev preview trial only |
| **Code Assistant** | $39 (annual) | R$ 207,87 | Code completions, AI chat, Jira integration |
| **Agentic Platform** | $59 (annual) | R$ 314,47 | All Code Assistant + autonomous agents, CLI, Code Review Agent, unlimited codebase connections |

- **Self-hosted:** SaaS, VPC, on-prem Kubernetes, fully air-gapped
- **LLM options:** Anthropic, OpenAI, Google, Meta, Mistral
- Zero code retention policy; SOC 2, GDPR, ISO 27001

---

### 1.7 Greptile

| Tier | USD/seat/month | BRL/seat/month | Key Limits |
|------|---------------|----------------|------------|
| **Cloud** | $30 | R$ 159,90 | 50 reviews/seat included; $1/review after (R$ 5,33) |
| **Enterprise** | Custom | Custom | Self-hosted, SSO/SAML, GitHub Enterprise, dedicated Slack |

- **No free plan**
- **Discounts:** 100% off for open source; 50% off for startups; up to 20% off for 1+ year contracts
- Unlimited repos and users on all plans

---

### 1.8 Cursor BugBot

| Tier | USD/user/month | BRL/user/month | Key Limits |
|------|---------------|----------------|------------|
| **BugBot** | $40 (monthly) / $32 (annual) | R$ 213,20 / R$ 170,56 | 200 PRs/month; unlimited reviews |

- **NOT included** in Cursor Pro subscription -- separate add-on
- Charges per user who authors PRs reviewed by BugBot (including external contributors)
- Cursor Pro ($20/mo) is separate for IDE features

---

### 1.9 GitLab Duo

| Component | USD/user/month | BRL/user/month | Notes |
|-----------|---------------|----------------|-------|
| **GitLab Premium** (base) | $29 (annual) | R$ 154,57 | Base platform |
| **GitLab Ultimate** (base) | $99 (annual) | R$ 527,67 | Base platform |
| **Duo Pro** (add-on) | $19 | R$ 101,27 | Available for Premium & Ultimate |
| **Duo Enterprise** (add-on) | $39 | R$ 207,87 | Ultimate only; full SDLC AI |
| **Premium + Duo Pro** | $48 | R$ 255,84 | Combined total |
| **Ultimate + Duo Enterprise** | $138 | R$ 735,54 | Combined total |

- Limited-time free credits: Premium = 12 credits/user/mo; Ultimate = 24 credits/user/mo

---

### 1.10 Linear (Triage Intelligence)

| Tier | USD/user/month | BRL/user/month | Key Features |
|------|---------------|----------------|--------------|
| **Free** | $0 | R$ 0 | Basic issue tracking |
| **Basic** | $10 | R$ 53,30 | Standard features |
| **Business** | $16 | R$ 85,28 | SLAs, AI Triage Intelligence, Zendesk/Intercom, Linear Insights |
| **Enterprise** | Custom (~$40/user at scale) | Custom (~R$ 213+) | SAML/SCIM, sub-initiatives, advanced security, migration support |

- Triage Intelligence available on **Business and Enterprise** only
- Enterprise 500-user benchmark: ~$239K/year (~R$ 1.27M/year); discounts 16-32%

---

## 2. LLM API Costs (for Building Your Own Tool)

### 2.1 Model Pricing per 1M Tokens

| Provider / Model | Input (USD) | Input (BRL) | Output (USD) | Output (BRL) | Notes |
|-----------------|-------------|-------------|--------------|--------------|-------|
| **OpenAI GPT-4o** | $2.50 | R$ 13,33 | $10.00 | R$ 53,30 | Cached: $1.25 input; Batch: 50% off |
| **OpenAI GPT-4o-mini** | $0.15 | R$ 0,80 | $0.60 | R$ 3,20 | Budget option |
| **Claude Sonnet 4.6** | $3.00 | R$ 15,99 | $15.00 | R$ 79,95 | 1M context at standard price (March 2026) |
| **Claude Opus 4.6** | $5.00 | R$ 26,65 | $25.00 | R$ 133,25 | Most capable; 1M context GA |
| **Gemini 2.5 Pro** | $1.25 | R$ 6,66 | $10.00 | R$ 53,30 | >200K context: $2.50 input; Batch: 50% off |
| **DeepSeek V3.2** | $0.28 (miss) / $0.028 (hit) | R$ 1,49 / R$ 0,15 | $0.42 | R$ 2,24 | Off-peak 50-75% discount |
| **DeepSeek R1** | $0.12 | R$ 0,64 | $0.20 | R$ 1,07 | Reasoning model |

### 2.2 Embedding Model Pricing per 1M Tokens

| Model | USD/1M tokens | BRL/1M tokens | Notes |
|-------|--------------|---------------|-------|
| **text-embedding-3-large** | $0.13 | R$ 0,69 | 3072 dimensions |
| **text-embedding-3-small** | $0.02 | R$ 0,11 | 1536 dimensions |
| **Batch API (large)** | $0.065 | R$ 0,35 | 50% off standard |

---

## 3. Vector Database Costs

| Solution | Type | Free Tier | Paid Pricing (USD) | Paid Pricing (BRL) |
|----------|------|-----------|-------------------|-------------------|
| **pgvector** | Self-hosted (PostgreSQL extension) | Fully free | Only infra costs | Only infra costs |
| **ChromaDB** | Self-hosted | Fully free | Only infra costs | Only infra costs |
| **Pinecone** | Cloud (Serverless) | 2GB storage, 1M reads/mo, 2M writes/mo | Standard: $50/mo min; $8.25/M reads, $2/M writes, $0.33/GB | Standard: R$ 266,50/mo min |
| **Qdrant Cloud** | Cloud (Managed) | 1GB free cluster | Pay-per-use (compute + memory + storage); Hybrid from $0.014/hr | ~R$ 0,07/hr hybrid |
| **Weaviate Cloud** | Cloud (Managed) | Sandbox (limited) | Flex: $45/mo; Plus: $280/mo; Premium: custom | Flex: R$ 239,85/mo; Plus: R$ 1.492,40/mo |
| **Upstash (Redis+Vector)** | Serverless | 256MB, 500K cmds/mo | $0.20/100K cmds; $0.25/GB storage | R$ 1,07/100K cmds |

---

## 4. Infrastructure Costs (Self-Hosting)

| Resource | Provider | Specs | USD/month | BRL/month |
|----------|----------|-------|-----------|-----------|
| **VPS (Budget)** | Hetzner CPX22 | 2 vCPU / 4 GB RAM | ~$9.50 | ~R$ 50,64 |
| **VPS (Mid)** | DigitalOcean | 2 vCPU / 4 GB RAM | $24 | R$ 127,92 |
| **VPS (AWS)** | AWS Lightsail | 1 vCPU / 2 GB RAM | $10 | R$ 53,30 |
| **VPS (AWS EC2)** | AWS t3.small | 2 vCPU / 2 GB RAM | ~$15 | ~R$ 79,95 |
| **Redis (Managed)** | Upstash (Serverless) | Pay-per-use | ~$0-5 (light use) | ~R$ 0-26,65 |
| **Redis (Managed)** | AWS ElastiCache | cache.t4g.micro | ~$12/mo | ~R$ 63,96 |
| **PostgreSQL (Managed)** | AWS RDS | db.t4g.micro (2 vCPU / 1 GB) | ~$12/mo | ~R$ 63,96 |
| **PostgreSQL (Managed)** | DigitalOcean | 1 vCPU / 1 GB / 10 GB | $15/mo | R$ 79,95 |

---

## 5. "Build Your Own" Cost Estimate

**Scenario:** Small team, 3-5 devs, ~50 MRs/month, ~200 issues/month

### 5.1 Token Consumption Estimate

| Activity | Tokens per event | Events/month | Total tokens/mo |
|----------|-----------------|--------------|-----------------|
| MR code review (diff + context) | ~8,000 input + ~2,000 output | 50 | 400K in / 100K out |
| MR summary generation | ~3,000 input + ~500 output | 50 | 150K in / 25K out |
| Issue triage/classification | ~1,500 input + ~300 output | 200 | 300K in / 60K out |
| Embedding generation (code chunks) | ~500 per chunk | 500 chunks/mo | 250K tokens |
| **Total** | | | **~1.1M input / 185K output + 250K embedding** |

### 5.2 Monthly Cost Breakdown - Option A: Budget (DeepSeek + Self-Hosted)

| Component | USD/month | BRL/month |
|-----------|-----------|-----------|
| DeepSeek V3.2 API (~1.1M input, ~185K output) | ~$0.39 | ~R$ 2,08 |
| Embedding (text-embedding-3-small, 250K tokens) | ~$0.005 | ~R$ 0,03 |
| VPS (Hetzner 2 vCPU / 4 GB) | ~$9.50 | ~R$ 50,64 |
| PostgreSQL + pgvector (self-hosted on VPS) | $0 (included in VPS) | R$ 0 |
| Redis (self-hosted on VPS) | $0 (included in VPS) | R$ 0 |
| **TOTAL** | **~$10** | **~R$ 53** |

### 5.3 Monthly Cost Breakdown - Option B: Mid-Range (Claude Sonnet + Managed Services)

| Component | USD/month | BRL/month |
|-----------|-----------|-----------|
| Claude Sonnet 4.6 API (~1.1M input, ~185K output) | ~$6.08 | ~R$ 32,41 |
| Embedding (text-embedding-3-large, 250K tokens) | ~$0.03 | ~R$ 0,16 |
| VPS (DigitalOcean 2 vCPU / 4 GB) | $24 | R$ 127,92 |
| PostgreSQL (DigitalOcean managed) | $15 | R$ 79,95 |
| Redis (Upstash serverless) | ~$3 | ~R$ 15,99 |
| Pinecone (Starter - free for this volume) | $0 | R$ 0 |
| **TOTAL** | **~$48** | **~R$ 256** |

### 5.4 Monthly Cost Breakdown - Option C: Premium (GPT-4o + AWS Managed)

| Component | USD/month | BRL/month |
|-----------|-----------|-----------|
| GPT-4o API (~1.1M input, ~185K output) | ~$4.60 | ~R$ 24,52 |
| Embedding (text-embedding-3-large, 250K tokens) | ~$0.03 | ~R$ 0,16 |
| VPS (AWS EC2 t3.small) | ~$15 | ~R$ 79,95 |
| PostgreSQL (AWS RDS db.t4g.micro) | ~$12 | ~R$ 63,96 |
| Redis (AWS ElastiCache) | ~$12 | ~R$ 63,96 |
| **TOTAL** | **~$44** | **~R$ 234** |

---

## 6. Side-by-Side Comparison: Buy vs Build

### Cost per month for 5 developers, ~50 MRs/month

| Solution | USD/month (5 devs) | BRL/month (5 devs) | Self-hosted? | Key Trade-off |
|----------|--------------------|--------------------|--------------|---------------|
| **Build Your Own (Budget)** | ~$10 | ~R$ 53 | Yes | Cheapest; needs dev effort to build & maintain |
| **Build Your Own (Mid)** | ~$48 | ~R$ 256 | Hybrid | Good balance; managed DB reliability |
| **Build Your Own (Premium)** | ~$44 | ~R$ 234 | Hybrid | AWS ecosystem; slightly more expensive |
| **What The Diff (Pro)** | $19 (org) | R$ 101 | No | Cheapest SaaS; limited to ~40 PRs/mo |
| **CodeRabbit (Lite)** | $60-75 | R$ 320-400 | No | Good value for unlimited PRs |
| **CodeRabbit (Pro)** | $120-150 | R$ 640-800 | No | Full features incl. Jira |
| **Sourcery (Pro)** | $60 | R$ 320 | No | Solid for private repos |
| **Sourcery (Team)** | $120 | R$ 640 | No | Adds analytics + security scan |
| **Bito (Team)** | $75 | R$ 400 | No | Good AI model access |
| **Bito (Professional)** | $125 | R$ 666 | No | Premium features |
| **Qodo (Free)** | $0 | R$ 0 | No | 30 PRs/mo free (promo); open-source PR-Agent |
| **Qodo (Teams)** | $150 | R$ 800 | No | Unlimited PRs (promo); 2,500 credits |
| **Greptile (Cloud)** | $150 | R$ 800 | No | 50 reviews/seat; no free tier |
| **Cursor BugBot** | $160-200 | R$ 853-1,066 | No | 200 PRs/mo; separate from IDE |
| **Tabnine (Code Assistant)** | $195 | R$ 1,039 | Optional | Full IDE + code review |
| **Tabnine (Agentic)** | $295 | R$ 1,572 | Optional | Autonomous agents; most complete |
| **GitLab Duo (Prem+Pro)** | $240 | R$ 1,279 | No | Requires GitLab Premium base |
| **GitLab Duo (Ult+Ent)** | $690 | R$ 3,678 | No | Most expensive; full SDLC AI |
| **Linear (Business)** | $80 | R$ 426 | No | Issue triage only (not code review) |

---

## 7. Key Observations

### Best Value for Small Teams (3-5 devs):
1. **Qodo Free + PR-Agent OSS** - R$ 0/mo for basic PR review (self-host PR-Agent with own LLM keys)
2. **Build Your Own (Budget)** - ~R$ 53/mo with DeepSeek + Hetzner; maximum flexibility
3. **What The Diff Pro** - R$ 101/mo per org; simplest setup but limited to ~40 PRs
4. **CodeRabbit Lite** - R$ 320-400/mo; unlimited PRs, good automation

### Best Value for Code Review Quality:
1. **CodeRabbit Pro** - R$ 640-800/mo; best-in-class PR reviews with Jira integration
2. **Greptile Cloud** - R$ 800/mo; deep codebase understanding (v4 accuracy improvements)
3. **Qodo Teams** - R$ 800/mo; strong multi-repo context

### Best for Self-Hosted / Air-Gapped:
1. **Qodo Enterprise** - On-prem, air-gapped options
2. **Tabnine** - SaaS, VPC, on-prem K8s, or fully offline
3. **PR-Agent OSS** - Fully open-source, bring your own LLM

### Most Cost-Effective LLM for Code Review:
1. **DeepSeek V3.2** - ~R$ 2/mo for 50 MRs (20-50x cheaper than GPT-4o)
2. **Gemini 2.5 Pro** - ~R$ 35/mo; good quality/price ratio
3. **GPT-4o** - ~R$ 25/mo; strong quality, well-documented
4. **Claude Sonnet 4.6** - ~R$ 32/mo; excellent code understanding

### Vector DB Recommendation for Small Teams:
- **pgvector** (free, self-hosted) or **Qdrant free tier** (1GB) are sufficient for 3-5 devs

---

## Sources

- [CodeRabbit Pricing](https://www.coderabbit.ai/pricing)
- [Qodo Pricing](https://www.qodo.ai/pricing/)
- [Sourcery Documentation](https://docs.sourcery.ai/Plans-and-Pricing/)
- [What The Diff Pricing](https://whatthediff.ai/pricing)
- [Bito Pricing](https://bito.ai/pricing/)
- [Tabnine Pricing](https://www.tabnine.com/pricing/)
- [Greptile Pricing](https://www.greptile.com/pricing)
- [Cursor BugBot](https://cursor.com/bugbot)
- [GitLab Pricing](https://about.gitlab.com/pricing/)
- [Linear Pricing](https://linear.app/pricing)
- [OpenAI API Pricing](https://openai.com/api/pricing/)
- [Anthropic Claude Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Google Gemini Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [DeepSeek API Pricing](https://api-docs.deepseek.com/quick_start/pricing)
- [Pinecone Pricing](https://www.pinecone.io/pricing/)
- [Qdrant Pricing](https://qdrant.tech/pricing/)
- [Weaviate Pricing](https://weaviate.io/pricing)
- [Upstash Redis Pricing](https://upstash.com/pricing/redis)
- [USD/BRL Exchange Rate - Trading Economics](https://tradingeconomics.com/brazil/currency)
- [USD/BRL Exchange Rate History 2026](https://www.exchangerates.org.uk/USD-BRL-spot-exchange-rates-history-2026.html)
- [Hetzner Cloud](https://www.hetzner.com/cloud)
- [DigitalOcean VPS](https://www.digitalocean.com/solutions/vps-hosting)
- [AWS RDS PostgreSQL Pricing](https://aws.amazon.com/rds/postgresql/pricing/)
- [AWS ElastiCache Pricing](https://aws.amazon.com/elasticache/pricing/)
