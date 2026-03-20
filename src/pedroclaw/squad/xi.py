"""Squad XI — time de agentes para code review.

Aratu (Captain): orquestra, distribui, consolida
Coral (Researcher): pesquisa regras e contexto
Nautilo (Logician): valida logica e consistencia
Baiacu (Contrarian): desafia achados, busca pontos cegos
"""

import json
from typing import Any

import structlog

from pedroclaw.agents.engine import InlineComment, ReviewResult
from pedroclaw.config import settings
from pedroclaw.observability import create_trace, litellm_metadata
from pedroclaw.squad.skills import format_skills_context, get_skills_for_files

logger = structlog.get_logger()


async def _call_llm(
    system: str,
    user: str,
    model: str | None = None,
    max_retries: int = 3,
    trace_id: str | None = None,
    parent_observation_id: str | None = None,
    generation_name: str = "llm_call",
) -> str:
    """Chamada LLM via LiteLLM com retry pra rate limit."""
    import asyncio

    import litellm

    for attempt in range(max_retries):
        try:
            response = await litellm.acompletion(
                model=model or settings.llm_review_model,
                api_key=settings.llm_review_api_key,
                api_base=settings.llm_review_api_base,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                metadata=litellm_metadata(trace_id, parent_observation_id, generation_name),
            )
            logger.info(
                "llm_call",
                model=model or settings.llm_review_model,
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
            )
            return response.choices[0].message.content or ""
        except litellm.RateLimitError:
            wait = 30 * (attempt + 1)
            logger.warning("rate_limit_hit", attempt=attempt + 1, wait_seconds=wait)
            await asyncio.sleep(wait)

    raise Exception("Rate limit exceeded after max retries")


def _extract_files_from_diff(diff: str) -> list[str]:
    """Extrai lista de arquivos do diff."""
    files = []
    for line in diff.split("\n"):
        if line.startswith("+++ b/"):
            files.append(line[6:])
    return files


def _parse_comments_json(content: str) -> list[dict[str, Any]]:
    """Extrai array JSON de uma resposta LLM."""
    json_str = content
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        json_str = content.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        logger.warning("json_parse_failed", content=content[:200])
    return []


# ============================================================
# ARATU — The Captain (Orchestrator)
# ============================================================

ARATU_SYSTEM = """Voce e Aratu 🦀, o capitao do Squad XI do Pedroclaw.
Seu papel e analisar o diff de um MR e identificar areas de risco.

Responda em JSON com esta estrutura:
```json
{
  "risk_areas": [
    {
      "file": "path/to/file.tsx",
      "lines": [10, 20, 30],
      "concerns": ["tipo de preocupacao"],
      "needs_specialist": false
    }
  ],
  "specialists_needed": ["react-specialist", "a11y-audit"],
  "overall_risk": "low" | "medium" | "high"
}
```

Analise o diff e identifique:
1. Arquivos e linhas que merecem atencao
2. Se precisa chamar especialistas (react-specialist, typescript-advanced, integration-review, ui-review, a11y-audit, quality-review)
3. Nivel geral de risco do MR

Seja conservador: so marque "needs_specialist: true" se o codigo tiver complexidade que justifique.
MRs simples (rename, i18n, config) nao precisam de especialistas.
"""


