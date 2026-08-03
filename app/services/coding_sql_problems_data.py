"""
Coding SQL Problems Data — database problems for the 1000-problem bank.

The generated bank (``coding_problems_data.py``) is built entirely from
function-language base problems. This module is the SQL coverage layer: a
hand-authored set of database problems, each graded by running the candidate's
query against an in-memory SQLite database built from ``sql_schema``, seeded
per test case with ``test_cases[].seed``, and compared as sorted row sets
against ``test_cases[].expected`` — exactly the contract the curated database
problems follow (see ``code_executor_service.CURATED_PROBLEMS``).

The entries carry both field conventions on purpose:

* the raw-bank camelCase fields (``testCases``, ``starterCode``,
  ``solutionCode``, ``companiesAsked``, …) so the bank integrity checks and
  the generator's shape expectations hold for every problem in the list, and
* the graded SQL fields (``sql_schema``, ``test_cases``, ``starter_code.sql``,
  ``solution_sql``) so the executor's SQL branch, the schema-figure builder,
  and ``problem_enrichment`` (which pops ``solution_sql`` before serving) can
  all consume the problem unchanged.

The ids (1001–1018) sit above the generated 1–1000 range, so regenerating the
bank never collides with them. ``code_executor_service`` merges this list into
the bank at import time; ``scratch/generate_1000_problems.py`` preserves it
when the bank is regenerated.
"""

from __future__ import annotations

