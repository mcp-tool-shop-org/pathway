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

Pathway Core est un moteur de parcours qui ne fait que l'ajout de données, où la fonction "annuler" ne fait jamais disparaître les connaissances acquises.

"Annuler" est une navigation. L'apprentissage persiste.

## Philosophie

La fonction "annuler" traditionnelle réécrit l'historique. Pathway ne le fait pas.

Lorsque vous revenez en arrière dans Pathway, vous créez un nouvel événement qui pointe vers le passé, et le chemin d'origine reste conservé. Lorsque vous apprenez quelque chose sur un chemin qui a échoué, cette connaissance persiste. Vos erreurs vous enseignent ; elles ne disparaissent pas.

Cela rend Pathway fondamentalement honnête quant à ce qui s'est passé.

## Fonctionnalités

- **Journal des événements en mode ajout uniquement**: Les événements ne sont jamais modifiés ni supprimés.
- **"Annuler" = déplacement du pointeur**: La navigation en arrière crée un nouvel événement et déplace le pointeur.
- **L'apprentissage persiste**: Les connaissances survivent aux navigations en arrière et aux embranchements.
- **Les embranchements sont une fonctionnalité de premier plan**: Divergence implicite, comme avec Git, sur les nouveaux travaux après une navigation en arrière.

## Démarrage rapide

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

## Points d'accès de l'API

- `POST /events` - Ajouter un événement.
- `GET /session/{id}/state` - Obtenir l'état dérivé (JourneyView, LearnedView, ArtifactView).
- `GET /session/{id}/events` - Obtenir les événements bruts.
- `GET /sessions` - Lister toutes les sessions.
- `GET /event/{id}` - Obtenir un événement unique.

## Types d'événements

14 types d'événements couvrant l'ensemble du cycle de vie du parcours :

| Type | Objectif |
| ------ | --------- |
| IntentCreated | Objectif et contexte de l'utilisateur. |
| TrailVersionCreated | Le chemin d'apprentissage/la carte. |
| WaypointEntered | Navigation dans le chemin. |
| ChoiceMade | L'utilisateur prend une décision de branchement. |
| StepCompleted | L'utilisateur complète un point de passage. |
| Blocked | L'utilisateur rencontre un obstacle. |
| Backtracked | L'utilisateur revient en arrière (annuler). |
| Replanned | Le chemin est révisé. |
| Merged | Les branches convergent. |
| ArtifactCreated | Résultat produit. |
| ArtifactSuperseded | Ancien résultat remplacé. |
| PreferenceLearned | Comment l'utilisateur aime apprendre. |
| ConceptLearned | Ce que l'utilisateur comprend. |
| ConstraintLearned | Informations sur l'environnement de l'utilisateur. |

## Vues dérivées

Le système calcule trois vues à partir des événements :

1. **JourneyView**: Position actuelle, branches, points de passage visités.
2. **LearnedView**: Préférences, concepts, contraintes avec des scores de confiance.
3. **ArtifactView**: Tous les résultats avec suivi des remplacements.

## Sécurité

- **Clé API**: Définissez la variable d'environnement `PATHWAY_API_KEY` pour protéger les points d'accès d'écriture.
- **Limite de la charge utile**: 1 Mo par défaut (configurable via `PATHWAY_MAX_PAYLOAD_SIZE`).
- **Validation de l'ID de session**: Alphanumérique + underscore/tiret, maximum 128 caractères.

## Tests

```bash
pytest  # 73 tests covering invariants, API, reducers, store
```

## Architecture

```
pathway/
├── models/         # Pydantic models for events and views
├── store/          # SQLite event store + JSONL import/export
├── reducers/       # Compute derived views from events
├── api/            # FastAPI endpoints
└── cli.py          # Command-line tools
```
