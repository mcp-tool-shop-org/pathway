<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="logo.png" alt="Pathway logo" width="400">
</p>

<p align="center">
    <em>Append-only journey engine where undo never erases learning.</em>
</p>

<p align="center">
    <a href="https://github.com/mcp-tool-shop-org/pathway/actions/workflows/ci.yml">
        <img src="https://github.com/mcp-tool-shop-org/pathway/actions/workflows/ci.yml/badge.svg" alt="CI">
    </a>
    <a href="https://pypi.org/project/mcpt-pathway/">
        <img src="https://img.shields.io/pypi/v/mcpt-pathway" alt="PyPI version">
    </a>
    <a href="https://opensource.org/licenses/MIT">
        <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
    </a>
    <a href="https://mcp-tool-shop-org.github.io/pathway/">
        <img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page">
    </a>
</p>

**Pathway Core é um sistema de acompanhamento que registra todas as ações, permitindo que você volte atrás sem perder o aprendizado.**

Voltar atrás é navegação. O aprendizado persiste.

## Filosofia

O "desfazer" tradicional reescreve o histórico. O Pathway não.

Quando você volta atrás no Pathway, você cria um novo evento que aponta para o evento anterior – o caminho original permanece. Quando você aprende algo em um caminho que não deu certo, esse conhecimento permanece. Seus erros ensinam; eles não desaparecem.

Isso torna o Pathway fundamentalmente transparente sobre o que aconteceu.

## Características

- **Registro de eventos somente para adição:** Os eventos nunca são editados ou excluídos.
- **"Desfazer" = movimento do ponteiro:** Voltar atrás cria um novo evento e move o ponteiro.
- **O aprendizado persiste:** O conhecimento sobrevive ao voltar atrás e às ramificações.
- **Ramificações são prioridade:** Divergência implícita semelhante ao Git em novos trabalhos após voltar atrás.

## Início Rápido

```bash
# Install
pip install -e ".[dev]"

# Initialize database
python -m pathway.cli init

# Import sample session
python -m pathway.cli import sample_session.jsonl

# View derived state
python -m pathway.cli state sess_001

# Start API server
python -m pathway.cli serve
```

## Pontos de Acesso da API

- `POST /events` - Adiciona um evento.
- `GET /session/{id}/state` - Obtém o estado derivado (JourneyView, LearnedView, ArtifactView).
- `GET /session/{id}/events` - Obtém os eventos brutos.
- `GET /sessions` - Lista todas as sessões.
- `GET /event/{id}` - Obtém um evento específico.

## Tipos de Eventos

14 tipos de eventos que cobrem todo o ciclo de vida do acompanhamento:

| Type | Propósito |
| ------ | --------- |
| IntentCreated | Objetivo e contexto do usuário. |
| TrailVersionCreated | O caminho de aprendizado/mapa. |
| WaypointEntered | Navegação pelo caminho. |
| ChoiceMade | O usuário toma uma decisão de ramificação. |
| StepCompleted | O usuário completa um ponto de referência. |
| Blocked | O usuário encontra um obstáculo. |
| Backtracked | O usuário volta atrás (desfaz). |
| Replanned | O caminho é revisado. |
| Merged | Ramificações convergem. |
| ArtifactCreated | Saída produzida. |
| ArtifactSuperseded | Saída antiga substituída. |
| PreferenceLearned | Como o usuário gosta de aprender. |
| ConceptLearned | O que o usuário entende. |
| ConstraintLearned | Fatos sobre o ambiente do usuário. |

## Visões Derivadas

O sistema calcula três visões a partir dos eventos:

1. **JourneyView**: Posição atual, ramificações, pontos de referência visitados.
2. **LearnedView**: Preferências, conceitos, restrições com níveis de confiança.
3. **ArtifactView**: Todas as saídas com rastreamento de substituição.

## Segurança

- **Chave da API**: Defina a variável de ambiente `PATHWAY_API_KEY` para proteger os pontos de acesso de escrita.
- **Limite de carga útil**: 1MB por padrão (configure via `PATHWAY_MAX_PAYLOAD_SIZE`).
- **Validação do ID da sessão**: Alfanumérico + sublinhado/hífen, máximo de 128 caracteres.

## Testes

```bash
pytest  # 73 tests covering invariants, API, reducers, store
```

## Arquitetura

```
pathway/
├── models/         # Pydantic models for events and views
├── store/          # SQLite event store + JSONL import/export
├── reducers/       # Compute derived views from events
├── api/            # FastAPI endpoints
└── cli.py          # Command-line tools
```