SQL_PROBLEMS: list[dict] = [
    {
        "id": 1001,
        "title": "Big Countries",
        "difficulty": "Easy",
        "topic": "Database",
        "tags": ["sql", "select"],
        "companiesAsked": ["Amazon", "Google"],
        "description": (
            "A country is big if it has an area of at least three million "
            "square kilometres, or a population of at least twenty-five "
            "million. Write a solution to find the name, population, and area "
            "of the big countries. Return the result table in **any order**.\n\n"
            "The `World` table records every country with its continent, area "
            "in square kilometres, population, and gross domestic product."
        ),
        "constraints": (
            "name is the primary key of World\n"
            "area is reported in square kilometres\n"
            "population is reported in whole people"
        ),
        "follow_up": None,
        "hints": [
            "Both thresholds are inclusive: area >= 3,000,000 or population >= 25,000,000.",
            "A plain WHERE with OR handles a country that meets only one of the two bars.",
        ],
        "timeComplexity": "O(n)",
        "spaceComplexity": "O(1)",
        "sql_schema": [
            "CREATE TABLE World (name VARCHAR(255) PRIMARY KEY, continent VARCHAR(255), area INT, population INT, gdp BIGINT);",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    World;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    World;\n"
            ),
        },
        "solution_sql": (
            "SELECT name, population, area FROM World\n"
            "WHERE area >= 3000000 OR population >= 25000000;\n"
        ),
        "solutionCode": (
            "SELECT name, population, area FROM World\n"
            "WHERE area >= 3000000 OR population >= 25000000;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO World (name, continent, area, population, gdp) VALUES ('Afghanistan', 'Asia', 652230, 25500100, 20343000000);",
                    "INSERT INTO World (name, continent, area, population, gdp) VALUES ('Albania', 'Europe', 28748, 2831741, 12960000000);",
                    "INSERT INTO World (name, continent, area, population, gdp) VALUES ('Algeria', 'Africa', 2381741, 37100000, 188681000000);",
                    "INSERT INTO World (name, continent, area, population, gdp) VALUES ('Andorra', 'Europe', 468, 78115, 3712000000);",
                    "INSERT INTO World (name, continent, area, population, gdp) VALUES ('Angola', 'Africa', 1246700, 20609294, 100990000000);",
                ],
                "expected": [
                    ["Afghanistan", 25500100, 652230],
                    ["Algeria", 37100000, 2381741],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO World (name, continent, area, population, gdp) VALUES ('Afghanistan', 'Asia', 652230, 25500100, 20343000000);",
                    "INSERT INTO World (name, continent, area, population, gdp) VALUES ('Albania', 'Europe', 28748, 2831741, 12960000000);",
                    "INSERT INTO World (name, continent, area, population, gdp) VALUES ('Algeria', 'Africa', 2381741, 37100000, 188681000000);",
                    "INSERT INTO World (name, continent, area, population, gdp) VALUES ('Andorra', 'Europe', 468, 78115, 3712000000);",
                    "INSERT INTO World (name, continent, area, population, gdp) VALUES ('Angola', 'Africa', 1246700, 20609294, 100990000000);",
                ],
                "expected": [
                    ["Afghanistan", 25500100, 652230],
                    ["Algeria", 37100000, 2381741],
                ],
            },
        ],
    },
    {
        "id": 1002,
        "title": "Employee Bonus",
        "difficulty": "Easy",
        "topic": "Database",
        "tags": ["sql", "left-join"],
        "companiesAsked": ["Amazon", "Bloomberg"],
        "description": (
            "Write a solution to report the name and bonus amount of each "
            "employee with a bonus of **less than 1000**. Employees whose "
            "bonus is missing entirely must also be listed, with `null` as "
            "their bonus — they never reached the threshold.\n\n"
            "A `LEFT JOIN` from `Employee` to `Bonus` keeps every employee "
            "even when no bonus record exists; the `null` bonus then has to "
            "pass the filter instead of being dropped by it."
        ),
        "constraints": (
            "empId is the primary key of Employee and of Bonus\n"
            "Every employee has exactly one bonus record or none at all"
        ),
        "follow_up": None,
        "hints": [
            "LEFT JOIN Bonus on empId so an employee with no bonus row still appears.",
            "The filter is bonus < 1000 OR bonus IS NULL — a WHERE-only '< 1000' would drop the nulls.",
        ],
        "timeComplexity": "O(n)",
        "spaceComplexity": "O(1)",
        "sql_schema": [
            "CREATE TABLE Employee (empId INT PRIMARY KEY, name VARCHAR(255), supervisor INT, salary INT);",
            "CREATE TABLE Bonus (empId INT PRIMARY KEY, bonus INT);",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Employee;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Employee;\n"
            ),
        },
        "solution_sql": (
            "SELECT e.name, b.bonus\n"
            "FROM Employee e\n"
            "LEFT JOIN Bonus b ON e.empId = b.empId\n"
            "WHERE b.bonus < 1000 OR b.bonus IS NULL;\n"
        ),
        "solutionCode": (
            "SELECT e.name, b.bonus\n"
            "FROM Employee e\n"
            "LEFT JOIN Bonus b ON e.empId = b.empId\n"
            "WHERE b.bonus < 1000 OR b.bonus IS NULL;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Employee (empId, name, supervisor, salary) VALUES (1, 'John', 3, 1000);",
                    "INSERT INTO Employee (empId, name, supervisor, salary) VALUES (2, 'Dan', 3, 2000);",
                    "INSERT INTO Employee (empId, name, supervisor, salary) VALUES (3, 'Brad', NULL, 4000);",
                    "INSERT INTO Employee (empId, name, supervisor, salary) VALUES (4, 'Thomas', 3, 4000);",
                    "INSERT INTO Bonus (empId, bonus) VALUES (2, 500);",
                    "INSERT INTO Bonus (empId, bonus) VALUES (4, 2000);",
                ],
                "expected": [
                    ["John", None],
                    ["Dan", 500],
                    ["Brad", None],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Employee (empId, name, supervisor, salary) VALUES (1, 'John', 3, 1000);",
                    "INSERT INTO Employee (empId, name, supervisor, salary) VALUES (2, 'Dan', 3, 2000);",
                    "INSERT INTO Employee (empId, name, supervisor, salary) VALUES (3, 'Brad', NULL, 4000);",
                    "INSERT INTO Employee (empId, name, supervisor, salary) VALUES (4, 'Thomas', 3, 4000);",
                    "INSERT INTO Bonus (empId, bonus) VALUES (2, 500);",
                    "INSERT INTO Bonus (empId, bonus) VALUES (4, 2000);",
                ],
                "expected": [
                    ["John", None],
                    ["Dan", 500],
                    ["Brad", None],
                ],
            },
        ],
    },
    {
        "id": 1003,
        "title": "Product Sales Analysis I",
        "difficulty": "Easy",
        "topic": "Database",
        "tags": ["sql", "join"],
        "companiesAsked": ["Amazon", "Microsoft"],
        "description": (
            "Write a solution to report the `product_name`, `year`, and "
            "`price` for each sale. Return the result table in **any order**.\n\n"
            "A product can appear in many sales, and a sale always references a "
            "product that exists — this is an inner join, not a `LEFT JOIN`, "
            "because there is nothing to preserve on the unmatched side."
        ),
        "constraints": (
            "(sale_id, year) is the primary key of Sales\n"
            "product_id is the primary key of Product\n"
            "price is the unit price, never the line total"
        ),
        "follow_up": None,
        "hints": [
            "Join Sales to Product on product_id to bring the name across.",
            "The columns to emit are product_name, year, and price — in that order.",
        ],
        "timeComplexity": "O(n)",
        "spaceComplexity": "O(1)",
        "sql_schema": [
            "CREATE TABLE Sales (sale_id INT, product_id INT, year INT, quantity INT, price INT);",
            "CREATE TABLE Product (product_id INT PRIMARY KEY, product_name VARCHAR(255));",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Sales;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Sales;\n"
            ),
        },
        "solution_sql": (
            "SELECT p.product_name, s.year, s.price\n"
            "FROM Sales s\n"
            "JOIN Product p ON s.product_id = p.product_id;\n"
        ),
        "solutionCode": (
            "SELECT p.product_name, s.year, s.price\n"
            "FROM Sales s\n"
            "JOIN Product p ON s.product_id = p.product_id;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Sales (sale_id, product_id, year, quantity, price) VALUES (1, 100, 2008, 10, 5000);",
                    "INSERT INTO Sales (sale_id, product_id, year, quantity, price) VALUES (2, 100, 2009, 12, 5000);",
                    "INSERT INTO Sales (sale_id, product_id, year, quantity, price) VALUES (7, 200, 2011, 15, 9000);",
                    "INSERT INTO Product (product_id, product_name) VALUES (100, 'Nokia');",
                    "INSERT INTO Product (product_id, product_name) VALUES (200, 'Apple');",
                ],
                "expected": [
                    ["Nokia", 2008, 5000],
                    ["Nokia", 2009, 5000],
                    ["Apple", 2011, 9000],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Sales (sale_id, product_id, year, quantity, price) VALUES (1, 100, 2008, 10, 5000);",
                    "INSERT INTO Sales (sale_id, product_id, year, quantity, price) VALUES (2, 100, 2009, 12, 5000);",
                    "INSERT INTO Sales (sale_id, product_id, year, quantity, price) VALUES (7, 200, 2011, 15, 9000);",
                    "INSERT INTO Product (product_id, product_name) VALUES (100, 'Nokia');",
                    "INSERT INTO Product (product_id, product_name) VALUES (200, 'Apple');",
                ],
                "expected": [
                    ["Nokia", 2008, 5000],
                    ["Nokia", 2009, 5000],
                    ["Apple", 2011, 9000],
                ],
            },
        ],
    },
    {
        "id": 1004,
        "title": "Managers with at Least 5 Direct Reports",
        "difficulty": "Medium",
        "topic": "Database",
        "tags": ["sql", "group-by", "self-join"],
        "companiesAsked": ["Google", "Amazon"],
        "description": (
            "Write a solution to find the managers with **at least five "
            "direct reports**. Return the result table in **any order**.\n\n"
            "The `managerId` column references the `id` of another row in the "
            "same table — an employee is a manager exactly when other rows "
            "point at them. Counting those pointers per person is the whole "
            "problem; no second table is involved."
        ),
        "constraints": (
            "id is the primary key of Employee\n"
            "managerId references Employee.id and is null for the head of the chain"
        ),
        "follow_up": None,
        "hints": [
            "Self-join Employee to itself on id = managerId so each report pairs with its manager.",
            "GROUP BY the manager and keep only groups whose COUNT(*) is at least 5.",
        ],
        "timeComplexity": "O(n)",
        "spaceComplexity": "O(1)",
        "sql_schema": [
            "CREATE TABLE Employee (id INT PRIMARY KEY, name VARCHAR(255), department VARCHAR(255), managerId INT);",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Employee;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Employee;\n"
            ),
        },
        "solution_sql": (
            "SELECT e1.name\n"
            "FROM Employee e1\n"
            "JOIN Employee e2 ON e1.id = e2.managerId\n"
            "GROUP BY e1.id, e1.name\n"
            "HAVING COUNT(*) >= 5;\n"
        ),
        "solutionCode": (
            "SELECT e1.name\n"
            "FROM Employee e1\n"
            "JOIN Employee e2 ON e1.id = e2.managerId\n"
            "GROUP BY e1.id, e1.name\n"
            "HAVING COUNT(*) >= 5;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (101, 'John', 'A', NULL);",
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (102, 'Dan', 'A', 101);",
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (103, 'James', 'A', 101);",
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (104, 'Amy', 'A', 101);",
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (105, 'Anne', 'A', 101);",
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (106, 'Ron', 'B', 101);",
                ],
                "expected": [["John"]],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (101, 'John', 'A', NULL);",
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (102, 'Dan', 'A', 101);",
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (103, 'James', 'A', 101);",
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (104, 'Amy', 'A', 101);",
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (105, 'Anne', 'A', 101);",
                    "INSERT INTO Employee (id, name, department, managerId) VALUES (106, 'Ron', 'B', 101);",
                ],
                "expected": [["John"]],
            },
        ],
    },
    {
        "id": 1005,
        "title": "Department Highest Salary",
        "difficulty": "Medium",
        "topic": "Database",
        "tags": ["sql", "join", "aggregation"],
        "companiesAsked": ["Meta", "Amazon", "Google"],
        "description": (
            "Write a solution to find employees who have the **highest "
            "salary in each of the departments**. Return the result table in "
            "**any order**.\n\n"
            "Every department must contribute its top earner, and a tie for "
            "first place means several employees from the same department all "
            "qualify — the answer is the set of people whose salary equals "
            "their department's maximum, not a single row per department."
        ),
        "constraints": (
            "id is the primary key of Employee\n"
            "departmentId is a foreign key referencing Department.id"
        ),
        "follow_up": None,
        "hints": [
            "Find each department's MAX(salary), then keep every employee whose salary equals it.",
            "A row-value IN — (departmentId, salary) IN (SELECT departmentId, MAX(salary) …) — is the cleanest way to express the tie.",
        ],
        "timeComplexity": "O(n log n)",
        "spaceComplexity": "O(1)",
        "sql_schema": [
            "CREATE TABLE Employee (id INT PRIMARY KEY, name VARCHAR(255), salary INT, departmentId INT);",
            "CREATE TABLE Department (id INT PRIMARY KEY, name VARCHAR(255));",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Employee;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Employee;\n"
            ),
        },
        "solution_sql": (
            "SELECT d.name AS Department, e.name AS Employee, e.salary AS Salary\n"
            "FROM Employee e\n"
            "JOIN Department d ON e.departmentId = d.id\n"
            "WHERE (e.departmentId, e.salary) IN (\n"
            "    SELECT departmentId, MAX(salary) FROM Employee GROUP BY departmentId\n"
            ");\n"
        ),
        "solutionCode": (
            "SELECT d.name AS Department, e.name AS Employee, e.salary AS Salary\n"
            "FROM Employee e\n"
            "JOIN Department d ON e.departmentId = d.id\n"
            "WHERE (e.departmentId, e.salary) IN (\n"
            "    SELECT departmentId, MAX(salary) FROM Employee GROUP BY departmentId\n"
            ");\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (1, 'Joe', 70000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (2, 'Jim', 90000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (3, 'Henry', 80000, 2);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (4, 'Sam', 60000, 2);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (5, 'Max', 90000, 1);",
                    "INSERT INTO Department (id, name) VALUES (1, 'IT');",
                    "INSERT INTO Department (id, name) VALUES (2, 'Sales');",
                ],
                "expected": [
                    ["IT", "Jim", 90000],
                    ["IT", "Max", 90000],
                    ["Sales", "Henry", 80000],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (1, 'Joe', 70000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (2, 'Jim', 90000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (3, 'Henry', 80000, 2);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (4, 'Sam', 60000, 2);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (5, 'Max', 90000, 1);",
                    "INSERT INTO Department (id, name) VALUES (1, 'IT');",
                    "INSERT INTO Department (id, name) VALUES (2, 'Sales');",
                ],
                "expected": [
                    ["IT", "Jim", 90000],
                    ["IT", "Max", 90000],
                    ["Sales", "Henry", 80000],
                ],
            },
        ],
    },
    {
        "id": 1006,
        "title": "Average Time of Process per Machine",
        "difficulty": "Medium",
        "topic": "Database",
        "tags": ["sql", "self-join"],
        "companiesAsked": ["Google", "Amazon"],
        "description": (
            "There is a factory website with several machines, each running "
            "the same number of processes. Write a solution to find the "
            "**average time each machine takes to complete a process**, "
            "rounded to 3 decimal places, as `processing_time`. Return the "
            "result table in **any order**.\n\n"
            "Each process has a `'start'` and an `'end'` activity on the same "
            "machine; the time a machine takes for a process is `end - start`. "
            "A machine's processing time is the average over all of its "
            "processes."
        ),
        "constraints": (
            "(machine_id, process_id, activity_type) is the primary key of Activity\n"
            "Every process has exactly one 'start' and one 'end' activity"
        ),
        "follow_up": None,
        "hints": [
            "Self-join Activity so one row pairs a process's 'start' with its 'end' — match on machine_id AND process_id.",
            "Average the per-process end - start differences and ROUND to 3 decimals.",
        ],
        "timeComplexity": "O(n)",
        "spaceComplexity": "O(1)",
        "sql_schema": [
            "CREATE TABLE Activity (machine_id INT, process_id INT, activity_type VARCHAR(20), timestamp FLOAT, PRIMARY KEY (machine_id, process_id, activity_type));",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Activity;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Activity;\n"
            ),
        },
        "solution_sql": (
            "SELECT a1.machine_id,\n"
            "       ROUND(AVG(a2.timestamp - a1.timestamp), 3) AS processing_time\n"
            "FROM Activity a1\n"
            "JOIN Activity a2\n"
            "  ON a1.machine_id = a2.machine_id\n"
            " AND a1.process_id = a2.process_id\n"
            " AND a1.activity_type = 'start'\n"
            " AND a2.activity_type = 'end'\n"
            "GROUP BY a1.machine_id;\n"
        ),
        "solutionCode": (
            "SELECT a1.machine_id,\n"
            "       ROUND(AVG(a2.timestamp - a1.timestamp), 3) AS processing_time\n"
            "FROM Activity a1\n"
            "JOIN Activity a2\n"
            "  ON a1.machine_id = a2.machine_id\n"
            " AND a1.process_id = a2.process_id\n"
            " AND a1.activity_type = 'start'\n"
            " AND a2.activity_type = 'end'\n"
            "GROUP BY a1.machine_id;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (0, 0, 'start', 0.712);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (0, 0, 'end', 1.520);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (0, 1, 'start', 3.140);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (0, 1, 'end', 4.120);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (1, 0, 'start', 0.550);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (1, 0, 'end', 1.550);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (1, 1, 'start', 0.430);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (1, 1, 'end', 1.420);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (2, 0, 'start', 4.100);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (2, 0, 'end', 4.512);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (2, 1, 'start', 2.500);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (2, 1, 'end', 5.000);",
                ],
                "expected": [
                    [0, 0.894],
                    [1, 0.995],
                    [2, 1.456],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (0, 0, 'start', 0.712);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (0, 0, 'end', 1.520);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (0, 1, 'start', 3.140);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (0, 1, 'end', 4.120);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (1, 0, 'start', 0.550);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (1, 0, 'end', 1.550);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (1, 1, 'start', 0.430);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (1, 1, 'end', 1.420);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (2, 0, 'start', 4.100);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (2, 0, 'end', 4.512);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (2, 1, 'start', 2.500);",
                    "INSERT INTO Activity (machine_id, process_id, activity_type, timestamp) VALUES (2, 1, 'end', 5.000);",
                ],
                "expected": [
                    [0, 0.894],
                    [1, 0.995],
                    [2, 1.456],
                ],
            },
        ],
    },
    {
        "id": 1007,
        "title": "Friend Requests II: Who Has the Most Friends",
        "difficulty": "Medium",
        "topic": "Database",
        "tags": ["sql", "union-all", "group-by"],
        "companiesAsked": ["Facebook", "Google"],
        "description": (
            "Write a solution to find the people who have the **most friends** "
            "and the most friends number. Return the result table with one row: "
            "the `id` of the person with the most friends and their friend "
            "count.\n\n"
            "A friendship exists when a `RequestAccepted` row pairs a "
            "`requester_id` with an `accepter_id`. Being on either side of a "
            "pair counts as a friendship, so the two columns are unioned into "
            "one id list before counting."
        ),
        "constraints": (
            "(requester_id, accepter_id) is the primary key of RequestAccepted\n"
            "A person can appear as both requester and accepter across rows"
        ),
        "follow_up": None,
        "hints": [
            "UNION ALL the requester_id and accepter_id columns into a single id column — UNION (not UNION ALL) would merge away a person's own pairs.",
            "GROUP BY id and ORDER BY the count descending with LIMIT 1 to keep the single most-friended person.",
        ],
        "timeComplexity": "O(n)",
        "spaceComplexity": "O(n)",
        "sql_schema": [
            "CREATE TABLE RequestAccepted (requester_id INT, accepter_id INT, accept_date DATE, PRIMARY KEY (requester_id, accepter_id));",
            "CREATE TABLE FriendRequest (sender_id INT, send_to_id INT, request_date DATE, PRIMARY KEY (sender_id, send_to_id));",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    RequestAccepted;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    RequestAccepted;\n"
            ),
        },
        "solution_sql": (
            "SELECT id, COUNT(*) AS num\n"
            "FROM (\n"
            "    SELECT requester_id AS id FROM RequestAccepted\n"
            "    UNION ALL\n"
            "    SELECT accepter_id FROM RequestAccepted\n"
            ") t\n"
            "GROUP BY id\n"
            "ORDER BY num DESC\n"
            "LIMIT 1;\n"
        ),
        "solutionCode": (
            "SELECT id, COUNT(*) AS num\n"
            "FROM (\n"
            "    SELECT requester_id AS id FROM RequestAccepted\n"
            "    UNION ALL\n"
            "    SELECT accepter_id FROM RequestAccepted\n"
            ") t\n"
            "GROUP BY id\n"
            "ORDER BY num DESC\n"
            "LIMIT 1;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO RequestAccepted (requester_id, accepter_id, accept_date) VALUES (1, 2, '2016-06-03');",
                    "INSERT INTO RequestAccepted (requester_id, accepter_id, accept_date) VALUES (1, 3, '2016-06-08');",
                    "INSERT INTO RequestAccepted (requester_id, accepter_id, accept_date) VALUES (2, 3, '2016-06-08');",
                    "INSERT INTO RequestAccepted (requester_id, accepter_id, accept_date) VALUES (3, 4, '2016-06-09');",
                    "INSERT INTO FriendRequest (sender_id, send_to_id, request_date) VALUES (1, 2, '2016-06-01');",
                    "INSERT INTO FriendRequest (sender_id, send_to_id, request_date) VALUES (1, 3, '2016-06-01');",
                    "INSERT INTO FriendRequest (sender_id, send_to_id, request_date) VALUES (1, 4, '2016-06-01');",
                    "INSERT INTO FriendRequest (sender_id, send_to_id, request_date) VALUES (2, 3, '2016-06-02');",
                    "INSERT INTO FriendRequest (sender_id, send_to_id, request_date) VALUES (3, 4, '2016-06-09');",
                ],
                "expected": [[3, 3]],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO RequestAccepted (requester_id, accepter_id, accept_date) VALUES (1, 2, '2016-06-03');",
                    "INSERT INTO RequestAccepted (requester_id, accepter_id, accept_date) VALUES (1, 3, '2016-06-08');",
                    "INSERT INTO RequestAccepted (requester_id, accepter_id, accept_date) VALUES (2, 3, '2016-06-08');",
                    "INSERT INTO RequestAccepted (requester_id, accepter_id, accept_date) VALUES (3, 4, '2016-06-09');",
                    "INSERT INTO FriendRequest (sender_id, send_to_id, request_date) VALUES (1, 2, '2016-06-01');",
                    "INSERT INTO FriendRequest (sender_id, send_to_id, request_date) VALUES (1, 3, '2016-06-01');",
                    "INSERT INTO FriendRequest (sender_id, send_to_id, request_date) VALUES (1, 4, '2016-06-01');",
                    "INSERT INTO FriendRequest (sender_id, send_to_id, request_date) VALUES (2, 3, '2016-06-02');",
                    "INSERT INTO FriendRequest (sender_id, send_to_id, request_date) VALUES (3, 4, '2016-06-09');",
                ],
                "expected": [[3, 3]],
            },
        ],
    },
    {
        "id": 1008,
        "title": "Median Employee Salary",
        "difficulty": "Hard",
        "topic": "Database",
        "tags": ["sql", "window-functions"],
        "companiesAsked": ["Google", "Stripe"],
        "description": (
            "Write a solution to find the **median salary of each company**. "
            "Return the result table in **any order**.\n\n"
            "For a company with an even number of employees, the median is the "
            "average of the two middle salaries; with an odd count, it is the "
            "single middle salary. A company whose employees all earn the same "
            "value contributes that value for every middle position. The "
            "median definition used here returns the middle row(s) — for an "
            "even count both middle salaries are returned."
        ),
        "constraints": (
            "id is the primary key of Employee\n"
            "company is not null\n"
            "Salaries are whole numbers"
        ),
        "follow_up": "Can you express the same answer with PERCENTILE_CONT over a subquery, and explain when the two definitions diverge?",
        "hints": [
            "Row-number each company's salaries in order and count them with a windowed COUNT.",
            "The middle rows sit at (cnt + 1) / 2 and (cnt + 2) / 2 — for odd counts those coincide, for even counts they are the two middle salaries.",
        ],
        "timeComplexity": "O(n log n)",
        "spaceComplexity": "O(n)",
        "sql_schema": [
            "CREATE TABLE Employee (id INT PRIMARY KEY, company VARCHAR(255), salary INT);",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Employee;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Employee;\n"
            ),
        },
        "solution_sql": (
            "SELECT company, salary\n"
            "FROM (\n"
            "    SELECT company, salary,\n"
            "           ROW_NUMBER() OVER (PARTITION BY company ORDER BY salary) AS rn,\n"
            "           COUNT(*) OVER (PARTITION BY company) AS cnt\n"
            "    FROM Employee\n"
            ") t\n"
            "WHERE rn BETWEEN (cnt + 1) / 2 AND (cnt + 2) / 2\n"
            "ORDER BY company, salary;\n"
        ),
        "solutionCode": (
            "SELECT company, salary\n"
            "FROM (\n"
            "    SELECT company, salary,\n"
            "           ROW_NUMBER() OVER (PARTITION BY company ORDER BY salary) AS rn,\n"
            "           COUNT(*) OVER (PARTITION BY company) AS cnt\n"
            "    FROM Employee\n"
            ") t\n"
            "WHERE rn BETWEEN (cnt + 1) / 2 AND (cnt + 2) / 2\n"
            "ORDER BY company, salary;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, company, salary) VALUES (1, 'A', 2341);",
                    "INSERT INTO Employee (id, company, salary) VALUES (2, 'A', 341);",
                    "INSERT INTO Employee (id, company, salary) VALUES (3, 'A', 15);",
                    "INSERT INTO Employee (id, company, salary) VALUES (4, 'A', 15314);",
                    "INSERT INTO Employee (id, company, salary) VALUES (5, 'A', 451);",
                    "INSERT INTO Employee (id, company, salary) VALUES (6, 'A', 513);",
                    "INSERT INTO Employee (id, company, salary) VALUES (7, 'B', 15);",
                    "INSERT INTO Employee (id, company, salary) VALUES (8, 'B', 13);",
                    "INSERT INTO Employee (id, company, salary) VALUES (9, 'B', 1154);",
                    "INSERT INTO Employee (id, company, salary) VALUES (10, 'B', 1345);",
                    "INSERT INTO Employee (id, company, salary) VALUES (11, 'B', 1221);",
                    "INSERT INTO Employee (id, company, salary) VALUES (12, 'B', 234);",
                    "INSERT INTO Employee (id, company, salary) VALUES (13, 'C', 2345);",
                    "INSERT INTO Employee (id, company, salary) VALUES (14, 'C', 2645);",
                    "INSERT INTO Employee (id, company, salary) VALUES (15, 'C', 2645);",
                    "INSERT INTO Employee (id, company, salary) VALUES (16, 'C', 2652);",
                    "INSERT INTO Employee (id, company, salary) VALUES (17, 'C', 65);",
                ],
                "expected": [
                    ["A", 451],
                    ["A", 513],
                    ["B", 234],
                    ["B", 1154],
                    # C has five salaries — an odd count, so the median is the
                    # single middle row. Only an even count yields two.
                    ["C", 2645],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, company, salary) VALUES (1, 'A', 2341);",
                    "INSERT INTO Employee (id, company, salary) VALUES (2, 'A', 341);",
                    "INSERT INTO Employee (id, company, salary) VALUES (3, 'A', 15);",
                    "INSERT INTO Employee (id, company, salary) VALUES (4, 'A', 15314);",
                    "INSERT INTO Employee (id, company, salary) VALUES (5, 'A', 451);",
                    "INSERT INTO Employee (id, company, salary) VALUES (6, 'A', 513);",
                    "INSERT INTO Employee (id, company, salary) VALUES (7, 'B', 15);",
                    "INSERT INTO Employee (id, company, salary) VALUES (8, 'B', 13);",
                    "INSERT INTO Employee (id, company, salary) VALUES (9, 'B', 1154);",
                    "INSERT INTO Employee (id, company, salary) VALUES (10, 'B', 1345);",
                    "INSERT INTO Employee (id, company, salary) VALUES (11, 'B', 1221);",
                    "INSERT INTO Employee (id, company, salary) VALUES (12, 'B', 234);",
                    "INSERT INTO Employee (id, company, salary) VALUES (13, 'C', 2345);",
                    "INSERT INTO Employee (id, company, salary) VALUES (14, 'C', 2645);",
                    "INSERT INTO Employee (id, company, salary) VALUES (15, 'C', 2645);",
                    "INSERT INTO Employee (id, company, salary) VALUES (16, 'C', 2652);",
                    "INSERT INTO Employee (id, company, salary) VALUES (17, 'C', 65);",
                ],
                "expected": [
                    ["A", 451],
                    ["A", 513],
                    ["B", 234],
                    ["B", 1154],
                    # C has five salaries — an odd count, so the median is the
                    # single middle row. Only an even count yields two.
                    ["C", 2645],
                ],
            },
        ],
    },
    {
        "id": 1009,
        "title": "Report Contiguous Dates",
        "difficulty": "Hard",
        "topic": "Database",
        "tags": ["sql", "window-functions", "union-all"],
        "companiesAsked": ["Google", "Amazon"],
        "description": (
            "The log records the system's state for each day of 2019: every date appears "
            "in exactly one of `Succeeded` (the system succeeded that day) or `Failed` "
            "(it failed). Write a solution to report the start and end date of each "
            "contiguous block of days that were entirely `succeeded` or entirely `failed`.\n\n"
            "Two adjacent dates belong to the same block only when the state did not change "
            "between them — a single state flip starts a new block even without a missing day.\n\n"
            "Return the result table as `period_state`, `start_date`, `end_date` in any order."
        ),
        "constraints": (
            "success_date is the primary key of Succeeded\n"
            "fail_date is the primary key of Failed\n"
            "Every date from 2019-01-01 to 2019-12-31 appears in exactly one table\n"
            "A block can be a single day"
        ),
        "follow_up": None,
        "hints": [
            "UNION ALL the two tables with a state flag so every date becomes one row.",
            "ROW_NUMBER() OVER (PARTITION BY state ORDER BY date) restarts at 1 for each state's own run — subtracting it from the date (date minus (rn - 1) days) gives a constant key per contiguous run.",
            "GROUP BY state and the run key, then take MIN and MAX of the dates.",
        ],
        "timeComplexity": "O(n log n)",
        "spaceComplexity": "O(n)",
        "sql_schema": [
            "CREATE TABLE Failed (fail_date DATE PRIMARY KEY);",
            "CREATE TABLE Succeeded (success_date DATE PRIMARY KEY);",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Succeeded;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Succeeded;\n"
            ),
        },
        "solution_sql": (
            "SELECT state AS period_state,\n"
            "       MIN(d) AS start_date,\n"
            "       MAX(d) AS end_date\n"
            "FROM (\n"
            "    SELECT d, state, DATE(d, '-' || (rn - 1) || ' days') AS grp\n"
            "    FROM (\n"
            "        SELECT d, state,\n"
            "               ROW_NUMBER() OVER (PARTITION BY state ORDER BY d) AS rn\n"
            "        FROM (\n"
            "            SELECT success_date AS d, 'succeeded' AS state FROM Succeeded\n"
            "            UNION ALL\n"
            "            SELECT fail_date AS d, 'failed' AS state FROM Failed\n"
            "        )\n"
            "    )\n"
            ")\n"
            "GROUP BY state, grp\n"
            "ORDER BY start_date;\n"
        ),
        "solutionCode": (
            "SELECT state AS period_state,\n"
            "       MIN(d) AS start_date,\n"
            "       MAX(d) AS end_date\n"
            "FROM (\n"
            "    SELECT d, state, DATE(d, '-' || (rn - 1) || ' days') AS grp\n"
            "    FROM (\n"
            "        SELECT d, state,\n"
            "               ROW_NUMBER() OVER (PARTITION BY state ORDER BY d) AS rn\n"
            "        FROM (\n"
            "            SELECT success_date AS d, 'succeeded' AS state FROM Succeeded\n"
            "            UNION ALL\n"
            "            SELECT fail_date AS d, 'failed' AS state FROM Failed\n"
            "        )\n"
            "    )\n"
            ")\n"
            "GROUP BY state, grp\n"
            "ORDER BY start_date;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Succeeded (success_date) VALUES ('2019-01-01');",
                    "INSERT INTO Succeeded (success_date) VALUES ('2019-01-02');",
                    "INSERT INTO Succeeded (success_date) VALUES ('2019-01-03');",
                    "INSERT INTO Succeeded (success_date) VALUES ('2019-01-06');",
                    "INSERT INTO Failed (fail_date) VALUES ('2019-01-04');",
                    "INSERT INTO Failed (fail_date) VALUES ('2019-01-05');",
                    "INSERT INTO Failed (fail_date) VALUES ('2019-01-07');",
                ],
                "expected": [
                    ["succeeded", "2019-01-01", "2019-01-03"],
                    ["failed", "2019-01-04", "2019-01-05"],
                    ["succeeded", "2019-01-06", "2019-01-06"],
                    ["failed", "2019-01-07", "2019-01-07"],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Succeeded (success_date) VALUES ('2019-01-01');",
                    "INSERT INTO Succeeded (success_date) VALUES ('2019-01-02');",
                    "INSERT INTO Succeeded (success_date) VALUES ('2019-01-03');",
                    "INSERT INTO Succeeded (success_date) VALUES ('2019-01-06');",
                    "INSERT INTO Failed (fail_date) VALUES ('2019-01-04');",
                    "INSERT INTO Failed (fail_date) VALUES ('2019-01-05');",
                    "INSERT INTO Failed (fail_date) VALUES ('2019-01-07');",
                ],
                "expected": [
                    ["succeeded", "2019-01-01", "2019-01-03"],
                    ["failed", "2019-01-04", "2019-01-05"],
                    ["succeeded", "2019-01-06", "2019-01-06"],
                    ["failed", "2019-01-07", "2019-01-07"],
                ],
            },
        ],
    },
    {
        "id": 1010,
        "title": "Nth Highest Salary",
        "difficulty": "Medium",
        "topic": "Database",
        "tags": ["sql", "subquery", "sorting"],
        "companiesAsked": ["Amazon", "Google"],
        "description": (
            "Write a solution to find the **3rd highest distinct salary** from the "
            "`Employee` table. If there is no third highest salary, the result must be `null`.\n\n"
            "'Distinct' collapses identical salaries: with salaries 300, 300, 200 the "
            "distinct list is 300, 200, so 200 is the 2nd highest."
        ),
        "constraints": (
            "id is the primary key of Employee\n"
            "Salary is a whole number and may repeat\n"
            "The answer is a single value, not a row per employee"
        ),
        "follow_up": None,
        "hints": [
            "ORDER BY salary DESC and skip the top two with OFFSET — LIMIT 1 OFFSET 2 is the third distinct salary.",
            "A bare SELECT ... LIMIT 1 OFFSET 2 returns no rows when fewer than three distinct salaries exist; wrapping it in an outer SELECT turns the empty result into a single null row.",
            "Put DISTINCT inside the subquery so equal salaries do not create separate ranks.",
        ],
        "timeComplexity": "O(n log n)",
        "spaceComplexity": "O(1)",
        "sql_schema": [
            "CREATE TABLE Employee (id INT PRIMARY KEY, salary INT);",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Employee;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Employee;\n"
            ),
        },
        "solution_sql": (
            "SELECT (\n"
            "    SELECT DISTINCT salary\n"
            "    FROM Employee\n"
            "    ORDER BY salary DESC\n"
            "    LIMIT 1 OFFSET 2\n"
            ") AS ThirdHighestSalary;\n"
        ),
        "solutionCode": (
            "SELECT (\n"
            "    SELECT DISTINCT salary\n"
            "    FROM Employee\n"
            "    ORDER BY salary DESC\n"
            "    LIMIT 1 OFFSET 2\n"
            ") AS ThirdHighestSalary;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, salary) VALUES (1, 100);",
                    "INSERT INTO Employee (id, salary) VALUES (2, 200);",
                    "INSERT INTO Employee (id, salary) VALUES (3, 300);",
                    "INSERT INTO Employee (id, salary) VALUES (4, 300);",
                ],
                "expected": [[100]],
            },
            {
                "seed": [
                    "INSERT INTO Employee (id, salary) VALUES (1, 100);",
                    "INSERT INTO Employee (id, salary) VALUES (2, 100);",
                ],
                "expected": [[None]],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, salary) VALUES (1, 100);",
                    "INSERT INTO Employee (id, salary) VALUES (2, 200);",
                    "INSERT INTO Employee (id, salary) VALUES (3, 300);",
                    "INSERT INTO Employee (id, salary) VALUES (4, 300);",
                ],
                "expected": [[100]],
            },
            {
                "seed": [
                    "INSERT INTO Employee (id, salary) VALUES (1, 100);",
                    "INSERT INTO Employee (id, salary) VALUES (2, 100);",
                ],
                "expected": [[None]],
            },
        ],
    },
    {
        "id": 1011,
        "title": "Game Play Analysis IV",
        "difficulty": "Medium",
        "topic": "Database",
        "tags": ["sql", "aggregation", "date-arithmetic"],
        "companiesAsked": ["Google", "Amazon"],
        "description": (
            "Report the **fraction of players that logged in on two consecutive days**: "
            "players whose very first login is followed by a login on the next day, out of "
            "all players. Round the fraction to two decimal places and return it as a "
            "single value in a column named `fraction`.\n\n"
            "A player counts only if their FIRST login has a next-day login; a login on "
            "the day after some later login does not qualify the player."
        ),
        "constraints": (
            "(player_id, event_date) is the primary key of Activity\n"
            "event_date is the day the player played\n"
            "games_played is the number of games started that day"
        ),
        "follow_up": None,
        "hints": [
            "The numerator counts distinct players who have a login exactly one day after their own first login — DATE(login, '+1 day').",
            "The denominator is the total number of distinct players.",
            "Multiply by 1.0 before dividing so SQLite does not do integer division, then ROUND to 2 decimals.",
        ],
        "timeComplexity": "O(n)",
        "spaceComplexity": "O(n)",
        "sql_schema": [
            "CREATE TABLE Activity (player_id INT, device_id INT, event_date DATE, games_played INT, PRIMARY KEY (player_id, event_date));",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Activity;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Activity;\n"
            ),
        },
        "solution_sql": (
            "SELECT ROUND(\n"
            "    COUNT(DISTINCT a.player_id) * 1.0 /\n"
            "    (SELECT COUNT(DISTINCT player_id) FROM Activity),\n"
            "    2\n"
            ") AS fraction\n"
            "FROM Activity a\n"
            "WHERE a.event_date = (\n"
            "    SELECT MIN(event_date) FROM Activity WHERE player_id = a.player_id\n"
            ")\n"
            "AND EXISTS (\n"
            "    SELECT 1 FROM Activity b\n"
            "    WHERE b.player_id = a.player_id\n"
            "      AND DATE(b.event_date) = DATE(a.event_date, '+1 day')\n"
            ");\n"
        ),
        "solutionCode": (
            "SELECT ROUND(\n"
            "    COUNT(DISTINCT a.player_id) * 1.0 /\n"
            "    (SELECT COUNT(DISTINCT player_id) FROM Activity),\n"
            "    2\n"
            ") AS fraction\n"
            "FROM Activity a\n"
            "WHERE a.event_date = (\n"
            "    SELECT MIN(event_date) FROM Activity WHERE player_id = a.player_id\n"
            ")\n"
            "AND EXISTS (\n"
            "    SELECT 1 FROM Activity b\n"
            "    WHERE b.player_id = a.player_id\n"
            "      AND DATE(b.event_date) = DATE(a.event_date, '+1 day')\n"
            ");\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (1, 2, '2016-03-01', 5);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (1, 2, '2016-03-02', 6);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (2, 3, '2017-06-25', 1);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (3, 1, '2016-03-02', 0);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (3, 4, '2018-07-03', 5);",
                ],
                "expected": [[0.33]],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (1, 2, '2016-03-01', 5);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (1, 2, '2016-03-02', 6);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (2, 3, '2017-06-25', 1);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (3, 1, '2016-03-02', 0);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (3, 4, '2018-07-03', 5);",
                ],
                "expected": [[0.33]],
            },
        ],
    },
    {
        "id": 1012,
        "title": "Department Top Three Salaries",
        "difficulty": "Hard",
        "topic": "Database",
        "tags": ["sql", "window-functions", "join"],
        "companiesAsked": ["Meta", "Amazon", "Google"],
        "description": (
            "Write a solution to find employees who have the **top three unique salaries** "
            "in each department. A department with fewer than three distinct salary levels "
            "returns one employee per available level.\n\n"
            "Two employees with the same salary occupy the same rank, so a department whose "
            "top three salaries are 90000, 85000, 85000, 70000 reports the four people "
            "earning 90000, 85000, or 70000.\n\n"
            "Return the result table as `Department`, `Employee`, `Salary` in any order."
        ),
        "constraints": (
            "id is the primary key of Employee\n"
            "departmentId is a foreign key referencing Department.id\n"
            "Every employee belongs to exactly one department"
        ),
        "follow_up": None,
        "hints": [
            "DENSE_RANK() OVER (PARTITION BY departmentId ORDER BY salary DESC) gives ranks 1, 2, 3, … with ties sharing a rank and no gaps.",
            "Keep only rnk <= 3, then join Department for the department name.",
        ],
        "timeComplexity": "O(n log n)",
        "spaceComplexity": "O(n)",
        "sql_schema": [
            "CREATE TABLE Employee (id INT PRIMARY KEY, name VARCHAR(255), salary INT, departmentId INT);",
            "CREATE TABLE Department (id INT PRIMARY KEY, name VARCHAR(255));",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Employee;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Employee;\n"
            ),
        },
        "solution_sql": (
            "SELECT d.name AS Department, e.name AS Employee, e.salary AS Salary\n"
            "FROM (\n"
            "    SELECT name, salary, departmentId,\n"
            "           DENSE_RANK() OVER (PARTITION BY departmentId ORDER BY salary DESC) AS rnk\n"
            "    FROM Employee\n"
            ") e\n"
            "JOIN Department d ON e.departmentId = d.id\n"
            "WHERE e.rnk <= 3\n"
            "ORDER BY Department, Salary DESC;\n"
        ),
        "solutionCode": (
            "SELECT d.name AS Department, e.name AS Employee, e.salary AS Salary\n"
            "FROM (\n"
            "    SELECT name, salary, departmentId,\n"
            "           DENSE_RANK() OVER (PARTITION BY departmentId ORDER BY salary DESC) AS rnk\n"
            "    FROM Employee\n"
            ") e\n"
            "JOIN Department d ON e.departmentId = d.id\n"
            "WHERE e.rnk <= 3\n"
            "ORDER BY Department, Salary DESC;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (1, 'Joe', 85000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (2, 'Henry', 80000, 2);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (3, 'Sam', 60000, 2);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (4, 'Max', 90000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (5, 'Janet', 69000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (6, 'Randy', 85000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (7, 'Will', 70000, 1);",
                    "INSERT INTO Department (id, name) VALUES (1, 'IT');",
                    "INSERT INTO Department (id, name) VALUES (2, 'Sales');",
                ],
                "expected": [
                    ["IT", "Max", 90000],
                    ["IT", "Joe", 85000],
                    ["IT", "Randy", 85000],
                    ["IT", "Will", 70000],
                    ["Sales", "Henry", 80000],
                    ["Sales", "Sam", 60000],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (1, 'Joe', 85000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (2, 'Henry', 80000, 2);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (3, 'Sam', 60000, 2);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (4, 'Max', 90000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (5, 'Janet', 69000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (6, 'Randy', 85000, 1);",
                    "INSERT INTO Employee (id, name, salary, departmentId) VALUES (7, 'Will', 70000, 1);",
                    "INSERT INTO Department (id, name) VALUES (1, 'IT');",
                    "INSERT INTO Department (id, name) VALUES (2, 'Sales');",
                ],
                "expected": [
                    ["IT", "Max", 90000],
                    ["IT", "Joe", 85000],
                    ["IT", "Randy", 85000],
                    ["IT", "Will", 70000],
                    ["Sales", "Henry", 80000],
                    ["Sales", "Sam", 60000],
                ],
            },
        ],
    },
    {
        "id": 1014,
        "title": "Product Price at a Given Date",
        "difficulty": "Medium",
        "topic": "Database",
        "tags": ["sql", "subquery", "date-arithmetic"],
        "companiesAsked": ["Amazon", "Google"],
        "description": (
            "You run a small hardware shop and reprice your stock over time. "
            "Each `Products` row records one price change: the `new_price` in "
            "effect starting on `change_date`. Write a solution to find the "
            "price of **every** product on **2019-08-16**.\n\n"
            "A product's price on that day is the price from its most recent "
            "change on or before the date; before its first recorded change it "
            "sells at its default price of **10**. A product whose only changes "
            "happened after the cutoff therefore reports 10. The result table "
            "holds `product_id` and `price`, in any order."
        ),
        "constraints": (
            "(product_id, change_date) is the primary key of Products\n"
            "change_date is the day the new price takes effect\n"
            "new_price is the price in effect from change_date onward\n"
            "Before its first change a product's price is 10"
        ),
        "follow_up": "Can you express the same answer with LAST_VALUE over a window, and say when the correlated subquery stays clearer?",
        "hints": [
            "The row that decides a product's price is the one with the largest change_date not after the cutoff — a per-product MAX over a filtered set.",
            "A correlated subquery that orders by change_date DESC and takes LIMIT 1 returns exactly that row; COALESCE(..., 10) supplies the default when no row qualifies.",
        ],
        "timeComplexity": "O(n log n)",
        "spaceComplexity": "O(1)",
        "sql_schema": [
            "CREATE TABLE Products (product_id INT, new_price INT, change_date DATE, PRIMARY KEY (product_id, change_date));",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Products;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Products;\n"
            ),
        },
        "solution_sql": (
            "SELECT p.product_id,\n"
            "       COALESCE(\n"
            "           (SELECT new_price FROM Products\n"
            "            WHERE product_id = p.product_id AND change_date <= '2019-08-16'\n"
            "            ORDER BY change_date DESC\n"
            "            LIMIT 1),\n"
            "           10\n"
            "       ) AS price\n"
            "FROM (SELECT DISTINCT product_id FROM Products) p;\n"
        ),
        "solutionCode": (
            "SELECT p.product_id,\n"
            "       COALESCE(\n"
            "           (SELECT new_price FROM Products\n"
            "            WHERE product_id = p.product_id AND change_date <= '2019-08-16'\n"
            "            ORDER BY change_date DESC\n"
            "            LIMIT 1),\n"
            "           10\n"
            "       ) AS price\n"
            "FROM (SELECT DISTINCT product_id FROM Products) p;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (1, 20, '2019-08-14');",
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (1, 30, '2019-08-15');",
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (1, 35, '2019-08-16');",
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (2, 50, '2019-08-14');",
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (2, 65, '2019-08-17');",
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (3, 20, '2019-08-18');",
                ],
                "expected": [
                    [1, 35],
                    [2, 50],
                    [3, 10],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (1, 20, '2019-08-14');",
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (1, 30, '2019-08-15');",
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (1, 35, '2019-08-16');",
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (2, 50, '2019-08-14');",
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (2, 65, '2019-08-17');",
                    "INSERT INTO Products (product_id, new_price, change_date) VALUES (3, 20, '2019-08-18');",
                ],
                "expected": [
                    [1, 35],
                    [2, 50],
                    [3, 10],
                ],
            },
        ],
    },
    {
        "id": 1015,
        "title": "Running Total of Orders",
        "difficulty": "Medium",
        "topic": "Database",
        "tags": ["sql", "window-functions", "aggregation"],
        "companiesAsked": ["Stripe", "Amazon"],
        "description": (
            "The sales dashboard wants a **running total** beside every order: "
            "the sum of the order's own `amount` and the `amount` of every "
            "order placed on or before its date, breaking same-day ties by "
            "`order_id`. Write a solution to report `order_id`, `order_date`, "
            "and `running_total`, ordered by `order_id`.\n\n"
            "The running total is cumulative: it never resets, and each order's "
            "figure includes all earlier ones. Two orders on the same date count "
            "in the order their ids sort, so the totals are deterministic."
        ),
        "constraints": (
            "order_id is the primary key of Orders\n"
            "amount is a whole number of currency units\n"
            "order_date is the day the order was placed"
        ),
        "follow_up": "What changes if the running total must restart per customer? (Hint: add a PARTITION BY customer_id.)",
        "hints": [
            "SUM(amount) OVER (ORDER BY order_date, order_id) accumulates the amount over every row up to and including the current one.",
            "Including order_id in the window ORDER BY makes the tie-break explicit — the sort key is then unique, so RANGE and ROWS frames agree.",
        ],
        "timeComplexity": "O(n log n)",
        "spaceComplexity": "O(n)",
        "sql_schema": [
            "CREATE TABLE Orders (order_id INT PRIMARY KEY, customer_id INT, order_date DATE, amount INT);",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Orders;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Orders;\n"
            ),
        },
        "solution_sql": (
            "SELECT order_id, order_date,\n"
            "       SUM(amount) OVER (ORDER BY order_date, order_id) AS running_total\n"
            "FROM Orders\n"
            "ORDER BY order_id;\n"
        ),
        "solutionCode": (
            "SELECT order_id, order_date,\n"
            "       SUM(amount) OVER (ORDER BY order_date, order_id) AS running_total\n"
            "FROM Orders\n"
            "ORDER BY order_id;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Orders (order_id, customer_id, order_date, amount) VALUES (1, 101, '2024-01-01', 150);",
                    "INSERT INTO Orders (order_id, customer_id, order_date, amount) VALUES (2, 102, '2024-01-02', 200);",
                    "INSERT INTO Orders (order_id, customer_id, order_date, amount) VALUES (3, 103, '2024-01-02', 75);",
                    "INSERT INTO Orders (order_id, customer_id, order_date, amount) VALUES (4, 101, '2024-01-05', 300);",
                    "INSERT INTO Orders (order_id, customer_id, order_date, amount) VALUES (5, 102, '2024-01-07', 50);",
                ],
                "expected": [
                    [1, "2024-01-01", 150],
                    [2, "2024-01-02", 350],
                    [3, "2024-01-02", 425],
                    [4, "2024-01-05", 725],
                    [5, "2024-01-07", 775],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Orders (order_id, customer_id, order_date, amount) VALUES (1, 101, '2024-01-01', 150);",
                    "INSERT INTO Orders (order_id, customer_id, order_date, amount) VALUES (2, 102, '2024-01-02', 200);",
                    "INSERT INTO Orders (order_id, customer_id, order_date, amount) VALUES (3, 103, '2024-01-02', 75);",
                    "INSERT INTO Orders (order_id, customer_id, order_date, amount) VALUES (4, 101, '2024-01-05', 300);",
                    "INSERT INTO Orders (order_id, customer_id, order_date, amount) VALUES (5, 102, '2024-01-07', 50);",
                ],
                "expected": [
                    [1, "2024-01-01", 150],
                    [2, "2024-01-02", 350],
                    [3, "2024-01-02", 425],
                    [4, "2024-01-05", 725],
                    [5, "2024-01-07", 775],
                ],
            },
        ],
    },
    {
        "id": 1016,
        "title": "Students and Examinations",
        "difficulty": "Easy",
        "topic": "Database",
        "tags": ["sql", "cross-join", "left-join", "group-by"],
        "companiesAsked": ["Meta", "Microsoft"],
        "description": (
            "The principal wants an attendance matrix: how many times **each "
            "student sat each subject's exam**. A student who never attempted a "
            "subject must still appear with a count of **0** — the absence of a "
            "row in `Examinations` is information, not an omission.\n\n"
            "Start from the cartesian product of `Students` and `Subjects` (every "
            "pair), then count how many `Examinations` rows match that pair. "
            "Report `student_id`, `student_name`, `subject_name`, and "
            "`attended_exams`, ordered by `student_id` then `subject_name`."
        ),
        "constraints": (
            "student_id is the primary key of Students\n"
            "subject_name is the primary key of Subjects\n"
            "An Examinations row records one sitting of a subject by a student"
        ),
        "follow_up": None,
        "hints": [
            "CROSS JOIN Students and Subjects to get every (student, subject) pair, then LEFT JOIN Examinations so a pair with no sitting still survives.",
            "COUNT(e.subject_name) counts only non-null join matches — a missing sitting contributes 0 rather than a phantom row.",
        ],
        "timeComplexity": "O(n * m)",
        "spaceComplexity": "O(n * m)",
        "sql_schema": [
            "CREATE TABLE Students (student_id INT PRIMARY KEY, student_name VARCHAR(255));",
            "CREATE TABLE Subjects (subject_name VARCHAR(255) PRIMARY KEY);",
            "CREATE TABLE Examinations (student_id INT, subject_name VARCHAR(255));",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Students;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Students;\n"
            ),
        },
        "solution_sql": (
            "SELECT s.student_id, s.student_name, sub.subject_name,\n"
            "       COUNT(e.subject_name) AS attended_exams\n"
            "FROM Students s\n"
            "CROSS JOIN Subjects sub\n"
            "LEFT JOIN Examinations e\n"
            "  ON s.student_id = e.student_id AND sub.subject_name = e.subject_name\n"
            "GROUP BY s.student_id, s.student_name, sub.subject_name\n"
            "ORDER BY s.student_id, sub.subject_name;\n"
        ),
        "solutionCode": (
            "SELECT s.student_id, s.student_name, sub.subject_name,\n"
            "       COUNT(e.subject_name) AS attended_exams\n"
            "FROM Students s\n"
            "CROSS JOIN Subjects sub\n"
            "LEFT JOIN Examinations e\n"
            "  ON s.student_id = e.student_id AND sub.subject_name = e.subject_name\n"
            "GROUP BY s.student_id, s.student_name, sub.subject_name\n"
            "ORDER BY s.student_id, sub.subject_name;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Students (student_id, student_name) VALUES (1, 'Alice');",
                    "INSERT INTO Students (student_id, student_name) VALUES (2, 'Bob');",
                    "INSERT INTO Students (student_id, student_name) VALUES (6, 'Alex');",
                    "INSERT INTO Students (student_id, student_name) VALUES (13, 'John');",
                    "INSERT INTO Subjects (subject_name) VALUES ('Math');",
                    "INSERT INTO Subjects (subject_name) VALUES ('Physics');",
                    "INSERT INTO Subjects (subject_name) VALUES ('Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Math');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Physics');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (2, 'Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Physics');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (13, 'Math');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (13, 'Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (13, 'Physics');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (2, 'Math');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Math');",
                ],
                "expected": [
                    [1, "Alice", "Math", 2],
                    [1, "Alice", "Physics", 2],
                    [1, "Alice", "Programming", 1],
                    [2, "Bob", "Math", 1],
                    [2, "Bob", "Physics", 0],
                    [2, "Bob", "Programming", 1],
                    [6, "Alex", "Math", 0],
                    [6, "Alex", "Physics", 0],
                    [6, "Alex", "Programming", 0],
                    [13, "John", "Math", 1],
                    [13, "John", "Physics", 1],
                    [13, "John", "Programming", 1],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Students (student_id, student_name) VALUES (1, 'Alice');",
                    "INSERT INTO Students (student_id, student_name) VALUES (2, 'Bob');",
                    "INSERT INTO Students (student_id, student_name) VALUES (6, 'Alex');",
                    "INSERT INTO Students (student_id, student_name) VALUES (13, 'John');",
                    "INSERT INTO Subjects (subject_name) VALUES ('Math');",
                    "INSERT INTO Subjects (subject_name) VALUES ('Physics');",
                    "INSERT INTO Subjects (subject_name) VALUES ('Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Math');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Physics');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (2, 'Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Physics');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (13, 'Math');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (13, 'Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (13, 'Physics');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (2, 'Math');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Math');",
                ],
                "expected": [
                    [1, "Alice", "Math", 2],
                    [1, "Alice", "Physics", 2],
                    [1, "Alice", "Programming", 1],
                    [2, "Bob", "Math", 1],
                    [2, "Bob", "Physics", 0],
                    [2, "Bob", "Programming", 1],
                    [6, "Alex", "Math", 0],
                    [6, "Alex", "Physics", 0],
                    [6, "Alex", "Programming", 0],
                    [13, "John", "Math", 1],
                    [13, "John", "Physics", 1],
                    [13, "John", "Programming", 1],
                ],
            },
        ],
    },
    {
        "id": 1017,
        "title": "Consecutive Numbers",
        "difficulty": "Medium",
        "topic": "Database",
        "tags": ["sql", "window-functions"],
        "companiesAsked": ["Stripe", "Google"],
        "description": (
            "The fraud team watches a stream of transactions, one per row, with "
            "strictly increasing `id`s. They want every **distinct number that "
            "appears at least three times in a row** — that is, on three "
            "consecutive `id`s. Return the result table with the single column "
            "`ConsecutiveNums`, deduplicated.\n\n"
            "'In a row' means adjacent ids: rows 4, 5 and 6 if ids are 4, 5, 6. "
            "A number appearing three times with a different number between them "
            "does not count."
        ),
        "constraints": (
            "id is the primary key of Logs\n"
            "id is strictly increasing, but may skip values\n"
            "num is the value logged for that row"
        ),
        "follow_up": "Can you also find numbers appearing exactly three times in a row by toggling a running streak flag instead of LAG?",
        "hints": [
            "Compare each row with the two rows before it: LAG(num, 1) and LAG(num, 2) over ORDER BY id make the three-way equality a single WHERE clause.",
            "Apply DISTINCT to the surviving numbers — the same value can complete a triple more than once.",
        ],
        "timeComplexity": "O(n)",
        "spaceComplexity": "O(n)",
        "sql_schema": [
            "CREATE TABLE Logs (id INT PRIMARY KEY, num INT);",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Logs;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Logs;\n"
            ),
        },
        "solution_sql": (
            "SELECT DISTINCT num AS ConsecutiveNums\n"
            "FROM (\n"
            "    SELECT num,\n"
            "           LAG(num) OVER (ORDER BY id) AS prev1,\n"
            "           LAG(num, 2) OVER (ORDER BY id) AS prev2\n"
            "    FROM Logs\n"
            ") t\n"
            "WHERE num = prev1 AND num = prev2;\n"
        ),
        "solutionCode": (
            "SELECT DISTINCT num AS ConsecutiveNums\n"
            "FROM (\n"
            "    SELECT num,\n"
            "           LAG(num) OVER (ORDER BY id) AS prev1,\n"
            "           LAG(num, 2) OVER (ORDER BY id) AS prev2\n"
            "    FROM Logs\n"
            ") t\n"
            "WHERE num = prev1 AND num = prev2;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Logs (id, num) VALUES (1, 1);",
                    "INSERT INTO Logs (id, num) VALUES (2, 1);",
                    "INSERT INTO Logs (id, num) VALUES (3, 1);",
                    "INSERT INTO Logs (id, num) VALUES (4, 2);",
                    "INSERT INTO Logs (id, num) VALUES (5, 1);",
                    "INSERT INTO Logs (id, num) VALUES (6, 2);",
                    "INSERT INTO Logs (id, num) VALUES (7, 2);",
                ],
                "expected": [[1]],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Logs (id, num) VALUES (1, 1);",
                    "INSERT INTO Logs (id, num) VALUES (2, 1);",
                    "INSERT INTO Logs (id, num) VALUES (3, 1);",
                    "INSERT INTO Logs (id, num) VALUES (4, 2);",
                    "INSERT INTO Logs (id, num) VALUES (5, 1);",
                    "INSERT INTO Logs (id, num) VALUES (6, 2);",
                    "INSERT INTO Logs (id, num) VALUES (7, 2);",
                ],
                "expected": [[1]],
            },
        ],
    },
    {
        "id": 1018,
        "title": "The Most Recent Three Orders",
        "difficulty": "Hard",
        "topic": "Database",
        "tags": ["sql", "window-functions", "join"],
        "companiesAsked": ["Amazon", "Meta"],
        "description": (
            "Support wants, for **every customer**, their **three most recent "
            "orders** with the product and the date. A customer with fewer than "
            "three orders lists what they have; a customer with no orders is "
            "omitted entirely. Ties on the same date are broken by `order_id` "
            "descending — the later-placed order wins the higher slot.\n\n"
            "Report `customer_name`, `customer_id`, `order_date`, and "
            "`product_name`, ordered by customer name then by `order_date` "
            "descending."
        ),
        "constraints": (
            "customer_id is the primary key of Customers\n"
            "order_id is the primary key of Orders\n"
            "customer_id in Orders references Customers.customer_id"
        ),
        "follow_up": "How would the answer change if a customer's ties must be broken by product name instead of order_id?",
        "hints": [
            "ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) numbers each customer's orders newest first; keep rn <= 3.",
            "Join back to Customers only after the window — joining before numbering would multiply each order by every matching customer name.",
        ],
        "timeComplexity": "O(n log n)",
        "spaceComplexity": "O(n)",
        "sql_schema": [
            "CREATE TABLE Customers (customer_id INT PRIMARY KEY, name VARCHAR(255));",
            "CREATE TABLE Orders (order_id INT PRIMARY KEY, customer_id INT, product_name VARCHAR(255), order_date DATE);",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Orders;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Orders;\n"
            ),
        },
        "solution_sql": (
            "SELECT c.name AS customer_name, o.customer_id, o.order_date, o.product_name\n"
            "FROM (\n"
            "    SELECT customer_id, order_date, product_name,\n"
            "           ROW_NUMBER() OVER (\n"
            "               PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC\n"
            "           ) AS rn\n"
            "    FROM Orders\n"
            ") o\n"
            "JOIN Customers c ON o.customer_id = c.customer_id\n"
            "WHERE o.rn <= 3\n"
            "ORDER BY c.name, o.order_date DESC;\n"
        ),
        "solutionCode": (
            "SELECT c.name AS customer_name, o.customer_id, o.order_date, o.product_name\n"
            "FROM (\n"
            "    SELECT customer_id, order_date, product_name,\n"
            "           ROW_NUMBER() OVER (\n"
            "               PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC\n"
            "           ) AS rn\n"
            "    FROM Orders\n"
            ") o\n"
            "JOIN Customers c ON o.customer_id = c.customer_id\n"
            "WHERE o.rn <= 3\n"
            "ORDER BY c.name, o.order_date DESC;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Customers (customer_id, name) VALUES (1, 'Winston');",
                    "INSERT INTO Customers (customer_id, name) VALUES (2, 'Jonathan');",
                    "INSERT INTO Customers (customer_id, name) VALUES (3, 'Annabelle');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (1, 1, 'Keyboard', '2020-07-31');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (2, 1, 'Mouse', '2020-07-31');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (3, 2, 'Laptop', '2020-07-29');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (4, 2, 'Monitor', '2020-07-29');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (5, 2, 'Speaker', '2020-07-31');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (6, 3, 'Printer', '2020-08-01');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (7, 3, 'Ink', '2020-08-01');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (8, 3, 'Paper', '2020-08-01');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (9, 3, 'Stapler', '2020-08-02');",
                ],
                "expected": [
                    ["Winston", 1, "2020-07-31", "Mouse"],
                    ["Winston", 1, "2020-07-31", "Keyboard"],
                    ["Jonathan", 2, "2020-07-31", "Speaker"],
                    ["Jonathan", 2, "2020-07-29", "Monitor"],
                    ["Jonathan", 2, "2020-07-29", "Laptop"],
                    ["Annabelle", 3, "2020-08-02", "Stapler"],
                    ["Annabelle", 3, "2020-08-01", "Paper"],
                    ["Annabelle", 3, "2020-08-01", "Ink"],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Customers (customer_id, name) VALUES (1, 'Winston');",
                    "INSERT INTO Customers (customer_id, name) VALUES (2, 'Jonathan');",
                    "INSERT INTO Customers (customer_id, name) VALUES (3, 'Annabelle');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (1, 1, 'Keyboard', '2020-07-31');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (2, 1, 'Mouse', '2020-07-31');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (3, 2, 'Laptop', '2020-07-29');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (4, 2, 'Monitor', '2020-07-29');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (5, 2, 'Speaker', '2020-07-31');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (6, 3, 'Printer', '2020-08-01');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (7, 3, 'Ink', '2020-08-01');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (8, 3, 'Paper', '2020-08-01');",
                    "INSERT INTO Orders (order_id, customer_id, product_name, order_date) VALUES (9, 3, 'Stapler', '2020-08-02');",
                ],
                "expected": [
                    ["Winston", 1, "2020-07-31", "Mouse"],
                    ["Winston", 1, "2020-07-31", "Keyboard"],
                    ["Jonathan", 2, "2020-07-31", "Speaker"],
                    ["Jonathan", 2, "2020-07-29", "Monitor"],
                    ["Jonathan", 2, "2020-07-29", "Laptop"],
                    ["Annabelle", 3, "2020-08-02", "Stapler"],
                    ["Annabelle", 3, "2020-08-01", "Paper"],
                    ["Annabelle", 3, "2020-08-01", "Ink"],
                ],
            },
        ],
    },
    {
        "id": 1013,
        "title": "Trips and Users",
        "difficulty": "Hard",
        "topic": "Database",
        "tags": ["sql", "join", "aggregation", "case"],
        "companiesAsked": ["Meta", "Google"],
        "description": (
            "Write a solution to find the **cancellation rate** of requests with unbanned "
            "users, per day, between 2013-10-01 and 2013-10-03. Round the rate to two "
            "decimal places and return the day and the rate.\n\n"
            "A trip is cancelled when its `status` is `cancelled_by_client` or "
            "`cancelled_by_driver`. Trips whose client or driver is banned are excluded "
            "entirely from both the numerator and the denominator."
        ),
        "constraints": (
            "id is the primary key of Trips\n"
            "users_id is the primary key of Users\n"
            "A trip has one client and one driver, both present in Users\n"
            "status is one of 'completed', 'cancelled_by_client', 'cancelled_by_driver'"
        ),
        "follow_up": None,
        "hints": [
            "Join Trips twice — once to Users as the client, once as the driver — keeping only 'No'-banned users on both sides.",
            "SUM(CASE WHEN status IN ('cancelled_by_client', 'cancelled_by_driver') THEN 1 ELSE 0 END) * 1.0 / COUNT(*) gives the rate without integer division.",
            "Filter request_at BETWEEN the two dates before grouping by day.",
        ],
        "timeComplexity": "O(n)",
        "spaceComplexity": "O(1)",
        "sql_schema": [
            "CREATE TABLE Trips (id INT PRIMARY KEY, client_id INT, driver_id INT, city_id INT, status VARCHAR(50), request_at DATE);",
            "CREATE TABLE Users (users_id INT PRIMARY KEY, banned VARCHAR(3), role VARCHAR(20));",
        ],
        "starterCode": (
            "-- Write your SQL query below\n"
            "SELECT\n"
            "    -- your columns here\n"
            "FROM\n"
            "    Trips;\n"
        ),
        "starter_code": {
            "sql": (
                "-- Write your SQL query below\n"
                "SELECT\n"
                "    -- your columns here\n"
                "FROM\n"
                "    Trips;\n"
            ),
        },
        "solution_sql": (
            "SELECT t.request_at AS Day,\n"
            "       ROUND(\n"
            "           SUM(CASE WHEN t.status IN ('cancelled_by_client', 'cancelled_by_driver')\n"
            "                    THEN 1 ELSE 0 END) * 1.0 / COUNT(*),\n"
            "           2\n"
            "       ) AS rate\n"
            "FROM Trips t\n"
            "JOIN Users c ON t.client_id = c.users_id AND c.banned = 'No'\n"
            "JOIN Users d ON t.driver_id = d.users_id AND d.banned = 'No'\n"
            "WHERE t.request_at BETWEEN '2013-10-01' AND '2013-10-03'\n"
            "GROUP BY t.request_at;\n"
        ),
        "solutionCode": (
            "SELECT t.request_at AS Day,\n"
            "       ROUND(\n"
            "           SUM(CASE WHEN t.status IN ('cancelled_by_client', 'cancelled_by_driver')\n"
            "                    THEN 1 ELSE 0 END) * 1.0 / COUNT(*),\n"
            "           2\n"
            "       ) AS rate\n"
            "FROM Trips t\n"
            "JOIN Users c ON t.client_id = c.users_id AND c.banned = 'No'\n"
            "JOIN Users d ON t.driver_id = d.users_id AND d.banned = 'No'\n"
            "WHERE t.request_at BETWEEN '2013-10-01' AND '2013-10-03'\n"
            "GROUP BY t.request_at;\n"
        ),
        "testCases": [
            {
                "seed": [
                    "INSERT INTO Users (users_id, banned, role) VALUES (1, 'No', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (2, 'Yes', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (3, 'No', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (4, 'No', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (10, 'No', 'driver');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (11, 'No', 'driver');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (12, 'No', 'driver');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (13, 'No', 'driver');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (1, 1, 10, 1, 'completed', '2013-10-01');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (2, 2, 11, 1, 'cancelled_by_driver', '2013-10-01');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (3, 3, 12, 6, 'completed', '2013-10-01');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (4, 4, 13, 6, 'cancelled_by_client', '2013-10-01');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (5, 1, 10, 1, 'completed', '2013-10-02');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (6, 2, 11, 6, 'completed', '2013-10-02');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (7, 3, 12, 6, 'completed', '2013-10-02');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (8, 2, 12, 12, 'completed', '2013-10-03');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (9, 3, 10, 12, 'completed', '2013-10-03');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (10, 4, 13, 12, 'cancelled_by_driver', '2013-10-03');",
                ],
                "expected": [
                    ["2013-10-01", 0.33],
                    ["2013-10-02", 0.0],
                    ["2013-10-03", 0.5],
                ],
            },
        ],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Users (users_id, banned, role) VALUES (1, 'No', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (2, 'Yes', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (3, 'No', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (4, 'No', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (10, 'No', 'driver');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (11, 'No', 'driver');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (12, 'No', 'driver');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (13, 'No', 'driver');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (1, 1, 10, 1, 'completed', '2013-10-01');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (2, 2, 11, 1, 'cancelled_by_driver', '2013-10-01');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (3, 3, 12, 6, 'completed', '2013-10-01');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (4, 4, 13, 6, 'cancelled_by_client', '2013-10-01');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (5, 1, 10, 1, 'completed', '2013-10-02');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (6, 2, 11, 6, 'completed', '2013-10-02');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (7, 3, 12, 6, 'completed', '2013-10-02');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (8, 2, 12, 12, 'completed', '2013-10-03');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (9, 3, 10, 12, 'completed', '2013-10-03');",
                    "INSERT INTO Trips (id, client_id, driver_id, city_id, status, request_at) VALUES (10, 4, 13, 12, 'cancelled_by_driver', '2013-10-03');",
                ],
                "expected": [
                    ["2013-10-01", 0.33],
                    ["2013-10-02", 0.0],
                    ["2013-10-03", 0.5],
                ],
            },
        ],
    },
]
