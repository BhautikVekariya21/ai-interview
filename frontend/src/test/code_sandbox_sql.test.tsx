import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import CodeSandbox from "@/components/CodeSandbox";
import {
  fetchCodingProblems,
  fetchCodingCatalog,
  fetchCodingProblem,
  type CodingProblem,
  type CodingProblemSummary,
} from "@/lib/api";

// The sandbox is a heavy component — mock everything it talks to that is not
// under test, leaving the real language-select + effectiveLang wiring live.
vi.mock("@/lib/api", () => ({
  fetchCodingProblems: vi.fn(),
  fetchCodingProblem: vi.fn(),
  fetchCodingCatalog: vi.fn(),
  fetchCodingSubmissions: vi.fn(async () => []),
  runCodingSolution: vi.fn(),
  submitCodingSolution: vi.fn(),
  // ScreenRecordGuard's hook fetches this on mount; report proctoring as off
  // so the gate never covers the editor under test.
  fetchProctorConfig: vi.fn(async () => ({
    enabled: false,
    required: false,
    chunk_interval_ms: 5000,
    max_chunk_bytes: 1_000_000,
  })),
}));

vi.mock("@/lib/interviewSession", () => ({
  getInterviewSessionId: vi.fn(() => "test-session"),
}));

vi.mock("@/hooks/useSessionStorage", () => ({
  loadSelectedProblemIds: vi.fn(async () => []),
}));

// ScreenRecordGuard is heavy (it fetches /proctor/config and mounts a
// full-viewport gate). Most tests stub it out entirely; the guard-lifecycle
// test counts mounts so it can pin that a catalogue pick never remounts the
// guard — a remount tears down the recorder and makes the browser re-ask for
// screen sharing.
const { guardMountCount } = vi.hoisted(() => ({ guardMountCount: { value: 0 } }));
vi.mock("@/components/ScreenRecordGuard", async () => {
  const React = await import("react");
  function MockScreenRecordGuard() {
    // Count mounts, not renders: the sandbox legitimately re-renders the
    // header on every state change (clock tick, language, pick spinner),
    // and only a true remount tears down the recorder.
    React.useEffect(() => {
      guardMountCount.value += 1;
    }, []);
    return <div data-testid="screen-record-guard" />;
  }
  return { default: MockScreenRecordGuard };
});

// Real CodeMirror is not needed to observe the language lock. The mock is a
// controlled textarea that propagates onChange like the real editor, so tests
// can both read the loaded starter and simulate the candidate editing.
vi.mock("@uiw/react-codemirror", async () => {
  const React = await import("react");
  return {
    default: (props: { value?: string; onChange?: (value: string) => void }) =>
      React.createElement("textarea", {
        "data-testid": "code-editor",
        value: props.value ?? "",
        onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) =>
          props.onChange?.(e.target.value),
      }),
  };
});

const dbProblem: CodingProblem = {
  id: "duplicate-emails",
  title: "Duplicate Emails",
  difficulty: "Easy",
  category: "Database",
  tags: ["sql", "group-by"],
  companies: [],
  description: "Find duplicate emails in the Person table.",
  constraints: "id is the primary key of Person",
  examples: [{ input: "Person: (1, a@b.com), (2, c@d.com), (3, a@b.com)", output: "[[a@b.com]]" }],
  starter_code: {
    sql: "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Person;\n",
  },
  sql_schema: ["CREATE TABLE Person (id INT PRIMARY KEY, email VARCHAR(255));"],
};

const codingProblem: CodingProblem = {
  id: "two-sum",
  title: "Two Sum",
  difficulty: "Easy",
  category: "Arrays & Hashing",
  tags: ["array", "hash-map"],
  companies: [],
  description: "Return indices of the two numbers that add up to target.",
  constraints: "2 <= nums.length <= 10^4",
  examples: [{ input: "nums = [2,7,11,15], target = 9", output: "[0, 1]" }],
  starter_code: {
    python: "def two_sum(nums: list[int], target: int) -> list[int]:\n    pass\n",
  },
};

// /coding/problems is metadata-only now, so the default practice list
// resolves to summaries and the sandbox fetches a problem's full detail by id
// when it is opened — exactly like a catalogue pick.
const dbSummary: CodingProblemSummary = {
  id: "duplicate-emails",
  title: "Duplicate Emails",
  difficulty: "Easy",
  category: "Database",
  tags: ["sql", "group-by"],
  companies: [],
  source: "curated",
};

