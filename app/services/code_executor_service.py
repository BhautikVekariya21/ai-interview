"""
Code Executor Service — Subprocess execution sandbox & AI Code Evaluator.

Supports Python 3, JavaScript (Node.js), and Rust code execution against
curated test suites with memory, execution time (ms), and AI Big-O analysis.
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from functools import lru_cache
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.services import problem_enrichment, static_harness
from app.services.code_runners import (
    DESIGN_HARNESS_BUILDERS,
    DESIGN_UNSUPPORTED,
    HARNESS_BUILDERS,
    VERIFY_UNTYPEABLE,
    build_sql_harness,
    get_spec,
    resolve_language,
)
from app.services.code_sandbox import SandboxUnavailable, get_sandbox
from app.services.llm_service import get_llm

# The generated 1000-problem bank is pure function-language data. SQL coverage
# lives in ``coding_sql_problems_data`` and is merged in here at import time so
# the bank index, catalogue and grading dispatch see the database problems
# without a regeneration step. ``scratch/generate_1000_problems.py`` writes
# them back into the file when the bank is regenerated.
from app.services.coding_problems_data import PROBLEMS as _CODING_BANK_PROBLEMS
from app.services.coding_sql_problems_data import SQL_PROBLEMS as _SQL_BANK_PROBLEMS

# Idempotent: a regeneration writes the SQL problems into the bank file, so a
# runtime extend must not re-add ids that are already present — doing so would
# duplicate ids 1001+ in the bank and break the id-uniqueness invariant.
_EXISTING_BANK_IDS = {p["id"] for p in _CODING_BANK_PROBLEMS}
_CODING_BANK_PROBLEMS.extend(
    p for p in _SQL_BANK_PROBLEMS if p["id"] not in _EXISTING_BANK_IDS
)

# ── Curated Problem Registry ──────────────────────────────────────────────────

CURATED_PROBLEMS: List[Dict[str, Any]] = [
    {
        "id": "two-sum",
        "entry_point": ["two_sum", "twoSum"],
        "title": "Two Sum",
        "difficulty": "Easy",
        "category": "Arrays & Hashing",
        "tags": ["array", "hash-map"],
        "companies": ["Google", "Amazon", "Meta", "Apple", "Microsoft"],
        "description": (
            "Given an array of integers `nums` and an integer `target`, return "
            "indices of the two numbers such that they add up to `target`.\n\n"
            "Assume each input has **exactly one solution**, and you may not use the same element twice."
        ),
        "constraints": "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9",
        "examples": [
            {"input": "nums = [2, 7, 11, 15], target = 9", "output": "[0, 1]"},
            {"input": "nums = [3, 2, 4], target = 6", "output": "[1, 2]"},
        ],
        "starter_code": {
            "python": "def two_sum(nums: list[int], target: int) -> list[int]:\n    # Your solution here\n    pass\n",
            "javascript": "function twoSum(nums, target) {\n  // Your solution here\n}\n",
            "rust": "pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {\n    // Your solution here\n    vec![]\n}\n",
        },
        "test_cases": [
            {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
            {"input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]},
            {"input": {"nums": [3, 3], "target": 6}, "expected": [0, 1]},
        ],
    },
    {
        "id": "valid-anagram",
        "entry_point": ["is_anagram", "isAnagram"],
        "title": "Valid Anagram",
        "difficulty": "Easy",
        "category": "Arrays & Hashing",
        "tags": ["string", "hash-table"],
        "companies": ["Amazon", "Google", "Microsoft"],
        "description": (
            "Given two strings `s` and `t`, return `true` if `t` is an anagram of `s`, and `false` otherwise."
        ),
        "constraints": "1 <= s.length, t.length <= 5 * 10^4",
        "examples": [
            {"input": 's = "anagram", t = "nagaram"', "output": "true"},
            {"input": 's = "rat", t = "car"', "output": "false"},
        ],
        "starter_code": {
            "python": "def is_anagram(s: str, t: str) -> bool:\n    # Your solution here\n    pass\n",
            "javascript": "function isAnagram(s, t) {\n  // Your solution here\n}\n",
            "rust": "pub fn is_anagram(s: String, t: String) -> bool {\n    // Your solution here\n    false\n}\n",
        },
        "test_cases": [
            {"input": {"s": "anagram", "t": "nagaram"}, "expected": True},
            {"input": {"s": "rat", "t": "car"}, "expected": False},
        ],
    },
    {
        "id": "valid-parentheses",
        "entry_point": ["is_valid", "isValid"],
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "category": "Stack",
        "tags": ["string", "stack"],
        "companies": ["Amazon", "Meta", "Google", "Bloomberg"],
        "description": (
            "Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', "
            "determine if the input string is valid."
        ),
        "constraints": "1 <= s.length <= 10^4",
        "examples": [
            {"input": 's = "()"', "output": "true"},
            {"input": 's = "()[]{}"', "output": "true"},
            {"input": 's = "(]"', "output": "false"},
        ],
        "starter_code": {
            "python": "def is_valid(s: str) -> bool:\n    # Your solution here\n    pass\n",
            "javascript": "function isValid(s) {\n  // Your solution here\n}\n",
            "rust": "pub fn is_valid(s: String) -> bool {\n    // Your solution here\n    false\n}\n",
        },
        "test_cases": [
            {"input": {"s": "()"}, "expected": True},
            {"input": {"s": "()[]{}"}, "expected": True},
            {"input": {"s": "(]"}, "expected": False},
        ],
    },
    {
        "id": "binary-search",
        "entry_point": ["search", "binary_search", "binarySearch"],
        "title": "Binary Search",
        "difficulty": "Easy",
        "category": "Binary Search",
        "tags": ["array", "binary-search"],
        "companies": ["Apple", "Google", "Microsoft"],
        "description": (
            "Given an array of integers `nums` sorted in ascending order, and an integer `target`, "
            "write a function to search `target` in `nums`. If target exists, return its index; otherwise, return -1."
        ),
        "constraints": "1 <= nums.length <= 10^4",
        "examples": [
            {"input": "nums = [-1,0,3,5,9,12], target = 9", "output": "4"},
            {"input": "nums = [-1,0,3,5,9,12], target = 2", "output": "-1"},
        ],
        "starter_code": {
            "python": "def search(nums: list[int], target: int) -> int:\n    # Your solution here\n    pass\n",
            "javascript": "function search(nums, target) {\n  // Your solution here\n}\n",
            "rust": "pub fn search(nums: Vec<i32>, target: i32) -> i32 {\n    // Your solution here\n    -1\n}\n",
        },
        "test_cases": [
            {"input": {"nums": [-1, 0, 3, 5, 9, 12], "target": 9}, "expected": 4},
            {"input": {"nums": [-1, 0, 3, 5, 9, 12], "target": 2}, "expected": -1},
        ],
    },
    {
        "id": "maximum-subarray",
        "entry_point": ["max_sub_array", "maxSubArray"],
        "title": "Maximum Subarray",
        "difficulty": "Medium",
        "category": "Dynamic Programming",
        "tags": ["array", "divide-and-conquer", "dp"],
        "companies": ["Amazon", "Microsoft", "Apple", "Cisco"],
        "description": (
            "Given an integer array `nums`, find the subarray with the largest sum, and return its sum."
        ),
        "constraints": "1 <= nums.length <= 10^5",
        "examples": [
            {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "output": "6"},
            {"input": "nums = [1]", "output": "1"},
        ],
        "starter_code": {
            "python": "def max_sub_array(nums: list[int]) -> int:\n    # Your solution here\n    pass\n",
            "javascript": "function maxSubArray(nums) {\n  // Your solution here\n}\n",
            "rust": "pub fn max_sub_array(nums: Vec<i32>) -> i32 {\n    // Your solution here\n    0\n}\n",
        },
        "test_cases": [
            {"input": {"nums": [-2, 1, -3, 4, -1, 2, 1, -5, 4]}, "expected": 6},
            {"input": {"nums": [1]}, "expected": 1},
            {"input": {"nums": [5, 4, -1, 7, 8]}, "expected": 23},
        ],
    },
    {
        "id": "lru-cache",
        "entry_point": ["LRUCache"],
        # Stateful design problem: the test case is a sequence of operations
        # against a class instance, not a pure function call, so the generic
        # function harness cannot grade it. Marked explicitly so it reports
        # "not graded" instead of being misgraded by an argument-binding guess.
        "grading": "unsupported",
        "grading_reason": (
            "Stateful design problems are executed but not auto-graded yet: the "
            "test case is an operation sequence against a class instance rather "
            "than a single function call."
        ),
        "title": "LRU Cache",
        "difficulty": "Hard",
        "category": "Design",
        "tags": ["hash-table", "linked-list", "design"],
        "companies": ["Amazon", "Google", "Meta", "Apple", "Microsoft"],
        "description": (
            "Design a data structure that follows the constraints of a **Least Recently Used (LRU) Cache**.\n\n"
            "Implement `get(key)` and `put(key, value)` in `O(1)` average time complexity."
        ),
        "constraints": "1 <= capacity <= 3000",
        "examples": [
            {"input": '["LRUCache", "put", "put", "get", "put", "get"]', "output": "[null, null, null, 1, null, -1]"},
        ],
        "starter_code": {
            "python": "class LRUCache:\n    def __init__(self, capacity: int):\n        pass\n    def get(self, key: int) -> int:\n        return -1\n    def put(self, key: int, value: int) -> None:\n        pass\n",
            "javascript": "class LRUCache {\n  constructor(capacity) {}\n  get(key) { return -1; }\n  put(key, value) {}\n}\n",
            "rust": "pub struct LRUCache {\n    capacity: usize,\n}\nimpl LRUCache {\n    pub fn new(capacity: i32) -> Self { LRUCache { capacity: capacity as usize } }\n    pub fn get(&mut self, key: i32) -> i32 { -1 }\n    pub fn put(&mut self, key: i32, value: i32) {}\n}\n",
        },
        "test_cases": [
            {"input": {"capacity": 2, "ops": [["put", 1, 1], ["put", 2, 2], ["get", 1], ["put", 3, 3], ["get", 2]]}, "expected": [None, None, 1, None, -1]},
        ],
    },
    # ── Database problems ──────────────────────────────────────────────────────
    #
    # These are graded by running the candidate's SQL against an in-memory
    # SQLite database built from ``sql_schema``, seeded per case with
    # ``test_cases[].seed``, and comparing the returned rows against
    # ``test_cases[].expected``. Result order is unspecified without an ORDER BY,
    # so the harness compares rows as sets. Difficulty mirrors the LeetCode
    # database ladder: Basic (Easy), Intermediate (Medium), Advanced (Hard).
    {
        "id": "combine-two-tables",
        "entry_point": [],
        "title": "Combine Two Tables",
        "difficulty": "Easy",
        "category": "Database",
        "tags": ["sql", "join"],
        "companies": ["Apple", "Amazon", "Google"],
        "description": (
            "Write a solution to report the first name, last name, city, and state "
            "of each person in the `Person` table. If the address of a `personId` "
            "is not present in the `Address` table, report `null` instead.\n\n"
            "A `LEFT JOIN` guarantees every person appears at least once, with "
            "`null` for the address columns when no matching address exists."
        ),
        "constraints": "personId is the primary key of Person\naddressId is the primary key of Address\nThere are no rows in Address with a null personId",
        "examples": [
            {
                "input": "Person: [(1, Wang, Allen), (2, Alice, Bob)]; Address: [(1, 2, New York City, New York)]",
                "output": "[[Allen, Wang, null, null], [Bob, Alice, New York City, New York]]",
            }
        ],
        "sql_schema": [
            "CREATE TABLE Person (personId INT PRIMARY KEY, lastName VARCHAR(255), firstName VARCHAR(255));",
            "CREATE TABLE Address (addressId INT PRIMARY KEY, personId INT, city VARCHAR(255), state VARCHAR(255));",
        ],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Person\n    LEFT JOIN Address ON Person.personId = Address.personId;\n"},
        "solution_sql": (
            "SELECT p.firstName, p.lastName, a.city, a.state\n"
            "FROM Person p\n"
            "LEFT JOIN Address a ON p.personId = a.personId;\n"
        ),
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Person (personId, lastName, firstName) VALUES (1, 'Wang', 'Allen');",
                    "INSERT INTO Person (personId, lastName, firstName) VALUES (2, 'Alice', 'Bob');",
                    "INSERT INTO Address (addressId, personId, city, state) VALUES (1, 2, 'New York City', 'New York');",
                    "INSERT INTO Address (addressId, personId, city, state) VALUES (2, 3, 'Leetcode', 'California');",
                ],
                "expected": [
                    ["Allen", "Wang", None, None],
                    ["Bob", "Alice", "New York City", "New York"],
                ],
            },
        ],
        "hints": [
            "A LEFT JOIN keeps every row from the left table even when the right side has no match.",
            "Join on Person.personId = Address.personId so each person pairs with exactly one address.",
        ],
        "follow_up": None,
    },
    {
        "id": "duplicate-emails",
        "entry_point": [],
        "title": "Duplicate Emails",
        "difficulty": "Easy",
        "category": "Database",
        "tags": ["sql", "group-by"],
        "companies": ["Amazon", "Google"],
        "description": (
            "Write a solution to report all the duplicate emails in the `Person` "
            "table. Note that an email is guaranteed **not** to be duplicated "
            "at most once — it either appears once or twice."
        ),
        "constraints": "id is the primary key of Person\nEach email appears at most twice",
        "examples": [
            {
                "input": "Person: [(1, a@b.com), (2, c@d.com), (3, a@b.com)]",
                "output": "[[a@b.com]]",
            }
        ],
        "sql_schema": ["CREATE TABLE Person (id INT PRIMARY KEY, email VARCHAR(255));"],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Person;\n"},
        "solution_sql": "SELECT email FROM Person GROUP BY email HAVING COUNT(*) > 1;\n",
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Person (id, email) VALUES (1, 'a@b.com');",
                    "INSERT INTO Person (id, email) VALUES (2, 'c@d.com');",
                    "INSERT INTO Person (id, email) VALUES (3, 'a@b.com');",
                ],
                "expected": [["a@b.com"]],
            },
        ],
        "hints": [
            "GROUP BY email and keep only groups with more than one row (HAVING COUNT(*) > 1).",
        ],
        "follow_up": None,
    },
    {
        "id": "employees-earning-more-than-managers",
        "entry_point": [],
        "title": "Employees Earning More Than Their Managers",
        "difficulty": "Easy",
        "category": "Database",
        "tags": ["sql", "self-join"],
        "companies": ["Amazon", "Google", "Microsoft"],
        "description": (
            "Write a solution to find the employees who earn more than their "
            "managers. Return the result table in **any order**. The `managerId` "
            "column references the `id` of another employee in the same table — "
            "a self-referencing foreign key."
        ),
        "constraints": "id is the primary key of Employee\nmanagerId is a foreign key referencing Employee.id",
        "examples": [
            {
                "input": "Employee: [(1, Joe, 70000, 3), (2, Henry, 80000, 4), (3, Sam, 60000, null), (4, Max, 90000, null)]",
                "output": "[[Joe]]",
            }
        ],
        "sql_schema": ["CREATE TABLE Employee (id INT PRIMARY KEY, name VARCHAR(255), salary INT, managerId INT);"],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Employee;\n"},
        "solution_sql": (
            "SELECT e1.name FROM Employee e1\n"
            "JOIN Employee e2 ON e1.managerId = e2.id\n"
            "WHERE e1.salary > e2.salary;\n"
        ),
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, name, salary, managerId) VALUES (1, 'Joe', 70000, 3);",
                    "INSERT INTO Employee (id, name, salary, managerId) VALUES (2, 'Henry', 80000, 4);",
                    "INSERT INTO Employee (id, name, salary, managerId) VALUES (3, 'Sam', 60000, NULL);",
                    "INSERT INTO Employee (id, name, salary, managerId) VALUES (4, 'Max', 90000, NULL);",
                ],
                "expected": [["Joe"]],
            },
        ],
        "hints": [
            "Self-join: the employee's manager is another row of the same table.",
            "Filter on e1.salary > e2.salary where e1.managerId = e2.id.",
        ],
        "follow_up": None,
    },
    {
        "id": "rank-scores",
        "entry_point": [],
        "title": "Rank Scores",
        "difficulty": "Medium",
        "category": "Database",
        "tags": ["sql", "window-functions"],
        "companies": ["Amazon", "Meta"],
        "description": (
            "Write a solution to find the rank of the scores. The ranking should "
            "be calculated according to the following rules:\n\n"
            "- The scores should be ranked from the highest to the lowest.\n"
            "- If there is a tie between two scores, both should have the same "
            "ranking.\n"
            "- After a tie, the next ranking number should be the next consecutive "
            "integer value (no gaps — this is a **dense** rank)."
        ),
        "constraints": "id is the primary key of Scores\nEach score is a decimal value between 0.00 and 4.00",
        "examples": [
            {
                "input": "Scores: [(1, 3.50), (2, 3.65), (3, 4.00), (4, 3.85), (5, 4.00), (6, 3.65)]",
                "output": "[[4.00, 1], [4.00, 1], [3.85, 2], [3.65, 3], [3.65, 3], [3.50, 4]]",
            }
        ],
        "sql_schema": ["CREATE TABLE Scores (id INT PRIMARY KEY, score DECIMAL(3, 2));"],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Scores;\n"},
        "solution_sql": "SELECT score, DENSE_RANK() OVER (ORDER BY score DESC) AS 'rank' FROM Scores;\n",
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Scores (id, score) VALUES (1, 3.50);",
                    "INSERT INTO Scores (id, score) VALUES (2, 3.65);",
                    "INSERT INTO Scores (id, score) VALUES (3, 4.00);",
                    "INSERT INTO Scores (id, score) VALUES (4, 3.85);",
                    "INSERT INTO Scores (id, score) VALUES (5, 4.00);",
                    "INSERT INTO Scores (id, score) VALUES (6, 3.65);",
                ],
                "expected": [[4.0, 1], [4.0, 1], [3.85, 2], [3.65, 3], [3.65, 3], [3.5, 4]],
            },
        ],
        "hints": [
            "DENSE_RANK() OVER (ORDER BY score DESC) assigns 1, 2, 3… with no gaps after ties.",
            "Without an ORDER BY on the outer query the row order is unspecified — the grader sorts both sides.",
        ],
        "follow_up": "Could you rank with gaps (RANK instead of DENSE_RANK) and explain when each is correct?",
    },
    {
        "id": "consecutive-numbers",
        "entry_point": [],
        "title": "Consecutive Numbers",
        "difficulty": "Medium",
        "category": "Database",
        "tags": ["sql", "self-join"],
        "companies": ["Google", "Microsoft"],
        "description": (
            "Write a solution to find all numbers that appear **at least three "
            "times consecutively** in the `Logs` table (the `id` column holds "
            "consecutive integers that identify each row's position). Return the "
            "result table in **any order**."
        ),
        "constraints": "id is the primary key of Logs\nid is an auto-incrementing integer with no gaps",
        "examples": [
            {
                "input": "Logs: [(1, 1), (2, 1), (3, 1), (4, 2), (5, 1), (6, 2), (7, 2)]",
                "output": "[[1]]",
            }
        ],
        "sql_schema": ["CREATE TABLE Logs (id INT PRIMARY KEY, num INT);"],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Logs;\n"},
        "solution_sql": (
            "SELECT DISTINCT l1.num AS ConsecutiveNums\n"
            "FROM Logs l1, Logs l2, Logs l3\n"
            "WHERE l1.id = l2.id - 1 AND l2.id = l3.id - 1\n"
            "  AND l1.num = l2.num AND l2.num = l3.num;\n"
        ),
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
        "hints": [
            "Join the table to itself three times, offsetting each copy by one id.",
            "Consecutive means l1.id = l2.id - 1 AND l2.id = l3.id - 1 with equal num values.",
        ],
        "follow_up": None,
    },
    {
        "id": "exchange-seats",
        "entry_point": [],
        "title": "Exchange Seats",
        "difficulty": "Medium",
        "category": "Database",
        "tags": ["sql", "case-when"],
        "companies": ["Amazon"],
        "description": (
            "Write a solution to swap the seat id of **every two consecutive "
            "students**. If the number of students is odd, the id of the last "
            "student is **not** swapped. Return the result table ordered by `id` "
            "in ascending order."
        ),
        "constraints": "id is the primary key of Seat\nThe number of rows is at most 1000",
        "examples": [
            {
                "input": "Seat: [(1, Abbot), (2, Doris), (3, Emerson), (4, Green), (5, Jeames)]",
                "output": "[(1, Doris), (2, Abbot), (3, Green), (4, Emerson), (5, Jeames)]",
            }
        ],
        "sql_schema": ["CREATE TABLE Seat (id INT PRIMARY KEY, student VARCHAR(255));"],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Seat;\n"},
        "solution_sql": (
            "SELECT s1.id, COALESCE(s2.student, s1.student) AS student\n"
            "FROM Seat s1\n"
            "LEFT JOIN Seat s2\n"
            "  ON (s1.id % 2 = 1 AND s1.id + 1 = s2.id)\n"
            "  OR (s1.id % 2 = 0 AND s1.id - 1 = s2.id)\n"
            "ORDER BY s1.id;\n"
        ),
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Seat (id, student) VALUES (1, 'Abbot');",
                    "INSERT INTO Seat (id, student) VALUES (2, 'Doris');",
                    "INSERT INTO Seat (id, student) VALUES (3, 'Emerson');",
                    "INSERT INTO Seat (id, student) VALUES (4, 'Green');",
                    "INSERT INTO Seat (id, student) VALUES (5, 'Jeames');",
                ],
                "expected": [
                    [1, "Doris"],
                    [2, "Abbot"],
                    [3, "Green"],
                    [4, "Emerson"],
                    [5, "Jeames"],
                ],
            },
        ],
        "hints": [
            "Odd ids swap with id + 1, even ids with id - 1, and the last odd id stays put.",
            "A LEFT JOIN on the partner id plus COALESCE keeps the unpaired last row.",
        ],
        "follow_up": None,
    },
    {
        "id": "department-top-three-salaries",
        "entry_point": [],
        "title": "Department Top Three Salaries",
        "difficulty": "Hard",
        "category": "Database",
        "tags": ["sql", "window-functions"],
        "companies": ["Google", "Meta", "Amazon"],
        "description": (
            "A company's executives are interested in seeing who earns the most "
            "money in each department. Write a solution to find the employees "
            "who have the **top three unique salaries** in each department. "
            "A customer's salary is considered in the top three unique salaries "
            "if it is one of the three highest distinct salaries for that "
            "department. Return the result ordered by department name, then by "
            "salary descending."
        ),
        "constraints": "id is the primary key of Employee\ndepartmentId is a foreign key referencing Department.id",
        "examples": [
            {
                "input": "Employee: [(1, Joe, 85000, 1), (2, Henry, 80000, 2), (3, Sam, 60000, 2), (4, Max, 90000, 1), (5, Janet, 69000, 1), (6, Randy, 85000, 1), (7, Will, 70000, 1)]; Department: [(1, IT), (2, Sales)]",
                "output": "[[IT, Max, 90000], [IT, Joe, 85000], [IT, Randy, 85000], [IT, Will, 70000], [Sales, Henry, 80000], [Sales, Sam, 60000]]",
            }
        ],
        "sql_schema": [
            "CREATE TABLE Employee (id INT PRIMARY KEY, name VARCHAR(255), salary INT, departmentId INT);",
            "CREATE TABLE Department (id INT PRIMARY KEY, name VARCHAR(255));",
        ],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Employee;\n"},
        "solution_sql": (
            "SELECT d.name AS Department, e.name AS Employee, e.salary AS Salary\n"
            "FROM Employee e\n"
            "JOIN Department d ON e.departmentId = d.id\n"
            "WHERE (SELECT COUNT(DISTINCT e2.salary) FROM Employee e2\n"
            "       WHERE e2.departmentId = e.departmentId\n"
            "         AND e2.salary > e.salary) < 3\n"
            "ORDER BY d.name, e.salary DESC;\n"
        ),
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
        "hints": [
            "A correlated subquery can count distinct higher salaries in the same department.",
            "DENSE_RANK() OVER (PARTITION BY departmentId ORDER BY salary DESC) keeps exactly the top three tiers.",
        ],
        "follow_up": "What changes if you must return the top three employees rather than top three salary values?",
    },
    {
        "id": "trips-and-users",
        "entry_point": [],
        "title": "Trips and Users",
        "difficulty": "Hard",
        "category": "Database",
        "tags": ["sql", "joins", "aggregation"],
        "companies": ["Google", "Amazon"],
        "description": (
            "Write a solution to find the **cancellation rate** of requests with "
            "unbanned users (both client and driver must not be banned) each day "
            "between `2013-10-01` and `2013-10-03`. Round the cancellation rate "
            "to two decimal places.\n\n"
            "The cancellation rate is computed by dividing the number of cancelled "
            "requests by the total number of requests made on that day. A request "
            "is cancelled when its status is either `cancelled_by_driver` or "
            "`cancelled_by_client`."
        ),
        "constraints": "id is the primary key of Trips\nusers_id is the primary key of Users\nEach user's role is either 'client' or 'driver'",
        "examples": [
            {
                "input": "Trips and Users per the LeetCode sample",
                "output": "[[2013-10-01, 0.33], [2013-10-02, 0.00], [2013-10-03, 0.50]]",
            }
        ],
        "sql_schema": [
            "CREATE TABLE Trips (id INT PRIMARY KEY, client_id INT, driver_id INT, city_id INT, status VARCHAR(50), request_at VARCHAR(50));",
            "CREATE TABLE Users (users_id INT PRIMARY KEY, banned VARCHAR(50), role VARCHAR(50));",
        ],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Trips;\n"},
        "solution_sql": (
            "SELECT t.request_at AS Day,\n"
            "       ROUND(SUM(CASE WHEN t.status IN ('cancelled_by_driver', 'cancelled_by_client') "
            "THEN 1.0 ELSE 0.0 END) / COUNT(*), 2) AS 'Cancellation Rate'\n"
            "FROM Trips t\n"
            "JOIN Users u1 ON t.client_id = u1.users_id AND u1.banned = 'No'\n"
            "JOIN Users u2 ON t.driver_id = u2.users_id AND u2.banned = 'No'\n"
            "WHERE t.request_at BETWEEN '2013-10-01' AND '2013-10-03'\n"
            "GROUP BY t.request_at;\n"
        ),
        "test_cases": [
            {
                "seed": [
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
                    "INSERT INTO Users (users_id, banned, role) VALUES (1, 'No', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (2, 'Yes', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (3, 'No', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (4, 'No', 'client');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (10, 'No', 'driver');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (11, 'No', 'driver');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (12, 'No', 'driver');",
                    "INSERT INTO Users (users_id, banned, role) VALUES (13, 'No', 'driver');",
                ],
                "expected": [["2013-10-01", 0.33], ["2013-10-02", 0.0], ["2013-10-03", 0.5]],
            },
        ],
        "hints": [
            "Join Trips to Users twice — once for the client, once for the driver — keeping only unbanned rows.",
            "Divide SUM(CASE WHEN status LIKE 'cancelled%' THEN 1.0 ELSE 0.0 END) by COUNT(*) and ROUND to 2.",
        ],
        "follow_up": None,
    },
    {
        "id": "human-traffic-of-stadium",
        "entry_point": [],
        "title": "Human Traffic of Stadium",
        "difficulty": "Hard",
        "category": "Database",
        "tags": ["sql", "self-join"],
        "companies": ["Google", "Meta"],
        "description": (
            "Write a solution to report the consecutive days with **more than or "
            "equal to 100** visitors. Return the result table ordered by `visit_date` "
            "in ascending order.\n\n"
            "Only days that belong to a group of **at least three consecutive** "
            "days (by `id`, which increases by exactly one each day) qualify. "
            "`visit_date` is the date of the visit, and `people` is the number of "
            "visitors on that day."
        ),
        "constraints": "id is the primary key of Stadium\nEach day has exactly one record\nvisit_date is a unique date",
        "examples": [
            {
                "input": "Stadium: [(1, 2017-01-01, 10), (2, 2017-01-02, 109), (3, 2017-01-03, 150), (4, 2017-01-04, 99), (5, 2017-01-05, 145), (6, 2017-01-06, 1455), (7, 2017-01-07, 199), (8, 2017-01-09, 188)]",
                "output": "[[5, 2017-01-05, 145], [6, 2017-01-06, 1455], [7, 2017-01-07, 199], [8, 2017-01-09, 188]]",
            }
        ],
        "sql_schema": ["CREATE TABLE Stadium (id INT PRIMARY KEY, visit_date DATE, people INT);"],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Stadium;\n"},
        "solution_sql": (
            "SELECT s1.id, s1.visit_date, s1.people\n"
            "FROM Stadium s1, Stadium s2, Stadium s3\n"
            "WHERE s1.people >= 100 AND s2.people >= 100 AND s3.people >= 100\n"
            "  AND ((s1.id = s2.id - 1 AND s2.id = s3.id - 1)\n"
            "    OR (s1.id = s2.id + 1 AND s2.id = s3.id + 1)\n"
            "    OR (s1.id = s2.id - 1 AND s2.id = s3.id + 1))\n"
            "GROUP BY s1.id, s1.visit_date, s1.people\n"
            "ORDER BY s1.id;\n"
        ),
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Stadium (id, visit_date, people) VALUES (1, '2017-01-01', 10);",
                    "INSERT INTO Stadium (id, visit_date, people) VALUES (2, '2017-01-02', 109);",
                    "INSERT INTO Stadium (id, visit_date, people) VALUES (3, '2017-01-03', 150);",
                    "INSERT INTO Stadium (id, visit_date, people) VALUES (4, '2017-01-04', 99);",
                    "INSERT INTO Stadium (id, visit_date, people) VALUES (5, '2017-01-05', 145);",
                    "INSERT INTO Stadium (id, visit_date, people) VALUES (6, '2017-01-06', 1455);",
                    "INSERT INTO Stadium (id, visit_date, people) VALUES (7, '2017-01-07', 199);",
                    "INSERT INTO Stadium (id, visit_date, people) VALUES (8, '2017-01-09', 188);",
                ],
                "expected": [
                    [5, "2017-01-05", 145],
                    [6, "2017-01-06", 1455],
                    [7, "2017-01-07", 199],
                    [8, "2017-01-09", 188],
                ],
            },
        ],
        "hints": [
            "Self-join the table three times so three consecutive ids share one query row.",
            "A day qualifies if it is the start, middle, or end of any three consecutive ids all above 100.",
        ],
        "follow_up": None,
    },
    {
        "id": "game-play-analysis",
        "entry_point": [],
        "title": "Game Play Analysis I",
        "difficulty": "Easy",
        "category": "Database",
        "tags": ["sql", "group-by"],
        "companies": ["Amazon", "Google", "Meta"],
        "description": (
            "Write a solution to find the **first login date** for each player. "
            "Return the result table in **any order**.\n\n"
            "The `Activity` table records every login: a player can log in on "
            "several dates, and a player's first login is the earliest "
            "`event_date` recorded for their `player_id`."
        ),
        "constraints": "player_id and event_date together form the primary key of Activity\nA player may log in on multiple days",
        "examples": [
            {
                "input": "Activity: [(1, 2, 2016-03-01, 5), (1, 2, 2016-05-02, 6), (2, 3, 2017-06-25, 1), (3, 1, 2016-03-02, 0), (3, 4, 2018-07-03, 5)]",
                "output": "[[1, 2016-03-01], [2, 2017-06-25], [3, 2016-03-02]]",
            }
        ],
        "sql_schema": [
            "CREATE TABLE Activity (player_id INT, device_id INT, event_date DATE, games_played INT, PRIMARY KEY (player_id, event_date));",
        ],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Activity;\n"},
        "solution_sql": "SELECT player_id, MIN(event_date) AS first_login FROM Activity GROUP BY player_id;\n",
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (1, 2, '2016-03-01', 5);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (1, 2, '2016-05-02', 6);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (2, 3, '2017-06-25', 1);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (3, 1, '2016-03-02', 0);",
                    "INSERT INTO Activity (player_id, device_id, event_date, games_played) VALUES (3, 4, '2018-07-03', 5);",
                ],
                "expected": [
                    [1, "2016-03-01"],
                    [2, "2017-06-25"],
                    [3, "2016-03-02"],
                ],
            },
        ],
        "hints": [
            "GROUP BY player_id and take MIN(event_date) — the earliest login per player.",
            "The table-level primary key is (player_id, event_date), so a player never has two logins on the same day.",
        ],
        "follow_up": "Could you also report the device each player logged in with on their first day?",
    },
    {
        "id": "customer-who-visited-but-did-not-make-any-transactions",
        "entry_point": [],
        "title": "Customer Who Visited but Did Not Make Any Transactions",
        "difficulty": "Easy",
        "category": "Database",
        "tags": ["sql", "left-join"],
        "companies": ["Apple", "Google"],
        "description": (
            "Write a solution to find the IDs of the customers who visited a "
            "store **without making any transactions** and the number of times "
            "they made these types of visits. Return the result table in **any "
            "order**.\n\n"
            "A visit is without a transaction when no row in `Transactions` "
            "references its `visit_id` — a customer may appear several times in "
            "`Visits`, and each such visit counts separately."
        ),
        "constraints": "visit_id is the primary key of Visits\ntransaction_id is the primary key of Transactions\nA customer may visit multiple times",
        "examples": [
            {
                "input": "Visits: [(1, 23), (2, 9), (4, 30), (5, 54), (6, 96), (7, 54), (8, 54)]; Transactions: [(2, 5, 310), (3, 5, 300), (9, 5, 200), (12, 1, 910), (13, 2, 970)]",
                "output": "[[54, 2], [30, 1], [96, 1]]",
            }
        ],
        "sql_schema": [
            "CREATE TABLE Visits (visit_id INT PRIMARY KEY, customer_id INT);",
            "CREATE TABLE Transactions (transaction_id INT PRIMARY KEY, visit_id INT, amount INT);",
        ],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Visits;\n"},
        "solution_sql": (
            "SELECT v.customer_id, COUNT(*) AS count_no_trans\n"
            "FROM Visits v\n"
            "LEFT JOIN Transactions t ON v.visit_id = t.visit_id\n"
            "WHERE t.transaction_id IS NULL\n"
            "GROUP BY v.customer_id;\n"
        ),
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Visits (visit_id, customer_id) VALUES (1, 23);",
                    "INSERT INTO Visits (visit_id, customer_id) VALUES (2, 9);",
                    "INSERT INTO Visits (visit_id, customer_id) VALUES (4, 30);",
                    "INSERT INTO Visits (visit_id, customer_id) VALUES (5, 54);",
                    "INSERT INTO Visits (visit_id, customer_id) VALUES (6, 96);",
                    "INSERT INTO Visits (visit_id, customer_id) VALUES (7, 54);",
                    "INSERT INTO Visits (visit_id, customer_id) VALUES (8, 54);",
                    "INSERT INTO Transactions (transaction_id, visit_id, amount) VALUES (2, 5, 310);",
                    "INSERT INTO Transactions (transaction_id, visit_id, amount) VALUES (3, 5, 300);",
                    "INSERT INTO Transactions (transaction_id, visit_id, amount) VALUES (9, 5, 200);",
                    "INSERT INTO Transactions (transaction_id, visit_id, amount) VALUES (12, 1, 910);",
                    "INSERT INTO Transactions (transaction_id, visit_id, amount) VALUES (13, 2, 970);",
                ],
                "expected": [[54, 2], [30, 1], [96, 1]],
            },
        ],
        "hints": [
            "LEFT JOIN Transactions on visit_id and keep only rows where the transaction side is NULL.",
            "COUNT(*) counts the visits per customer — a customer can appear several times in Visits.",
        ],
        "follow_up": None,
    },
    {
        "id": "market-analysis-i",
        "entry_point": [],
        "title": "Market Analysis I",
        "difficulty": "Medium",
        "category": "Database",
        "tags": ["sql", "left-join", "aggregation"],
        "companies": ["Amazon", "Microsoft"],
        "description": (
            "Write a solution to find for each user the join date and the "
            "number of orders they made **as a buyer in 2019**. Return the "
            "result table in **any order**.\n\n"
            "A user with no orders in 2019 must still appear, with a count of "
            "0 — filtering inside a `WHERE` clause would drop them entirely, "
            "so the 2019 window belongs in the join itself."
        ),
        "constraints": "user_id is the primary key of Users\norder_id is the primary key of Orders\nitem_id is the primary key of Items\nOrders.buyer_id references Users.user_id",
        "examples": [
            {
                "input": "Users: [(1, 2018-01-01, Lenovo), (2, 2018-02-09, Samsung), (3, 2018-01-19, LG), (4, 2018-05-21, HP)]; Orders: [(1, 2019-08-01, 4, 1, 2), (2, 2018-08-02, 2, 1, 3), (3, 2019-08-03, 3, 2, 3), (4, 2018-08-04, 1, 4, 2), (5, 2018-08-04, 1, 3, 4), (6, 2019-08-05, 2, 2, 4)]",
                "output": "[[1, 2018-01-01, 1], [2, 2018-02-09, 2], [3, 2018-01-19, 0], [4, 2018-05-21, 0]]",
            }
        ],
        "sql_schema": [
            "CREATE TABLE Users (user_id INT PRIMARY KEY, join_date DATE, favorite_brand VARCHAR(50));",
            "CREATE TABLE Orders (order_id INT PRIMARY KEY, order_date DATE, item_id INT, buyer_id INT, seller_id INT);",
            "CREATE TABLE Items (item_id INT PRIMARY KEY, item_brand VARCHAR(50));",
        ],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Users;\n"},
        "solution_sql": (
            "SELECT u.user_id AS buyer_id, u.join_date,\n"
            "       COUNT(o.order_id) AS orders_in_2019\n"
            "FROM Users u\n"
            "LEFT JOIN Orders o ON u.user_id = o.buyer_id\n"
            "  AND o.order_date BETWEEN '2019-01-01' AND '2019-12-31'\n"
            "GROUP BY u.user_id, u.join_date;\n"
        ),
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Users (user_id, join_date, favorite_brand) VALUES (1, '2018-01-01', 'Lenovo');",
                    "INSERT INTO Users (user_id, join_date, favorite_brand) VALUES (2, '2018-02-09', 'Samsung');",
                    "INSERT INTO Users (user_id, join_date, favorite_brand) VALUES (3, '2018-01-19', 'LG');",
                    "INSERT INTO Users (user_id, join_date, favorite_brand) VALUES (4, '2018-05-21', 'HP');",
                    "INSERT INTO Orders (order_id, order_date, item_id, buyer_id, seller_id) VALUES (1, '2019-08-01', 4, 1, 2);",
                    "INSERT INTO Orders (order_id, order_date, item_id, buyer_id, seller_id) VALUES (2, '2018-08-02', 2, 1, 3);",
                    "INSERT INTO Orders (order_id, order_date, item_id, buyer_id, seller_id) VALUES (3, '2019-08-03', 3, 2, 3);",
                    "INSERT INTO Orders (order_id, order_date, item_id, buyer_id, seller_id) VALUES (4, '2018-08-04', 1, 4, 2);",
                    "INSERT INTO Orders (order_id, order_date, item_id, buyer_id, seller_id) VALUES (5, '2018-08-04', 1, 3, 4);",
                    "INSERT INTO Orders (order_id, order_date, item_id, buyer_id, seller_id) VALUES (6, '2019-08-05', 2, 2, 4);",
                    "INSERT INTO Items (item_id, item_brand) VALUES (1, 'Samsung');",
                    "INSERT INTO Items (item_id, item_brand) VALUES (2, 'Lenovo');",
                    "INSERT INTO Items (item_id, item_brand) VALUES (3, 'LG');",
                    "INSERT INTO Items (item_id, item_brand) VALUES (4, 'HP');",
                ],
                "expected": [
                    [1, "2018-01-01", 1],
                    [2, "2018-02-09", 2],
                    [3, "2018-01-19", 0],
                    [4, "2018-05-21", 0],
                ],
            },
        ],
        "hints": [
            "A LEFT JOIN keeps users with zero 2019 orders — use COUNT(o.order_id), not COUNT(*), so the unmatched rows count as 0.",
            "Put the 2019 window in the JOIN condition (o.order_date BETWEEN '2019-01-01' AND '2019-12-31'), not a WHERE clause — WHERE would drop users without 2019 orders.",
        ],
        "follow_up": "Could you also report each user's favorite brand among the items they sold (Market Analysis II)?",
    },
    {
        "id": "sales-person",
        "entry_point": [],
        "title": "Sales Person",
        "difficulty": "Easy",
        "category": "Database",
        "tags": ["sql", "not-in", "subquery"],
        "companies": ["Amazon", "Google", "Apple"],
        "description": (
            "Write a solution to report the names of all salespersons who did "
            "not have any orders related to the company with the name **RED**. "
            "Return the result table in **any order**.\n\n"
            "A salesperson qualifies when *none* of their orders is for a RED "
            "company — salespeople with no orders at all also qualify."
        ),
        "constraints": "sales_id is the primary key of SalesPerson\ncom_id is the primary key of Company\norder_id is the primary key of Orders\nOrders.com_id references Company.com_id\nOrders.sales_id references SalesPerson.sales_id",
        "examples": [
            {
                "input": "SalesPerson: [(1, John, 100000, 6, 2006-04-01), (2, Amy, 12000, 5, 2010-05-01), (3, Mark, 65000, 12, 2008-12-25), (4, Pam, 25000, 25, 2005-01-01), (5, Alex, 5000, 10, 2007-02-03)]; Company: [(1, RED, Boston), (2, ORANGE, New York), (3, YELLOW, Sunnyvale), (4, GREEN, Austin)]; Orders: [(1, 2014-01-01, 3, 4, 10000), (2, 2014-02-01, 4, 5, 5000), (3, 2014-03-01, 1, 1, 50000), (4, 2014-04-01, 1, 4, 25000)]",
                "output": "[[Amy], [Mark], [Alex]]",
            }
        ],
        "sql_schema": [
            "CREATE TABLE SalesPerson (sales_id INT PRIMARY KEY, name VARCHAR(255), salary INT, commission_rate INT, hire_date DATE);",
            "CREATE TABLE Company (com_id INT PRIMARY KEY, name VARCHAR(255), city VARCHAR(255));",
            "CREATE TABLE Orders (order_id INT PRIMARY KEY, order_date DATE, com_id INT, sales_id INT, amount INT);",
        ],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    SalesPerson;\n"},
        "solution_sql": (
            "SELECT name FROM SalesPerson\n"
            "WHERE sales_id NOT IN (\n"
            "    SELECT sales_id FROM Orders\n"
            "    WHERE com_id = (SELECT com_id FROM Company WHERE name = 'RED')\n"
            ");\n"
        ),
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO SalesPerson (sales_id, name, salary, commission_rate, hire_date) VALUES (1, 'John', 100000, 6, '2006-04-01');",
                    "INSERT INTO SalesPerson (sales_id, name, salary, commission_rate, hire_date) VALUES (2, 'Amy', 12000, 5, '2010-05-01');",
                    "INSERT INTO SalesPerson (sales_id, name, salary, commission_rate, hire_date) VALUES (3, 'Mark', 65000, 12, '2008-12-25');",
                    "INSERT INTO SalesPerson (sales_id, name, salary, commission_rate, hire_date) VALUES (4, 'Pam', 25000, 25, '2005-01-01');",
                    "INSERT INTO SalesPerson (sales_id, name, salary, commission_rate, hire_date) VALUES (5, 'Alex', 5000, 10, '2007-02-03');",
                    "INSERT INTO Company (com_id, name, city) VALUES (1, 'RED', 'Boston');",
                    "INSERT INTO Company (com_id, name, city) VALUES (2, 'ORANGE', 'New York');",
                    "INSERT INTO Company (com_id, name, city) VALUES (3, 'YELLOW', 'Sunnyvale');",
                    "INSERT INTO Company (com_id, name, city) VALUES (4, 'GREEN', 'Austin');",
                    "INSERT INTO Orders (order_id, order_date, com_id, sales_id, amount) VALUES (1, '2014-01-01', 3, 4, 10000);",
                    "INSERT INTO Orders (order_id, order_date, com_id, sales_id, amount) VALUES (2, '2014-02-01', 4, 5, 5000);",
                    "INSERT INTO Orders (order_id, order_date, com_id, sales_id, amount) VALUES (3, '2014-03-01', 1, 1, 50000);",
                    "INSERT INTO Orders (order_id, order_date, com_id, sales_id, amount) VALUES (4, '2014-04-01', 1, 4, 25000);",
                ],
                "expected": [["Amy"], ["Mark"], ["Alex"]],
            },
        ],
        "hints": [
            "Start from SalesPerson and exclude anyone whose sales_id appears in an order for the RED company.",
            "NOT IN against the subquery of sales_ids with RED orders — salespeople with no orders are automatically kept.",
        ],
        "follow_up": None,
    },
    {
        "id": "rising-temperature",
        "entry_point": [],
        "title": "Rising Temperature",
        "difficulty": "Easy",
        "category": "Database",
        "tags": ["sql", "self-join"],
        "companies": ["Amazon", "Bloomberg", "Google"],
        "description": (
            "Write a solution to find all dates' `id` with higher temperatures "
            "compared to its **previous dates** (yesterday). Return the result "
            "table in **any order**.\n\n"
            "The previous date is the record with `recordDate` exactly one day "
            "earlier — the comparison is between a day and the calendar day "
            "before it, not the preceding row in the table."
        ),
        "constraints": "id is the primary key of Weather\nrecordDate is unique\nThere are no duplicate dates",
        "examples": [
            {
                "input": "Weather: [(1, 2015-01-01, 10), (2, 2015-01-02, 25), (3, 2015-01-03, 20), (4, 2015-01-04, 30)]",
                "output": "[[2], [4]]",
            }
        ],
        "sql_schema": ["CREATE TABLE Weather (id INT PRIMARY KEY, recordDate DATE, temperature INT);"],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Weather;\n"},
        "solution_sql": (
            "SELECT w1.id FROM Weather w1\n"
            "JOIN Weather w2 ON w1.recordDate = date(w2.recordDate, '+1 day')\n"
            "WHERE w1.temperature > w2.temperature;\n"
        ),
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Weather (id, recordDate, temperature) VALUES (1, '2015-01-01', 10);",
                    "INSERT INTO Weather (id, recordDate, temperature) VALUES (2, '2015-01-02', 25);",
                    "INSERT INTO Weather (id, recordDate, temperature) VALUES (3, '2015-01-03', 20);",
                    "INSERT INTO Weather (id, recordDate, temperature) VALUES (4, '2015-01-04', 30);",
                ],
                "expected": [[2], [4]],
            },
        ],
        "hints": [
            "Self-join Weather so each row pairs with the row exactly one day earlier.",
            "date(recordDate, '+1 day') in the join moves the earlier record forward a day; keep pairs where today is warmer.",
        ],
        "follow_up": "Could you generalise this to any N-day lag using a window function?",
    },
    {
        "id": "students-and-examinations",
        "entry_point": [],
        "title": "Students and Examinations",
        "difficulty": "Easy",
        "category": "Database",
        "tags": ["sql", "cross-join", "left-join"],
        "companies": ["Microsoft", "Amazon"],
        "description": (
            "Write a solution to find the number of times each student attended "
            "each exam. Return the result table ordered by `student_id` and "
            "`subject_name`.\n\n"
            "Every student must appear for **every** subject — a student who "
            "never took a subject still shows a count of 0 — so the student × "
            "subject grid is built before any counting happens."
        ),
        "constraints": "student_id and subject_name together form the primary key of Examinations\nstudent_id is the primary key of Students\nsubject_name is the primary key of Subjects",
        "examples": [
            {
                "input": "Students: [(1, Alice), (2, Bob), (13, John), (6, Alex)]; Subjects: [(Math), (Physics), (Programming)]; Examinations: [(1, Math), (1, Physics), (1, Programming), (2, Programming), (1, Physics), (1, Math), (13, Math), (13, Programming), (13, Physics), (2, Math), (1, Math)]",
                "output": "[[1, Alice, Math, 3], [1, Alice, Physics, 2], [1, Alice, Programming, 1], [2, Bob, Math, 1], [2, Bob, Physics, 0], [2, Bob, Programming, 1], [6, Alex, Math, 0], [6, Alex, Physics, 0], [6, Alex, Programming, 0], [13, John, Math, 1], [13, John, Physics, 1], [13, John, Programming, 1]]",
            }
        ],
        "sql_schema": [
            "CREATE TABLE Students (student_id INT PRIMARY KEY, student_name VARCHAR(50));",
            "CREATE TABLE Subjects (subject_name VARCHAR(50) PRIMARY KEY);",
            "CREATE TABLE Examinations (student_id INT, subject_name VARCHAR(50), PRIMARY KEY (student_id, subject_name));",
        ],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Students;\n"},
        "solution_sql": (
            "SELECT s.student_id, s.student_name, sub.subject_name,\n"
            "       COUNT(e.student_id) AS attended_exams\n"
            "FROM Students s\n"
            "CROSS JOIN Subjects sub\n"
            "LEFT JOIN Examinations e\n"
            "  ON s.student_id = e.student_id AND sub.subject_name = e.subject_name\n"
            "GROUP BY s.student_id, s.student_name, sub.subject_name\n"
            "ORDER BY s.student_id, sub.subject_name;\n"
        ),
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Students (student_id, student_name) VALUES (1, 'Alice');",
                    "INSERT INTO Students (student_id, student_name) VALUES (2, 'Bob');",
                    "INSERT INTO Students (student_id, student_name) VALUES (13, 'John');",
                    "INSERT INTO Students (student_id, student_name) VALUES (6, 'Alex');",
                    "INSERT INTO Subjects (subject_name) VALUES ('Math');",
                    "INSERT INTO Subjects (subject_name) VALUES ('Physics');",
                    "INSERT INTO Subjects (subject_name) VALUES ('Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Math');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Physics');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (2, 'Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Physics');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Math');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (13, 'Math');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (13, 'Programming');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (13, 'Physics');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (2, 'Math');",
                    "INSERT INTO Examinations (student_id, subject_name) VALUES (1, 'Math');",
                ],
                "expected": [
                    [1, "Alice", "Math", 3],
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
        "hints": [
            "CROSS JOIN Students × Subjects forms the full grid, then LEFT JOIN Examinations on both keys.",
            "COUNT(e.student_id) counts only actual attendances — unmatched grid cells get 0.",
        ],
        "follow_up": None,
    },
    {
        "id": "last-person-to-fit-in-the-bus",
        "entry_point": [],
        "title": "Last Person to Fit in the Bus",
        "difficulty": "Hard",
        "category": "Database",
        "tags": ["sql", "window-functions"],
        "companies": ["Uber", "Amazon"],
        "description": (
            "There is a queue of people waiting to board a bus. However, the "
            "bus has a **weight limit of 1000 kilograms**, so there may be some "
            "people who cannot board.\n\n"
            "Write a solution to find the `person_name` of the **last person** "
            "that can fit on the bus without exceeding the weight limit. The "
            "people board in `turn` order, and each person's weight adds to the "
            "running total — the last person who fits is the one whose boarding "
            "keeps the cumulative weight at or below 1000."
        ),
        "constraints": "person_id is the primary key of Queue\nturn is unique and determines the boarding order\nWeight is a positive integer",
        "examples": [
            {
                "input": "Queue: [(5, Alice, 250, 1), (4, Bob, 175, 5), (3, Alex, 350, 2), (6, John Cena, 400, 3), (1, Winston, 500, 6), (2, Marie, 200, 4)]",
                "output": "[[John Cena]]",
            }
        ],
        "sql_schema": ["CREATE TABLE Queue (person_id INT PRIMARY KEY, person_name VARCHAR(50), weight INT, turn INT);"],
        "starter_code": {"sql": "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    Queue;\n"},
        "solution_sql": (
            "SELECT person_name FROM (\n"
            "    SELECT person_name,\n"
            "           SUM(weight) OVER (ORDER BY turn) AS total_weight\n"
            "    FROM Queue\n"
            ") WHERE total_weight <= 1000\n"
            "ORDER BY total_weight DESC LIMIT 1;\n"
        ),
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Queue (person_id, person_name, weight, turn) VALUES (5, 'Alice', 250, 1);",
                    "INSERT INTO Queue (person_id, person_name, weight, turn) VALUES (4, 'Bob', 175, 5);",
                    "INSERT INTO Queue (person_id, person_name, weight, turn) VALUES (3, 'Alex', 350, 2);",
                    "INSERT INTO Queue (person_id, person_name, weight, turn) VALUES (6, 'John Cena', 400, 3);",
                    "INSERT INTO Queue (person_id, person_name, weight, turn) VALUES (1, 'Winston', 500, 6);",
                    "INSERT INTO Queue (person_id, person_name, weight, turn) VALUES (2, 'Marie', 200, 4);",
                ],
                "expected": [["John Cena"]],
            },
        ],
        "hints": [
            "A running total in turn order is a window sum: SUM(weight) OVER (ORDER BY turn).",
            "Keep the rows whose cumulative weight is at most 1000 and take the one with the largest total.",
        ],
        "follow_up": "Could you report every person who boards, in boarding order, instead of just the last one?",
    },
]

# ── Problem Bank Adapter ──────────────────────────────────────────────────────
#
# `coding_problems_data.PROBLEMS` uses a different schema than CURATED_PROBLEMS:
# numeric `id`, camelCase `testCases`, JSON-*string* inputs/expected values, and
# a single JavaScript-only `starterCode`. Normalize it into the curated shape so
# one execution path serves both sources.


def _parse_json_ish(raw: Any) -> Any:
    """Decode a test-case value that may be a JSON string or already typed."""
    if not isinstance(raw, str):
        return raw
    text = raw.strip()
    if not text:
        return text
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        # Not JSON — treat as a plain string literal (e.g. a word answer).
        return raw


def _param_names_from_starter(starter: str, arity: int) -> Optional[List[str]]:
    """Recover parameter names from the bank's JavaScript starter.

    Bank test-case inputs are positional, so inference can only call the
    parameters ``arg0``/``arg1``. The starter names them properly — ``prices``,
    ``nums``, ``target`` — and a candidate reads those names as part of the
    problem statement. Returns None unless exactly `arity` plain identifiers are
    found, so a destructured or defaulted parameter list is left alone rather
    than mis-mapped.
    """
    match = re.search(r"function\s+[A-Za-z_$][\w$]*\s*\(([^)]*)\)", starter or "")
    if not match:
        return None
    raw = match.group(1).strip()
    if not raw:
        return None
    names = [part.strip() for part in raw.split(",")]
    if len(names) != arity:
        return None
    if not all(re.fullmatch(r"[A-Za-z_$][\w$]*", n) for n in names):
        return None
    return names


def _entry_point_from_starter(starter: str) -> List[str]:
    """Recover the expected function name from starter code.

    The bank never declares an entry point, but its starter code always
    contains exactly one signature, so the name is recoverable rather than
    guessed. Both the JS name and its snake_case form are offered so a
    candidate writing idiomatic Python still resolves.
    """
    names: List[str] = []
    for pattern in (
        r"function\s+([A-Za-z_$][\w$]*)\s*\(",
        r"def\s+([A-Za-z_][\w]*)\s*\(",
        r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:function|\()",
        r"class\s+([A-Za-z_$][\w$]*)",
    ):
        names.extend(re.findall(pattern, starter or ""))

    expanded: List[str] = []
    for name in names:
        if name not in expanded:
            expanded.append(name)
        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        if snake not in expanded:
            expanded.append(snake)

    # When a starter declares several helpers plus a `solution`/`solve` driver
    # (e.g. encode + decode + solution), the driver is what produces the final
    # answer. Grading the first-declared helper instead compares an intermediate
    # value against the expected output and fails a correct submission.
    if len(names) > 1:
        drivers = [n for n in expanded if n in ("solution", "solve")]
        if drivers:
            expanded = drivers + [n for n in expanded if n not in drivers]
    return expanded


def _is_class_starter(starter: str) -> bool:
    """True when the starter's solution entity is a class, not a function."""
    return bool(re.match(r"\s*class\s+[A-Za-z_$][\w$]*", starter or ""))


