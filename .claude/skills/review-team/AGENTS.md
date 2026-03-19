# Review Team (Squad XI) - Guia para Agentes

## Visao geral

O Squad XI e o engine de review builtin do Pedroclaw. Ele orquestra 4 agentes + especialistas sob demanda para revisar MRs do GitLab.

## Arquitetura

```
MR com workflow::in-review
        |
        v
  Aratu (Captain)
  Analisa diff, classifica risco
        |
   +----+----+
   v    v    v
 Coral  Nautilo  Baiacu
 (pesquisa (valida   (desafia
  regras)  achados)  achados)
   |    |    |
   +----+----+
        v
  Aratu consolida + deduplica
  Risco medio/alto?
   +----+----+
   SIM       NAO
   v         v
Especialistas  Posta
em paralelo    comentarios
   v
  Posta
```

## Agentes

### Aratu (Captain) 🦀

**Papel**: Orquestrador. Recebe o diff bruto e decide o que fazer.

**Input**: Diff do MR + info do MR (titulo, descricao, branch)

**Output** (JSON):
```json
{
  "risk_areas": [
    {
      "file": "path/to/file.tsx",
      "lines": [10, 20, 30],
      "concerns": ["uso de any", "cor hardcoded"],
      "needs_specialist": false
    }
  ],
  "specialists_needed": ["react-specialist", "a11y-audit"],
  "overall_risk": "medium"
}
```

**Regras do Aratu**:
- Seja conservador: so marque `needs_specialist: true` se o codigo tiver complexidade que justifique
- MRs simples (rename, i18n, config) nao precisam de especialistas
- Classifique risco como `low` se o diff for < 50 linhas e nao tocar em logica de negocio

### Coral (Researcher) 🪸

**Papel**: Pesquisadora. Usa as regras do projeto pra encontrar violacoes.

**Input**: Diff + regras/skills do projeto (carregadas automaticamente)

**Output** (JSON array):
```json
[
  {"file": "path/file.tsx", "line": 15, "severity": "warning", "body": "Descricao concisa."}
]
```

**Regras da Coral**:
- Comente APENAS violacoes reais das regras fornecidas
- 1-2 frases por comentario, sem enrolacao
- NAO comente formatacao (Biome/ESLint cuida)
- NAO reclame de nomes de variaveis
- NUNCA use travessao (caractere —)
- Se nao encontrar violacoes, retorne array vazio

### Nautilo (Logician) 🐚

**Papel**: Validador. Filtra falsos positivos da Coral.

**Input**: Achados da Coral + diff original

**Output**: Mesmo formato, so com achados validados

**Regras do Nautilo**:
- Remova achados que sao falsos positivos
- Verifique se arquivo e linha estao corretos
- Melhore descricoes se necessario
- Se todos forem falsos positivos, retorne array vazio

### Baiacu (Contrarian) 🐡

**Papel**: Desafiador. Busca o que os outros perderam.

**Input**: Achados validados + diff original

**Output**: APENAS achados NOVOS (nao repetir os existentes)

**Regras do Baiacu**:
- Foque em: seguranca, edge cases, race conditions, vazamento de dados entre tenants
- Questione: "e se esse input for null?", "e se dois requests chegarem ao mesmo tempo?"
- Seja criterioso: so adicione se for realmente relevante
- NAO repita achados que ja estao na lista

## Especialistas

Chamados pelo Aratu quando `overall_risk` e `medium` ou `high`.

Cada especialista recebe:
1. O diff completo
2. A skill/regra especifica da sua area (se existir no projeto)

### Mapeamento de especialistas por tipo de arquivo

| Extensao | Especialistas carregados |
|----------|------------------------|
| `.tsx` | react-specialist, typescript-advanced, ui-review, a11y-audit, design-system |
| `.ts` | typescript-advanced, sdk-types, integration-review |
| `.css`, `.module.styl` | design-system, ui-review |
| `queries.ts` | integration-review, sdk-types |
| `actions.ts` | integration-review, sdk-types |
| `page.tsx` | module-architecture |