const codingSummary: CodingProblemSummary = {
  id: "two-sum",
  title: "Two Sum",
  difficulty: "Easy",
  category: "Arrays & Hashing",
  tags: ["array", "hash-map"],
  companies: [],
  source: "curated",
};

// An imported competition statement (ids 2000+). The catalogue lists it as a
// summary; practice now lands on the first imported problem rather than the
// first hand-written entry, so the sandbox must open this one by default.
const importedSummary: CodingProblemSummary = {
  id: "2000",
  title: "K Friends",
  difficulty: "Medium",
  category: "Graphs",
  tags: [],
  companies: [],
  source: "imported",
};

const importedProblem: CodingProblem = {
  id: "2000",
  title: "K Friends",
  difficulty: "Medium",
  category: "Graphs",
  tags: [],
  companies: [],
  description:
    "There are n persons who initially don't know each other. On each morning, " +
    "two of them, who were not friends before, become friends.",
  constraints: "Time limit: 2 seconds\nMemory limit: 244 MB",
  examples: [{ input: "5 3 2\n1 2\n2 3", output: "3" }],
  starter_code: {
    python: "import sys\n\ndef main():\n    data = sys.stdin.read().split()\n    # Your code here\n",
  },
  grading: "stdio",
  hidden_test_count: 5,
};

// The default landing prefers the first *Easy* imported statement, falling back
// to Medium then Hard. The Medium fixture above pins the fallback; these two
// siblings pin the tier order itself.
const importedEasySummary: CodingProblemSummary = {
  id: "2001",
  title: "Sum of Two",
  difficulty: "Easy",
  category: "Math",
  tags: [],
  companies: [],
  source: "imported",
};

const importedEasyProblem: CodingProblem = {
  id: "2001",
  title: "Sum of Two",
  difficulty: "Easy",
  category: "Math",
  tags: [],
  companies: [],
  description: "Given two integers a and b, print their sum.",
  constraints: "Time limit: 2 seconds\nMemory limit: 244 MB",
  examples: [{ input: "2 3", output: "5" }],
  starter_code: {
    python: "import sys\n\ndef main():\n    data = sys.stdin.read().split()\n    # Your code here\n",
  },
  grading: "stdio",
  hidden_test_count: 5,
};

const importedHardSummary: CodingProblemSummary = {
  id: "2002",
  title: "Mountain Climb",
  difficulty: "Hard",
  category: "Graphs",
  tags: [],
  companies: [],
  source: "imported",
};

const importedHardProblem: CodingProblem = {
  id: "2002",
  title: "Mountain Climb",
  difficulty: "Hard",
  category: "Graphs",
  tags: [],
  companies: [],
  description: "Count the ways to climb the mountain under the constraints.",
  constraints: "Time limit: 3 seconds\nMemory limit: 512 MB",
  examples: [{ input: "3", output: "3" }],
  starter_code: {
    python: "import sys\n\ndef main():\n    data = sys.stdin.read().split()\n    # Your code here\n",
  },
  grading: "stdio",
  hidden_test_count: 5,
};

// The sandbox loads the list as summaries and fetches detail per problem on
// open, so every test wires both: the summaries it renders and the detail map
// its by-id fetches resolve against. An id with no detail rejects, exactly as
// a real 404 would.
// jest-dom's `toHaveValue` compares by strict equality, so asymmetric matchers
// (`expect.stringMatching`) never pass. Read the textarea value and assert on
// the plain string instead.
function editorValue(): string {
  return (screen.getByTestId("code-editor") as HTMLTextAreaElement).value;
}

function mockProblemFetch(
  summaries: CodingProblemSummary[],
  details: Record<string, CodingProblem>,
) {
  vi.mocked(fetchCodingProblems).mockResolvedValue(summaries);
  vi.mocked(fetchCodingProblem).mockImplementation((id: string) => {
    const detail = details[id];
    return detail
      ? Promise.resolve(detail)
      : Promise.reject(new Error(`unknown problem ${id}`));
  });
}

// A bank (1000-problem catalogue) database problem, ids 1001+. The catalogue
// lists it as a summary; the sandbox fetches the detail by id on pick.
const bankSummary: CodingProblemSummary = {
  id: "1001",
  title: "Big Countries",
  difficulty: "Easy",
  category: "Database",
  tags: ["sql", "select"],
  companies: [],
  source: "bank",
};

