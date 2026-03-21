"""Squad XI — time de agentes para code review.

Aratu (Captain): orquestra, distribui, consolida
Coral (Researcher): pesquisa regras e contexto
Nautilo (Logician): valida logica e consistencia
Baiacu (Contrarian): desafia achados, busca pontos cegos

Each squad member is an agno.Agent with structured output (Pydantic models).
Orchestration remains as async Python for complex data-flow control;
AgnoInstrumentor traces each agent.arun() call automatically.
"""

import asyncio
import json
from typing import Any

import structlog
from agno.agent import Agent
from agno.workflow import Workflow
from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput

from pedroclaw.agents.engine import InlineComment, ReviewResult
from pedroclaw.agents.llm import get_model
from pedroclaw.agents.models import AratuAnalysis, Finding, FindingsList
from pedroclaw.knowledge.agno_kb import get_knowledge_base
from pedroclaw.squad.skills import format_skills_context, get_skills_for_files

logger = structlog.get_logger()


# ============================================================
# Helper
# ============================================================

def _extract_files_from_diff(diff: str) -> list[str]:
    """Extrai lista de arquivos do diff."""
    files = []
    for line in diff.split("\n"):
        if line.startswith("+++ b/"):
            files.append(line[6:])
    return files


def _findings_to_dicts(findings_list: FindingsList) -> list[dict[str, Any]]:
    """Convert structured FindingsList to list of dicts (backward compat)."""
    return [f.model_dump() for f in findings_list.findings]


# ============================================================
# ARATU — The Captain (Orchestrator)
# ============================================================

ARATU_SYSTEM = """Voce e Aratu 🦀, o capitao do Squad XI do Pedroclaw.
Seu papel e analisar o diff de um MR e identificar areas de risco.

Analise o diff e identifique:
1. Arquivos e linhas que merecem atencao
2. Se precisa chamar especialistas (react-specialist, typescript-advanced, integration-review, ui-review, a11y-audit, quality-review)
3. Nivel geral de risco do MR

Seja conservador: so marque "needs_specialist: true" se o codigo tiver complexidade que justifique.
MRs simples (rename, i18n, config) nao precisam de especialistas.
"""

_aratu_agent = Agent(
    name="Aratu",
    model=get_model(),
    instructions=[ARATU_SYSTEM],
    output_schema=AratuAnalysis,
    markdown=False,
)


async def aratu_analyze(diff: str, mr_info: dict[str, Any]) -> AratuAnalysis:
    """Aratu analisa o diff e identifica areas de risco."""
    title = mr_info.get("title", "")
    description = mr_info.get("description", "") or ""

    user_prompt = f"## MR: {title}\n{description[:300]}\n\n## Diff\n```diff\n{diff[:8000]}\n```"
    response = await _aratu_agent.arun(user_prompt)

    if isinstance(response.content, AratuAnalysis):
        return response.content

    logger.warning("aratu_structured_output_failed", content_type=type(response.content).__name__)
    return AratuAnalysis()


# ============================================================
# CORAL — The Researcher
# ============================================================

CORAL_SYSTEM = """Voce e Coral 🪸, a pesquisadora do Squad XI do Pedroclaw.
Seu papel e revisar o diff usando as regras do projeto.

Voce recebera as SKILLS (regras do projeto) relevantes para os arquivos no diff.
Analise o codigo e encontre violacoes dessas regras.

Regras para comentar:
- APENAS violacoes reais das skills/regras fornecidas
- 1-2 frases por comentario, sem enrolacao
- NAO comente formatacao (Biome cuida)
- NUNCA use travessao (caractere —)
- Se nao encontrar violacoes, retorne lista vazia
"""

_coral_agent = Agent(
    name="Coral",
    model=get_model(),
    instructions=[CORAL_SYSTEM],
    output_schema=FindingsList,
    markdown=False,
)


