# Coding Sandbox

The coding sandbox is the multi-language code-execution environment behind the
interview platform's coding round. Candidates open a problem in the full-screen
editor (`frontend/src/components/CodeSandbox.tsx`), write a solution, and the
backend grades it in an isolated sandbox against the problem's recorded test
cases.

This page documents the sandbox architecture and the **SQL (database)
language** support. The service files live under `app/services/`:

| File | Role |
| --- | --- |
| `code_runners.py` | Per-language execution specs and generic test harnesses |
| `code_executor_service.py` | Problem registry (curated + 1000-problem bank) and grading dispatch |
| `code_sandbox.py` | Isolation backends: Docker, Piston, Judge0, local subprocess |
| `static_harness.py` | Signature inference + starter generation for statically typed languages |
| `problem_diagrams.py` | Figures for statements, incl. database **schema diagrams** |
| `problem_enrichment.py` | Judge-grade statements, constraints, examples, hints |

---

## Languages

The sandbox ships 15 languages:

Python 3, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Ruby, PHP, Swift,
Objective-C, Erlang, Haskell, and **SQL**.

Each language is declared as a `LanguageSpec` in `code_runners.LANGUAGES`,
which names the container image, source filename, run command, aliases, and the
Piston/Judge0 identifiers used by the HTTP backends.

### SQL

SQL is declared as a first-class language key `"sql"` with the aliases
`sqlite`, `sqlite3`, `mysql`, `postgres`, `postgresql`, and `database`. It is
deliberately **not** a Piston/Judge0 runtime: those services have no reliable
SQL dialect. Instead the SQL spec reuses the shared Python image, because the
grading harness is a Python program that drives the `sqlite3` module from the
standard library — no extra infrastructure or image is required. The Docker and
subprocess backends therefore cover SQL out of the box.

| Spec field | Value |
| --- | --- |
| Name | `SQL` |
| Image | `python:3.12-alpine` |
| Source name | `main.py` |
| Run command | `python -I /build/main.py` |
| Aliases | `sqlite`, `sqlite3`, `mysql`, `postgres`, `postgresql`, `database` |
| Piston / Judge0 | (unset — covered by Docker/subprocess backends) |

---

## The grading contract

Every runner obeys one contract: the program prints a single line
`RESULTS_JSON:[...]` holding one `{passed, actual, expected}` object per test
case. If that line is absent, the run **failed** — there is no code path that
invents a passing result.

SQL grading fits this contract unchanged. `build_sql_harness` in
`code_runners.py` wraps the candidate's query in a Python program that, for
each test case:

1. opens an in-memory SQLite database (`sqlite3.connect(":memory:")`),
2. executes the problem's `CREATE TABLE` schema statements,
3. executes the case's `INSERT` seed statements,
4. runs the candidate's query, and
5. compares the returned rows against the case's expected rows.

Because SQL result order is unspecified without an `ORDER BY`, the harness
compares **sorted row sets** rather than emitted order — a query returning the
right rows in a different order is a pass, not a failure. A query that errors
is a failure carrying the SQLite message; it can never be graded as a pass.

---

## Database problems

Database problems are graded with a query, not a function call. In
`code_executor_service.CURATED_PROBLEMS` they are marked by three fields:

| Field | Meaning |
| --- | --- |
| `sql_schema` | `CREATE TABLE` statements that build the database per case |
| `starter_code.sql` | The SQL starter shown in the editor |
| `test_cases[].seed` | `INSERT` statements that populate the tables for that case |
| `test_cases[].expected` | The result rows the query must return |
| `solution_sql` | Authoring/test artifact: the reference query used to verify the suite grades correctly |

The curated ladder mirrors LeetCode's database tiering — Basic, Intermediate,
and Advanced:

| Difficulty | Problem | Technique |
| --- | --- | --- |
| Easy | Combine Two Tables | `LEFT JOIN` with `NULL` handling |
| Easy | Duplicate Emails | `GROUP BY … HAVING COUNT(*) > 1` |
| Easy | Employees Earning More Than Their Managers | Self-join |
| Easy | Game Play Analysis I | `MIN(event_date)` per player (`GROUP BY`) |
| Easy | Customer Who Visited but Did Not Make Any Transactions | `LEFT JOIN` + `IS NULL` filter |
| Easy | Sales Person | `NOT IN` subquery excluding RED-company orders |
| Easy | Rising Temperature | Self-join with `date(recordDate, '+1 day')` |
| Easy | Students and Examinations | `CROSS JOIN` + `LEFT JOIN` + `COUNT` (zeros preserved) |
| Medium | Rank Scores | `DENSE_RANK()` window function |
| Medium | Consecutive Numbers | Three-way self-join on consecutive ids |
| Medium | Exchange Seats | Parity swap with `LEFT JOIN` + `COALESCE` |
| Medium | Market Analysis I | Date-windowed `LEFT JOIN` + `COUNT` |
| Medium | Last Person to Fit in the Bus | Cumulative `SUM() OVER (ORDER BY turn)` ≤ 1000 |
| Hard | Department Top Three Salaries | Correlated subquery over distinct salaries |
| Hard | Trips and Users | Multi-join aggregation with `ROUND` |
| Hard | Human Traffic of Stadium | Three-way self-join over consecutive days |

Each problem also ships a judge-grade description, constraints, hints, and —
where the ladder calls for it — a follow-up, and, like every other problem,
examples that are **replayed from the graded test cases**, so a statement can
never disagree with what the grader asserts.

### SQL coverage in the problem bank

