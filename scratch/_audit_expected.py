"""Find problems a do-nothing stub would pass on."""
from app.services.code_executor_service import _problem_bank_index, CURATED_PROBLEMS

bank = _problem_bank_index()

none_expected = []
empty_expected = []
falsy_expected = []
no_tests = []

for pid, p in bank.items():
    tcs = p["test_cases"]
    if not tcs:
        no_tests.append(pid)
        continue
    exps = [tc["expected"] for tc in tcs]
    if all(e is None for e in exps):
        none_expected.append(pid)
    if all(e == "" for e in exps):
        empty_expected.append(pid)
    if all(not e and e is not None and e != "" for e in exps):
        falsy_expected.append((pid, exps[:3]))

print("bank_indexed", len(bank))
print("no_tests", len(no_tests), no_tests[:10])
print("all_expected_None (python `pass` passes)", len(none_expected), none_expected[:10])
print("all_expected_empty_string", len(empty_expected), empty_expected[:10])
print("all_expected_falsy", len(falsy_expected), falsy_expected[:10])

# Any test case where expected is None at all?
any_none = [pid for pid, p in bank.items() if any(tc["expected"] is None for tc in p["test_cases"])]
print("any_expected_None", len(any_none), any_none[:10])

# Curated set sanity
for p in CURATED_PROBLEMS:
    exps = [tc["expected"] for tc in p["test_cases"]]
    if any(e is None for e in exps):
        print("curated_has_None", p["id"], exps)
