/**
 * LeetCode-style Python starter templates for the interview code pad.
 * Picks a skeleton matching the question's topic so candidates start from
 * a runnable scaffold instead of a blank editor.
 */

interface StarterTemplate {
  pattern: RegExp;
  code: string;
}

const templates: StarterTemplate[] = [
  {
    pattern: /\b(sql|query|select|database table|join)\b/i,
    code: `# Write your SQL as a string and print it, or simulate the data in Python.
query = """
SELECT *
FROM table_name
WHERE condition;
"""
print(query.strip())
`,
  },
  {
    pattern: /\b(recursion|recursive|fibonacci|factorial|tree|traverse|dfs|depth[- ]first)\b/i,
    code: `class Solution:
    def solve(self, n):
        # Base case
        if n <= 1:
            return n
        # Recursive case
        return self.solve(n - 1) + self.solve(n - 2)


if __name__ == "__main__":
    solution = Solution()
    print(solution.solve(10))  # Test your solution
`,
  },
  {
    pattern: /\b(sort|sorted|sorting|order the|arrange)\b/i,
    code: `class Solution:
    def solve(self, nums):
        # Implement your sorting logic here
        for i in range(len(nums)):
            for j in range(0, len(nums) - i - 1):
                if nums[j] > nums[j + 1]:
                    nums[j], nums[j + 1] = nums[j + 1], nums[j]
        return nums


if __name__ == "__main__":
    solution = Solution()
    print(solution.solve([5, 2, 9, 1, 7]))  # Test your solution
`,
  },
  {
    pattern: /\b(linked list|stack|queue|hash ?map|hash ?table|dictionary|data structure)\b/i,
    code: `class Solution:
    def solve(self, data):
        # Choose the right data structure for the problem
        seen = {}
        result = []
        for item in data:
            if item not in seen:
                seen[item] = True
                result.append(item)
        return result


if __name__ == "__main__":
    solution = Solution()
    print(solution.solve([1, 2, 2, 3, 1]))  # Test your solution
`,
  },
  {
    pattern: /\b(string|substring|palindrome|reverse|anagram|character)\b/i,
    code: `class Solution:
    def solve(self, s):
        # Work through the string here
        result = ""
        for ch in s:
            result = ch + result
        return result


if __name__ == "__main__":
    solution = Solution()
    print(solution.solve("hello"))  # Test your solution
`,
  },
  {
    pattern: /\b(loop|iterate|iteration|array|list|sum|count|find|maximum|minimum|largest|smallest)\b/i,
    code: `class Solution:
    def solve(self, nums):
        # Loop through the input and build your answer
        result = 0
        for num in nums:
            result += num
        return result


if __name__ == "__main__":
    solution = Solution()
    print(solution.solve([1, 2, 3, 4, 5]))  # Test your solution
`,
  },
  {
    pattern: /\b(if|condition|check whether|determine if|valid|boolean)\b/i,
    code: `class Solution:
    def solve(self, value):
        # Add your conditions here
        if value > 0:
            return "positive"
        elif value < 0:
            return "negative"
        else:
            return "zero"


if __name__ == "__main__":
    solution = Solution()
    print(solution.solve(5))  # Test your solution
`,
  },
];

const genericTemplate = `class Solution:
    def solve(self):
        # Write your code here
        pass


if __name__ == "__main__":
    solution = Solution()
    print(solution.solve())  # Test your solution
`;

/** Return a runnable Python skeleton matched to the question's topic. */
export function getStarterCode(questionText: string): string {
  const text = questionText || "";
  for (const template of templates) {
    if (template.pattern.test(text)) {
      return template.code;
    }
  }
  return genericTemplate;
}
