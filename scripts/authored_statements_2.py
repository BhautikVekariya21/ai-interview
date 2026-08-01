"""Hand-authored statements, part 2 — strings, stacks, binary search, linked
lists, trees, DP.

Split from `authored_statements.py` only for file size; the two dicts are merged
by `scripts/build_authored_statements.py`. Same rules apply — see that module's
docstring, in particular: **no entry may state an example**, and every
`explanations[i]` must agree with recorded test case `i`.

Note on the linked-list and tree problems: this bank stores them as flat arrays
rather than node objects (the signature really is `reverseList(head: int[])`),
so the statements are written to that representation deliberately. Saying
"ListNode" here would describe an API the grader does not accept.
"""

from typing import Any, Dict

AUTHORED_2: Dict[int, Dict[str, Any]] = {
    # ── Strings ──────────────────────────────────────────────────────────────
    31: {
        "statement": (
            "A phrase is a **palindrome** if, after converting all uppercase "
            "letters into lowercase letters and removing all non-alphanumeric "
            "characters, it reads the same forward and backward. Alphanumeric "
            "characters include letters and numbers.\n\n"
            "Given a string `s`, return `true` if it is a palindrome, or `false` "
            "otherwise."
        ),
        "explanations": [
            "After lowercasing and dropping non-alphanumeric characters, s becomes 'amanaplanacanalpanama', which is a palindrome.",
            "After the same normalisation s becomes 'raceacar', which is not a palindrome.",
            "s is a single space. After removing non-alphanumeric characters s becomes the empty string, and an empty string reads the same both ways.",
        ],
        "constraints_exact": [
            "1 <= s.length <= 2 * 10^5",
            "`s` consists only of printable ASCII characters.",
        ],
        "follow_up": "Can you solve it in O(n) time using O(1) extra space?",
        "hints": [
            "Building a cleaned copy of the string is the straightforward route, and it "
            "costs O(n) extra space.",
            "Two pointers walking inward avoid the copy: skip non-alphanumeric characters "
            "in place on each side and compare the survivors case-insensitively.",
        ],
    },
    42: {
        "statement": (
            "Given a string `s`, find the length of the **longest substring** "
            "without duplicate characters.\n\n"
            "A **substring** is a contiguous non-empty sequence of characters "
            "within a string."
        ),
        "explanations": [
            "The answer is 'abc', with the length of 3.",
            "The answer is 'b', with the length of 1.",
            "The answer is 'wke', with the length of 3. Notice that the answer must be a substring — 'pwke' is a subsequence and not a substring.",
        ],
        "constraints_exact": [
            "0 <= s.length <= 5 * 10^4",
            "`s` consists of English letters, digits, symbols and spaces.",
        ],
        "follow_up": "Can you solve it in O(n) time using O(min(n, m)) extra space, where m is the size of the character set?",
        "hints": [
            "Maintain a window that is always duplicate-free. Extend it on the right, "
            "and when the new character is already inside, pull the left edge in.",
            "Storing each character's last index lets the left edge jump straight past "
            "the previous occurrence instead of creeping one step at a time.",
        ],
    },
    43: {
        "statement": (
            "You are given a string `s` and an integer `k`. You can choose any "
            "character of the string and change it to any other uppercase English "
            "character. You can perform this operation **at most** `k` times.\n\n"
            "Return the length of the longest substring containing the same letter "
            "you can get after performing the above operations."
        ),
        "explanations": [
            "Replace the two 'A's with two 'B's, or vice versa, and the entire string of length 4 becomes a single repeated letter.",
            "Replace the one 'A' in the middle with 'B' to form 'AABBBBA'; the substring 'BBBB' has length 4.",
        ],
        "constraints_exact": [
            "1 <= s.length <= 10^5",
            "`s` consists of only uppercase English letters.",
            "0 <= k <= s.length",
        ],
        "follow_up": "Can you solve it in O(n) time using O(1) extra space?",
        "hints": [
            "A window is valid when the number of characters you would have to replace "
            "— its length minus the count of its most frequent letter — is at most k.",
            "Grow the window on the right and shrink it on the left only when it becomes "
            "invalid. The window never needs to shrink below the best length already found.",
        ],
    },
    44: {
        "statement": (
            "Given two strings `s` and `t` of lengths `m` and `n` respectively, "
            "return the **minimum window substring** of `s` such that every "
            "character in `t` (**including duplicates**) is included in the "
            "window. If there is no such substring, return the empty string `\"\"`."
            "\n\nThe testcases will be generated such that the answer is "
            "**unique**."
        ),
        "explanations": [
            "The minimum window substring 'BANC' includes 'A', 'B' and 'C' from string t.",
            "The entire string s is the minimum window.",
            "Both 'a's from t must be included in the window. Since the largest window of s only has one 'a', return the empty string.",
        ],
        "constraints_exact": [
            "m == s.length",
            "n == t.length",
            "1 <= m, n <= 10^5",
            "`s` and `t` consist of uppercase and lowercase English letters.",
        ],
        "follow_up": "Could you find an algorithm that runs in O(m + n) time?",
        "hints": [
            "Count what t requires, then slide a window over s tracking how many of "
            "those requirements are currently satisfied.",
            "Expand right until the window is valid, then contract from the left as far "
            "as it stays valid, recording the best length each time. Each character enters "
            "and leaves the window once.",
        ],
    },
    45: {
        "statement": (
            "Given two strings `s1` and `s2`, return `true` if `s2` contains a "
            "**permutation** of `s1`, or `false` otherwise.\n\n"
            "In other words, return `true` if one of `s1`'s permutations is a "
            "substring of `s2`."
        ),
        "explanations": [
            "s2 contains one permutation of s1 — the substring 'ba' beginning at index 3.",
            "No window of s2 of length 2 is a rearrangement of 'ab'.",
        ],
        "constraints_exact": [
            "1 <= s1.length, s2.length <= 10^4",
            "`s1` and `s2` consist of lowercase English letters.",
        ],
        "follow_up": "Can you solve it in O(n) time using O(1) extra space?",
        "hints": [
            "A permutation of s1 has exactly s1's letter counts and exactly s1's length. "
            "So you are looking for a fixed-width window whose counts match.",
            "Slide a window of length s1.length across s2, adding the entering character "
            "and removing the leaving one. Comparing two 26-slot count arrays is O(1).",
        ],
    },
    57: {
        "statement": (
            "Given an encoded string, return its decoded string.\n\n"
            "The encoding rule is: `k[encoded_string]`, where the "
            "`encoded_string` inside the square brackets is being repeated "
            "exactly `k` times. Note that `k` is guaranteed to be a positive "
            "integer.\n\n"
            "You may assume that the input string is always valid: there are no "
            "extra white spaces, square brackets are well-formed, and the "
            "original data does not contain any digits — digits are only for "
            "those repeat numbers, `k`. There is no limit on the nesting depth."
        ),
        "explanations": [
            "'a' repeats 3 times and 'bc' repeats 2 times, giving 'aaa' followed by 'bcbc'.",
            "The inner group 2[c] decodes to 'cc', so the body becomes 'acc', and repeating that 3 times gives 'accaccacc'.",
            "'abc' repeats 3 times, 'cd' repeats 3 times, and the trailing 'ef' is copied as is.",
        ],
        "constraints_exact": [
            "1 <= s.length <= 30",
            "`s` consists of lowercase English letters, digits, and square brackets '[]'.",
            "`s` is guaranteed to be a valid input.",
            "All the integers in `s` are in the range [1, 300].",
        ],
        "follow_up": "Can you solve it in O(n * maxK) time?",
        "hints": [
            "Nesting means an inner group must finish before the outer one can repeat — "
            "that is exactly what a stack is for.",
            "On '[' push the repeat count and the string built so far, then start fresh. "
            "On ']' pop them and append the finished group the recorded number of times.",
        ],
    },
    49: {
        "statement": (
            "Given a string `s` containing just the characters `'('`, `')'`, "
            "`'{'`, `'}'`, `'['` and `']'`, determine if the input string is "
            "valid.\n\n"
            "An input string is valid if:\n\n"
            "- Open brackets must be closed by the same type of brackets.\n"
            "- Open brackets must be closed in the correct order.\n"
            "- Every close bracket has a corresponding open bracket of the same "
            "type."
        ),
        "explanations": [
            "The single pair of round brackets opens and closes correctly.",
            "Each pair opens and closes immediately in the correct order.",
            "The '(' is closed by a ']' rather than a ')', so the bracket types do not match.",
        ],
        "constraints_exact": [
            "1 <= s.length <= 10^4",
            "`s` consists of parentheses only: '()[]{}'.",
        ],
        "follow_up": "Can you solve it in O(n) time using O(n) extra space?",
        "hints": [
            "The most recently opened bracket must be the first one closed. That "
            "last-in-first-out rule is precisely a stack.",
            "Push opening brackets; on a closing bracket, the stack must be non-empty "
            "and its top must be the matching opener. At the end the stack must be empty.",
        ],
    },
    51: {
        "statement": (
            "You are given an array of strings `tokens` that represents an "
            "arithmetic expression in a **Reverse Polish Notation**.\n\n"
            "Evaluate the expression and return an integer that represents its "
            "value.\n\n"
            "**Note that:**\n\n"
            "- The valid operators are `'+'`, `'-'`, `'*'` and `'/'`.\n"
            "- Each operand may be an integer or another expression.\n"
            "- The division between two integers always **truncates toward "
            "zero**.\n"
            "- There will not be any division by zero.\n"
            "- The input represents a valid arithmetic expression in reverse "
            "polish notation.\n"
            "- The answer and all the intermediate calculations can be "
            "represented in a **32-bit** integer."
        ),
        "explanations": [
            "The expression is evaluated as ((2 + 1) * 3) = 9.",
            "The expression is evaluated as (4 + (13 / 5)) = 4 + 2 = 6, since division truncates toward zero.",
            "The expression evaluates step by step to 22.",
        ],
        "constraints_exact": [
            "1 <= tokens.length <= 10^4",
            "`tokens[i]` is either an operator ('+', '-', '*' or '/'), or an integer in the range [-200, 200].",
        ],
        "follow_up": "Can you solve it in O(n) time using O(n) extra space?",
        "hints": [
            "In RPN an operator always applies to the two most recent values, so push "
            "numbers onto a stack and let operators consume the top two.",
            "Mind the operand order for '-' and '/': the value popped first is the "
            "right-hand side. Truncation toward zero differs from floor division for "
            "negative results in some languages.",
        ],
    },
    52: {
        "statement": (
            "Given an array of integers `temperatures` that represents the daily "
            "temperatures, return an array `answer` such that `answer[i]` is the "
            "number of days you have to wait after the `i`-th day to get a warmer "
            "temperature.\n\n"
            "If there is no future day for which this is possible, keep "
            "`answer[i] == 0` instead."
        ),
        "explanations": [
            "From day 0 (73) a warmer day arrives the very next day; from day 2 (75) you must wait until day 6 (76), which is 4 days later; the last two days never get warmer, so they stay 0.",
            "Every day is warmer than the one before, so each wait is 1 — except the final day, which has no future.",
        ],
        "constraints_exact": [
            "1 <= temperatures.length <= 10^5",
            "30 <= temperatures[i] <= 100",
        ],
        "follow_up": "Can you solve it in O(n) time using O(n) extra space?",
        "hints": [
            "Each day is waiting for the next strictly greater value to its right. "
            "Comparing every pair is O(n^2); the answers can be resolved in one pass instead.",
            "Keep a stack of indices whose answers are still unknown, with decreasing "
            "temperatures. A warmer day pops every index it beats, and the distance "
            "between the two indices is that day's answer.",
        ],
    },
    53: {
        "statement": (
            "Given an array of integers `heights` representing the histogram's bar "
            "height where the **width of each bar is 1**, return the area of the "
            "largest rectangle in the histogram.\n\n"
            "A rectangle must be made of whole bars standing next to each other: "
            "if it spans a range of bars, its height cannot exceed the shortest "
            "bar in that range."
        ),
        "explanations": [
            "The largest rectangle spans the two bars of heights 5 and 6 at indices 2 and 3. Limited by the shorter of the two, it is 2 wide and 5 tall, giving an area of 10.",
            "The largest rectangle is the single bar of height 4, or both bars at height 2 — both give an area of 4.",
        ],
        "constraints_exact": [
            "1 <= heights.length <= 10^5",
            "0 <= heights[i] <= 10^4",
        ],
        "follow_up": "Can you solve it in O(n) time using O(n) extra space?",
        "hints": [
            "Fix a bar and ask how far its own height can extend: left until a shorter "
            "bar blocks it, right until the same. That width times its height is one candidate.",
            "A stack of indices with increasing heights finds both boundaries in a single "
            "pass. When a shorter bar arrives, every taller bar it pops has just found its "
            "right edge, and the new stack top is its left edge.",
        ],
    },
    56: {
        "statement": (
            "We are given an array `asteroids` of integers representing asteroids "
            "in a row. The indices of the asteroids in the array represent their "
            "relative position in space.\n\n"
            "For each asteroid, the absolute value represents its size, and the "
            "sign represents its direction (positive meaning right, negative "
            "meaning left). Each asteroid moves at the same speed.\n\n"
            "Find out the state of the asteroids after all collisions. If two "
            "asteroids meet, the smaller one will explode. If both are the same "
            "size, both will explode. Two asteroids moving in the same direction "
            "will never meet."
        ),
        "explanations": [
            "The 10 and -5 collide, resulting in 10. The 5 and 10 never collide because they both move right.",
            "The 8 and -8 collide, and being equal in size, both explode.",
            "The 10 and -5 collide, resulting in 10. Then the 2 and -5 have already gone, so 10 remains alone.",
        ],
        "constraints_exact": [
            "2 <= asteroids.length <= 10^4",
            "-1000 <= asteroids[i] <= 1000",
            "asteroids[i] != 0",
        ],
        "follow_up": "Can you solve it in O(n) time using O(n) extra space?",
        "hints": [
            "A collision only happens when a right-moving asteroid is immediately "
            "followed by a left-moving one. Everything else passes by untouched.",
            "Push survivors onto a stack. A negative asteroid keeps fighting the positive "
            "top of the stack until it is destroyed, destroys them all, or meets a negative "
            "asteroid and is safe.",
        ],
    },
    55: {
        "statement": (
            "The **next greater element** of some element `x` in an array is the "
            "first greater element that is **to the right** of `x` in the same "
            "array.\n\n"
            "You are given two **distinct 0-indexed** integer arrays `nums1` and "
            "`nums2`, where `nums1` is a subset of `nums2`.\n\n"
            "For each `0 <= i < nums1.length`, find the index `j` such that "
            "`nums1[i] == nums2[j]` and determine the next greater element of "
            "`nums2[j]` in `nums2`. If there is no next greater element, then the "
            "answer for this query is `-1`.\n\n"
            "Return an array `ans` of length `nums1.length` such that `ans[i]` is "
            "the next greater element as described above."
        ),
        "explanations": [
            "For 4 there is no greater number to its right in nums2, so the answer is -1. For 1 the next greater number is 3. For 2 there is no number greater than it to its right, so -1.",
            "For 2 the next greater number is 3. For 4 there is no next greater number, so -1.",
        ],
        "constraints_exact": [
            "1 <= nums1.length <= nums2.length <= 1000",
            "0 <= nums1[i], nums2[i] <= 10^4",
            "All integers in nums1 and nums2 are unique.",
            "All the integers of nums1 also appear in nums2.",
        ],
        "follow_up": "Could you find an O(nums1.length + nums2.length) solution?",
        "hints": [
            "Solve it for every element of nums2 first, then answer each query by lookup. "
            "The values are unique, so a value-to-answer map is unambiguous.",
            "A decreasing monotonic stack over nums2 resolves all next-greater answers in "
            "one pass: each new value pops — and answers — every smaller value beneath it.",
        ],
    },

    # ── Binary search ────────────────────────────────────────────────────────
    58: {
        "statement": (
            "Given an array of integers `nums` which is sorted in ascending order, "
            "and an integer `target`, write a function to search `target` in "
            "`nums`. If `target` exists, then return its index. Otherwise, return "
            "`-1`.\n\n"
            "You must write an algorithm with O(log n) runtime complexity."
        ),
        "explanations": [
            "9 exists in nums and its index is 4.",
            "2 does not exist in nums, so the answer is -1.",
            "The array holds a single element which is the target, at index 0.",
        ],
        "constraints_exact": [
            "1 <= nums.length <= 10^4",
            "-10^4 < nums[i], target < 10^4",
            "All the integers in nums are unique.",
            "nums is sorted in ascending order.",
        ],
        "follow_up": "Can you solve it in O(log n) time using O(1) extra space?",
        "hints": [
            "Compare with the middle element and discard the half that cannot contain "
            "the target.",
            "Compute the midpoint as low + (high - low) / 2 rather than (low + high) / 2 "
            "— in fixed-width integer languages the latter can overflow.",
        ],
    },
    59: {
        "statement": (
            "There is an integer array `nums` sorted in ascending order (with "
            "**distinct** values).\n\n"
            "Prior to being passed to your function, `nums` is **possibly "
            "rotated** at an unknown pivot index `k` such that the resulting "
            "array is `[nums[k], nums[k+1], ..., nums[n-1], nums[0], ..., "
            "nums[k-1]]`.\n\n"
            "Given the array `nums` **after** the possible rotation and an "
            "integer `target`, return the index of `target` if it is in `nums`, "
            "or `-1` if it is not in `nums`.\n\n"
            "You must write an algorithm with O(log n) runtime complexity."
        ),
        "explanations": [
            "The target 0 sits at index 4 of the rotated array.",
            "3 does not appear anywhere in the array.",
            "The array holds only the value 1, which is not the target.",
        ],
        "constraints_exact": [
            "1 <= nums.length <= 5000",
            "-10^4 <= nums[i] <= 10^4",
            "All values of nums are unique.",
            "nums is an ascending array that is possibly rotated.",
            "-10^4 <= target <= 10^4",
        ],
        "follow_up": "Can you solve it in O(log n) time using O(1) extra space?",
        "hints": [
            "Rotation breaks the array into two sorted runs, but at any midpoint at "
            "least one side is still fully sorted.",
            "Work out which half is sorted, check whether the target lies inside that "
            "half's known range, and recurse into that half or the other accordingly.",
        ],
    },
    62: {
        "statement": (
            "Koko loves to eat bananas. There are `n` piles of bananas, the "
            "`i`-th pile has `piles[i]` bananas. The guards have gone and will "
            "come back in `h` hours.\n\n"
            "Koko can decide her bananas-per-hour eating speed of `k`. Each hour, "
            "she chooses some pile of bananas and eats `k` bananas from that pile. "
            "If the pile has less than `k` bananas, she eats all of them instead "
            "and will not eat any more bananas during this hour.\n\n"
            "Koko likes to eat slowly but still wants to finish eating all the "
            "bananas before the guards return.\n\n"
            "Return the minimum integer `k` such that she can eat all the bananas "
            "within `h` hours."
        ),
        "explanations": [
            "At a speed of 4 the piles take 1, 2, 2 and 3 hours, totalling 8 — exactly the time available. Any slower speed would take too long.",
            "With only 5 hours for 5 piles, Koko must clear each pile in a single hour, so her speed must match the largest pile, 30.",
            "The extra sixth hour lets her drop to 23 — the pile of 30 now takes two hours and the rest one each.",
        ],
        "constraints_exact": [
            "1 <= piles.length <= 10^4",
            "piles.length <= h <= 10^9",
            "1 <= piles[i] <= 10^9",
        ],
        "follow_up": "Can you solve it in O(n log m) time, where m is the largest pile?",
        "hints": [
            "You are not searching the array — you are searching the answer. Speeds run "
            "from 1 to max(piles).",
            "Checking a speed is easy: sum the ceiling of each pile divided by k and "
            "compare with h. That check is monotonic in k, so binary search the smallest "
            "speed that passes.",
        ],
    },
    64: {
        "statement": (
            "Given a non-negative integer `x`, return the square root of `x` "
            "rounded down to the nearest integer. The returned integer should be "
            "**non-negative** as well.\n\n"
            "You **must not use** any built-in exponent function or operator."
        ),
        "explanations": [
            "The square root of 4 is exactly 2.",
            "The square root of 8 is 2.82842..., and since we round down to the nearest integer, 2 is returned.",
            "The square root of 1 is exactly 1.",
        ],
        "constraints_exact": [
            "0 <= x <= 2^31 - 1",
        ],
        "follow_up": "Can you solve it in O(log n) time using O(1) extra space?",
        "hints": [
            "The answer lies in [0, x], and 'is mid * mid <= x' is monotonic — true for "
            "every candidate up to the answer and false after it.",
            "Binary search for the largest such mid. Guard the multiplication against "
            "overflow near 2^31 - 1, or compare with mid <= x / mid instead.",
        ],
    },

    # ── Linked list (stored as flat arrays in this bank) ─────────────────────
    65: {
        "statement": (
            "Given the sequence of node values of a singly linked list, reverse "
            "the list and return the sequence of node values of the reversed "
            "list.\n\n"
            "The list is represented as an array of its values in order from head "
            "to tail, and your answer should use the same representation."
        ),
        "explanations": [
            "Reading the list backwards from tail to head gives 5, 4, 3, 2, 1.",
            "The two nodes swap places.",
            "The list is empty, so there is nothing to reverse.",
        ],
        "constraints_exact": [
            "The number of nodes in the list is in the range [0, 5000].",
            "-5000 <= Node.val <= 5000",
        ],
        "follow_up": (
            "A linked list can be reversed either iteratively or recursively. "
            "Could you implement both?"
        ),
        "hints": [
            "Walk the list carrying a pointer to the node before the current one, and "
            "flip each link as you pass it.",
            "Save the next node before overwriting the current node's link, or you lose "
            "the rest of the list.",
        ],
    },
    66: {
        "statement": (
            "You are given the node values of two sorted linked lists `l1` and "
            "`l2`, each in non-decreasing order.\n\n"
            "Merge the two lists into one **sorted** list. The list should be made "
            "by splicing together the nodes of the first two lists.\n\n"
            "Return the node values of the merged linked list, in order. Each list "
            "is represented as an array of its values from head to tail."
        ),
        "explanations": [
            "Taking the smaller head each time interleaves the two lists into 1, 1, 2, 3, 4, 4.",
            "Both lists are empty, so the merged list is empty too.",
            "The first list is empty, so the result is just the second list.",
        ],
        "constraints_exact": [
            "The number of nodes in both lists is in the range [0, 50].",
            "-100 <= Node.val <= 100",
            "Both l1 and l2 are sorted in non-decreasing order.",
        ],
        "follow_up": "Can you solve it in O(n + m) time?",
        "hints": [
            "Compare the two current heads and take the smaller one, advancing only that "
            "list.",
            "When one list runs out, the remainder of the other is already sorted and can "
            "be appended wholesale.",
        ],
    },
    70: {
        "statement": (
            "Given the sequence of node values of a singly linked list, return "
            "`true` if it is a **palindrome** — that is, if the values read the "
            "same from head to tail as from tail to head — or `false` otherwise.\n\n"
            "The list is represented as an array of its values in order from head "
            "to tail."
        ),
        "explanations": [
            "The values read 1, 2, 2, 1 in both directions.",
            "Read forwards the values are 1, 2; read backwards they are 2, 1.",
        ],
        "constraints_exact": [
            "The number of nodes in the list is in the range [1, 10^5].",
            "0 <= Node.val <= 9",
        ],
        "follow_up": (
            "Could you do it in O(n) time and O(1) space?"
        ),
        "hints": [
            "Comparing the ends inward is easy with random access; a real linked list "
            "gives you only forward traversal.",
            "Find the middle with a slow and a fast pointer, reverse the second half in "
            "place, then compare the two halves node by node.",
        ],
    },

    # ── Trees (stored as level-order arrays in this bank) ────────────────────
    72: {
        "statement": (
            "Given the `root` of a binary tree, return its **maximum depth**.\n\n"
            "A binary tree's **maximum depth** is the number of nodes along the "
            "longest path from the root node down to the farthest leaf node.\n\n"
            "The tree is given in level order, where `null` marks a missing "
            "child."
        ),
        "explanations": [
            "The longest root-to-leaf path runs 3 → 20 → 15 (or 3 → 20 → 7), visiting 3 nodes.",
            "The root has only a right child, so the longest path visits 2 nodes.",
            "The tree is empty, so its depth is 0.",
        ],
        "constraints_exact": [
            "The number of nodes in the tree is in the range [0, 10^4].",
            "-100 <= Node.val <= 100",
        ],
        "follow_up": "Can you solve it in O(n) time?",
        "hints": [
            "The depth of a tree is one more than the deeper of its two subtrees — the "
            "recursion writes itself.",
            "A breadth-first traversal counting completed levels avoids deep recursion "
            "on a skewed tree.",
        ],
    },
    74: {
        "statement": (
            "Given the root of a binary tree, invert the tree — swap the left "
            "and right child of every node — and return it.\n\n"
            "The tree is given in level order as the array `arr`, and your answer "
            "should use the same representation."
        ),
        "explanations": [
            "Swapping the children at every level mirrors the tree, so 4's children become 7 and 2, and their children follow in mirrored order.",
            "The root's two children swap places.",
        ],
        "constraints_exact": [
            "The number of nodes in the tree is in the range [0, 100].",
            "-100 <= Node.val <= 100",
        ],
        "follow_up": "Can you solve it in O(n) time?",
        "hints": [
            "Swap the two children of a node, then invert each subtree. The order of "
            "those two steps does not matter.",
            "Any traversal works as long as every node is visited exactly once — "
            "recursion or an explicit queue both do.",
        ],
    },
    77: {
        "statement": (
            "Given the `root` of a binary tree, return the **level order "
            "traversal** of its nodes' values — from left to right, level by "
            "level.\n\n"
            "The tree is given in level order, where `null` marks a missing "
            "child."
        ),
        "explanations": [
            "The root forms the first level, its children 9 and 20 the second, and 20's children 15 and 7 the third.",
            "The tree has a single node, which forms the only level.",
            "The tree is empty, so there are no levels to report.",
        ],
        "constraints_exact": [
            "The number of nodes in the tree is in the range [0, 2000].",
            "-1000 <= Node.val <= 1000",
        ],
        "follow_up": "Can you solve it in O(n) time using O(n) extra space?",
        "hints": [
            "A queue visits nodes in exactly this order. The only extra work is knowing "
            "where one level ends.",
            "Record the queue's size before draining it — that count is precisely the "
            "current level's width.",
        ],
    },

    # ── Dynamic programming ──────────────────────────────────────────────────
    79: {
        "statement": (
            "You are climbing a staircase. It takes `n` steps to reach the top.\n\n"
            "Each time you can either climb `1` or `2` steps. In how many distinct "
            "ways can you climb to the top?"
        ),
        "explanations": [
            "There are two ways to climb to the top: 1 step + 1 step, or 2 steps.",
            "There are three ways to climb to the top: 1+1+1, 1+2, or 2+1.",
            "There are eight distinct orderings of 1- and 2-step moves that sum to 5.",
        ],
        "constraints_exact": [
            "1 <= n <= 45",
        ],
        "follow_up": "Can you solve it in O(n) time using O(1) extra space?",
        "hints": [
            "The last move onto step n came from either step n - 1 or step n - 2, and "
            "those two sets of routes are disjoint.",
            "So ways(n) = ways(n-1) + ways(n-2) — the Fibonacci recurrence. Only the "
            "previous two values are ever needed, so two variables suffice.",
        ],
    },
    80: {
        "statement": (
            "You are a professional robber planning to rob houses along a street. "
            "Each house has a certain amount of money stashed, the only constraint "
            "stopping you from robbing each of them is that adjacent houses have "
            "security systems connected and **it will automatically contact the "
            "police if two adjacent houses were broken into on the same night**.\n\n"
            "Given an integer array `nums` representing the amount of money in "
            "each house, return the maximum amount of money you can rob tonight "
            "**without alerting the police**."
        ),
        "explanations": [
            "Rob house 0 (money = 1) and then rob house 2 (money = 3). Total amount you can rob = 1 + 3 = 4.",
            "Rob houses 0, 2 and 4 (money = 2 + 9 + 1 = 12).",
            "Rob the first and last houses for 2 + 2 = 4; taking the two middle houses would yield less.",
        ],
        "constraints_exact": [
            "1 <= nums.length <= 100",
            "0 <= nums[i] <= 400",
        ],
        "follow_up": "Can you solve it in O(n) time using O(1) extra space?",
        "hints": [
            "At each house you either take it — and must skip the previous one — or "
            "skip it and keep whatever the previous house allowed.",
            "best(i) = max(best(i-1), best(i-2) + nums[i]). Only two running totals are "
            "needed, so the array of subresults can be dropped.",
        ],
    },
}
