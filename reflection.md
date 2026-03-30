# PawPal+ Project Reflection

## 1. System Design

Core user actions:

- The user can enter and update basic owner and pet information.
- The user can add and manage pet care tasks (for example walks, feeding, medication, enrichment, and grooming) with details like duration and priority.
- The user can generate and view a daily plan that uses constraints and priorities, with a clear explanation of why the plan was chosen.


**a. Initial design**

- My initial UML used four main classes: OwnerProfile, PetProfile, CareTask, and Scheduler.
- OwnerProfile stores owner-specific scheduling constraints, including available minutes, preferred task times, and hard constraints.
- PetProfile stores pet attributes (species, age, energy level, medical notes) and exposes care-needs-related methods.
- CareTask represents a schedulable unit of pet care with duration, priority, due window, recurrence, and completion status.
- Scheduler is responsible for producing a daily task plan, resolving conflicts, scoring tasks, and explaining why tasks were selected.
- The initial separation was intentional: profile classes hold domain data, while scheduling logic is centralized in Scheduler.

**b. Design changes**

- Yes. After asking Copilot to review [pawpal_system.py](pawpal_system.py), I noticed a missing relationship and a potential scaling bottleneck.
- Missing relationship: `CareTask` did not indicate which pet it belonged to. I added a `pet_name` field so task ownership is explicit and multi-pet scheduling is possible.
- Coordination bottleneck: there was no orchestration class to manage owner, pets, and task collections together. I added a `PawPalSystem` class to centralize task management and delegate planning to `Scheduler`.
- These changes improve cohesion: entity classes remain focused on data, the scheduler stays algorithm-focused, and system-level workflow lives in one place.

**c. UML updates after final implementation**

- `CareTask` gained `scheduled_weekday: int` and `scheduled_time: str` to support weekly recurrence and HH:MM-based sorting. `is_due_today()` now takes a `weekday` parameter.
- `Scheduler` grew from 4 methods to 10. The additions — `sort_by_time()`, `detect_time_conflicts()`, `score_task()`, `explain_decision()`, `get_last_explanations()`, `get_last_conflicts()` — reflect that sorting and conflict detection belong to the scheduling layer, not the system orchestrator.
- `PawPalSystem` gained `filter_tasks()`, `get_tasks_by_status()`, `get_tasks_for_window()`, and `reset_for_new_day()`, reflecting that day-to-day task management is an orchestration concern.
- Two new relationships were added to the UML: `Scheduler ..> OwnerProfile` (reads budget and preferences directly) and `CareTask --> PetProfile` (ownership via `pet_name`).

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- My scheduler considers four main constraints: daily time budget (`daily_available_minutes`), task priority, due window (`morning/afternoon/evening/anytime`), and task recurrence/status (only pending tasks due today are considered).
- It also applies conflict resolution so duplicate tasks in the same due window are reduced to the highest-value option (higher priority first, shorter duration as tie-breaker).
- Priority is scored as the strongest signal, then adjusted by task-type weights (for example medication and vet appointments), then by timing context (fixed windows and owner preferences).
- I chose this order because safety-critical and urgent tasks should be favored first, while preference and convenience should influence selection only after essentials are covered.

**b. Tradeoffs**

- One key tradeoff is using a greedy ranking strategy instead of a global optimization algorithm.
- This means the scheduler may miss a mathematically perfect combination of tasks in some edge cases, but it stays simple, explainable, and fast for daily personal planning.
- For this scenario, that tradeoff is reasonable because owners need transparent decisions they can trust and adjust quickly, not a black-box optimizer.

