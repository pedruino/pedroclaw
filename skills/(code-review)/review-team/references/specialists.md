# Especialistas do Review Team

## Quando sao chamados

Especialistas so sao acionados pelo Aratu quando:
1. `overall_risk` e `medium` ou `high`
2. O tipo de arquivo no diff corresponde a area do especialista

Isso economiza tokens: MRs simples (rename, config, i18n) nao chamam especialistas.

## Lista de especialistas

### react-specialist

**Foco**: React 19 e Next.js 16

**Verifica**:
- Server Components vs Client Components (decisao correta?)
- `'use client'` so quando necessario (hooks, browser APIs, event handlers)
- `page.tsx` sempre Server Component
- Data fetching: `serverFetch`/`serverFetchSafe`, nunca fetch direto
- `Promise.all()` pra fetches paralelos (sem waterfalls)
- Zustand pra estado global (nunca Context + useState pra estado mutavel)
- nuqs pra URL state
- React Hook Form + Zod pra forms

### typescript-advanced

**Foco**: TypeScript 5 strict

**Verifica**:
- Zero `any` (usar `unknown` com narrowing)
- Zero `@ts-ignore` (usar `@ts-expect-error` com justificativa)
- `as` type assertions com justificativa
- Return types explicitos em funcoes exportadas
- `type` sobre `interface`
- Tipos do SDK (`@soft-suite-platform/application`), nunca duplicar manualmente
- Generics corretos

### integration-review

**Foco**: Integracao com backend

**Verifica**:
- Server Actions retornando `ActionResult<T>`
- Validacao com Zod antes de chamar backend
- `queries.ts` com `'server-only'` como primeira linha
- `API_ROUTES` constant pra paths (nunca hardcoded)
- Barrel exports: tipos + actions em `_lib/index.ts`, NUNCA queries
- Paginacao: `PAGINATION_DEFAULTS`, `buildPaginationParams`

### ui-review

**Foco**: Design System e UI

**Verifica**:
- Zero cores hardcoded (no #hex, rgb(), bg-blue-500)
- CSS custom properties / design tokens
- Componentes de `@soft-suite-platform/ui`
- Icons: Lucide React apenas, nunca emojis no UI
- Zero `@apply` no Tailwind
- i18n: todas as strings user-facing com traducao
- `FeatureBadge` pra status de features

### a11y-audit

**Foco**: Acessibilidade WCAG 2.1 AA

**Verifica**:
- HTML semantico (`<nav>`, `<main>`, `<section>`, etc.)
- ARIA roles corretos
- Navegacao por teclado
- Labels em todos os inputs de formulario
- Mensagens de erro acessiveis
- Contraste de cores (via tokens)
- Focus management

### quality-review

**Foco**: Qualidade geral de codigo

**Verifica**:
- Zero `console.log` (usar structured logging)
- Zero imports/variaveis nao usados
- Performance: re-renders desnecessarios, waterfalls
- TODO/FIXME/HACK (debt tracking)
- Zustand stores sem selectors (causa re-render global)
- Dynamic imports pra componentes pesados
