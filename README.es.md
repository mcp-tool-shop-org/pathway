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

Pathway Core es un motor de aprendizaje que solo permite añadir información, donde deshacer nunca borra lo aprendido.

Deshacer es navegación. El aprendizaje persiste.

## Filosofía

La función de deshacer tradicional reescribe el historial. Pathway no lo hace.

Cuando retrocedes en Pathway, creas un nuevo evento que apunta hacia atrás; la ruta original permanece. Cuando aprendes algo en una ruta fallida, ese conocimiento persiste. Tus errores te enseñan; no desaparecen.

Esto hace que Pathway sea fundamentalmente honesto sobre lo que sucedió.

## Características

- **Registro de eventos de solo escritura**: Los eventos nunca se editan ni se eliminan.
- **Deshacer = movimiento de puntero**: Retroceder crea un nuevo evento y mueve el puntero.
- **El aprendizaje persiste**: El conocimiento se mantiene a través de la retrocesión y las bifurcaciones.
- **Las bifurcaciones son de primera clase**: Divergencia implícita similar a Git en nuevos trabajos después de retroceder.

## Inicio rápido

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

## Puntos finales de la API

- `POST /events` - Añadir un evento.
- `GET /session/{id}/state` - Obtener el estado derivado (JourneyView, LearnedView, ArtifactView).
- `GET /session/{id}/events` - Obtener eventos sin procesar.
- `GET /sessions` - Listar todas las sesiones.
- `GET /event/{id}` - Obtener un evento individual.

## Tipos de eventos

14 tipos de eventos que cubren todo el ciclo de vida del aprendizaje:

| Type | Propósito |
| ------ | --------- |
| IntentCreated | Objetivo y contexto del usuario. |
| TrailVersionCreated | La ruta de aprendizaje/mapa. |
| WaypointEntered | Navegación a través de la ruta. |
| ChoiceMade | El usuario toma una decisión de bifurcación. |
| StepCompleted | El usuario completa un punto de referencia. |
| Blocked | El usuario encuentra una dificultad. |
| Backtracked | El usuario retrocede (deshacer). |
| Replanned | La ruta se revisa. |
| Merged | Las bifurcaciones convergen. |
| ArtifactCreated | Resultado producido. |
| ArtifactSuperseded | Resultado antiguo reemplazado. |
| PreferenceLearned | Cómo le gusta aprender al usuario. |
| ConceptLearned | Lo que el usuario entiende. |
| ConstraintLearned | Información sobre el entorno del usuario. |

## Vistas derivadas

El sistema calcula tres vistas a partir de los eventos:

1. **JourneyView**: Posición actual, bifurcaciones, puntos de referencia visitados.
2. **LearnedView**: Preferencias, conceptos, restricciones con puntajes de confianza.
3. **ArtifactView**: Todos los resultados con seguimiento de reemplazos.

## Seguridad

- **Clave de API**: Establece la variable de entorno `PATHWAY_API_KEY` para proteger los puntos finales de escritura.
- **Límite de carga útil**: 1 MB por defecto (configurable a través de `PATHWAY_MAX_PAYLOAD_SIZE`).
- **Validación del ID de sesión**: Alfanumérico + guion bajo/guion, máximo 128 caracteres.

## Pruebas

```bash
pytest  # 73 tests covering invariants, API, reducers, store
```

## Arquitectura

```
pathway/
├── models/         # Pydantic models for events and views
├── store/          # SQLite event store + JSONL import/export
├── reducers/       # Compute derived views from events
├── api/            # FastAPI endpoints
└── cli.py          # Command-line tools
```
