import os
import re
import glob

# Search in both pages and components
files_to_update = glob.glob(r'e:\ai-interview\frontend\src\pages\*.tsx') + \
                  glob.glob(r'e:\ai-interview\frontend\src\components\*.tsx') + \
                  [r'e:\ai-interview\frontend\src\App.tsx']

replacements = [
    (r'bg-\[\#FFF6EB\]', r'bg-[#F1F7F9]'),
    (r'bg-\[\#FAF5EF\]', r'bg-[#FFFFFF]'),
    (r'bg-\[\#FAF2E8\]', r'bg-[#FFFFFF]'),
    (r'bg-\[\#EBE4DC\]', r'bg-[#F1F7F9]'),
    (r'bg-\[\#FFEFE5\]', r'bg-[#F1F7F9]'),
    (r'bg-\[\#F0F5FF\]', r'bg-[#F1F7F9]'),
    (r'text-\[\#161616\]', r'text-[#000]'),
    (r'bg-\[\#161616\]', r'bg-[#000]'),
    (r'border-\[\#161616\]', r'border-[#000]'),
    (r'text-black/60', r'text-black/70'),
    (r'text-black/70', r'text-black/80'),
    (r'font-black', r'font-semibold'),
    (r'rounded-full', r'rounded-xl') 
]

for filepath in files_to_update:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Don't override the Landing h1 again properly if it's already font-semibold
        # Same replacements to be safe everywhere
        original_content = content
        
        for old, new in replacements:
            content = re.sub(old, new, content)
            
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filepath}")

print("Done updating all files.")