const bankProblem: CodingProblem = {
  id: "1001",
  title: "Big Countries",
  difficulty: "Easy",
  category: "Database",
  tags: ["sql", "select"],
  companies: [],
  description:
    "A country is big if its area is at least three million square kilometres " +
    "or its population is at least twenty-five million. Write a solution to " +
    "find the name, population, and area of the big countries.",
  constraints:
    "name is the primary key of World\narea is reported in square kilometres",
  examples: [
    {
      input: "World table with five countries",
      output: "[[Afghanistan, 25500100, 652230], [Algeria, 37100000, 2381741]]",
      diagram: {
        kind: "schema",
        tables: [
          {
            name: "World",
            columns: [
              { name: "name", type: "VARCHAR(255)", key: "PK" },
              { name: "continent", type: "VARCHAR(255)" },
              { name: "area", type: "INT" },
              { name: "population", type: "INT" },
            ],
            rows: [
              ["Afghanistan", "Asia", 652230, 25500100],
              ["Algeria", "Africa", 2381741, 37100000],
            ],
          },
        ],
      },
    },
  ],
  starter_code: {
    sql: "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    World;\n",
  },
  sql_schema: [
    "CREATE TABLE World (name VARCHAR(255) PRIMARY KEY, continent VARCHAR(255), area INT, population INT, gdp BIGINT);",
  ],
};

function renderSandbox() {
  return render(
    <MemoryRouter initialEntries={["/coding"]}>
      <CodeSandbox />
    </MemoryRouter>,
  );
}