async def coral_research(diff: str, skills_context: str) -> list[dict[str, Any]]:
    """Coral pesquisa violacoes usando as regras do projeto."""
    user_prompt = f"## Regras do Projeto\n{skills_context}\n\n## Diff\n```diff\n{diff}\n```"
    response = await _coral_agent.arun(user_prompt)

    if isinstance(response.content, FindingsList):
        return _findings_to_dicts(response.content)

    logger.warning("coral_structured_output_failed", content_type=type(response.content).__name__)
    return []


# ============================================================
# NAUTILO — The Logician
# ============================================================

NAUTILO_SYSTEM = """Voce e Nautilo 🐚, o logico do Squad XI do Pedroclaw.
Seu papel e validar os achados da pesquisadora (Coral).

Voce recebera:
1. O diff do MR
2. Os achados da Coral (lista de violacoes)

Para cada achado, valide:
- O achado e realmente uma violacao? Ou e um falso positivo?
- A linha e o arquivo estao corretos?
- A sugestao de correcao faz sentido?

Mantenha apenas achados validos.
Se um achado for falso positivo, remova-o.
Se a descricao puder ser melhorada, melhore-a.
NUNCA use travessao (caractere —).
Se todos forem falsos positivos, retorne lista vazia.
"""

_nautilo_agent = Agent(
    name="Nautilo",
    model=get_model(),
    instructions=[NAUTILO_SYSTEM],
    output_schema=FindingsList,
    markdown=False,
)


