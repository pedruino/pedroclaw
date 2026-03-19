"""Sincroniza labels workflow:: no grupo do GitLab com as definicoes do Pedroclaw."""

import os
import gitlab

GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GROUP_ID = os.getenv("GITLAB_GROUP_ID")  # ID do grupo soft-suite

# Labels de workflow com cores e descricoes padronizadas
WORKFLOW_LABELS = {
    "workflow::triagem": {
        "color": "#6699cc",
        "description": "Agente de triagem analisando issue de cliente.",
    },
    "workflow::conceito": {
        "color": "#d1bcf9",
        "description": "Ideia registrada, ainda nao priorizada.",
    },
    "workflow::especificacao": {
        "color": "#c39bd3",
        "description": "PM escrevendo user stories e requisitos.",
    },
    "workflow::revisao-spec": {
        "color": "#f0ad4e",
        "description": "Arquiteto + PM revisando spec. Arquiteto escreve SDD tecnico.",
    },
    "workflow::ready-for-dev": {
        "color": "#5cb85c",
        "description": "Spec + SDD aprovados. Pipeline automatizada pode iniciar.",
    },
    "workflow::in-dev": {
        "color": "#428bca",
        "description": "Em desenvolvimento (agente automatizado ou dev manual).",
    },
    "workflow::in-review": {
        "color": "#f0e68c",
        "description": "AI review + revisao humana (2 devs + 1 maintainer).",
    },
    "workflow::done": {
        "color": "#d9534f",
        "description": "Concluido.",
    },
}

# Labels de tipo
TYPE_LABELS = {
    "type::feature": {"color": "#36b37e", "description": "Nova funcionalidade."},
    "type::bugfix": {"color": "#ff5630", "description": "Correcao de bug."},
    "type::refactor": {"color": "#6554c0", "description": "Refatoracao de codigo."},
    "type::docs": {"color": "#00b8d9", "description": "Documentacao."},
    "type::chore": {"color": "#97a0af", "description": "Tarefa de manutencao."},
}

# Labels de prioridade
PRIORITY_LABELS = {
    "priority::critical": {"color": "#ff0000", "description": "Prioridade critica. Resolver imediatamente."},
    "priority::high": {"color": "#ff5630", "description": "Prioridade alta."},
    "priority::medium": {"color": "#ffab00", "description": "Prioridade media."},
    "priority::low": {"color": "#36b37e", "description": "Prioridade baixa."},
}


def sync_group_labels(group_id: str) -> None:
    gl = gitlab.Gitlab(url=GITLAB_URL, private_token=GITLAB_TOKEN)
    group = gl.groups.get(group_id)

    existing = {l.name: l for l in group.labels.list(per_page=100, iterator=True)}

    all_labels = {**WORKFLOW_LABELS, **TYPE_LABELS, **PRIORITY_LABELS}

    created = 0
    updated = 0

    for name, config in all_labels.items():
        if name in existing:
            label = existing[name]
            needs_update = False
            if label.color != config["color"]:
                needs_update = True
            if label.description != config["description"]:
                needs_update = True
            if needs_update:
                label.color = config["color"]
                label.description = config["description"]
                label.save()
                updated += 1
                print(f"  Atualizado: {name}")
        else:
            group.labels.create({
                "name": name,
                "color": config["color"],
                "description": config["description"],
            })
            created += 1
            print(f"  Criado: {name}")

    print(f"\nTotal: {created} criados, {updated} atualizados, {len(all_labels)} labels definidos.")


if __name__ == "__main__":
    if not GITLAB_TOKEN:
        print("Defina GITLAB_TOKEN no ambiente.")
        exit(1)
    if not GROUP_ID:
        print("Defina GITLAB_GROUP_ID no ambiente.")
        print("Dica: va no grupo no GitLab > Settings > General > Group ID")
        exit(1)
    sync_group_labels(GROUP_ID)
