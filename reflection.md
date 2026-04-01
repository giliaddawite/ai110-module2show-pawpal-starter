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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
