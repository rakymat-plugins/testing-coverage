#!/usr/bin/env bash
set -euo pipefail

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_source="$source_dir/skills/testing-coverage"
skill_dir="$HOME/.claude/skills/testing-coverage"
commands_dir="$HOME/.claude/commands"

if [ ! -d "$skill_source" ]; then
  echo "error: cannot find skills/testing-coverage next to this script." >&2
  echo "       Run install.sh from inside a clone of the repo." >&2
  exit 1
fi

# Replace rather than merge, so files removed upstream don't linger.
rm -rf "$skill_dir"
mkdir -p "$skill_dir"

for item in SKILL.md references templates scripts; do
  [ -e "$skill_source/$item" ] && cp -r "$skill_source/$item" "$skill_dir/"
done
rm -rf "$skill_dir/scripts/__pycache__"
echo "Installed skill to $skill_dir"

mkdir -p "$commands_dir"
for command in testing-assess.md testing-plan.md testing-implement.md; do
  cp "$source_dir/commands/$command" "$commands_dir/"
done
echo "Installed 3 commands to $commands_dir"

if command -v python3 >/dev/null 2>&1; then
  echo "Python found ($(command -v python3)) - the stack detector will work."
elif command -v python >/dev/null 2>&1; then
  echo "Python found ($(command -v python)) - the stack detector will work."
else
  echo "WARNING: no python3/python on PATH. The workflow still works;"
  echo "         stack detection falls back to manual inspection."
fi

cat <<'EOF'

Done. Run these in order, in any project:
  /testing-assess      decide which kinds of testing this project needs
  /testing-plan        write the plan + phased task list
  /testing-implement   build it, one layer at a time, green before moving on

...or just ask in plain language, e.g. 'what tests does this project need'.
EOF
