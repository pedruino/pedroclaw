# Descoberta de regras do projeto

O Review Team descobre regras automaticamente do projeto sendo revisado, sem necessidade de configuracao manual.

## Estrategia de busca

### 1. Volume montado (preferencial)

No `docker-compose.yml`, o projeto e montado como volume read-only:

```yaml
worker:
  volumes:
    - ${FRONTEND_PATH}:/workspace/frontend:ro
```

O sistema le os arquivos diretamente do filesystem.

### 2. GitLab API (fallback)

Se o volume nao estiver montado, busca via API do GitLab usando o `project_id` do webhook:

```python
project = gl.projects.get(project_id)
tree = project.repository_tree(path='.windsurf/rules', ref='main')
for item in tree:
    content = project.files.get(item['path'], ref='main').decode()
```

### 3. Cache local

Regras descobertas sao cacheadas por 1 hora pra evitar chamadas repetidas ao GitLab API.

## Mapeamento de paths

| Path | Tipo | Prioridade |
|------|------|-----------|
| `.windsurf/rules/constitution.md` | Regra mandatoria | 1 (sempre carrega) |
| `.windsurf/rules/all.md` | Regra geral | 1 |
| `.windsurf/rules/design-system.md` | Regra de design | 2 |
| `.windsurf/rules/module-creation.md` | Regra de modulo | 2 |
| `.windsurf/skills/*/AGENTS.md` | Skill detalhada | 3 |
| `.windsurf/skills/*/SKILL.md` | Skill resumida | 3 |
| `.cursor/rules/*.md` | Regra Cursor | 2 |
| `.claude/agents/**/*.md` | Agente Claude | 3 |
| `CLAUDE.md` | Overview projeto | 2 |
| `biome.json` | Lint config | 4 (so extrai regras relevantes) |

## Selecao por tipo de arquivo

Nem todas as regras sao carregadas. O sistema analisa os arquivos no diff e seleciona:

```python
FILE_SKILLS_MAP = {
    ".tsx": ["react-specialist", "typescript-advanced", "ui-review", "a11y-audit", "design-system"],
    ".ts": ["typescript-advanced", "sdk-types", "integration-review"],
    ".css": ["design-system", "ui-review"],
}

ALWAYS_LOAD = ["constitution", "all", "quality-review"]
```

## Limite de tokens

O contexto total de skills e limitado a 30k caracteres (~7.5k tokens) pra evitar:
- Rate limit do provider (30k tokens/min no tier gratis da Anthropic)
- Custo excessivo por review
- Diluicao de contexto (muitas regras = LLM perde foco)

Prioridade de truncamento:
1. `constitution` + `all` (sempre inteiros)
2. Skills especificas por tipo de arquivo
3. Skills genericas (truncadas se passar do limite)

## Fallback generico

Se nenhuma regra for encontrada no projeto, o sistema usa regras genericas:

- TypeScript strict (no `any`, explicit return types, prefer `type` over `interface`)
- React (Server Components by default, `'use client'` so quando necessario)
- Security (validate input, no `dangerouslySetInnerHTML` sem sanitizacao)
- Accessibility (WCAG 2.1 AA, semantic HTML, ARIA)
- Performance (no waterfall fetches, use `Promise.all`)
- Code quality (no `console.log`, no unused imports)
