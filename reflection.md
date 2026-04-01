# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

**Three core user actions:**

1. **Add a pet and owner profile** — The user enters their name, how much time they have available per day, and their pet's details (name, species, breed, age, any special needs). This is the foundation the rest of the system builds on.

2. **Add and manage care tasks** — The user creates tasks such as walks, feedings, medication reminders, grooming sessions, and enrichment activities. Each task has a name, category, estimated duration (in minutes), and a priority level (high / medium / low).

3. **Generate and view today's daily plan** — The user requests a scheduled plan for the day. The system fits the highest-priority tasks into the owner's available time window, displays the ordered schedule, and explains why each task was included or excluded.

**Building blocks (classes and responsibilities):**

- **`Owner`**
  - Attributes: `name`, `available_minutes` (daily time budget), `preferences` (dict)
  - Methods: `add_pet()`, `get_pets()`

- **`Pet`**
  - Attributes: `name`, `species`, `breed`, `age`, `special_needs` (list)
  - Methods: `add_task()`, `get_tasks()`, `__repr__()`

- **`Task`**
  - Attributes: `name`, `category` (walk/feed/meds/grooming/enrichment), `duration_minutes`, `priority` (1–3), `is_completed`
  - Methods: `complete()`, `__repr__()`

- **`Scheduler`**
  - Attributes: `owner` (Owner), `pet` (Pet), `tasks` (list of Task)
  - Methods: `generate_plan()`, `explain_plan()`, `get_unscheduled()`

**Relationships:**
- An `Owner` has one or more `Pet` objects.
- A `Pet` owns a list of `Task` objects.
- The `Scheduler` takes an `Owner` and a `Pet`, reads the task list, and produces an ordered plan that fits within `owner.available_minutes`, prioritizing by `task.priority` then shortest duration (to fit more tasks).

**b. Design changes**

After an AI review of `pawpal_system.py`, two issues were identified and fixed:

1. **`Scheduler` was missing an explicit `tasks` attribute.**
   The original skeleton only stored `owner` and `pet`. That meant `generate_plan()` would have had to call `pet.get_tasks()` silently inside every method — an implicit coupling that makes the class harder to test and reason about. The fix: `__init__` now assigns `self.tasks = pet.get_tasks() or []` so the data source is obvious and testable in isolation.

2. **Priority mismatch between UI strings and internal integers.**
   `app.py` uses `"low"` / `"medium"` / `"high"` strings, but `Task.priority` was typed as `int` (1–3). Without a conversion layer this would cause a silent type bug when wiring the UI to the backend. The fix: added a `PRIORITY_MAP` constant (`{"high": 1, "medium": 2, "low": 3}`) and a `VALID_CATEGORIES` set at the top of the module so callers have a clear conversion path.

One AI suggestion that was *not* accepted: making `Scheduler` automatically re-fetch `pet.get_tasks()` on every call to `generate_plan()`. That would cause the plan to silently change mid-session if tasks are mutated. Keeping `self.tasks` as a snapshot set at construction time is more predictable.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints:

1. **Total available time** (`owner.available_minutes`) — the hard outer limit. No plan can exceed it.
2. **Task priority** (`task.priority`: 1 = high, 2 = medium, 3 = low) — the primary sort key. High-priority tasks (medication, feeding) are always scheduled before lower-priority ones.
3. **Task duration** (`task.duration_minutes`) — used as a tiebreaker within the same priority level. Shorter tasks are scheduled first to fit more tasks into the available window.

Time was treated as the most important constraint because it is the only hard limit — you physically cannot do more than 24 hours of care in a day. Priority was chosen second because pet health tasks (meds, feeding) have real consequences if skipped. Duration as a tiebreaker was a deliberate choice to maximise the number of completed tasks rather than just the total minutes used.

**b. Tradeoffs**

**Tradeoff: greedy scheduling by priority, not by value-per-minute (knapsack)**

The scheduler uses a greedy algorithm: it sorts all tasks by `(priority, duration)` and adds them one by one until the time budget runs out. It never considers whether swapping a medium-duration medium-priority task for two short low-priority tasks might produce a "better" day overall.

A true optimal solution would require a 0/1 knapsack algorithm — trying all combinations to maximise total value (e.g. sum of priority weights) within the time budget. That would be O(n × W) in time and space (where W is available_minutes), which is tractable but significantly more complex to implement and explain to a non-technical user.

The greedy approach is reasonable here because:
- Pet care priorities are explicit and meaningful — a high-priority medication should always beat a low-priority enrichment activity, regardless of duration arithmetic.
- The owner's intent is already encoded in the priority field, so greedy selection closely matches what a person would do manually.
- For typical household task counts (5–15 tasks), the greedy result is usually identical to the optimal result.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used across every phase of the project, but in a deliberately layered way:

- **Design brainstorming (Phase 1):** Used AI to validate the class structure and identify missing relationships before writing a single line of implementation code. The most useful prompt pattern was anchoring questions to the actual file: *"Based on #file:pawpal_system.py, does the Scheduler have everything it needs to generate a plan?"* This produced specific, actionable feedback rather than generic advice.