async def aratu_analyze(diff: str, mr_info: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
    """Aratu analisa o diff e identifica areas de risco."""
    title = mr_info.get("title", "")
    description = mr_info.get("description", "") or ""

    user_prompt = f"## MR: {title}\n{description[:300]}\n\n## Diff\n```diff\n{diff[:8000]}\n```"
    response = await _call_llm(
        ARATU_SYSTEM, user_prompt,
        trace_id=trace_id, generation_name="aratu",
    )

    json_str = response
    if "```json" in response:
        json_str = response.split("```json")[1].split("```")[0].strip()

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("aratu_parse_failed")
        result = {"risk_areas": [], "specialists_needed": [], "overall_risk": "medium"}

    return result


# ============================================================
# CORAL — The Researcher
# ============================================================

CORAL_SYSTEM = """Voce e Coral 🪸, a pesquisadora do Squad XI do Pedroclaw.
Seu papel e revisar o diff usando as regras do projeto.

Voce recebera as SKILLS (regras do projeto) relevantes para os arquivos no diff.
Analise o codigo e encontre violacoes dessas regras.

Responda APENAS com um JSON array de achados:
```json
[
  {"file": "path/file.tsx", "line": 15, "severity": "warning", "body": "Descricao concisa do problema."}
]
```

Regras para comentar:
- APENAS violacoes reais das skills/regras fornecidas
- 1-2 frases por comentario, sem enrolacao
- NAO comente formatacao (Biome cuida)
- NUNCA use travessao (caractere —)
- Se nao encontrar violacoes, retorne array vazio: []
"""


async def coral_research(diff: str, skills_context: str, trace_id: str | None = None) -> list[dict[str, Any]]:
    """Coral pesquisa violacoes usando as regras do projeto."""
    user_prompt = f"## Regras do Projeto\n{skills_context}\n\n## Diff\n```diff\n{diff}\n```"
    response = await _call_llm(
        CORAL_SYSTEM, user_prompt,
        trace_id=trace_id, generation_name="coral",
    )
    findings = _parse_comments_json(response)
    return findings


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

Responda com o array FILTRADO, mantendo apenas achados validos.
Se um achado for falso positivo, remova-o.
Se a descricao puder ser melhorada, melhore-a.

Formato: mesmo JSON array da entrada, so com os achados validados.
```json
[
  {"file": "path/file.tsx", "line": 15, "severity": "warning", "body": "Descricao validada e concisa."}
]
```

NUNCA use travessao (caractere —).
Se todos forem falsos positivos, retorne array vazio: []
"""


async def nautilo_validate(
    diff: str, coral_findings: list[dict[str, Any]], trace_id: str | None = None
) -> list[dict[str, Any]]:
    """Nautilo valida os achados da Coral, removendo falsos positivos."""
    user_prompt = (
        f"## Achados da Coral\n```json\n{json.dumps(coral_findings, ensure_ascii=False, indent=2)}\n```\n\n"
        f"## Diff\n```diff\n{diff}\n```"
    )
    response = await _call_llm(
        NAUTILO_SYSTEM, user_prompt,
        trace_id=trace_id, generation_name="nautilo",
    )
    validated = _parse_comments_json(response)
    return validated


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

Responda com um JSON array de achados NOVOS (que nao estao na lista):
```json
[
  {"file": "path/file.tsx", "line": 15, "severity": "critical", "body": "Problema nao visto pelos outros."}
]
```

NUNCA use travessao (caractere —).
Se nao encontrar nada novo, retorne array vazio: []
Seja criterioso: so adicione se for realmente relevante.
"""


async def baiacu_challenge(
    diff: str, validated_findings: list[dict[str, Any]], trace_id: str | None = None
) -> list[dict[str, Any]]:
    """Baiacu desafia achados e busca pontos cegos."""
    user_prompt = (
        f"## Achados ja validados\n```json\n{json.dumps(validated_findings, ensure_ascii=False, indent=2)}\n```\n\n"
        f"## Diff\n```diff\n{diff}\n```"
    )
    response = await _call_llm(
        BAIACU_SYSTEM, user_prompt,
        trace_id=trace_id, generation_name="baiacu",
    )
    findings = _parse_comments_json(response)
    return findings


# ============================================================
# SPECIALIST AGENTS (chamados sob demanda pelo Aratu)
# ============================================================

SPECIALIST_SYSTEM = """Voce e um especialista em {specialty} do Squad XI do Pedroclaw.
Analise o diff focando APENAS na sua area de especialidade.

Responda com um JSON array de achados:
```json
[
  {{"file": "path/file.tsx", "line": 15, "severity": "warning", "body": "Descricao concisa."}}
]
```

NUNCA use travessao (caractere —).
1-2 frases por comentario. Se nao encontrar problemas na sua area, retorne: []
"""

SPECIALIST_NAMES = {
    "react-specialist": "React 19 e Next.js 16 (Server/Client Components, hooks, data fetching, re-renders)",
    "typescript-advanced": "TypeScript strict (tipos, generics, narrowing, SDK types)",
    "integration-review": "integracao backend (ActionResult, server-only, API_ROUTES, Zod validation)",
    "ui-review": "Design System (tokens, cores, componentes UI, i18n, Lucide icons)",
    "a11y-audit": "acessibilidade (WCAG 2.1 AA, ARIA, semantica, keyboard navigation)",
    "quality-review": "qualidade de codigo (console.log, unused code, performance, re-renders)",
}


async def call_specialist(
    specialty: str, diff: str, skill_content: str, trace_id: str | None = None
) -> list[dict[str, Any]]:
    """Chama um agente especialista."""
    system = SPECIALIST_SYSTEM.format(specialty=SPECIALIST_NAMES.get(specialty, specialty))
    if skill_content:
        system += f"\n\nRegras da sua especialidade:\n{skill_content}"

    user_prompt = f"## Diff\n```diff\n{diff}\n```"
    response = await _call_llm(
        system, user_prompt,
        trace_id=trace_id, generation_name=f"specialist_{specialty}",
    )
    findings = _parse_comments_json(response)
    return findings


# ============================================================
# SQUAD XI — Orquestracao completa
# ============================================================

async def squad_review(diff: str, mr_info: dict[str, Any], existing_comments: list[dict[str, Any]] | None = None) -> ReviewResult:
    """Executa o review completo do Squad XI."""
    import asyncio

    mr_title = mr_info.get("title", "")
    mr_id = mr_info.get("iid") or mr_info.get("id")
    logger.info("squad_xi_start", mr_title=mr_title)

    trace_id = create_trace("squad-review")

    # 0. Montar contexto de comentarios existentes pra evitar duplicatas
    existing_context = ""
    if existing_comments:
        existing_context = (
            "\n\n## Comentarios ja postados pelo Pedroclaw (NAO repita esses):\n"
            + "\n".join(f"- {c['file']}:{c['line']} {c['body']}" for c in existing_comments if c.get("file"))
        )

    # 1. Aratu analisa e identifica riscos
    analysis = await aratu_analyze(diff, mr_info, trace_id=trace_id)
    overall_risk = analysis.get("overall_risk", "medium")
    specialists_needed = analysis.get("specialists_needed", [])

    logger.info("aratu_analysis", risk=overall_risk, specialists=specialists_needed)

    # 2. Descobrir regras do projeto e carregar skills relevantes
    from pedroclaw.squad.skills import discover_project_rules

    diff_files = _extract_files_from_diff(diff)
    project_id = mr_info.get("project_id") or mr_info.get("target_project_id")
    all_rules = discover_project_rules(project_id=project_id)
    skills = get_skills_for_files(diff_files, all_rules)
    skills_context = format_skills_context(skills)

    # 3. Coral pesquisa violacoes (com skills + comentarios existentes como contexto)
    coral_findings = await coral_research(diff, skills_context + existing_context, trace_id=trace_id)
    logger.info("coral_findings", count=len(coral_findings))

    # 4. Nautilo valida (remove falsos positivos)
    validated = await nautilo_validate(diff, coral_findings, trace_id=trace_id)
    logger.info("nautilo_validated", original=len(coral_findings), validated=len(validated))

    # 5. Baiacu desafia (busca pontos cegos)
    baiacu_findings = await baiacu_challenge(diff, validated, trace_id=trace_id)
    logger.info("baiacu_findings", count=len(baiacu_findings))

    # 6. Se Aratu pediu especialistas, chama em paralelo
    specialist_findings: list[dict[str, Any]] = []
    if specialists_needed and overall_risk in ("medium", "high"):
        specialist_tasks = []
        for spec in specialists_needed:
            if spec in SPECIALIST_NAMES:
                skill_content = skills.get(spec, "")
                specialist_tasks.append(call_specialist(spec, diff, skill_content, trace_id=trace_id))

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
