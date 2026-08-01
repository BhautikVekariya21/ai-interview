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
vi.mock("@/components/ScreenRecordGuard", () => ({
  default: () => {
    guardMountCount.value += 1;
    return <div data-testid="screen-record-guard" />;
  },
}));

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
    vi.mocked(fetchCodingProblems).mockResolvedValue([dbProblem, codingProblem]);

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
    const editor = screen.getByTestId("code-editor");
    expect(editor).toHaveValue(expect.stringMatching(/FROM\s+Person;/));
  });

  it("keeps the full language picker and Python default for a coding problem", async () => {
    vi.mocked(fetchCodingProblems).mockResolvedValue([codingProblem, dbProblem]);

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

    const editor = screen.getByTestId("code-editor");
    expect(editor).toHaveValue(expect.stringContaining("def two_sum"));
  });

  it("resets a database problem back to its SQL starter after the candidate edits", async () => {
    vi.mocked(fetchCodingProblems).mockResolvedValue([dbProblem]);

    renderSandbox();

    const select = await screen.findByRole("combobox");
    await waitFor(() => expect(select).toHaveValue("sql"));

    // Candidate overwrites the SQL starter with an arbitrary edit.
    const editor = screen.getByTestId("code-editor");
    fireEvent.change(editor, { target: { value: "SELECT nonsense;" } });
    expect(editor).toHaveValue("SELECT nonsense;");

    // Reset consults the effective language (SQL) and restores the starter.
    fireEvent.click(screen.getByTitle("Reset code to starter template"));
    await waitFor(() =>
      expect(editor).toHaveValue(expect.stringMatching(/FROM\s+Person;/)),
    );
    expect(editor).not.toHaveValue(expect.stringContaining("nonsense"));
    expect(editor).not.toHaveValue(expect.stringContaining("def "));
  });

  it("locks a bank database problem to SQL and renders its schema diagram after picking it from the catalogue", async () => {
    vi.mocked(fetchCodingProblems).mockResolvedValue([codingProblem]);
    // The catalogue is server-paged: the bank problem appears in the listing
    // but is not part of the curated set, so picking it must fetch by id.
    vi.mocked(fetchCodingCatalog).mockResolvedValue({
      problems: [bankSummary],
      total: 1,
      offset: 0,
      limit: 100,
      topics: [],
    });
    vi.mocked(fetchCodingProblem).mockResolvedValue(bankProblem);

    renderSandbox();

    // Practice mode — open the All Problems browser.
    fireEvent.click(screen.getByTitle("Browse every problem"));

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
    expect(screen.getByText("Big Countries")).toBeInTheDocument();

    // The first example carries the schema figure: the World table card with
    // its PK badge and the seeded rows the query runs against.
    expect(screen.getByText("World")).toBeInTheDocument();
    expect(screen.getByText("PK")).toBeInTheDocument();
    expect(screen.getAllByText("Afghanistan").length).toBeGreaterThan(0);

    // The editor opened with the bank problem's SQL starter.
    const editor = screen.getByTestId("code-editor");
    expect(editor).toHaveValue(expect.stringMatching(/FROM\s+World;/));
  });

  it("auto-selects SQL for a bank database problem picked from the All Problems catalog", async () => {
    vi.mocked(fetchCodingProblems).mockResolvedValue([codingProblem]);
    vi.mocked(fetchCodingCatalog).mockResolvedValue({
      problems: [bankSummary],
      total: 1,
      offset: 0,
      limit: 100,
      topics: [],
    });
    vi.mocked(fetchCodingProblem).mockResolvedValue(bankProblem);

    renderSandbox();

    // Practice mode — open the All Problems browser.
    fireEvent.click(screen.getByTitle("Browse every problem"));

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
    expect(screen.getByText("Big Countries")).toBeInTheDocument();

    // The editor opened with the bank problem's SQL starter.
    const editor = screen.getByTestId("code-editor");
    expect(editor).toHaveValue(expect.stringMatching(/FROM\s+World;/));
  });

  it("keeps ScreenRecordGuard mounted when a bank problem is picked from the catalogue", async () => {
    vi.mocked(fetchCodingProblems).mockResolvedValue([codingProblem]);
    vi.mocked(fetchCodingCatalog).mockResolvedValue({
      problems: [bankSummary],
      total: 1,
      offset: 0,
      limit: 100,
      topics: [],
    });
    vi.mocked(fetchCodingProblem).mockResolvedValue(bankProblem);

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
});
