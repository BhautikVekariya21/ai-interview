"""Hand-authored problem statements — the overlay `scripts/enrich_problems.py`
would have produced if an LLM key were live.

Why this file exists
--------------------
`app/services/problem_enrichment.py` builds a *derived* statement from each
problem's own test data. That layer is honest but bounded: it can name the
arguments, snap the bounds and print the examples, and it stops there. It cannot
write "where the width of each bar is 1", because that fact appears nowhere in
the data — it is the definition of the problem, not an observation about it.
Every judge-grade statement turns on a sentence of exactly that kind.

So the sentences are written here, by hand, and loaded through the same overlay
the generator targets (`data/problem_enrichment.json`). Nothing about the
pipeline changes; the file it reads is simply no longer empty.

The invariant from the generator holds here too, and it is the important one:
**no entry may state an example.** Examples are replayed from `test_cases` by
`enrich()`. An authored `explanations[i]` annotates recorded case *i* and must
be checked against the real recorded values — `verify()` in
`scripts/build_authored_statements.py` fails the build if a statement's prose
contradicts the data, so a wrong explanation cannot ship quietly.

Keys per entry
--------------
statement          full prose; replaces the derived description (>=120 chars)
explanations       one per recorded test case, in order, positionally matched
constraints_exact  the real bounds; REPLACES the widened derived ones
follow_up          the closing complexity nudge
hints              collapsed in the UI, so they cost nothing until asked for
"""

from typing import Any, Dict

# ── Arrays & hashing ─────────────────────────────────────────────────────────

