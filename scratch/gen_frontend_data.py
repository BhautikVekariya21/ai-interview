"""Generate frontend codingProblemsData.ts from backend PROBLEMS."""
import json
import sys

sys.path.insert(0, ".")
from app.services.coding_problems_data import PROBLEMS

lines = []
lines.append("/**")
lines.append(
    " * Coding Problems Data — Fallback/offline dataset used when the backend is unreachable."
)
lines.append(f" * Auto-generated from backend coding_problems_data.py ({len(PROBLEMS)} problems).")
lines.append(" */")
lines.append("")
lines.append("export interface CodingProblem {")
lines.append("  id: number;")
lines.append('  title: string;')
lines.append('  difficulty: "Easy" | "Medium" | "Hard";')
lines.append("  topic: string;")
lines.append("  tags: string[];")
lines.append("  description: string;")
lines.append("  constraints: string;")
lines.append("  testCases: { input: string; expected: string }[];")
lines.append("  starterCode: string;")
lines.append("  solutionCode: string;")
lines.append("  hints: string[];")
lines.append("  timeComplexity: string;")
lines.append("  spaceComplexity: string;")
lines.append("  companiesAsked: string[];")
lines.append("}")
lines.append("")

# Extract unique topics in order
topics = list(dict.fromkeys(p["topic"] for p in PROBLEMS))
lines.append("export const CODING_TOPICS = [")
for t in topics:
    lines.append(f"  {json.dumps(t)},")
lines.append("] as const;")
lines.append("")
lines.append("export type CodingTopic = (typeof CODING_TOPICS)[number];")
lines.append("")
lines.append(
    "export const DIFFICULTY_COLORS: Record<string, { bg: string; text: string; border: string }> = {"
)
lines.append(
    '  Easy: { bg: "bg-emerald-500/10", text: "text-emerald-500", border: "border-emerald-500/20" },'
)
lines.append(
    '  Medium: { bg: "bg-amber-500/10", text: "text-amber-500", border: "border-amber-500/20" },'
)
lines.append(
    '  Hard: { bg: "bg-red-500/10", text: "text-red-500", border: "border-red-500/20" },'
)
lines.append("};")
lines.append("")
lines.append("export const CODING_PROBLEMS: CodingProblem[] = [")

for p in PROBLEMS:
    tc_parts = []
    for tc in p["testCases"]:
        entry = (
            "{ input: "
            + json.dumps(tc["input"])
            + ", expected: "
            + json.dumps(tc["expected"])
            + " }"
        )
        tc_parts.append(entry)
    tc_str = "[" + ", ".join(tc_parts) + "]"

    lines.append("  {")
    lines.append(f"    id: {p['id']},")
    lines.append(f"    title: {json.dumps(p['title'])},")
    lines.append(f"    difficulty: {json.dumps(p['difficulty'])},")
    lines.append(f"    topic: {json.dumps(p['topic'])},")
    lines.append(f"    tags: {json.dumps(p['tags'])},")
    lines.append(f"    description: {json.dumps(p['description'])},")
    lines.append(f"    constraints: {json.dumps(p['constraints'])},")
    lines.append(f"    testCases: {tc_str},")
    lines.append(f"    starterCode: {json.dumps(p['starterCode'])},")
    lines.append(f"    solutionCode: {json.dumps(p['solutionCode'])},")
    lines.append(f"    hints: {json.dumps(p['hints'])},")
    lines.append(f"    timeComplexity: {json.dumps(p['timeComplexity'])},")
    lines.append(f"    spaceComplexity: {json.dumps(p['spaceComplexity'])},")
    lines.append(f"    companiesAsked: {json.dumps(p['companiesAsked'])},")
    lines.append("  },")

lines.append("];")
lines.append("")

output_path = "frontend/src/components/codingProblemsData.ts"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Generated {len(PROBLEMS)} problems -> {output_path}")
