# Catalogue verification receipt — 2026-09-22

Catalogue integrity only, not source/test certification. Run the following Python
from the reconciliation worktree root; it validates the frozen source candidate,
not a moving branch. Historical refs are deliberately excluded from active ancestry.

```python
import pathlib, re, subprocess
root = pathlib.Path.cwd()
cat = root / "peter/patch-catalog"
target = "0769f3455b"
def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()
text = (cat / "index.md").read_text()
active = text.split("## Current active stack", 1)[1].split("## Historical", 1)[0]
rows = [r for r in active.splitlines() if r.startswith("| 2026-")]
refs = []
for row in rows:
    cells = row.split("|")
    final = cells[2].rsplit("→", 1)[-1]
    tokens = re.findall(r"`([^`]+)`", final)
    assert tokens and all(re.fullmatch(r"[0-9a-f]{10,40}", t) for t in tokens), final
    link = re.search(r"\]\((reports/[^)]+)\)", row).group(1)
    report = (cat / link).read_text()
    header = report.split("\n## ", 1)[0]
    for ref in tokens:
        git("rev-parse", "--verify", ref + "^{commit}")
        subprocess.run(["git", "merge-base", "--is-ancestor", ref, target], check=True)
        assert "`" + ref + "`" in header, (link, ref)
        refs.append(ref)
links = 0
for path in cat.rglob("*.md"):
    for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
        if "://" in link or link.startswith(("#", "mailto:")):
            continue
        dest = link.split("#", 1)[0]
        assert (path.parent / dest).exists(), (path, link)
        links += 1
historic = [p for p in (cat / "reports").glob("*.md") if not p.name.startswith("2026-09-22-")]
assert all("Historical report as of 2026-09-22" in p.read_text().split("\n## ",1)[0] for p in historic)
changed = git("diff", "--name-only", target).splitlines()
assert all(p.startswith("peter/patch-catalog/") and p.endswith(".md") for p in changed)
subprocess.run(["git", "diff", "--check"], check=True)
print(f"PASS: {len(rows)} active rows; {len(refs)} active refs resolve and are ancestors of {target}; exact IDs in linked headers")
print(f"PASS: {links} relative links exist; {len(historic)} prior reports explicitly historical")
print("PASS: tracked delta is catalogue Markdown only; git diff --check clean")
```

## Execution result

```text
PASS: 8 active rows; 19 active refs resolve and are ancestors of 0769f3455b; exact IDs in linked headers
PASS: 109 relative links exist; 45 prior reports explicitly historical
PASS: tracked delta is catalogue Markdown only; git diff --check clean
```

No source suite was run in this pass.
