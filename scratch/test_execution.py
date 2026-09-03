"""Test code execution for all available languages."""
import sys
sys.path.insert(0, ".")
from app.services.coding_problems_service import execute_problem, _detect_local_compilers

print("=== Compiler Detection ===")
compilers = _detect_local_compilers()
for lang, available in compilers.items():
    status = "AVAILABLE" if available else "NOT FOUND"
    print(f"  {lang}: {status}")

print()
print("=== Testing Python Execution (Two Sum) ===")
result = execute_problem(1, """
import json

def solve(nums, target):
    m = {}
    for i, n in enumerate(nums):
        if target - n in m:
            return [m[target - n], i]
        m[n] = i
    return []
""", "python")

print(f"Language: {result['language']}")
print(f"Provider: {result['provider']}")
print(f"Passed: {result['passed_tests']}/{result['total_tests']}")
print(f"All passed: {result['all_passed']}")
for r in result["results"]:
    p = "PASS" if r["passed"] else "FAIL"
    print(f"  {r['input']} -> {r['actual']} (expected {r['expected']}) = {p}")

print()
print("=== Testing JavaScript Execution (Two Sum) ===")
try:
    result = execute_problem(1, """
function solve(nums, target) {
    const map = new Map();
    for (let i = 0; i < nums.length; i++) {
        const c = target - nums[i];
        if (map.has(c)) return [map.get(c), i];
        map.set(nums[i], i);
    }
    return [];
}
""", "javascript")
    print(f"Language: {result['language']}")
    print(f"Provider: {result['provider']}")
    print(f"Passed: {result['passed_tests']}/{result['total_tests']}")
    print(f"All passed: {result['all_passed']}")
except Exception as e:
    print(f"ERROR: {e}")

# Test Java if available
if compilers.get("java"):
    print()
    print("=== Testing Java Execution (Two Sum) ===")
    try:
        result = execute_problem(1, """
public static void solve(long[] nums, long target) {
    java.util.Map<Long, Integer> map = new java.util.HashMap<>();
    for (int i = 0; i < nums.length; i++) {
        long c = target - nums[i];
        if (map.containsKey(c)) {
            System.out.print("[" + map.get(c) + "," + i + "]");
            return;
        }
        map.put(nums[i], i);
    }
    System.out.print("[]");
}
""", "java")
        print(f"Provider: {result['provider']}")
        print(f"Passed: {result['passed_tests']}/{result['total_tests']}")
    except Exception as e:
        print(f"ERROR: {e}")

print()
print("=== DONE ===")