async def nautilo_validate(diff: str, coral_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nautilo valida os achados da Coral, removendo falsos positivos."""
    user_prompt = (
        f"## Achados da Coral\n```json\n{json.dumps(coral_findings, ensure_ascii=False, indent=2)}\n```\n\n"
        f"## Diff\n```diff\n{diff}\n```"
    )
    response = await _nautilo_agent.arun(user_prompt)

    if isinstance(response.content, FindingsList):
        return _findings_to_dicts(response.content)

    logger.warning("nautilo_structured_output_failed", content_type=type(response.content).__name__)
    return []


# ============================================================
# BAIACU — The Contrarian
# ============================================================

BAIACU_SYSTEM = """Voce e Baiacu 🐡, o contrarian do Squad XI do Pedroclaw.
Seu papel e encontrar o que os outros perderam.

Voce recebera:
1. O diff do MR
2. Os achados ja validados pelo time

Seu trabalho:
- Encontrar problemas que os outros NAO viram
- Focar em: seguranca, edge cases, race conditions, vazamento de dados entre tenants
- Questionar: "e se esse input for null?", "e se dois requests chegarem ao mesmo tempo?"
- NAO repita achados que ja estao na lista

Responda com achados NOVOS (que nao estao na lista de validados). Formato de saida (lista em `findings`):
```json
{
  "findings": [
    {"file": "path/file.tsx", "line": 15, "severity": "critical", "body": "Problema nao visto pelos outros."}
  ]
}
```

NUNCA use travessao (caractere —).
Se nao encontrar nada novo, retorne `"findings": []`.
Seja criterioso: so adicione se for realmente relevante.
"""

_baiacu_agent = Agent(
    name="Baiacu",
    model=get_model(),
    instructions=[BAIACU_SYSTEM],
    output_schema=FindingsList,
    markdown=False,
)


async def baiacu_challenge(diff: str, validated_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Baiacu desafia achados e busca pontos cegos."""
    user_prompt = (
        f"## Achados ja validados\n```json\n{json.dumps(validated_findings, ensure_ascii=False, indent=2)}\n```\n\n"
        f"## Diff\n```diff\n{diff}\n```"
    )
    response = await _baiacu_agent.arun(user_prompt)

    if isinstance(response.content, FindingsList):
        return _findings_to_dicts(response.content)

    logger.warning("baiacu_structured_output_failed", content_type=type(response.content).__name__)
    return []


# ============================================================
# SPECIALIST AGENTS (chamados sob demanda pelo Aratu)
# ============================================================

SPECIALIST_NAMES = {
    "react-specialist": "React 19 e Next.js 16 (Server/Client Components, hooks, data fetching, re-renders)",
    "typescript-advanced": "TypeScript strict (tipos, generics, narrowing, SDK types)",
    "integration-review": "integracao backend (ActionResult, server-only, API_ROUTES, Zod validation)",
    "ui-review": "Design System (tokens, cores, componentes UI, i18n, Lucide icons)",
    "a11y-audit": "acessibilidade (WCAG 2.1 AA, ARIA, semantica, keyboard navigation)",
    "quality-review": "qualidade de codigo (console.log, unused code, performance, re-renders)",
}


def _create_specialist_agent(specialty: str, skill_content: str) -> Agent:
    """Factory: cria um agente especialista dinamicamente."""
    system = (
        f"Voce e um especialista em {SPECIALIST_NAMES.get(specialty, specialty)} do Squad XI do Pedroclaw.\n"
        "Analise o diff focando APENAS na sua area de especialidade.\n"
        "NUNCA use travessao (caractere —).\n"
        "1-2 frases por comentario. Se nao encontrar problemas na sua area, retorne lista vazia."
    )
    if skill_content:
        system += f"\n\nRegras da sua especialidade:\n{skill_content}"

    return Agent(
        name=f"Specialist-{specialty}",
        model=get_model(),
        instructions=[system],
        output_schema=FindingsList,
        markdown=False,
    )


async def call_specialist(specialty: str, diff: str, skill_content: str) -> list[dict[str, Any]]:
    """Chama um agente especialista."""
    agent = _create_specialist_agent(specialty, skill_content)
    user_prompt = f"## Diff\n```diff\n{diff}\n```"
    response = await agent.arun(user_prompt)

    if isinstance(response.content, FindingsList):
        return _findings_to_dicts(response.content)

    logger.warning("specialist_structured_output_failed", specialty=specialty)
    return []


# ============================================================
# SQUAD XI — Orquestracao completa
# ============================================================

async def squad_review(diff: str, mr_info: dict[str, Any], existing_comments: list[dict[str, Any]] | None = None) -> ReviewResult:
    """Executa o review completo do Squad XI."""
    mr_title = mr_info.get("title", "")
    logger.info("squad_xi_start", mr_title=mr_title)

    # 0. Montar contexto de comentarios existentes pra evitar duplicatas
    existing_context = ""
    if existing_comments:
        existing_context = (
            "\n\n## Comentarios ja postados pelo Pedroclaw (NAO repita esses):\n"
            + "\n".join(f"- {c['file']}:{c['line']} {c['body']}" for c in existing_comments if c.get("file"))
        )

    # 1. Aratu analisa e identifica riscos
    analysis = await aratu_analyze(diff, mr_info)
    overall_risk = analysis.overall_risk
    specialists_needed = analysis.specialists_needed

    logger.info("aratu_analysis", risk=overall_risk, specialists=specialists_needed)

    # 2. Descobrir regras do projeto e carregar skills relevantes
    from pedroclaw.squad.skills import discover_project_rules

    diff_files = _extract_files_from_diff(diff)
    project_id = mr_info.get("project_id") or mr_info.get("target_project_id")
    all_rules = discover_project_rules(project_id=project_id)
    skills = get_skills_for_files(diff_files, all_rules)
    skills_context = format_skills_context(skills)

    # 3. Coral pesquisa violacoes (com skills + comentarios existentes como contexto)
    coral_findings = await coral_research(diff, skills_context + existing_context)
    logger.info("coral_findings", count=len(coral_findings))

    # 4. Nautilo valida (remove falsos positivos)
    validated = await nautilo_validate(diff, coral_findings)
    logger.info("nautilo_validated", original=len(coral_findings), validated=len(validated))

    # 5. Baiacu desafia (busca pontos cegos)
    baiacu_findings = await baiacu_challenge(diff, validated)
    logger.info("baiacu_findings", count=len(baiacu_findings))

    # 6. Se Aratu pediu especialistas, chama em paralelo
    specialist_findings: list[dict[str, Any]] = []
    if specialists_needed and overall_risk in ("medium", "high"):
        specialist_tasks = []
        for spec in specialists_needed:
            if spec in SPECIALIST_NAMES:
                skill_content = skills.get(spec, "")
                specialist_tasks.append(call_specialist(spec, diff, skill_content))

        if specialist_tasks:
            results = await asyncio.gather(*specialist_tasks)
            for result in results:
                specialist_findings.extend(result)
            logger.info("specialists_called", count=len(specialists_needed), findings=len(specialist_findings))

    # 7. Aratu consolida todos os achados (deduplica)
    all_findings = validated + baiacu_findings + specialist_findings
    deduplicated = _deduplicate_findings(all_findings)

    logger.info(
        "squad_xi_done",
        total_findings=len(deduplicated),
        coral=len(coral_findings),
        validated=len(validated),
        baiacu=len(baiacu_findings),
        specialists=len(specialist_findings),
    )

    # 8. Converter pra InlineComments
    comments = []
    for item in deduplicated:
        if isinstance(item, dict) and "file" in item and "line" in item and "body" in item:
            comments.append(
                InlineComment(
                    file_path=item["file"],
                    line=int(item["line"]),
                    body=item["body"],
                    severity=item.get("severity", "warning"),
                )
            )

    approved = len(comments) == 0

    return ReviewResult(inline_comments=comments, approved=approved, engine="squad-xi")


def _deduplicate_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove achados duplicados (mesmo arquivo + linha proxima + conteudo similar)."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []

    for f in findings:
        key = f"{f.get('file', '')}:{f.get('line', 0)}"
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


def _workflow_input_as_text(step_input: StepInput) -> str:
    s = step_input.get_input_as_string()
    return s if s is not None else ""


def _parse_workflow_mr_input(text: str) -> tuple[str, dict[str, Any]]:
    """Extract diff and ``mr_info`` from a Studio message (same idea as worker prompts)."""
    title = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("## mr"):
            if ":" in stripped:
                title = stripped.split(":", 1)[1].strip()
            else:
                title = stripped[2:].replace("MR", "", 1).strip()
            break

    diff = ""
    if "```diff" in text:
        try:
            diff = text.split("```diff", 1)[1].split("```", 1)[0].strip()
        except IndexError:
            diff = ""
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            candidate = parts[1].strip()
            if candidate.startswith("diff ") or candidate.startswith("diff\n"):
                diff = candidate

    return diff, {"title": title or "Untitled MR", "description": ""}


async def pedroclaw_full_review_executor(step_input: StepInput) -> StepOutput:
    """Runs :func:`squad_review` — output matches :class:`pedroclaw.agents.engine.ReviewResult` (dict form)."""
    try:
        text = _workflow_input_as_text(step_input)
        diff, mr_info = _parse_workflow_mr_input(text)
        if not diff.strip():
            return StepOutput(
                success=False,
                content={
                    "error": "missing_diff",
                    "message": "Inclua o patch num bloco ```diff ... ``` (igual ao worker/GitLab).",
                },
            )
        result = await squad_review(diff, mr_info, None)
        return StepOutput(
            content={
                "inline_comments": [c.to_dict() for c in result.inline_comments],
                "approved": result.approved,
                "engine": result.engine,
            },
        )
    except Exception as exc:
        logger.exception("pedroclaw_full_review_executor_failed")
        return StepOutput(success=False, content={"error": "executor_failed", "message": str(exc)})


def _agentos_postgres_db(workflow_db_id: str) -> Any:
    from agno.db.postgres import PostgresDb

    from pedroclaw.config import agentos_database_url

    return PostgresDb(id=workflow_db_id, db_url=agentos_database_url())


def create_squad_xi_workflow() -> Workflow:
    """Multi-step Squad XI pipeline for AgentOS / Agno Studio (workflow registry).

    GitLab review jobs still use :func:`squad_review` for full orchestration (skills,
    specialists, dedup). This workflow exposes the same agent stages for Studio and
    ``os.agno.com`` when connected to this AgentOS instance.

    **Per-step output** is each agent's schema (e.g. ``FindingsList``), *not* :class:`~pedroclaw.agents.engine.ReviewResult`.
    For the same JSON shape as production, use :func:`create_pedroclaw_full_review_workflow`.
    """
    db = _agentos_postgres_db("pedroclaw-agentos")
    return Workflow(
        id="squad-xi-review",
        name="Squad XI Review",
        description="MR code review: Aratu (risk) → Coral (rules) → Nautilo (validate) → Baiacu (contrarian)",
        db=db,
        steps=[
            Step(
                name="aratu",
                description="Analyze diff for risk areas and specialist needs",
                agent=_aratu_agent,
            ),
            Step(
                name="coral",
                description="Find rule violations using project skills context",
                agent=_coral_agent,
            ),
            Step(
                name="nautilo",
                description="Validate findings and drop false positives",
                agent=_nautilo_agent,
            ),
            Step(
                name="baiacu",
                description="Challenge findings and surface blind spots",
                agent=_baiacu_agent,
            ),
        ],
        add_workflow_history_to_steps=True,
    )


def create_pedroclaw_full_review_workflow() -> Workflow:
    """Single-step workflow: runs :func:`squad_review` and returns ``ReviewResult`` as a dict.

    Use this on ``os.agno.com`` when you want **inline_comments / approved / engine** — the same
    contract as GitLab and :class:`pedroclaw.agents.engine.ReviewResult`.
    """
    db = _agentos_postgres_db("pedroclaw-full-review")
    return Workflow(
        id="pedroclaw-full-mr-review",
        name="Pedroclaw Full MR Review",
        description="Review completo (skills, especialistas, dedup) — saida = ReviewResult (inline_comments, approved, engine)",
        db=db,
        steps=[
            Step(
                name="squad_review",
                description="Executa squad_review() — mesmo resultado que o worker",
                executor=pedroclaw_full_review_executor,
            ),
        ],
        add_workflow_history_to_steps=False,
    )


class SquadXI:
    """Squad XI workflow agent for AgentOS integration."""
    
    @staticmethod
    def create_agent() -> Agent:
        """Create an Agno Agent that represents the Squad XI workflow."""
        
        return Agent(
            name="Squad XI Review",
            model=get_model(),
            instructions=[f"""
            You are the Squad XI review workflow coordinator.
            
            When given a code review request, execute the full Squad XI review process:
            
            1. **Aratu (Captain)**: Analyze risk level and determine if specialists are needed
            2. **Coral (Researcher)**: Research violations using project skills and context
            3. **Nautilo (Logician)**: Validate findings and remove false positives
            4. **Baiacu (Contrarian)**: Challenge findings and look for blind spots
            5. **Specialists**: If needed, call domain specialists in parallel
            6. **Consolidation**: Deduplicate and organize all findings
            
            Input format should include:
            - diff: The code diff to review
            - mr_title: Title of the merge request (optional)
            - skills: Project-specific skills and rules (optional)
            
            Return a structured result with:
            - status: "completed" or "failed"
            - inline_comments: List of comment objects with file_path, line, body, severity
            - approved: boolean indicating if MR should be approved
            - engine: "squad-xi"
            - total_findings: integer count of findings
            - error: string if failed
            
            Be thorough but practical. Focus on real issues that affect code quality, security, and maintainability.
            """],
            knowledge=get_knowledge_base(),
            tools=[],
            add_history_to_context=True,
            num_history_runs=3,
            add_datetime_to_context=True,
            markdown=True,
        )