def _normalize_design_tests(tests: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """Convert LeetCode design test cases into ``{ctor, ops, expected}`` form.

    The bank stores design cases in the two-parallel-array shape
    ``[["push", "getMin"], [[-2], []]]``: method names beside their argument
    lists. Returns None when a case does not match that shape, so the caller
    reports "not graded" rather than guessing at a binding.
    """
    normalized: List[Dict[str, Any]] = []
    for tc in tests:
        raw, expected = tc.get("input"), tc.get("expected")
        if not (isinstance(raw, list) and len(raw) == 2):
            return None
        op_names, op_args = raw
        if not (isinstance(op_names, list) and isinstance(op_args, list)):
            return None
        if len(op_names) != len(op_args) or not isinstance(expected, list):
            return None
        if len(expected) != len(op_names):
            return None

        ops: List[List[Any]] = []
        for name, args in zip(op_names, op_args):
            if not isinstance(name, str):
                return None
            ops.append([name] + (list(args) if isinstance(args, list) else [args]))
        # The bank's sequences begin at the first method call; the constructor
        # takes no arguments in every design problem present.
        normalized.append({"ctor": [], "ops": ops, "expected": expected})
    return normalized


@lru_cache(maxsize=1)
def _problem_bank_index() -> Dict[str, Dict[str, Any]]:
    """Index the 1000-problem bank by string ID, normalized to curated shape."""
    try:
        from app.services.coding_problems_data import PROBLEMS
    except Exception as exc:  # pragma: no cover - data module is static
        logger.warning(f"Coding problem bank unavailable: {exc}")
        return {}

    index: Dict[str, Dict[str, Any]] = {}
    for raw in PROBLEMS:
        starter = raw.get("starterCode", "") or ""
        tests = [
            {
                "input": _parse_json_ish(tc.get("input")),
                "expected": _parse_json_ish(tc.get("expected")),
            }
            for tc in raw.get("testCases", []) or []
        ]
        problem = {
            "id": str(raw.get("id")),
            "entry_point": _entry_point_from_starter(starter),
            "title": raw.get("title", "Untitled"),
            "difficulty": raw.get("difficulty", "Medium"),
            # NOT raw["topic"]: the bank's own topic field is mis-assigned —
            # "Two Sum" is filed under Tries, "Contains Duplicate" under
            # Segment Tree. The tags are accurate, so the topic is re-derived.
            "category": problem_enrichment.topic_for(raw.get("tags", [])),
            "tags": raw.get("tags", []),
            "companies": raw.get("companiesAsked", []),
            "description": raw.get("description", ""),
            "constraints": raw.get("constraints", ""),
            "examples": [
                {"input": str(tc.get("input", "")), "output": str(tc.get("expected", ""))}
                for tc in (raw.get("testCases") or [])[:2]
            ],
            # The bank only ships JavaScript starter code; other languages fall
            # back to the frontend's generic template.
            "starter_code": {"javascript": starter},
            "test_cases": tests,
            "hints": raw.get("hints", []),
            "time_complexity": raw.get("timeComplexity", ""),
            "space_complexity": raw.get("spaceComplexity", ""),
        }
        if _is_class_starter(starter):
            design_tests = _normalize_design_tests(tests)
            if design_tests is None:
                problem["grading"] = "unsupported"
                problem["grading_reason"] = (
                    f"'{problem['title']}' is a design problem whose test cases are "
                    "not in a replayable operation-sequence form, so it is executed "
                    "but not auto-graded."
                )
            else:
                problem["grading"] = "design"
                problem["test_cases"] = design_tests
        index[problem["id"]] = problem
    return index


def _lookup_problem_bank(problem_id: str) -> Optional[Dict[str, Any]]:
    return _problem_bank_index().get(str(problem_id))


def _entry_candidates(problem: Dict[str, Any]) -> List[str]:
    """Entry-point names declared for a problem, most specific first."""
    declared = problem.get("entry_point") or []
    if isinstance(declared, str):
        declared = [declared]
    # Generic names last, so a declared name always wins.
    return list(declared) + ["solve", "solution"]


def _with_static_starters(problem: Dict[str, Any]) -> Dict[str, Any]:
    """Fill in starter code for every language the signature can be typed in.

    Generated from the same inferred signature the grading harness calls, so the
    starter a candidate is shown always matches what the harness invokes. Only
    languages the problem does not already ship are filled — a hand-written
    starter is never overwritten by an inferred one.
    """
    if problem.get("grading") in ("design", "unsupported"):
        return problem
    # Database problems answer with a query, not a function — there is no
    # signature to infer and no per-language function starter to generate. The
    # problem ships its own ``sql`` starter (or the editor offers a generic SQL
    # template), so inference would only produce noise.
    if problem.get("sql_schema"):
        return problem

    cases = problem.get("test_cases") or []
    existing = problem.get("starter_code") or {}
    entries = _entry_candidates(problem)
    # Bank inputs are positional, so the readable parameter names live only in
    # the JavaScript starter. Reuse them across every generated language.
    signature = static_harness.infer_signature(cases)
    names = (
        _param_names_from_starter(existing.get("javascript", ""), len(signature.params))
        if signature
        else None
    )

    generated = {}
    for language in static_harness.starter_languages():
        if existing.get(language):
            continue
        starter = static_harness.build_starter(language, cases, entries, names)
        if starter:
            generated[language] = starter

    if not generated:
        return problem
    return {**problem, "starter_code": {**existing, **generated}}


_REVIEW_UNAVAILABLE = (
    "Automated code review is unavailable right now. Your test results above "
    "are unaffected."
)


# ── Code Execution Engine ──────────────────────────────────────────────────────


class CodeExecutorService:
    """Multi-language code execution engine backed by an isolated sandbox.

    Candidate code always runs through :mod:`app.services.code_sandbox`, which
    picks the first backend able to run the language (Piston, Docker, or — only
    with an explicit opt-in — a local subprocess). If no backend can run it, the
    request fails with an explanation; there is no simulated result.
    """

    def __init__(self) -> None:
        self.sandbox = get_sandbox()
        logger.info(
            f"CodeExecutorService initialised | sandbox backends: {self.sandbox.describe()}"
        )

    def get_curated_problems(self) -> List[Dict[str, Any]]:
        """Return curated coding problems with metadata."""
        return [
            {
                "id": p["id"],
                "title": p["title"],
                "difficulty": p["difficulty"],
                "category": p["category"],
                "tags": p["tags"],
                "companies": p["companies"],
                "description": p["description"],
                "constraints": p["constraints"],
                "examples": p["examples"],
                "follow_up": p.get("follow_up"),
                "hints": p.get("hints", []),
                "starter_code": _with_static_starters(p)["starter_code"],
                # Database problems carry the schema the editor needs to render
                # the table diagram and restrict the language picker to SQL.
                "sql_schema": p.get("sql_schema"),
            }
            for p in (problem_enrichment.enrich(c) for c in CURATED_PROBLEMS)
        ]

    def get_problem_catalog(
        self,
        search: str = "",
        difficulty: str = "",
        topic: str = "",
        offset: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """A browsable index of every problem: the curated set plus the bank.

        Deliberately *not* built on :meth:`get_curated_problems`, which returns
        six hand-written problems — a practice list needs the whole catalogue.
        Only listing metadata is returned; descriptions, examples and starter
        code are large and are fetched per problem on open.

        Filtering happens here rather than client-side because the full bank is
        ~1000 entries and shipping all of them on every list render is wasteful.
        """
        rows = self._catalog_rows()

        needle = (search or "").strip().lower()
        want_difficulty = (difficulty or "").strip().lower()
        want_topic = (topic or "").strip().lower()

        if needle or want_difficulty or want_topic:
            filtered = []
            for row in rows:
                if want_difficulty and row["difficulty"].lower() != want_difficulty:
                    continue
                if want_topic and row["category"].lower() != want_topic:
                    continue
                if needle and needle not in row["_haystack"]:
                    continue
                filtered.append(row)
            rows = filtered

        total = len(rows)
        start = max(offset, 0)
        window = rows[start : start + max(min(limit, 500), 1)]
        return {
            "problems": [{k: v for k, v in r.items() if not k.startswith("_")} for r in window],
            "total": total,
            "offset": start,
            "limit": limit,
            "topics": self._catalog_topics(),
        }

    @staticmethod
    @lru_cache(maxsize=1)
    def _catalog_rows() -> List[Dict[str, Any]]:
        """Listing metadata for curated + bank problems, curated first.

        A bank entry whose id collides with a curated one is dropped, so the
        hand-written version (which has multi-language starters and real
        examples) wins.
        """
        rows: List[Dict[str, Any]] = []
        seen: set[str] = set()

        def add(pid: str, title: str, difficulty: str, category: str,
                tags: List[str], companies: List[str], source: str) -> None:
            if pid in seen:
                return
            seen.add(pid)
            rows.append({
                "id": pid,
                "title": title,
                "difficulty": difficulty,
                "category": category,
                "tags": tags or [],
                "companies": companies or [],
                "source": source,
                "_haystack": " ".join(
                    [title, category, " ".join(tags or []), " ".join(companies or [])]
                ).lower(),
            })

        for p in CURATED_PROBLEMS:
            add(str(p["id"]), p["title"], p["difficulty"], p["category"],
                p.get("tags", []), p.get("companies", []), "curated")

        for pid, p in _problem_bank_index().items():
            add(pid, p["title"], p["difficulty"], p["category"],
                p.get("tags", []), p.get("companies", []), "bank")

        return rows

    @staticmethod
    @lru_cache(maxsize=1)
    def _catalog_topics() -> List[str]:
        """Distinct topics across the catalogue, for the practice-list filter."""
        return sorted({r["category"] for r in CodeExecutorService._catalog_rows() if r["category"]})

    def get_problem_by_id(self, problem_id: str) -> Optional[Dict[str, Any]]:
        """Find a problem by ID in the curated set, then the 1000-problem bank.

        Returns None for an unknown ID so the caller can 404. This used to
        fabricate a stub problem whose single test case was
        ``{"input": "test_input_1", "expected": "passed"}`` — every unknown ID,
        including all 1000 numeric IDs in the problem bank, therefore reported a
        pass against a test that asserted nothing.
        """
        for p in CURATED_PROBLEMS:
            if p["id"] == problem_id:
                return problem_enrichment.enrich(_with_static_starters(p))
        found = _lookup_problem_bank(problem_id)
        return problem_enrichment.enrich(_with_static_starters(found)) if found else None

    def get_problem_source(self, problem_id: str) -> Optional[Dict[str, Any]]:
        """The normalized problem *before* enrichment is applied.

        The batch statement generator needs this: feeding it the enriched
        description would make each rerun expand its own previous output
        instead of the original one-line source.
        """
        for p in CURATED_PROBLEMS:
            if p["id"] == problem_id:
                return _with_static_starters(p)
        found = _lookup_problem_bank(problem_id)
        return _with_static_starters(found) if found else None

    def _strip_ts_types(self, ts_code: str) -> str:
        """Strip TypeScript annotations so Node can run the source directly.

        Regex type-stripping is approximate; it covers the shapes that appear in
        starter code. A construct it mangles produces a real Node syntax error,
        which is reported as such rather than being silently graded.
        """
        clean = re.sub(
            r":\s*(?:number|string|boolean|any|void|unknown|never|object|Array<[^>]+>|[\w\[\]]+)(?=[,\)\s=;{])",
            "",
            ts_code,
        )
        clean = re.sub(r"interface\s+\w+\s*\{[^}]*\}", "", clean)
        clean = re.sub(r"type\s+\w+\s*=[^;]+;", "", clean)
        return clean

    def execute_code(
        self,
        problem_id: str,
        language: str,
        code: str,
    ) -> Dict[str, Any]:
        """Execute candidate code against a problem's test suite, in a sandbox.

        Every outcome is grounded in a real container run. When a language can
        be graded, results come from the program's own ``RESULTS_JSON`` line;
        when it can only be compiled, ``success`` is False and the reason says
        so. Nothing here reports a pass for code that did not run.
        """
        problem = self.get_problem_by_id(problem_id)
        if problem is None:
            return self._error(f"Unknown problem '{problem_id}'.")

        lang_key = resolve_language(language)
        spec = get_spec(language) if lang_key else None
        if not spec:
            return self._error(f"Unsupported language '{language}'.")

        if not code.strip():
            return self._error("No code submitted.")

        if not self.sandbox.available():
            return self._error(
                "Code execution is unavailable: no sandbox backend is reachable "
                "on this host. No tests were run."
            )

        if not self.sandbox.supports(spec):
            return self._error(
                f"{spec.name} execution is not provisioned on this host: no "
                f"available sandbox backend can run it. No tests were run."
            )

        test_cases = problem.get("test_cases") or []
        if not test_cases:
            return self._error(f"Problem '{problem_id}' has no test cases defined.")

        # A database problem is answered with a query, not a function call. Its
        # test cases carry seed/expected rows and no ``input`` key, so running a
        # coding language against them would report a string of opaque KeyError
        # failures. Say what is wrong instead of making the candidate debug a
        # harness.
        if problem.get("sql_schema") and lang_key != "sql":
            return self._error(
                f"'{problem.get('title')}' is a database problem and must be "
                f"answered with SQL, not {spec.name}."
            )

        # Stateful/design problems have no generic grading strategy.
        if problem.get("grading") == "unsupported":
            return self._compile_only(
                spec, lang_key, code,
                reason=problem.get("grading_reason")
                or f"'{problem.get('title')}' is not auto-graded.",
            )

        if problem.get("grading") == "design":
            design_builder = DESIGN_HARNESS_BUILDERS.get(lang_key)
            if design_builder is None:
                return self._compile_only(
                    spec, lang_key, code,
                    reason=DESIGN_UNSUPPORTED.format(lang=spec.name),
                )
            source = self._strip_ts_types(code) if lang_key == "typescript" else code
            harness = design_builder(source, test_cases, self._entry_points(problem))
            return self._run_graded(spec, harness, test_cases)

        # SQL is graded by building an in-memory SQLite database from the
        # problem's schema, running the candidate's query against each case's
        # seed data, and comparing the resulting rows. The language is a Python
        # harness (see ``code_runners.build_sql_harness``), so it must take the
        # SQL path before the function-call harnesses — a query is not a
        # function, and the generic harnesses would misgrade it.
        if lang_key == "sql":
            schema = problem.get("sql_schema") or []
            if not schema:
                return self._error(
                    f"Problem '{problem_id}' is not a database problem — SQL "
                    "grading needs a schema."
                )
            harness = build_sql_harness(code, test_cases, schema)
            return self._run_graded(spec, harness, test_cases)

        entry_points = self._entry_points(problem)

        builder = HARNESS_BUILDERS.get(lang_key)
        if builder is None:
            # Statically typed language. static_harness infers a signature from
            # the test data and generates a typed program around the submission;
            # it returns None when the data cannot be typed exactly, and we
            # compile without grading rather than guess at a binding.
            harness = static_harness.build_program(
                lang_key, test_cases, entry_points, code
            )
            if harness is not None:
                return self._run_graded(spec, harness, test_cases)
            return self._compile_only(
                spec, lang_key, code, reason=VERIFY_UNTYPEABLE.format(lang=spec.name)
            )

        source = self._strip_ts_types(code) if lang_key == "typescript" else code
        harness = builder(source, test_cases, entry_points)
        return self._run_graded(spec, harness, test_cases)

    @staticmethod
    def _entry_points(problem: Dict[str, Any]) -> List[str]:
        """Candidate function names for this problem, most specific first."""
        return _entry_candidates(problem)

    @staticmethod
    def _error(message: str) -> Dict[str, Any]:
        """A failure with no test results — never a pass."""
        return {
            "success": False,
            "passed": False,
            "runtime_ms": 0.0,
            "test_results": [],
            "stdout": "",
            "stderr": "",
            "error": message,
        }

    def _run_graded(
        self,
        spec: Any,
        harness: str,
        test_cases: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Run a harnessed program and parse its RESULTS_JSON verdict."""
        files = {spec.source_name: harness}
        try:
            result = self.sandbox.run(spec, files)
        except SandboxUnavailable as exc:
            return self._error(str(exc))
        except Exception as exc:
            logger.exception("Sandbox run failed")
            return self._error(f"Execution failed: {exc}")

        if result.timed_out:
            return {**self._error(result.stderr), "runtime_ms": result.duration_ms}

        stderr = result.stderr

        marker = "RESULTS_JSON:"
        if marker not in result.stdout:
            # No verdict line ⇒ compilation failed, the program crashed, the
            # entry point was missing, or it was killed. Report the diagnostic,
            # never a grade.
            detail = (stderr or result.stdout or "").strip()
            if spec.compile_cmd and not result.compile_ok:
                message = f"Compilation Error:\n{detail}"
            else:
                message = detail or "Execution produced no test results."
            return {
                **self._error(message),
                "stdout": result.stdout,
                "stderr": stderr,
                "runtime_ms": result.duration_ms,
            }

        # rpartition, not partition: candidate code could print a forged
        # RESULTS_JSON line of its own, but the harness always prints after every
        # test has run, so the *last* occurrence is the harness's verdict.
        head, _, tail = result.stdout.rpartition(marker)
        try:
            results = json.loads(tail.strip().splitlines()[0])
        except (ValueError, IndexError) as exc:
            return {
                **self._error(f"Could not parse test results: {exc}"),
                "stdout": result.stdout,
                "stderr": stderr,
                "runtime_ms": result.duration_ms,
            }

        if not isinstance(results, list) or len(results) != len(test_cases):
            # A submission can print its own RESULTS_JSON line to forge a
            # verdict. We can't stop it printing, but we refuse to accept a
            # result set that doesn't match the suite we asked it to run.
            return {
                **self._error(
                    f"Harness reported {len(results) if isinstance(results, list) else 'invalid'} "
                    f"results for {len(test_cases)} test cases."
                ),
                "stdout": head.strip(),
                "stderr": stderr,
                "runtime_ms": result.duration_ms,
            }

        return {
            "success": True,
            "passed": bool(results) and all(r.get("passed") is True for r in results),
            "runtime_ms": result.duration_ms,
            "test_results": results,
            "stdout": head.strip(),
            "stderr": stderr,
            "error": None,
        }

    def _compile_only(
        self,
        spec: Any,
        lang_key: str,
        code: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Compile (or syntax-check) without grading, and say so explicitly.

        Used for statically typed languages and stateful design problems. The
        response is deliberately ``success=False`` with an empty
        ``test_results``: a green checkmark here would be the same lie this
        module previously told.

        The submission is wrapped in its language's prelude first. Starter code
        for these languages is function-only — the harness normally supplies the
        ``package`` clause, imports and ``main`` — so compiling it verbatim would
        fail on the harness's conventions rather than on the candidate's code.
        """
        files = {spec.source_name: static_harness.wrap_standalone(lang_key, code)}
        try:
            if spec.compile_cmd:
                built = self.sandbox.run(spec, files, compile_only=True)
                if not built.compile_ok or built.exit_code != 0:
                    return {
                        **self._error(f"Compilation Error:\n{built.stderr.strip()}"),
                        "stderr": built.stderr,
                        "runtime_ms": built.duration_ms,
                    }
                note = "Compiled successfully. "
                elapsed = built.duration_ms
            else:
                note = ""
                elapsed = 0.0
        except SandboxUnavailable as exc:
            return self._error(str(exc))
        except Exception as exc:
            logger.exception("Sandbox compile failed")
            return self._error(f"Execution failed: {exc}")

        return {
            "success": False,
            "passed": False,
            "runtime_ms": elapsed,
            "test_results": [],
            "stdout": "",
            "stderr": "",
            "error": note + reason,
        }

    def evaluate_ai_code_quality(
        self,
        problem_title: str,
        language: str,
        code: str,
        timeout_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Use LLM to generate Big-O complexity & code quality feedback.

        Bounded by `timeout_seconds` (default `CODE_REVIEW_TIMEOUT_SECONDS`).
        The review is the optional half of a submission — the test verdict is
        the part the candidate is waiting on — so an LLM that is slow, down, or
        unconfigured must not hold the response. It previously could: a submit
        took 65 seconds to come back and then reported no review anyway.
        """
        prompt = (
            f"Analyze the following {language.capitalize()} code for the problem '{problem_title}':\n\n"
            f"```\n{code}\n```\n\n"
            "Provide a brief evaluation with:\n"
            "1. Time Complexity (Big-O)\n"
            "2. Space Complexity (Big-O)\n"
            "3. Code Readability score (0-100)\n"
            "4. Two actionable optimization / clean code suggestions."
        )

        def _ask() -> Optional[str]:
            return get_llm().generate(
                prompt=prompt,
                system_prompt="You are an expert technical interviewer evaluating candidate code.",
                temperature=0.3,
                max_tokens=500,
            )

        budget = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.CODE_REVIEW_TIMEOUT_SECONDS
        )
        # A daemon pool so an overrunning call is abandoned rather than joined
        # at shutdown; the future is left to finish and discarded.
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="code-review")
        try:
            reply = executor.submit(_ask).result(timeout=budget)
            if reply:
                return {"analysis": reply}
            return {"analysis": _REVIEW_UNAVAILABLE}
        except FuturesTimeout:
            logger.warning(f"AI code evaluation exceeded {budget}s; returning verdict without it")
            return {"analysis": _REVIEW_UNAVAILABLE}
        except Exception as exc:
            # The old fallback asserted a fixed O(N)/O(N), a score of 88, and
            # "Code passes structural test cases" for code it had never seen
            # analysed and tests it had not consulted. Say nothing instead of
            # something invented.
            logger.warning(f"AI code evaluation unavailable: {exc}")
            return {"analysis": _REVIEW_UNAVAILABLE}
        finally:
            executor.shutdown(wait=False)


_code_executor_instance: Optional[CodeExecutorService] = None


def get_code_executor_service() -> CodeExecutorService:
    global _code_executor_instance
    if _code_executor_instance is None:
        _code_executor_instance = CodeExecutorService()
    return _code_executor_instance
