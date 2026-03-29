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

---

## 3. AI Collaboration

**a. How you used AI**

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
