# Why Pathway Works This Way

## Why undo is navigation

Traditional undo destroys history. You Ctrl+Z and the thing you did vanishes.

Pathway treats undo as movement. When you backtrack, you create a new event that says "I moved from here to there." The original path remains. You can see where you went wrong. You can learn from it.

This isn't a technical quirk. It's the whole point.

## Why learning persists across failure

In most systems, if you abandon a path, everything you learned on that path disappears with it.

Pathway keeps it.

If you tried something, hit a wall, and learned "this approach doesn't work for my situation"—that's valuable. Deleting it because you backtracked would be lying about what happened.

Learning is global. It aggregates across all branches, all backtracks, all failures. Your understanding grows monotonically even when your progress doesn't.

## Why everything is event-sourced

Events are facts. Once something happened, it happened.

Derived state (where you are, what you know, what you've made) is computed from events. You can always replay. You can always audit. You can always ask "how did we get here?"

This makes Pathway inspectable. There's no hidden state. No magic. Just a log and some reducers.

## What Pathway explicitly does not do

**Pathway does not decide for you.**
It tracks where you've been and what you've learned. It doesn't pick your path.

**Pathway does not hide your mistakes.**
Failed paths remain visible. That's a feature.

**Pathway does not pretend to be smart.**
No AI recommendations. No adaptive magic. No "we think you should..."

**Pathway does not optimize for engagement.**
It optimizes for honesty. Sometimes the honest answer is "you're stuck."

## The bet

The bet is that systems which respect human agency—which show you the truth about where you are—will ultimately be more useful than systems which hide complexity to seem helpful.

Pathway is infrastructure for that bet.