AUTHORED: Dict[int, Dict[str, Any]] = {
    1: {
        "statement": (
            "Given an array of integers `nums` and an integer `target`, return "
            "the indices of the two numbers such that they add up to `target`.\n\n"
            "You may assume that each input has **exactly one solution**, and you "
            "may not use the same element twice.\n\n"
            "You can return the answer in any order."
        ),
        "explanations": [
            "Because nums[0] + nums[1] == 2 + 7 == 9, we return [0, 1].",
            "Because nums[1] + nums[2] == 2 + 4 == 6, we return [1, 2].",
            "Because nums[0] + nums[1] == 3 + 3 == 6, we return [0, 1].",
        ],
        "constraints_exact": [
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i] <= 10^9",
            "-10^9 <= target <= 10^9",
            "Only one valid answer exists.",
        ],
        "follow_up": "Can you come up with an algorithm that is less than O(n^2) time complexity?",
        "hints": [
            "The brute force is two nested loops over every pair. Think about what "
            "that inner loop is really asking: \"have I already seen target - nums[i]?\"",
            "A hash map answers \"have I seen this value, and where?\" in O(1). Build "
            "it as you go rather than up front, and the same pass both queries and fills it.",
        ],
    },
    2: {
        "statement": (
            "Given an integer array `nums`, return `true` if any value appears "
            "**at least twice** in the array, and return `false` if every element "
            "is distinct."
        ),
        "explanations": [
            "The element 1 occurs at indices 0 and 3, so the array contains a duplicate.",
            "All four elements are distinct, so no value repeats.",
            "Several values repeat here — 1 appears three times and 3 appears three times.",
        ],
        "constraints_exact": [
            "1 <= nums.length <= 10^5",
            "-10^9 <= nums[i] <= 10^9",
        ],
        "follow_up": "Can you solve it in O(n) time using O(n) extra space?",
        "hints": [
            "Sorting brings equal values next to each other, which turns the question "
            "into a single adjacent-pair scan — O(n log n) and no extra space.",
            "If you may spend memory instead, a hash set lets you stop at the first "
            "value you have already seen.",
        ],
    },
    3: {
        "statement": (
            "Given two strings `s` and `t`, return `true` if `t` is an anagram of "
            "`s`, and `false` otherwise.\n\n"
            "An **anagram** is a word or phrase formed by rearranging the letters "
            "of a different word or phrase, typically using all the original "
            "letters exactly once."
        ),
        "explanations": [
            "Both strings contain the same letters with the same multiplicities — three a's, one n, one g, one r and one m.",
            "'rat' and 'car' have the same length but differ in their letters, so neither is a rearrangement of the other.",
            "Both strings are the single letter 'a'.",
        ],
        "constraints_exact": [
            "1 <= s.length, t.length <= 5 * 10^4",
            "`s` and `t` consist of lowercase English letters.",
        ],
        "follow_up": (
            "What if the inputs contain Unicode characters? How would you adapt "
            "your solution to such a case?"
        ),
        "hints": [
            "Two strings of different lengths can never be anagrams — check that first "
            "and you have thrown away most of the work.",
            "You do not need to sort. Count each letter of `s`, then subtract the "
            "letters of `t`; if any count goes negative or ends non-zero, it is not an anagram.",
        ],
    },
    4: {
        "statement": (
            "Given an array of strings `strs`, group the anagrams together. You "
            "can return the answer in any order.\n\n"
            "An **anagram** is a word or phrase formed by rearranging the letters "
            "of a different word or phrase, typically using all the original "
            "letters exactly once."
        ),
        "explanations": [
            "'eat', 'tea' and 'ate' share the letters a, e and t; 'tan' and 'nat' share a, n and t; 'bat' matches nothing else.",
            "The single empty string forms a group of its own.",
        ],
        "constraints_exact": [
            "1 <= strs.length <= 10^4",
            "0 <= strs[i].length <= 100",
            "strs[i] consists of lowercase English letters.",
        ],
        "follow_up": "Can you solve it in O(n * k log k) time, where k is the maximum string length?",
        "hints": [
            "Anagrams are equal under some canonical form. Sorting a word's letters "
            "gives one such form: 'eat', 'tea' and 'ate' all become 'aet'.",
            "Use that canonical form as a hash-map key and append each original word "
            "to its bucket. A 26-length count tuple works as a key too, and avoids the sort.",
        ],
    },
    5: {
        "statement": (
            "Given an integer array `nums` and an integer `k`, return the `k` most "
            "frequent elements. You may return the answer in any order.\n\n"
            "It is guaranteed that the answer is **unique**."
        ),
        "explanations": [
            "1 occurs three times and 2 occurs twice, making them the two most frequent values; 3 occurs once and is excluded.",
            "There is only one distinct value, so it is trivially the most frequent.",
        ],
        "constraints_exact": [
            "1 <= nums.length <= 10^5",
            "-10^4 <= nums[i] <= 10^4",
            "k is in the range [1, the number of unique elements in the array].",
            "It is guaranteed that the answer is unique.",
        ],
        "follow_up": (
            "Your algorithm's time complexity must be better than O(n log n), "
            "where n is the array's size."
        ),
        "hints": [
            "Count occurrences first — that part is unavoidably O(n). The question is "
            "how you pick the top k out of those counts without sorting all of them.",
            "A frequency can never exceed n, so you can bucket values by count into an "
            "array of n + 1 lists and read it from the back. That is O(n) overall.",
        ],
    },
    6: {
        "statement": (
            "Given an integer array `nums`, return an array `answer` such that "
            "`answer[i]` is equal to the product of all the elements of `nums` "
            "except `nums[i]`.\n\n"
            "The product of any prefix or suffix of `nums` is guaranteed to fit in "
            "a **32-bit** integer.\n\n"
            "You must write an algorithm that runs in O(n) time and **without "
            "using the division operation**."
        ),
        "explanations": [
            "answer[0] = 2*3*4 = 24, answer[1] = 1*3*4 = 12, answer[2] = 1*2*4 = 8 and answer[3] = 1*2*3 = 6.",
            "Every position except index 2 has the zero in its product, so only answer[2] = (-1)*1*(-3)*3 = 9 is non-zero.",
        ],
        "constraints_exact": [
            "2 <= nums.length <= 10^5",
            "-30 <= nums[i] <= 30",
            "The product of any prefix or suffix of nums is guaranteed to fit in a 32-bit integer.",
        ],
        "follow_up": (
            "Can you solve the problem in O(1) extra space complexity? (The output "
            "array does not count as extra space for space complexity analysis.)"
        ),
        "hints": [
            "Everything except nums[i] splits cleanly into two halves: everything to "
            "its left, and everything to its right.",
            "Fill the output with prefix products in a left-to-right pass, then walk "
            "back from the right multiplying in a running suffix product. Two passes, no division.",
        ],
    },
    7: {
        "statement": (
            "Given an unsorted array of integers `nums`, return the length of the "
            "longest consecutive elements sequence.\n\n"
            "You must write an algorithm that runs in O(n) time."
        ),
        "explanations": [
            "The longest consecutive run of elements is [1, 2, 3, 4], so its length is 4.",
            "The longest consecutive run is [0, 1, 2, 3, 4, 5, 6, 7, 8], so its length is 9.",
            "The array is empty, so there is no sequence and the answer is 0.",
        ],
        "constraints_exact": [
            "0 <= nums.length <= 10^5",
            "-10^9 <= nums[i] <= 10^9",
        ],
        "follow_up": "Can you solve it in O(n) time using O(n) extra space?",
        "hints": [
            "Sorting solves it in O(n log n), but the bound rules that out. Put every "
            "value in a hash set and think about which element you should start counting from.",
            "Only start a count at x when x - 1 is absent — x is then the head of its run. "
            "Every element is visited at most twice, so the whole scan stays linear.",
        ],
    },
    9: {
        "statement": (
            "Given an array `nums` of size `n`, return the majority element.\n\n"
            "The majority element is the element that appears **more than "
            "⌊n / 2⌋ times**. You may assume that the majority element always "
            "exists in the array."
        ),
        "explanations": [
            "3 appears twice out of three elements, which is more than ⌊3/2⌋ = 1.",
            "2 appears four times out of seven elements, which is more than ⌊7/2⌋ = 3.",
        ],
        "constraints_exact": [
            "n == nums.length",
            "1 <= n <= 5 * 10^4",
            "-10^9 <= nums[i] <= 10^9",
        ],
        "follow_up": "Could you solve the problem in linear time and in O(1) space?",
        "hints": [
            "A hash-map count is the obvious O(n) time, O(n) space answer. The "
            "interesting version drops the space.",
            "Boyer-Moore voting: hold a candidate and a counter. Matching elements "
            "increment it, differing ones decrement it, and a zero counter takes a new "
            "candidate. A strict majority always survives the cancellations.",
        ],
    },
    13: {
        "statement": (
            "Given a **non-empty** array of integers `nums`, every element appears "
            "twice except for one. Find that single one.\n\n"
            "You must implement a solution with linear runtime complexity and use "
            "only constant extra space."
        ),
        "explanations": [
            "The pair of 2s cancels out, leaving 1.",
            "The pairs of 1s and 2s cancel out, leaving 4.",
            "There is a single element and it has no pair.",
        ],
        "constraints_exact": [
            "1 <= nums.length <= 3 * 10^4",
            "-3 * 10^4 <= nums[i] <= 3 * 10^4",
            "Each element in the array appears twice except for one element which appears only once.",
        ],
        "follow_up": "Can you solve it in O(n) time using O(1) extra space?",
        "hints": [
            "The constant-space requirement rules out a hash set. Look for an "
            "operation where a value combined with itself vanishes.",
            "XOR is its own inverse: x ^ x == 0 and x ^ 0 == x. XOR the whole array "
            "together and every pair annihilates, leaving the lone element.",
        ],
    },
    15: {
        "statement": (
            "Given an array `nums` containing `n` distinct numbers in the range "
            "`[0, n]`, return the only number in the range that is **missing** "
            "from the array."
        ),
        "explanations": [
            "n = 3, so the numbers are drawn from [0, 3]. 2 is the one that does not appear.",
            "n = 2, so the numbers are drawn from [0, 2]. 2 is the one that does not appear.",
            "n = 9, so the numbers are drawn from [0, 9]. 8 is the one that does not appear.",
        ],
        "constraints_exact": [
            "n == nums.length",
            "1 <= n <= 10^4",
            "0 <= nums[i] <= n",
            "All the numbers of nums are unique.",
        ],
        "follow_up": (
            "Could you implement a solution using only O(1) extra space complexity "
            "and O(n) runtime complexity?"
        ),
        "hints": [
            "The full range [0, n] has a known sum, n * (n + 1) / 2. Compare it with "
            "what the array actually sums to.",
            "XOR works too and cannot overflow: fold together every index, every value, "
            "and n itself. Each present number cancels its own index and the missing one survives.",
        ],
    },
    17: {
        "statement": (
            "Given an unsorted integer array `nums`, return the smallest missing "
            "**positive** integer.\n\n"
            "You must implement an algorithm that runs in O(n) time and uses "
            "O(1) auxiliary space."
        ),
        "explanations": [
            "The numbers 1 and 3 are in the array, but 2 is missing.",
            "1 and 2 are present, so the smallest missing positive is 3.",
            "The smallest positive integer 1 is missing.",
        ],
        "constraints_exact": [
            "1 <= nums.length <= 10^5",
            "-2^31 <= nums[i] <= 2^31 - 1",
        ],
        "follow_up": "Can you solve it in O(n) time using O(1) extra space?",
        "hints": [
            "With n elements the answer is always in [1, n + 1] — the array cannot "
            "possibly contain every one of those n + 1 candidates.",
            "That bound lets the array be its own hash table. Swap each value v in "
            "[1, n] to index v - 1, then scan for the first position whose value is wrong.",
        ],
    },
    32: {
        "statement": (
            "Given an integer array `nums`, return all the triplets "
            "`[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k` and "
            "`j != k`, and `nums[i] + nums[j] + nums[k] == 0`.\n\n"
            "Notice that the solution set must **not contain duplicate triplets**."
        ),
        "explanations": [
            "The distinct triplets summing to zero are [-1, -1, 2] and [-1, 0, 1]. Notice that the order of the output and the order of the triplets does not matter.",
            "The only possible triplet does not sum to zero.",
            "The only possible triplet sums to zero.",
        ],
        "constraints_exact": [
            "3 <= nums.length <= 3000",
            "-10^5 <= nums[i] <= 10^5",
        ],
        "follow_up": "Can you solve it in O(n^2) time using O(1) extra space?",
        "hints": [
            "Sort the array first. Sorting makes duplicates adjacent, which is what "
            "lets you skip them cleanly, and it enables a two-pointer inner scan.",
            "Fix the first element, then walk two pointers inward from both ends of the "
            "remaining suffix: a sum below zero moves the left pointer right, above zero "
            "moves the right pointer left. Skip equal neighbours to avoid repeat triplets.",
        ],
    },
    33: {
        "statement": (
            "You are given an integer array `height` of length `n`. There are `n` "
            "vertical lines drawn such that the two endpoints of the `i`-th line "
            "are `(i, 0)` and `(i, height[i])`.\n\n"
            "Find two lines that together with the x-axis form a container, such "
            "that the container contains the most water.\n\n"
            "Return the maximum amount of water a container can store. Notice that "
            "you may **not** slant the container."
        ),
        "explanations": [
            "The lines at indices 1 and 8 have heights 8 and 7. They are 7 apart, and the water level is set by the shorter of the two, so the area is 7 * 7 = 49.",
            "Two lines of height 1 that are 1 apart hold an area of 1.",
        ],
        "constraints_exact": [
            "n == height.length",
            "2 <= n <= 10^5",
            "0 <= height[i] <= 10^4",
        ],
        "follow_up": "Can you solve it in O(n) time using O(1) extra space?",
        "hints": [
            "The area between two lines is (distance apart) * (height of the shorter "
            "line). Start with the widest possible pair — the two ends.",
            "Moving the taller line inward can never help: width shrinks and the height "
            "is still capped by the shorter line. So always move the shorter one, and "
            "one pass suffices.",
        ],
    },
    34: {
        "statement": (
            "Given `n` non-negative integers representing an elevation map where "
            "the width of each bar is `1`, compute how much water it can trap "
            "after raining."
        ),
        "explanations": [
            "The elevation map [0,1,0,2,1,0,1,3,2,1,2,1] traps 6 units of rain water. Each dip holds water up to the lower of the tallest bars on its left and right.",
            "The two dips between the bars of height 4 and 5 trap 9 units in total.",
        ],
        "constraints_exact": [
            "n == height.length",
            "1 <= n <= 2 * 10^4",
            "0 <= height[i] <= 10^5",
        ],
        "follow_up": "Can you solve it in O(n) time using O(1) extra space?",
        "hints": [
            "Think per column, not per puddle. The water sitting above index i is "
            "min(tallest bar to its left, tallest bar to its right) - height[i], floored at zero.",
            "Precomputing both maxima costs O(n) space. Two pointers converging from the "
            "ends remove it: whichever side has the smaller running maximum is the side "
            "whose water level is already known.",
        ],
    },
}