### Especialistas always-on

- `quality-review`: sempre carregado
- `typescript-advanced`: sempre carregado (em projetos TypeScript)

## Descoberta de regras

### Ordem de busca

O sistema busca regras no repositorio sendo revisado. A busca acontece via:
1. **Volume montado** (docker-compose): path local do projeto montado em `/workspace/frontend`
2. **GitLab API**: busca arquivos diretamente no repositorio via API (fallback)

### Paths buscados

```
.windsurf/rules/*.md          -> Regras mandatorias do Windsurf
.windsurf/skills/*/SKILL.md   -> Skills do Windsurf (resumo)
.windsurf/skills/*/AGENTS.md  -> Skills do Windsurf (detalhado)
.cursor/rules/*.md            -> Regras do Cursor
.claude/rules/*.md            -> Regras do Claude
.claude/agents/**/*.md        -> Agentes do Claude
CLAUDE.md                     -> Overview do projeto
biome.json                    -> Regras de lint (Biome)
.eslintrc.*                   -> Regras de lint (ESLint)
```

### Selecao inteligente

Nem todas as regras sao carregadas pra cada review. O sistema seleciona baseado nos arquivos no diff:

- Arquivos `.tsx` -> carrega skills de React, UI, a11y, design-system
- Arquivos `queries.ts` -> carrega skills de integracao, SDK
- Arquivos `.css` -> carrega skills de design-system

### Limite de contexto

Skills sao truncadas se o total passar de 30k caracteres, priorizando:
1. `constitution.md` (sempre primeiro)
2. `all.md` (regras gerais)
3. Skills especificas por tipo de arquivo

### Fallback

Se o projeto nao tiver regras definidas, o sistema usa um conjunto generico de boas praticas:
- TypeScript strict (no any, explicit return types)
- React best practices (Server Components first)
- Security (input validation, no dangerouslySetInnerHTML)
- Accessibility (WCAG 2.1 AA)
- Performance (no waterfall fetches)

## Formato de saida

Cada comentario e um `InlineComment`:

```json
{
  "file_path": "src/app/(modules)/drive/_components/Upload.tsx",
  "line": 42,
  "body": "Cor hardcoded `bg-blue-500`. Use o token `--accent-primary`.",
  "severity": "warning"
}
```

Severidades:
- `critical` (🔴): bug, seguranca, crash potencial
- `warning` (🟡): violacao de regra, pratica nao recomendada
- `suggestion` (💡): melhoria, alternativa melhor

## Deduplicacao

### Camada 1: LLM-level
Coral recebe a lista de comentarios ja existentes no prompt, evitando que os agentes repitam.

### Camada 2: Codigo
Worker compara `arquivo:linha` dos novos achados com os existentes e descarta duplicatas.

### Camada 3: Redis lock
Lock por `project:mr` (TTL 10min) previne que dois webhooks processem o mesmo MR simultaneamente.

### Camada 4: DB check
Verifica se ja existe review `completed` ou `running` pro mesmo MR antes de iniciar.

## Rate limiting

- Retry com backoff exponencial (30s, 60s, 90s) quando bater rate limit do provider
- Skills truncadas a 30k chars pra reduzir tokens
- Aratu usa diff truncado (8k chars) pra classificacao rapida

## Configuracao

Via `config/default.yaml`:

```yaml
review:
  engine: "builtin"  # builtin (Squad XI) | coderabbit
  builtin:
    model: "claude-sonnet-4-6"
    max_diff_lines: 1500
    temperature: 0.1
```

Via `.env`:

```env
REVIEW_ENGINE=builtin
LLM_REVIEW_MODEL=claude-sonnet-4-6
LLM_REVIEW_API_KEY=sk-ant-xxx
FRONTEND_PATH=/path/to/project  # pra carregar skills via volume
```
