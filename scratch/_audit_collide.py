from app.services.coding_problems_data import PROBLEMS

base = [p for p in PROBLEMS if "(Variation" not in p["title"]]
print("base_count", len(base))
print("base_id_range", min(p["id"] for p in base), max(p["id"] for p in base))

# Themed variants are the ones the generator created (Domain: prefix in description)
themed = [p for p in PROBLEMS if p["description"].startswith("**Domain:")]
print("themed_count", len(themed))
print("themed_id_range", min(p["id"] for p in themed), max(p["id"] for p in themed))

originals = [p for p in PROBLEMS if not p["description"].startswith("**Domain:")]
print("original_count", len(originals))
print("original_id_range", min(p["id"] for p in originals), max(p["id"] for p in originals))
o_ids = {p["id"] for p in originals}
t_ids = [p["id"] for p in themed]
print("themed_ids_colliding_with_originals", len([i for i in t_ids if i in o_ids]))
print("themed_internal_dupes", len(t_ids) - len(set(t_ids)))
print("max_id_overall", max(p["id"] for p in PROBLEMS))

# Which originals carry the prefix-sum leak?
LEAK = "const prefix = [0];"
print("leaky_originals", [(p["id"], p["title"]) for p in originals if LEAK in p["starterCode"]])
print("leaky_themed", [(p["id"], p["title"]) for p in themed if LEAK in p["starterCode"]])
