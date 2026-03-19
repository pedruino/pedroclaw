# Squad XI: Detalhes do time de agentes

## Origem do nome

XI (onze) referencia um time de futebol: 11 jogadores com posicoes especificas, coordenados por um capitao. O Squad XI tem 4 agentes base + 6 especialistas sob demanda = 10 posicoes, mais o Pedroclaw como o "tecnico" que orquestra tudo.

## Agentes base

### Aratu (Captain) 🦀

Caranguejo brasileiro (Aratus pisonii). Rapido, adaptavel, vive entre a terra e o mar. Representa a capacidade de navegar entre diferentes contextos (tipos de arquivo, linguagens, frameworks).

**Responsabilidades:**
- Analisar o diff e identificar areas de risco
- Decidir nivel de risco (low/medium/high)
- Selecionar quais especialistas chamar
- Consolidar e deduplicar achados de todos os agentes

### Coral (Researcher) 🪸

Corais filtram o oceano, capturando nutrientes do que passa. Representa a capacidade de filtrar regras relevantes e encontrar violacoes no fluxo de codigo.

**Responsabilidades:**
- Carregar skills/regras do projeto
- Pesquisar violacoes no diff usando as regras como contexto
- Retornar achados estruturados (arquivo, linha, severidade, descricao)

### Nautilo (Logician) 🐚

O nautilo (Nautilus) tem a concha em espiral logaritmica perfeita, simbolo de precisao matematica. Representa validacao rigorosa e logica.

**Responsabilidades:**
- Validar cada achado da Coral contra o diff real
- Remover falsos positivos
- Corrigir linhas e arquivos incorretos
- Melhorar descricoes imprecisas

### Baiacu (Contrarian) 🐡

O baiacu (pufferfish) infla quando ameacado, forando predadores a reconsiderar. Representa o papel de provocador que forca o time a reconsiderar suas conclusoes.

**Responsabilidades:**
- Encontrar problemas que os outros perderam
- Focar em seguranca, edge cases, race conditions
- Questionar premissas implicitas no codigo
- NAO repetir achados existentes

## Especialistas

Chamados sob demanda pelo Aratu quando o risco e medio ou alto.

| Especialista | Area | Skill associada |
|-------------|------|----------------|
| react-specialist | React 19, Next.js 16 | react-specialist |
| typescript-advanced | TypeScript strict | typescript-advanced |
| integration-review | Backend integration | integration-review |
| ui-review | Design System | ui-review |
| a11y-audit | Acessibilidade | a11y-audit |
| quality-review | Qualidade geral | quality-review |

## Custo por review

| Componente | Tokens (estimativa) | Custo Claude Sonnet |
|-----------|-------------------|-------------------|
| Aratu (classificacao) | ~3k input, ~1k output | R$ 0,13 |
| Coral (pesquisa) | ~30k input, ~2k output | R$ 0,64 |
| Nautilo (validacao) | ~5k input, ~1k output | R$ 0,16 |
| Baiacu (contrarian) | ~5k input, ~1k output | R$ 0,16 |
| Especialistas (0-3) | ~10k input, ~1k output cada | R$ 0,24 cada |
| **Total tipico** | **~50k input, ~6k output** | **~R$ 1,30** |

Para 165 MRs/mes: ~R$ 215/mes com Claude Sonnet.
