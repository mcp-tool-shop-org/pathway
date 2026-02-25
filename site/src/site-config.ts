import type { SiteConfig } from '@mcptoolshop/site-theme';

export const config: SiteConfig = {
  title: 'Pathway',
  description: 'Append-only journey engine where undo never erases learning.',
  logoBadge: 'PW',
  brandName: 'Pathway',
  repoUrl: 'https://github.com/mcp-tool-shop-org/pathway',
  footerText: 'MIT Licensed \u2014 built by <a href="https://github.com/mcp-tool-shop-org" style="color:var(--color-muted);text-decoration:underline">mcp-tool-shop-org</a>',

  hero: {
    badge: 'Open source',
    headline: 'Pathway',
    headlineAccent: 'Undo is navigation. Learning persists.',
    description: 'An append-only journey engine where backtracking creates new events instead of erasing history. Mistakes teach \u2014 they don\u2019t disappear.',
    primaryCta: { href: '#quick-start', label: 'Get started' },
    secondaryCta: { href: '#philosophy', label: 'Why Pathway?' },
    previews: [
      { label: 'Init', code: 'python -m pathway.cli init' },
      { label: 'Import', code: 'python -m pathway.cli import session.jsonl' },
      { label: 'Serve', code: 'python -m pathway.cli serve' },
    ],
  },

  sections: [
    {
      kind: 'features',
      id: 'features',
      title: 'Features',
      subtitle: 'Event-sourced journeys with first-class learning.',
      features: [
        { title: 'Append-Only Log', desc: 'Events are never edited or deleted. The full history is always preserved.' },
        { title: 'Undo = Pointer Move', desc: 'Backtracking creates a new event and moves head \u2014 the original path remains intact.' },
        { title: 'Learning Persists', desc: 'Knowledge survives across backtracking and branches. Failed paths still teach.' },
        { title: 'First-Class Branching', desc: 'Git-like implicit divergence when new work happens after a backtrack.' },
        { title: 'Derived Views', desc: 'JourneyView, LearnedView, and ArtifactView computed from the event stream in real time.' },
        { title: 'FastAPI + SQLite', desc: 'REST API with built-in auth, payload limits, and SQLite persistence out of the box.' },
      ],
    },
    {
      kind: 'features',
      id: 'philosophy',
      title: 'Philosophy',
      subtitle: 'Traditional undo rewrites history. Pathway doesn\u2019t.',
      features: [
        { title: 'Honest History', desc: 'Every event that happened is recorded. There is no way to pretend something didn\u2019t happen.' },
        { title: 'Mistakes Are Data', desc: 'A failed attempt isn\u2019t wasted \u2014 it\u2019s a preference learned, a concept understood, or a constraint discovered.' },
        { title: 'Navigation, Not Erasure', desc: 'Going back doesn\u2019t delete the forward path. It\u2019s a new event that says "I chose to revisit."' },
      ],
    },
    {
      kind: 'code-cards',
      id: 'quick-start',
      title: 'Quick Start',
      cards: [
        {
          title: 'Install & init',
          code: 'pip install mcpt-pathway\n\npython -m pathway.cli init\npython -m pathway.cli import sample_session.jsonl',
        },
        {
          title: 'View state',
          code: '# Derived state for a session\npython -m pathway.cli state sess_001\n\n# Start API server\npython -m pathway.cli serve',
        },
        {
          title: 'API usage',
          code: '# Append an event\ncurl -X POST /events -d \'{"type": "StepCompleted", ...}\'\n\n# Get derived state\ncurl /session/sess_001/state',
        },
        {
          title: 'Derived views',
          code: '# JourneyView: position, branches, waypoints\n# LearnedView: preferences, concepts, constraints\n# ArtifactView: outputs with supersedence tracking',
        },
      ],
    },
    {
      kind: 'data-table',
      id: 'events',
      title: 'Event Types',
      subtitle: '14 event types covering the full journey lifecycle.',
      columns: ['Type', 'Purpose'],
      rows: [
        ['IntentCreated', 'User\u2019s goal and context'],
        ['TrailVersionCreated', 'The learning path/map'],
        ['WaypointEntered', 'Navigation through trail'],
        ['ChoiceMade', 'User makes a branching decision'],
        ['StepCompleted', 'User completes a waypoint'],
        ['Blocked', 'User hits friction'],
        ['Backtracked', 'User goes back (undo)'],
        ['Replanned', 'Trail is revised'],
        ['Merged', 'Branches converge'],
        ['ArtifactCreated', 'Output produced'],
        ['ArtifactSuperseded', 'Old output replaced'],
        ['PreferenceLearned', 'How user likes to learn'],
        ['ConceptLearned', 'What user understands'],
        ['ConstraintLearned', 'User\u2019s environment facts'],
      ],
    },
    {
      kind: 'api',
      id: 'api',
      title: 'API Reference',
      apis: [
        { signature: 'POST /events', description: 'Append an event to the log.' },
        { signature: 'GET /session/{id}/state', description: 'Get derived state (JourneyView, LearnedView, ArtifactView).' },
        { signature: 'GET /session/{id}/events', description: 'Get raw events for a session.' },
        { signature: 'GET /sessions', description: 'List all sessions.' },
        { signature: 'GET /event/{id}', description: 'Get a single event by ID.' },
      ],
    },
  ],
};