- **Scaffolding (Phase 2):** AI generated the class skeletons (attributes, method stubs, docstrings) from the UML description. The key was providing a precise spec rather than asking for generic Python classes.

- **Algorithm implementation (Phase 3):** AI was asked focused, single-concept questions: *"How do I use a lambda key to sort HH:MM strings by time?"* and *"What is the interval overlap condition for conflict detection?"*. Broad questions like "write a scheduler" produced bloated, hard-to-own results; narrow questions produced composable pieces.

- **Test generation (Phase 4):** AI drafted an initial test plan covering happy paths. The most valuable prompt was asking specifically for *edge cases*: *"What are the most important edge cases to test for a scheduler with recurring tasks and conflict detection?"* This surfaced the "touching tasks" boundary case (A ends at 09:30, B starts at 09:30 — not a conflict) which would not have been tested otherwise.

- **Documentation:** AI was used to draft docstrings and README sections from the working code, then edited to match the actual behaviour rather than a generic description.

**b. Judgment and verification**

The clearest moment of rejection was around the `Scheduler.tasks` attribute. AI suggested making `generate_plan()` re-fetch `pet.get_tasks()` on every call so the scheduler always works with the most up-to-date task list. This sounds correct in isolation, but I rejected it for two reasons:

1. **Predictability:** If tasks are mutated between two calls to `generate_plan()` in the same session, the plan would silently change. A snapshot taken at construction time makes the plan stable for the duration of a session.
2. **Testability:** A scheduler that pulls live data is harder to test in isolation — you have to mutate the pet to set up each test case. With a snapshot, you can pass any list of tasks directly.

The AI suggestion was verified by writing a mental simulation: "If I call `generate_plan()` twice in the same button click, what should happen?" The answer was clear — the same result both times. The snapshot approach passes that test; the live-fetch approach does not.

---

## 4. Testing and Verification

**a. What you tested**

Five behaviour groups, 34 tests total:

1. **`generate_plan`** — priority ordering, budget ceiling, completed-task exclusion, sequential start times, and four edge cases (empty pet, zero budget, exact-fit budget, pre-completed tasks).
2. **`sort_by_time`** — chronological HH:MM sort, untimed-tasks-last sentinel, empty list, single item.
3. **`filter_tasks`** — status filter, category filter, AND-combined filter, no-match empty return, no-args passthrough.
4. **`detect_conflicts`** — overlapping windows, touching-not-overlapping (strict `<`), same start time, single task (no pairs), tasks without a start time skipped.
5. **Recurring tasks** — daily +1 day, weekly +7 days, new occurrence starts incomplete with no start_time, one-time task returns `None`, `pet.complete_task()` grows and does not grow the task list correctly, `None` due_date defaults to today.

These tests mattered because the most common failure mode for a scheduler is a silent off-by-one or boundary error — not a crash. Without explicit tests for "touching is not overlapping" and "zero budget returns empty", the system might appear to work in demos but fail on real inputs.

**b. Confidence**

⭐⭐⭐⭐ **4 / 5** — high confidence in the backend logic layer; moderate confidence in the full system.

Edge cases I would test next with more time:
- **Multi-pet budget competition:** what happens when two pets share one owner and the combined task load exceeds the budget? Currently each pet is scheduled independently.
- **Midnight-crossing tasks:** a task starting at `"23:30"` for 60 minutes would overflow to `"24:30"` — the current `_minutes_to_time` helper would produce `"24:30"` which is not a valid time string.
- **Knapsack vs. greedy comparison:** a parameterised test that verifies the greedy result is within an acceptable margin of the optimal result for a range of input sizes.

---

## 5. Reflection

**a. What went well**

The CLI-first workflow was the strongest decision of the project. By building and verifying all logic in `pawpal_system.py` + `main.py` before touching `app.py`, every Streamlit session-state bug was a wiring issue rather than a logic issue. The boundary between "what the backend does" and "what the UI shows" stayed clean throughout.

The test suite structure — grouping tests into five classes by behaviour rather than by method — also made failures immediately readable. When a test named `test_touching_tasks_not_a_conflict` fails, you know exactly which behaviour broke and why.

**b. What you would improve**

Two things:

1. **`Task.start_time` mutability:** `assign_start_times()` mutates tasks in place, which means generating a plan twice at different start hours leaves the tasks with whichever times were assigned last. A cleaner design would return a separate `ScheduledTask` dataclass that wraps a `Task` with a computed start time, leaving the original `Task` immutable.

2. **UI integration tests:** The Streamlit layer was verified manually. In a production system, `pytest` with `streamlit.testing` would catch regressions when the UI is changed — particularly around session-state initialisation order.

**c. Key takeaway**

The most important thing learned: **AI is a powerful junior collaborator, not an architect.** AI can generate correct code for a well-specified piece of logic in seconds. But it cannot decide *which* logic to build, *why* one design is better than another for this specific scenario, or *when* a technically correct suggestion is the wrong tradeoff for the project. Every time a suggestion was accepted without evaluation — the live-fetch `generate_plan`, the auto-re-execute recurring scheduler — it created a subtle problem that only became visible later.

The role of "lead architect" is not to write more code than AI; it is to make decisions that AI cannot make: what to build, what tradeoffs to accept, and what tests actually prove the system is trustworthy.
