"""Skills loader: descobre regras do projeto sendo revisado em runtime.

Estrategia de busca:
1. Volume montado (FRONTEND_PATH) - le direto do filesystem
2. GitLab API - busca arquivos do repositorio via API
3. Fallback - regras genericas de boas praticas
"""

from pathlib import Path

import structlog

from pedroclaw.config import settings

logger = structlog.get_logger()

# Paths onde buscar regras (ordem de prioridade)
RULE_PATHS = [
    ".windsurf/rules",
    ".cursor/rules",
    ".claude/rules",
]

SKILL_PATHS = [
    ".windsurf/skills",
    ".claude/agents",
]

ROOT_FILES = [
    "CLAUDE.md",
    "biome.json",
]

# Skills por tipo de arquivo
FILE_SKILLS_MAP: dict[str, list[str]] = {
    ".tsx": ["react-specialist", "typescript-advanced", "ui-review", "a11y-audit", "design-system"],
    ".ts": ["typescript-advanced", "sdk-types", "integration-review"],
    ".css": ["design-system", "ui-review"],
    ".module.styl": ["design-system", "ui-review"],
}

ALWAYS_LOAD_RULES = ["constitution", "all"]
ALWAYS_LOAD_SKILLS = ["quality-review"]

# Fallback: regras genericas quando o projeto nao tem regras proprias
FALLBACK_RULES = """
## Regras genericas de boas praticas

### TypeScript
- Zero `any` (usar `unknown` com narrowing)
- Zero `@ts-ignore` (usar `@ts-expect-error` com justificativa)
- Return types explicitos em funcoes exportadas
- Prefer `type` over `interface`

### React / Next.js
- Server Components por padrao
- `'use client'` so quando necessario (hooks, browser APIs, event handlers)
- `Promise.all()` pra fetches paralelos
- Zustand pra estado global mutavel

### Seguranca
- Validar e sanitizar input do usuario
- Nunca `dangerouslySetInnerHTML` sem sanitizacao
- Cache: `no-store` pra dados sensiveis

### Acessibilidade
- WCAG 2.1 AA
- HTML semantico, ARIA roles, navegacao por teclado

### Qualidade
- Zero `console.log` (usar structured logging)
- Zero imports nao usados
- Sem waterfall fetches
"""


def _discover_from_filesystem(base_path: str) -> dict[str, str]:
    """Descobre regras de um projeto no filesystem local."""
    base = Path(base_path)
    if not base.exists():
        logger.debug("filesystem_path_not_found", path=base_path)
        return {}

    discovered: dict[str, str] = {}

    # Busca regras mandatorias
    for rule_dir in RULE_PATHS:
        rule_path = base / rule_dir
        if rule_path.exists():
            for md_file in sorted(rule_path.glob("*.md")):
                name = md_file.stem
                try:
                    discovered[name] = md_file.read_text(encoding="utf-8")
                    logger.debug("rule_discovered", name=name, source="filesystem", chars=len(discovered[name]))
                except Exception as e:
                    logger.warning("rule_read_failed", name=name, error=str(e))

    # Busca skills (SKILL.md e AGENTS.md)
    for skill_dir in SKILL_PATHS:
        skill_path = base / skill_dir
        if skill_path.exists():
            for skill_folder in sorted(skill_path.iterdir()):
                if not skill_folder.is_dir():
                    continue
                name = skill_folder.name
                # Prefere AGENTS.md (mais completo), fallback pra SKILL.md
                agents_file = skill_folder / "AGENTS.md"
                skill_file = skill_folder / "SKILL.md"
                target = agents_file if agents_file.exists() else skill_file if skill_file.exists() else None
                if target:
                    try:
                        discovered[name] = target.read_text(encoding="utf-8")
                        logger.debug("skill_discovered", name=name, source="filesystem", file=target.name)
                    except Exception as e:
                        logger.warning("skill_read_failed", name=name, error=str(e))

    # Busca arquivos na raiz
    for root_file in ROOT_FILES:
        root_path = base / root_file
        if root_path.exists():
            try:
                name = root_path.stem.lower()
                discovered[name] = root_path.read_text(encoding="utf-8")
                logger.debug("root_file_discovered", name=name, source="filesystem")
            except Exception as e:
                logger.warning("root_file_read_failed", name=root_file, error=str(e))

    return discovered


