import os
from collections import defaultdict

stats = defaultdict(lambda: {"files": 0, "lines": 0})

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", "data", "data_release", ".hypothesis"]]
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                lines = sum(1 for _ in fh)
            category = path.split(os.sep)[1] if os.sep in path else "root"
            stats[category]["files"] += 1
            stats[category]["lines"] += lines

total_files = sum(s["files"] for s in stats.values())
total_lines = sum(s["lines"] for s in stats.values())

print(f"{'Category':<12} {'Files':>6} {'Lines':>8}")
print("-" * 28)
for cat in sorted(stats.keys()):
    print(f"{cat:<12} {stats[cat]['files']:>6} {stats[cat]['lines']:>8}")
print("-" * 28)
print(f"{'TOTAL':<12} {total_files:>6} {total_lines:>8}")
