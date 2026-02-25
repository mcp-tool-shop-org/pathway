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

Pathway Core è un motore di percorso che registra solo aggiunte, dove l'operazione di annullamento non cancella mai ciò che è stato appreso.

L'annullamento è navigazione. L'apprendimento persiste.

## Filosofia

L'annullamento tradizionale riscrive la cronologia. Pathway non lo fa.

Quando si torna indietro in Pathway, si crea un nuovo evento che punta al percorso precedente: il percorso originale rimane. Quando si impara qualcosa su un percorso fallito, quella conoscenza persiste. I propri errori insegnano; non scompaiono.

Questo rende Pathway fondamentalmente trasparente su ciò che è accaduto.

## Funzionalità

- **Registro eventi di sola aggiunta**: Gli eventi non vengono mai modificati o eliminati.
- **Annulla = spostamento del puntatore**: Tornare indietro crea un nuovo evento e sposta il puntatore.
- **L'apprendimento persiste**: La conoscenza sopravvive anche durante le operazioni di annullamento e la creazione di diramazioni.
- **Le diramazioni sono una funzionalità di primo livello**: Divergenza implicita simile a Git su nuovi lavori dopo aver fatto marcia indietro.

## Guida rapida

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

## Punti finali API

- `POST /events` - Aggiunge un evento.
- `GET /session/{id}/state` - Ottiene lo stato derivato (JourneyView, LearnedView, ArtifactView).
- `GET /session/{id}/events` - Ottiene gli eventi grezzi.
- `GET /sessions` - Elenca tutte le sessioni.
- `GET /event/{id}` - Ottiene un singolo evento.

## Tipi di eventi

14 tipi di eventi che coprono l'intero ciclo di vita del percorso:

| Type | Scopo |
| ------ | --------- |
| IntentCreated | Obiettivo e contesto dell'utente. |
| TrailVersionCreated | Il percorso/la mappa di apprendimento. |
| WaypointEntered | Navigazione all'interno del percorso. |
| ChoiceMade | L'utente prende una decisione di diramazione. |
| StepCompleted | L'utente completa un punto di riferimento. |
| Blocked | L'utente incontra un ostacolo. |
| Backtracked | L'utente torna indietro (annulla). |
| Replanned | Il percorso viene rivisto. |
| Merged | Le diramazioni convergono. |
| ArtifactCreated | Output prodotto. |
| ArtifactSuperseded | Output precedente sostituito. |
| PreferenceLearned | Come l'utente preferisce imparare. |
| ConceptLearned | Cosa l'utente comprende. |
| ConstraintLearned | Informazioni sull'ambiente dell'utente. |

## Viste derivate

Il sistema calcola tre viste dagli eventi:

1. **JourneyView**: Posizione corrente, diramazioni, punti di riferimento visitati.
2. **LearnedView**: Preferenze, concetti, vincoli con punteggi di confidenza.
3. **ArtifactView**: Tutti gli output con il tracciamento delle sostituzioni.

## Sicurezza

- **Chiave API**: Imposta la variabile d'ambiente `PATHWAY_API_KEY` per proteggere i punti finali di scrittura.
- **Limite della dimensione del payload**: 1 MB (configurabile tramite `PATHWAY_MAX_PAYLOAD_SIZE`).
- **Validazione dell'ID della sessione**: Alfanumerico + underscore/trattino, massimo 128 caratteri.

## Test

```bash
pytest  # 73 tests covering invariants, API, reducers, store
```

## Architettura

```
pathway/
├── models/         # Pydantic models for events and views
├── store/          # SQLite event store + JSONL import/export
├── reducers/       # Compute derived views from events
├── api/            # FastAPI endpoints
└── cli.py          # Command-line tools
```