describe("CodeSandbox SQL lock", () => {
  it("auto-selects SQL and restricts the language picker for a database problem", async () => {
    mockProblemFetch(
      [dbSummary, codingSummary],
      { "duplicate-emails": dbProblem, "two-sum": codingProblem },
    );

    renderSandbox();

    // The header <select> only exists after the curated problems load.
    const select = await screen.findByRole("combobox");
    await waitFor(() => expect(select).toHaveValue("sql"));

    // The picker is locked: SQL is the only offered language.
    const options = Array.from(select.querySelectorAll("option")).map((o) => o.value);
    expect(options).toEqual(["sql"]);
    expect(screen.getByText("SQL")).toBeInTheDocument();
    expect(screen.queryByText("Python 3")).not.toBeInTheDocument();

    // The editor opened with the problem's SQL starter, not a function template.
    expect(editorValue()).toMatch(/FROM\s+Person;/);
  });

  it("keeps the full language picker and Python default for a coding problem", async () => {
    mockProblemFetch(
      [codingSummary, dbSummary],
      { "duplicate-emails": dbProblem, "two-sum": codingProblem },
    );

    renderSandbox();

    const select = await screen.findByRole("combobox");
    await waitFor(() => expect(select).toHaveValue("python"));

    const options = Array.from(select.querySelectorAll("option")).map((o) => o.value);
    // All 14 function languages — SQL is only ever offered while a database
    // problem is open, so it must NOT appear for a coding problem.
    expect(options.length).toBe(14);
    expect(options).not.toContain("sql");
    expect(options).toContain("python");
    expect(screen.getByText("Python 3")).toBeInTheDocument();
    expect(screen.queryByText("SQL")).not.toBeInTheDocument();

    expect(editorValue()).toContain("def two_sum");
  });

  it("resets a database problem back to its SQL starter after the candidate edits", async () => {
    mockProblemFetch([dbSummary], { "duplicate-emails": dbProblem });

    renderSandbox();

    const select = await screen.findByRole("combobox");
    await waitFor(() => expect(select).toHaveValue("sql"));

    // Candidate overwrites the SQL starter with an arbitrary edit.
    const editor = screen.getByTestId("code-editor");
    fireEvent.change(editor, { target: { value: "SELECT nonsense;" } });
    expect(editor).toHaveValue("SELECT nonsense;");

    // Reset consults the effective language (SQL) and restores the starter.
    fireEvent.click(screen.getByTitle("Reset code to starter template"));
    await waitFor(() => expect(editorValue()).toMatch(/FROM\s+Person;/));
    expect(editorValue()).not.toContain("nonsense");
    expect(editorValue()).not.toContain("def ");
  });

  it("locks a bank database problem to SQL and renders its schema diagram after picking it from the catalogue", async () => {
    // The default practice list resolves to summaries; the sandbox fetches
    // detail by id on open (the default first problem here) and on each pick.
    mockProblemFetch(
      [codingSummary],
      { "two-sum": codingProblem, "1001": bankProblem },
    );
    // The catalogue is server-paged: the bank problem appears in the listing
    // but is not part of the curated set, so picking it must fetch by id.
    vi.mocked(fetchCodingCatalog).mockResolvedValue({
      problems: [bankSummary],
      total: 1,
      offset: 0,
      limit: 100,
      topics: [],
    });

    renderSandbox();

    // Practice mode — open the All Problems browser. The button only exists
    // once the sandbox has left its initial loading screen.
    fireEvent.click(await screen.findByTitle("Browse every problem"));

    // The catalogue loads (debounced server call) and lists the bank problem.
    const row = await screen.findByText("Big Countries");
    fireEvent.click(row);

    // Picking it fetches the detail and selects it — the sandbox must then
    // lock the language to SQL exactly like a curated database problem.
    await waitFor(() => expect(screen.getByRole("combobox")).toHaveValue("sql"));

    const select = screen.getByRole("combobox");
    const options = Array.from(select.querySelectorAll("option")).map((o) => o.value);
    expect(options).toEqual(["sql"]);

    // The selected problem is the bank one, not a silently ignored pick.
    // Header and statement pane both show the title once it is active.
    expect(screen.getAllByText("Big Countries").length).toBeGreaterThan(0);

    // The first example carries the schema figure: the World table card with
    // its PK badge and the seeded rows the query runs against.
    expect(screen.getByText("World")).toBeInTheDocument();
    expect(screen.getByText("PK")).toBeInTheDocument();
    expect(screen.getAllByText("Afghanistan").length).toBeGreaterThan(0);

    // The editor opened with the bank problem's SQL starter.
    expect(editorValue()).toMatch(/FROM\s+World;/);
  });

  it("auto-selects SQL for a bank database problem picked from the All Problems catalog", async () => {
    mockProblemFetch(
      [codingSummary],
      { "two-sum": codingProblem, "1001": bankProblem },
    );
    vi.mocked(fetchCodingCatalog).mockResolvedValue({
      problems: [bankSummary],
      total: 1,
      offset: 0,
      limit: 100,
      topics: [],
    });

    renderSandbox();

    // Practice mode — open the All Problems browser (rendered after load).
    fireEvent.click(await screen.findByTitle("Browse every problem"));

    // The catalogue loads (debounced server call) and lists the bank problem.
    const row = await screen.findByText("Big Countries");
    fireEvent.click(row);

    // Picking id 1001 fetches the detail (it is not in the curated set) and
    // selects it — the sql_schema guard must lock the language to SQL exactly
    // as for a curated database problem, with no other language offered.
    await waitFor(() => expect(screen.getByRole("combobox")).toHaveValue("sql"));

    const select = screen.getByRole("combobox");
    const options = Array.from(select.querySelectorAll("option")).map((o) => o.value);
    expect(options).toEqual(["sql"]);
    expect(screen.queryByText("Python 3")).not.toBeInTheDocument();

    // The bank problem, not a silently ignored pick, is now on screen.
    // Header and statement pane both show the title once it is active.
    expect(screen.getAllByText("Big Countries").length).toBeGreaterThan(0);

    // The editor opened with the bank problem's SQL starter.
    expect(editorValue()).toMatch(/FROM\s+World;/);
  });

  it("keeps ScreenRecordGuard mounted when a bank problem is picked from the catalogue", async () => {
    mockProblemFetch(
      [codingSummary],
      { "two-sum": codingProblem, "1001": bankProblem },
    );
    vi.mocked(fetchCodingCatalog).mockResolvedValue({
      problems: [bankSummary],
      total: 1,
      offset: 0,
      limit: 100,
      topics: [],
    });

    // The counter is shared across tests in this file, so snapshot the current
    // value and assert the delta rather than an absolute number.
    const mountsAtStart = guardMountCount.value;

    renderSandbox();

    // The sandbox leaves its initial loading screen once the curated set
    // loads; the guard mounts exactly once at that point.
    await screen.findByRole("combobox");
    await waitFor(() => expect(guardMountCount.value).toBe(mountsAtStart + 1));

    // Picking a bank problem used to flip the full-screen `loading` branch,
    // which unmounted the guard — tearing down the recorder so the browser
    // re-asked to share the screen the moment the sandbox remounted it. The
    // pick must leave the mounted guard untouched (still exactly one mount).
    fireEvent.click(screen.getByTitle("Browse every problem"));
    const row = await screen.findByText("Big Countries");
    fireEvent.click(row);

    await waitFor(() => expect(screen.getByRole("combobox")).toHaveValue("sql"));
    expect(guardMountCount.value).toBe(mountsAtStart + 1);

    // The guard is the real mounted component, not the old null stub.
    expect(screen.getByTestId("screen-record-guard")).toBeInTheDocument();
  });

  it("lands on the first imported problem by default, not the first curated one", async () => {
    // The catalogue lists curated first, so summaries[0] is the hand-written
    // Two Sum — but practice must open the imported statement, not it.
    mockProblemFetch(
      [codingSummary, importedSummary],
      { "two-sum": codingProblem, "2000": importedProblem },
    );

    renderSandbox();

    // The header and statement pane both render the active problem's title;
    // the imported statement is what opened, and Two Sum never did.
    const titles = await screen.findAllByText("K Friends");
    expect(titles.length).toBeGreaterThan(0);
    expect(screen.queryByText("Two Sum")).not.toBeInTheDocument();

    // A stdio problem is graded in every language — interpreted ones through
    // the in-sandbox driver, compiled ones natively — so the picker is NOT
    // narrowed; only the starter differs. SQL is still never offered.
    const select = await screen.findByRole("combobox");
    await waitFor(() => expect(select).toHaveValue("python"));
    const options = Array.from(select.querySelectorAll("option")).map((o) => o.value);
    expect(options.length).toBe(14);
    expect(options).toContain("python");
    expect(options).toContain("ruby");
    expect(options).toContain("cpp");
    expect(options).not.toContain("sql");

    // The editor opened with the imported problem's Python stdin starter, not
    // a function-shaped template — the whole-program grading path.
    expect(editorValue()).toContain("import sys");
    expect(editorValue()).not.toContain("def two_sum");
  });

  it("prefers the first Easy imported problem as the default landing", async () => {
    // Easy beats Medium and Hard no matter where it sits in the list: the
    // catalogue lists curated first and the hard statement before the easy
    // one, but practice must open the approachable statement.
    mockProblemFetch(
      [codingSummary, importedHardSummary, importedSummary, importedEasySummary],
      {
        "two-sum": codingProblem,
        "2002": importedHardProblem,
        "2000": importedProblem,
        "2001": importedEasyProblem,
      },
    );

    renderSandbox();

    const titles = await screen.findAllByText("Sum of Two");
    expect(titles.length).toBeGreaterThan(0);
    expect(screen.queryByText("K Friends")).not.toBeInTheDocument();
    expect(screen.queryByText("Mountain Climb")).not.toBeInTheDocument();
    expect(screen.queryByText("Two Sum")).not.toBeInTheDocument();
  });

  it("falls back to the first Medium imported problem when no Easy exists", async () => {
    // Only Hard and Medium are imported: the Medium statement wins even though
    // the Hard one precedes it in the list.
    mockProblemFetch(
      [codingSummary, importedHardSummary, importedSummary],
      {
        "two-sum": codingProblem,
        "2002": importedHardProblem,
        "2000": importedProblem,
      },
    );

    renderSandbox();

    const titles = await screen.findAllByText("K Friends");
    expect(titles.length).toBeGreaterThan(0);
    expect(screen.queryByText("Mountain Climb")).not.toBeInTheDocument();
    expect(screen.queryByText("Two Sum")).not.toBeInTheDocument();
  });

  it("lands on an imported Hard problem rather than the curated first entry", async () => {
    // The corpus here is all-Hard imported: it still wins over the hand-written
    // Two Sum that leads the catalogue, so practice never falls back to curated.
    mockProblemFetch(
      [codingSummary, importedHardSummary],
      { "two-sum": codingProblem, "2002": importedHardProblem },
    );

    renderSandbox();

    const titles = await screen.findAllByText("Mountain Climb");
    expect(titles.length).toBeGreaterThan(0);
    expect(screen.queryByText("Two Sum")).not.toBeInTheDocument();
  });
});