def _discover_from_gitlab(project_id: int) -> dict[str, str]:
    """Descobre regras de um projeto via GitLab API."""
    try:
        from pedroclaw.gitlab.client import gitlab_client
        project = gitlab_client._project(project_id)
    except Exception as e:
        logger.warning("gitlab_discovery_failed", error=str(e))
        return {}

    discovered: dict[str, str] = {}

    # Busca regras nos paths conhecidos
    all_paths = RULE_PATHS + SKILL_PATHS
    for search_path in all_paths:
        try:
            tree = project.repository_tree(path=search_path, ref="main", per_page=50)
            for item in tree:
                if item["type"] == "blob" and item["name"].endswith(".md"):
                    try:
                        file_content = project.files.get(item["path"], ref="main")
                        content = file_content.decode().decode("utf-8")
                        name = Path(item["name"]).stem
                        discovered[name] = content
                        logger.debug("rule_discovered", name=name, source="gitlab_api")
                    except Exception:
                        pass
                elif item["type"] == "tree":
                    # Subdiretorio de skill: busca AGENTS.md ou SKILL.md
                    for target_file in ["AGENTS.md", "SKILL.md"]:
                        try:
                            file_path = f"{item['path']}/{target_file}"
                            file_content = project.files.get(file_path, ref="main")
                            content = file_content.decode().decode("utf-8")
                            discovered[item["name"]] = content
                            logger.debug("skill_discovered", name=item["name"], source="gitlab_api")
                            break
                        except Exception:
                            pass
        except Exception:
            pass

    # Busca arquivos na raiz
    for root_file in ROOT_FILES:
        try:
            file_content = project.files.get(root_file, ref="main")
            content = file_content.decode().decode("utf-8")
            discovered[Path(root_file).stem.lower()] = content
        except Exception:
            pass

    return discovered


def discover_project_rules(project_id: int | None = None) -> dict[str, str]:
    """Descobre regras do projeto, tentando filesystem primeiro, depois GitLab API, depois fallback."""
    # 1. Tenta filesystem (volume montado)
    frontend_path = settings.frontend_path
    discovered = _discover_from_filesystem(frontend_path)

    if discovered:
        logger.info("rules_discovered", source="filesystem", count=len(discovered))
        return discovered

    # 2. Tenta GitLab API
    if project_id:
        discovered = _discover_from_gitlab(project_id)
        if discovered:
            logger.info("rules_discovered", source="gitlab_api", count=len(discovered))
            return discovered

    # 3. Fallback
    logger.info("rules_discovered", source="fallback", count=1)
    return {"fallback": FALLBACK_RULES}


def get_skills_for_files(file_paths: list[str], all_rules: dict[str, str] | None = None) -> dict[str, str]:
    """Seleciona skills relevantes baseado nos arquivos no diff."""
    if all_rules is None:
        all_rules = discover_project_rules()

    needed_skills: set[str] = set()

    # Always load
    for rule_name in ALWAYS_LOAD_RULES + ALWAYS_LOAD_SKILLS:
        if rule_name in all_rules:
            needed_skills.add(rule_name)

    # Por tipo de arquivo
    for fp in file_paths:
        for ext, skills in FILE_SKILLS_MAP.items():
            if fp.endswith(ext):
                for skill in skills:
                    if skill in all_rules:
                        needed_skills.add(skill)
                break

        if fp.endswith("queries.ts") or fp.endswith("actions.ts"):
            for s in ["integration-review", "sdk-types"]:
                if s in all_rules:
                    needed_skills.add(s)

        if fp.endswith("page.tsx"):
            if "module-architecture" in all_rules or "module-creation" in all_rules:
                needed_skills.add("module-architecture" if "module-architecture" in all_rules else "module-creation")

    # Se nao encontrou nenhuma skill especifica, carrega tudo disponivel
    if not needed_skills and all_rules:
        needed_skills = set(all_rules.keys())

    return {name: all_rules[name] for name in needed_skills if name in all_rules}


def format_skills_context(skills: dict[str, str], max_chars: int = 30000) -> str:
    """Formata skills como contexto pro LLM, respeitando limite de tokens."""
    parts = []
    total = 0

    # Prioridade: constitution e all primeiro
    priority = ["constitution", "all", "fallback"]
    ordered = priority + [s for s in skills if s not in priority]

    for name in ordered:
        if name not in skills:
            continue
        content = skills[name]
        if total + len(content) > max_chars:
            remaining = max_chars - total
            if remaining > 500:
                content = content[:remaining] + "\n... (truncado)"
            else:
                break
        parts.append(f"### REGRA: {name}\n{content}")
        total += len(content)

    logger.info("skills_formatted", count=len(parts), total_chars=total)
    return "\n\n---\n\n".join(parts)
