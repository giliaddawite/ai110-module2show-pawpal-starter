# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## Smarter Scheduling

Beyond basic priority-based planning, `pawpal_system.py` includes several algorithmic features:

### Sort by time
`Scheduler.sort_by_time(tasks)` sorts any task list by its `HH:MM` start time using a lambda key that converts the string to total minutes — so `"09:05"` correctly sorts before `"10:00"` via integer comparison, not string comparison.

### Filter by status or category
`Scheduler.filter_tasks(tasks, completed=, category=)` lets you slice the task list by completion status, category (walk / feed / meds / grooming / enrichment), or both at once. Useful for showing only today's pending tasks or only medication reminders.

### Auto-assign start times
`Scheduler.assign_start_times(plan, start_hour=8)` walks through the generated plan and stamps each task with a sequential `HH:MM` start time, assuming tasks run back-to-back from the given hour (default 08:00).

### Conflict detection
`Scheduler.detect_conflicts(tasks)` scans all tasks that have a `start_time` set and returns every pair whose time windows overlap — using the interval overlap condition `A.start < B.end AND B.start < A.end`.

### Recurring tasks
Tasks can be marked `recurrence="daily"` or `recurrence="weekly"`. When `pet.complete_task(task)` is called, it uses Python's `timedelta` to calculate the next due date (`+1 day` or `+7 days`) and automatically appends a fresh copy of the task to the pet's task list — no manual rescheduling required.

### Run the CLI demo
```bash
python main.py
```

---

## Testing PawPal+

### Run the test suite

```bash
python -m pytest
```

Or with verbose output to see each test name:

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

The suite lives in `tests/test_pawpal.py` and contains **34 tests** across 5 groups:

| Group | Tests | What is verified |
|---|---|---|
| `TestGeneratePlan` | 9 | Tasks scheduled by priority; plan never exceeds time budget; completed tasks excluded; start times auto-assigned sequentially; edge cases: empty pet, zero budget, exact-fit budget |
| `TestSortByTime` | 4 | Tasks returned in chronological HH:MM order; tasks without a start time sort last; empty list and single-item list handled safely |
| `TestFilterTasks` | 6 | Filter by completion status, by category, and by both combined (AND logic); no-match returns empty list; no-args returns all tasks unchanged |
| `TestDetectConflicts` | 6 | Overlapping windows flagged; touching edges (end == start) not a conflict; same start time is a conflict; single task returns no pairs; tasks without start_time are ignored |
| `TestRecurringTasks` | 9 | Daily task next occurrence = today + 1 day; weekly = today + 7 days; rescheduled task is incomplete with no start_time; one-time task returns None; `pet.complete_task()` auto-appends next occurrence; `due_date=None` defaults to today |

### Confidence level

⭐⭐⭐⭐ **4 / 5**

The core scheduling logic — priority ordering, time budget enforcement, conflict detection, and recurring task rescheduling — is well covered by happy-path and edge-case tests. One star is held back because:

- The greedy scheduler is not tested against an optimal solution (no knapsack comparison).
- Integration between the Streamlit UI (`app.py`) and the backend has no automated tests; only manual verification.
- Multi-pet scheduling (tasks competing across pets for one owner's time budget) has no dedicated tests yet.
