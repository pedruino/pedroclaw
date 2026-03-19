"""Pluggable review engine — builtin (LiteLLM), CodeRabbit, or PR-Agent."""

import json
from abc import ABC, abstractmethod
from typing import Any

import structlog

from pedroclaw.config import settings

logger = structlog.get_logger()

# Rules extracted from Soft Suite frontend governance
# Source: .windsurf/rules/constitution.md, all.md, design-system.md, module-creation.md, biome.json
REVIEW_RULES = """
## Soft Suite Frontend Rules (enforce these strictly)

### TypeScript (from constitution.md + all.md)
- 100% TypeScript, zero JavaScript files
- NEVER use `any` — use `unknown` with type narrowing
- NEVER use `@ts-ignore` — use `@ts-expect-error` with justification if absolutely needed
- No `as` type assertions without justification
- Explicit return types on all exported functions
- Prefer `type` over `interface`
- All API types MUST come from SDK (`@soft-suite-platform/application`), never duplicate manually

### React / Next.js (from all.md + react-specialist)
- Server Components by default — only add `'use client'` when truly needed (hooks, browser APIs, event handlers)
- `page.tsx` MUST always be a Server Component
- Data fetching: use `serverFetch` (required data) or `serverFetchSafe` (optional data)
- Use `Promise.all()` for parallel fetches, never sequential waterfalls
- Zustand for global mutable state — NEVER use React Context with useState for mutable state
- nuqs for URL state
- React Hook Form + Zod for forms

### Design System (from design-system.md)
- NEVER hardcode colors (no #hex, no rgb(), no bg-blue-500 etc.)
- Always use CSS custom properties / design tokens
- Use components from `@soft-suite-platform/ui`
- Icons: Lucide React ONLY, never emojis in UI
- No `@apply` in Tailwind

### i18n (from constitution.md)
- ALL user-facing text must use translations — no hardcoded strings
- Exceptions: aria-label, test IDs, internal logs

### Security (from constitution.md + integration-review)
- Multi-tenant: use `cache: 'no-store'` or `tenantAwareCache` with tenantId
- Never `dangerouslySetInnerHTML` without sanitization
- Validate and sanitize all user input
- No SSRF: validate URLs before fetching

### Module Structure (from module-creation.md)
- kebab-case for directories, PascalCase for components, camelCase for utilities
- Barrel exports in `_lib/index.ts` (export types + actions, NOT queries)
- queries.ts must start with `'server-only'`
- Standard structure: page.tsx, layout.tsx, loading.tsx, error.tsx, _components/, _lib/

### Accessibility (from a11y-audit)
- WCAG 2.1 AA mandatory
- Semantic HTML, proper ARIA roles, keyboard navigation
- Forms with proper labels and error messages

### Code Quality (from quality-review + biome.json)
- No console.log (use structured logging)
- No unused imports/variables
- Biome formatting: 2-space indent, 120 char line width, single quotes, trailing commas

### Integration / Backend (from integration-review + sdk-types)
- Server Actions must return `ActionResult<T>` pattern
- Server Actions must validate input with Zod before calling backend
- queries.ts must import `'server-only'` as first line
- Use `API_ROUTES` constant for endpoint paths, never hardcode URLs
- Barrel exports in `_lib/index.ts`: export types + actions, NEVER export queries
- Pagination: use `PAGINATION_DEFAULTS` and `buildPaginationParams`

### Performance (from vercel-react-best-practices + quality-review)
- No waterfall fetches (sequential awaits that could be parallel)
- Avoid unnecessary re-renders: memoize callbacks/values in client components
- Use dynamic imports for heavy components not needed on first render
- No large objects in Zustand stores without selectors

### Plan-Driven Architecture (from constitution.md)
- Features must be controlled by tenant plan (basic/standard/enterprise), never hardcoded
- Use `FeatureBadge` component for feature status badges
- Multi-tenant: never leak data between tenants, always include tenantId in cache keys
"""


class InlineComment:
    """A review comment tied to a specific file and line."""

    def __init__(self, file_path: str, line: int, body: str, severity: str = "warning") -> None:
        self.file_path = file_path
        self.line = line
        self.body = body
        self.severity = severity

    def to_dict(self) -> dict[str, Any]:
        return {"file_path": self.file_path, "line": self.line, "body": self.body, "severity": self.severity}


class ReviewResult:
    """Standardized review output — inline comments, not a wall of text."""

    def __init__(
        self,
        inline_comments: list[InlineComment] | None = None,
        approved: bool = False,
        engine: str = "unknown",
    ) -> None:
        self.inline_comments = inline_comments or []
        self.approved = approved
        self.engine = engine


class ReviewEngine(ABC):
    """Abstract review engine interface."""

    @abstractmethod
    async def review(
        self, diff: str, mr_info: dict[str, Any], context: str = "", existing_comments: list[dict[str, Any]] | None = None
    ) -> ReviewResult:
        """Review a merge request diff and return inline comments."""


class BuiltinEngine(ReviewEngine):
    """Builtin review engine — usa o Squad XI (Aratu, Coral, Nautilo, Baiacu)."""

    async def review(
        self, diff: str, mr_info: dict[str, Any], context: str = "", existing_comments: list[dict[str, Any]] | None = None
    ) -> ReviewResult:
        from pedroclaw.squad.xi import squad_review
        return await squad_review(diff, mr_info, existing_comments)


class CodeRabbitEngine(ReviewEngine):
    """Delegates code review to CodeRabbit.

    Pedroclaw handles workflow/triage; CodeRabbit handles the actual review
    via its native GitLab integration.
    """

    async def review(
        self, diff: str, mr_info: dict[str, Any], context: str = "", existing_comments: list[dict[str, Any]] | None = None
    ) -> ReviewResult:
        logger.info("coderabbit_engine", mr_title=mr_info.get("title"))
        return ReviewResult(engine="coderabbit")


class PRAgentEngine(ReviewEngine):
    """Review engine using self-hosted PR-Agent."""

    def __init__(self) -> None:
        self._config = settings.review.get("pr_agent", {})
        self._model = self._config.get("model", settings.llm_review_model)

    async def review(
        self, diff: str, mr_info: dict[str, Any], context: str = "", existing_comments: list[dict[str, Any]] | None = None
    ) -> ReviewResult:
        logger.info("pr_agent_engine", mr_title=mr_info.get("title"))
        builtin = BuiltinEngine()
        return await builtin.review(diff, mr_info, context, existing_comments)


def get_review_engine() -> ReviewEngine:
    """Factory: returns the configured review engine."""
    engine_name = settings.review_engine

    engines: dict[str, type[ReviewEngine]] = {
        "builtin": BuiltinEngine,
        "coderabbit": CodeRabbitEngine,
        "pr_agent": PRAgentEngine,
    }

    engine_cls = engines.get(engine_name)
    if not engine_cls:
        raise ValueError(f"Unknown review engine: {engine_name}. Choose from: {list(engines.keys())}")

    logger.info("review_engine_loaded", engine=engine_name)
    return engine_cls()