The 1000-problem bank (`coding_problems_data.py`) is generated from
function-language base problems, so it used to hold no database questions at
all. It now ships a hand-authored SQL coverage set
(`coding_sql_problems_data.py`): thirteen classic database problems (ids
1001–1013) spanning the same Basic / Intermediate / Advanced tiers — Big
Countries, Employee Bonus, and Product Sales Analysis I (Basic); Managers with
at Least 5 Direct Reports, Department Highest Salary, Average Time of Process
per Machine, Friend Requests II, Nth Highest Salary, and Game Play Analysis IV
(Intermediate); and Median Employee Salary, Report Contiguous Dates,
Department Top Three Salaries, and Trips and Users (Advanced).

The entries are shaped exactly like the curated ladder — `sql_schema`, a `sql`
starter, `test_cases[].seed`/`expected`, and a `solution_sql` reference — and
are merged into the bank at import time by `code_executor_service`, so the
catalogue, schema figures, enrichment, and the SQL grading branch treat them
identically to curated problems. They are never disguised: a themed title over
a borrowed schema would lie about the content, so
`scratch/generate_1000_problems.py` preserves them verbatim and only samples
function-language problems for its variants. Their ids sit above the generated
1–1000 range, so regenerating the bank can never collide with them.

### The reference solution is never served to candidates

`solution_sql` is an authoring artifact. When a database problem is served to a
candidate (`get_curated_problems`, `get_problem_by_id`), `problem_enrichment`
pops it from the enriched payload so the answer never ships with the question.
A regression test (`test_reference_solution_is_never_served_to_candidates`)
pins this behaviour shut.

### Grading dispatch

`CodeExecutorService.execute_code` resolves the language and dispatches:

- A database problem submitted in a **function language** (e.g. Python) is
  rejected up front with a clear message: the problem must be answered with
  SQL. Without this guard the function-call harnesses would report a string of
  opaque `KeyError` failures.
- A database problem submitted in **SQL** takes the dedicated SQL branch, which
  builds the query harness and runs it through the normal graded path.
- A **coding problem** submitted in SQL is rejected: SQL grading needs a
  schema, and guessing would misgrade.
- SQL never falls through to the function-call harnesses — `sql` is absent from
  `HARNESS_BUILDERS` by design, so the explicit branch is the only path.

---

## Schema diagrams

LeetCode database problems ship with a picture of the schema. We cannot use
those assets, so `problem_diagrams.build_schema_diagram` derives one from the
problem's own `sql_schema` and seed data: one card per table, its columns with
types and key badges (PK / UQ / FK), and a few seeded rows.

Because the picture is computed from the same statements the grader executes,
it cannot disagree with the seed. The frontend renders the spec as real DOM
(`Schema` component in `frontend/src/components/ProblemDiagram.tsx`) — never a
generated markup string — so problem data cannot inject anything into the page.
The schema figure appears only on the first example, matching the existing
figure policy for array/grid/tree problems.

---

## Statement enrichment

`problem_enrichment` treats database problems as a distinct class
(`_is_database_problem`): there is no function signature to infer, so the
generic typed-signature machinery is skipped. `_enrich_sql` instead:

- replays examples from the seed statements and expected rows (never invented),
- attaches the schema diagram to the first example,
- carries through the authored description, constraints, hints, and follow-up,
- strips `solution_sql` before the payload is served.

---

## Frontend

`frontend/src/components/CodeSandbox.tsx` wires SQL through the whole editor:

- The language selector offers the 14 function languages; when a database
  problem is open the picker is **locked to a single SQL option**
  (`effectiveLang`). SQL is never offered for a coding problem (the grader
  would reject it), and a stale Python selection can never send a query
  through a function harness.
- The CodeMirror editor uses the `@codemirror/lang-sql` extension
  (`frontend/package.json`) for syntax highlighting and autocompletion.
- The file tab and upload picker use the `.sql` extension.
- `frontend/src/lib/api.ts` types carry `SupportedCodingLang = … | "sql"`,
  `CodingProblem.sql_schema`, and the `DiagramSpec.kind = "schema"` figure spec.

---

## Testing

The SQL suite lives in `tests/test_code_execution.py`. The key property tests
run under the **local Python interpreter** (the harness is pure stdlib
`json` + `sqlite3`), so no container is required:

- `test_every_database_reference_solution_passes_its_own_tests` — every shipped
  reference query must pass its own suite through the real sqlite3 engine.
- `test_no_sql_starter_passes_its_own_tests` — a starter stub must never pass.
- `test_every_bank_database_reference_solution_passes_its_own_tests` /
  `test_no_bank_sql_starter_passes_its_own_tests` — the same reference/starter
  sweep over the bank's SQL coverage set.
- `test_bank_sql_reference_is_never_served_to_candidates` — the answer-leak
  pin extended to bank database problems.
- `test_bank_sql_problem_serves_schema_and_seed` — a served bank database
  problem carries its schema, per-case seeds and replayed examples.
- `test_sql_harness_orders_results_as_sets_not_sequences` — order-insensitive
  row-set comparison.
- `test_wrong_sql_query_fails` / `test_sql_syntax_error_is_a_failure_not_a_pass`
  — wrong or malformed queries are failures, never passes.
- `test_sql_execute_path_is_taken_before_function_harnesses` — SQL routes to
  the query harness, not a function-call wrapper.
- `test_sql_on_non_database_problem_is_rejected` and
  `test_database_problem_in_a_function_language_fails_honestly` — the guard
  paths.
- `test_reference_solution_is_never_served_to_candidates` — the answer-leak
  regression.
- Schema-figure tests verify `build_schema_diagram` parses columns, key badges,
  `DECIMAL(3, 2)` types, multi-line schema, and `NULL` seed values.
