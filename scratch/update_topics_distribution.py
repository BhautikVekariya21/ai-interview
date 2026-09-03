import json
import sys
import random

sys.path.insert(0, 'e:/ai-interview')
from app.services.coding_problems_data import PROBLEMS

NEW_TOPICS = [
    'Graphs', 'Backtracking', 'Bit Manipulation', 'Math & Geometry', 
    'Tries', 'Greedy', 'Heap / Priority Queue', 'Divide & Conquer',
    'Segment Tree', 'Disjoint Set (Union-Find)', 'Topological Sort'
]
OLD_TOPICS = [
    'Arrays & Hashing', 'Two Pointers', 'Sliding Window', 'Stack', 
    'Binary Search', 'Linked List', 'Trees', 'Dynamic Programming'
]
ALL_TOPICS = OLD_TOPICS + NEW_TOPICS

for p in PROBLEMS:
    p['topic'] = random.choice(ALL_TOPICS)

output_lines = [
    '"""',
    'Coding Problems Data — 1000 simulated problems.',
    '"""',
    '',
    'PROBLEMS = ['
]

for p in PROBLEMS:
    output_lines.append(f'    {json.dumps(p, indent=4).replace(chr(10), chr(10) + "    ")},')
output_lines.append(']')

with open('e:/ai-interview/app/services/coding_problems_data.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print('Updated topics for 1000 problems!')
