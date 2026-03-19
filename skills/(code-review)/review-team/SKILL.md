---
name: review-team
description: >
  Squad XI: time de agentes especializados para code review automatizado em MRs do GitLab.
  Use quando: precisar revisar MRs com validacao de regras do projeto, deteccao de violacoes,
  e comentarios inline no GitLab. NAO use para: reviews manuais, projetos sem regras definidas,
  ou quando CodeRabbit ja esta configurado como engine.
license: MIT
metadata:
  author: Pedro Escobar
  version: 1.0.0
  category: code-review
  tags:
    - gitlab
    - code-review
    - multi-agent
    - squad-xi
---

# Review Team (Squad XI) 🦀

Time de agentes especializados para code review automatizado, integrado ao GitLab via webhooks.

## Como funciona

O Squad XI e composto por 4 agentes que trabalham em sequencia:

| Agente | Papel | O que faz |
|--------|-------|-----------|
| 🦀 **Aratu** (Captain) | Orquestrador | Analisa o diff, classifica risco, decide se precisa de especialistas |
| 🪸 **Coral** (Researcher) | Pesquisadora | Pesquisa violacoes usando as regras do projeto |
| 🐚 **Nautilo** (Logician) | Validador | Valida achados da Coral, remove falsos positivos |
| 🐡 **Baiacu** (Contrarian) | Desafiador | Busca pontos cegos, edge cases, problemas de seguranca |

## Fluxo de execucao

1. **Aratu** recebe o diff e classifica areas de risco (low/medium/high)
2. **Regras do projeto** sao descobertas automaticamente (ver Descoberta de Regras)
3. **Coral** pesquisa violacoes usando as regras como contexto
4. **Nautilo** valida os achados, removendo falsos positivos
5. **Baiacu** desafia os achados validados, buscando o que os outros perderam
6. Se risco medio/alto, **especialistas** sao chamados em paralelo
7. Achados sao deduplicados e postados como comentarios inline no GitLab

## Descoberta de regras

A skill busca regras automaticamente no repositorio sendo revisado, nesta ordem de prioridade:

1. `.windsurf/rules/*.md` (regras mandatorias)
2. `.windsurf/skills/*/SKILL.md` e `*/AGENTS.md` (skills especializadas)
3. `.cursor/rules/*.md`
4. `.claude/rules/*.md` e `.claude/agents/**/*.md`
5. `CLAUDE.md` (raiz do projeto)
6. `biome.json` ou `.eslintrc.*` (regras de lint)

Se o projeto nao tiver regras, usa fallback com regras genericas de boas praticas.

## Especialistas (chamados sob demanda)

| Especialista | Quando e chamado | Foco |
|-------------|-----------------|------|
| react-specialist | Arquivos `.tsx` no diff | Server/Client Components, hooks, re-renders |
| typescript-advanced | Sempre | `any`, tipos, SDK types, generics |
| integration-review | `queries.ts`, `actions.ts` | ActionResult, server-only, validacao |
| ui-review | Componentes no diff | Design tokens, cores, i18n, icons |
| a11y-audit | Arquivos `.tsx` no diff | WCAG 2.1 AA, ARIA, semantica |
| quality-review | Sempre | console.log, unused code, performance |

## Trigger

Review e disparado apenas quando a MR tem o label `workflow::in-review`.

## Formato dos comentarios

```
🦀🔴: Uso de `any` no tipo de retorno. Use `unknown` com narrowing.
🦀🟡: Cor hardcoded `bg-blue-500`. Use o token `--accent-primary`.
🦀💡: O cast `as WorkspaceFormData` e redundante aqui.
```

## Deduplicacao

- Busca comentarios existentes do Pedroclaw na MR antes de postar
- Lock por `project:mr` via Redis (TTL 10min) previne reviews paralelos
- Verifica no banco se ja existe review completed pro mesmo MR

## Skills relacionadas

| Skill | Usar quando |
|-------|------------|
| postgres-best-practices | Revisando DDLs ou queries SQL |
| dbt-analytics-engineering | Revisando modelos dbt |
| airflow-operations | Revisando DAGs |
