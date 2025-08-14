#!/usr/bin/env bash
set -euo pipefail

deny='-name node_modules -o -name .git -o -name .venv -o -name venv -o -name dist -o -name build -o -name .next'

OUT=PROJECT_SUMMARY.md
echo "# Project Summary" > "$OUT"
echo -e "\n## Git" >> "$OUT"
echo "Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'n/a')" >> "$OUT"
echo -e "\nLatest commits:" >> "$OUT"; (git log --oneline -n 8 || true) >> "$OUT"

echo -e "\n## Structure (depth 2)" >> "$OUT"
find . -maxdepth 2 -type d \( $deny \) -prune -o -print >> "$OUT"

echo -e "\n## Key files" >> "$OUT"
ls -1 README* LICENSE* CONTRIBUTING* DEPLOYMENT.md IMPLEMENTATION_* STRATEGIC_VISION.md AUTONOMOUS_* 2>/dev/null >> "$OUT" || true

echo -e "\n## Manifests detected" >> "$OUT"
for f in requirements.txt pyproject.toml package.json go.mod Dockerfile docker-compose.* firestore.rules firestore.indexes.json firebase.json; do
  [ -f "$f" ] && echo "- $f" >> "$OUT"
done

echo -e "\n## Python entrypoints guess" >> "$OUT"
grep -R --line-number -E 'if __name__ == .__main__.' -n -- *.py **/*.py 2>/dev/null | sed 's|^| - |' >> "$OUT" || true

echo -e "\n## Tests present?" >> "$OUT"
(ls -R | grep -iE '(^|/)(test|tests)__?' || echo "No obvious tests") >> "$OUT"

# Agents
AS=AGENTS_SUMMARY.md
echo "# Agents Summary" > "$AS"
find agents -type f -maxdepth 3 -print 2>/dev/null | sort >> "$AS"
echo -e "\n---\n### First lines of role prompts\n" >> "$AS"
for f in $(find agents -type f -maxdepth 3 -name '*.md' 2>/dev/null | sort); do
  echo -e "\n## $f\n" >> "$AS"
  head -n 40 "$f" >> "$AS"
done

# Orchestration
OS=ORCHESTRATION_SUMMARY.md
echo "# Orchestration Summary" > "$OS"
find orchestration -type f -maxdepth 4 -print 2>/dev/null | sort >> "$OS"
echo -e "\n---\n### Excerpts\n" >> "$OS"
for f in $(find orchestration -type f -maxdepth 3 -name '*.md' -o -name '*.py' 2>/dev/null | sort); do
  echo -e "\n## $f\n" >> "$OS"
  head -n 80 "$f" >> "$OS"
done

# Run/Tests hints
echo -e "\n## How to run (guessed)" >> "$OUT"
if [ -f requirements.txt ]; then
  echo "- Python: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >> "$OUT"
  echo "- Run agents: try python start_autonomous_pipeline.py or python main.py" >> "$OUT"
  echo "- Tests: pytest -q (if tests present)" >> "$OUT"
fi
if [ -f firebase.json ]; then
  echo "- Firebase: npm i -g firebase-tools && firebase emulators:start" >> "$OUT"
fi

echo -e "\n---\nGenerated $(date -Is)" >> "$OUT"
echo "Wrote $OUT, $AS, $OS"
