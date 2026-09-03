import os
import re
import glob

files_to_update = glob.glob(r'e:\ai-interview\frontend\src\pages\*.tsx') + \
                  glob.glob(r'e:\ai-interview\frontend\src\components\*.tsx') + \
                  [r'e:\ai-interview\frontend\src\App.tsx']

string_replacements = [
    ('card-3d-wrapper ', ''),
    ('card-3d-wrapper', ''),
    ('glass ', 'bg-white shadow-sm border border-black/10 '),
    ('"glass"', '"bg-white shadow-sm border border-black/10"'),
    ('bg-card border-border', 'bg-white border-black/10 shadow-sm'),
    ('bg-card border border-border', 'bg-white border border-black/10 shadow-sm'),
    ('text-gradient', 'text-black'),
    ('glow-accent', 'ring-1 ring-black/5'),
    ('bg-white/10 backdrop-blur-md border border-white/20', 'bg-[#F1F7F9] border border-black/10 shadow-sm'),
    ('bg-background/60 backdrop-blur-md border border-border/50', 'bg-white border border-black/5 rounded-xl shadow-sm pb-1'),
    ('border-glass-border', 'border-black/5'),
    ('border-border/50', 'border-black/5'),
    ('border-border', 'border-black/10'),
    ('bg-primary/20 animate-pulse-slow', 'bg-transparent'),
    ('bg-accent/20 animate-float', 'bg-transparent'),
]

for filepath in files_to_update:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original = content
        for old, new in string_replacements:
            content = content.replace(old, new)
            
        # Regex for the linear-gradient bg classes
        content = re.sub(r'bg-\[\s*linear-gradient[^\)]+\)\]', 'bg-white', content)
            
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Flattened {filepath}")

print("Done flattening UI.")