- A second tradeoff is in `detect_time_conflicts()`: it only flags tasks that share an exact `HH:MM` start time — it does not check for overlapping durations.
- For example, a 30-minute walk starting at `08:00` and a 10-minute feeding starting at `08:15` would conflict in reality (both active at 08:15–08:30), but the current method would not catch it because the start times differ.
- Checking for duration overlap would require comparing every pair of tasks (O(n²)), which adds complexity and is harder to explain to an owner. Exact-time matching is O(n), easy to understand, and sufficient for a simple daily planner where tasks are usually assigned to distinct start times.
- A Pythonic `itertools.groupby` rewrite was considered but rejected: it requires pre-sorting the list before grouping (a silent precondition) and adds an import, while the current `setdefault` loop is one readable pass with no hidden requirements.

---

## 3. AI Collaboration

**a. How you used AI**


- 
- I used AI for design review, class skeleton refinement, and implementation scaffolding of scheduling logic and validation rules.
- The most helpful prompts were specific and file-aware, such as asking for missing relationships and potential bottlenecks in `pawpal_system.py`, then requesting focused changes (not broad rewrites).
- I also used AI to generate a Mermaid UML that stayed aligned with the actual implemented class structure.

**b. Judgment and verification**

- I did not blindly accept generic scheduling suggestions that introduced unnecessary complexity (for example advanced optimization setup too early).
- Instead, I evaluated suggestions against assignment scope (CLI-first, modular OOP, explainable logic), then kept a simpler greedy scheduler with explicit scoring and conflict handling.
- I verified decisions by running targeted pytest checks and a CLI demo to confirm behavior matched the intended constraints.

---

## 4. Testing and Verification

**a. What you tested**

- I tested that generated plans obey the owner time budget, conflict resolution keeps the highest-priority duplicate, unknown-pet tasks are rejected, and scheduler explanations are produced.
- These tests are important because they cover correctness (selection logic), data integrity (pet-task relationship), and transparency (explainable output), which are core promises of PawPal+.

**b. Confidence**

- I am moderately high confidence for baseline daily scheduling behavior because the algorithm is deterministic and the key constraints are covered by tests.
- With more time, I would test edge cases like many tasks with identical scores, weekly recurrence across calendar boundaries, and stricter hard-constraint enforcement (for example blocked time windows).

---

## 5. Reflection

**a. What went well**

- I am most satisfied with the clean separation of responsibilities: data modeling in profile/task classes, planning logic in `Scheduler`, and orchestration in `PawPalSystem`.

**b. What you would improve**

- In another iteration, I would improve recurrence modeling with real date handling and add richer conflict rules that account for task dependencies (for example medication after feeding).

**c. Key takeaway**

- A key takeaway is that AI is most useful when given precise, scoped prompts and then paired with human verification; architecture and testing decisions still require deliberate judgment.

---

## 6. Prompt Comparison (OpenAI vs Claude)

For a more complex algorithmic task, I compared model outputs for **weekly task rescheduling**.

**Task chosen**

- "If a weekly task cannot be scheduled on its target day due to budget overflow, automatically reschedule it to the next valid weekday within 7 days while preserving priority order and avoiding duplicate task-type conflicts for the same pet."

**Shared prompt used with both models**

- "In `pawpal_system.py`, design a modular Python solution for weekly rescheduling. Add helper methods for: (1) finding next valid weekday, (2) checking duplicate conflict constraints, and (3) applying reschedule updates. Return type hints, edge-case handling, and pytest-ready function boundaries."

**Model comparison**

- **OpenAI (GPT-5.3-Codex)** produced the more modular and Pythonic solution.
- It separated responsibilities into smaller helpers, used clearer type hints and guard clauses, and aligned better with existing class boundaries (`Scheduler` for policy, `CareTask` for task state).
- The proposed method signatures were easier to test in isolation and required fewer structural changes to existing code.
- **Claude** produced a workable approach, but it leaned toward a larger monolithic rescheduling function with more branching, which was harder to unit test and refactor incrementally.

**Why this mattered for PawPal+**

- The OpenAI output fit the project style (small deterministic helpers + explicit constraints), making it easier to integrate without breaking current tests.
- It also improved maintainability: future features like holiday skipping or blackout windows can be added as focused helper methods instead of rewriting one large function.
