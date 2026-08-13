#!/usr/bin/env bash
#
# Installer for the testing-coverage skill + its three slash commands.
#
# Works on macOS, Linux, WSL, and Windows (Git Bash / Cygwin).
#
#   ./install.sh              install for every project (~/.claude)
#   ./install.sh --local      install for this project only (./.claude)
#   ./install.sh --uninstall  remove a previous install
#   ./install.sh --help
#
set -euo pipefail

SKILL_NAME="testing-coverage"
COMMANDS=(testing-assess.md testing-plan.md testing-implement.md)
PAYLOAD=(SKILL.md references templates scripts)

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_source="$source_dir/skills/$SKILL_NAME"
command_source="$source_dir/commands"

scope="global"
mode="install"

for arg in "$@"; do
  case "$arg" in
    --local|--project) scope="local" ;;
    --global) scope="global" ;;
    --uninstall|--remove) mode="uninstall" ;;
    -h|--help)
      # Print the header comment block, stopping at the first non-comment line
      # so this stays correct if the header changes length.
      awk 'NR<3 {next} /^#/ {sub(/^# ?/, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
      exit 0
      ;;
    *)
      echo "error: unknown option '$arg' (try --help)" >&2
      exit 2
      ;;
  esac
done

if [ "$scope" = "local" ]; then
  base="$(pwd)/.claude"
  scope_label="this project ($(pwd))"
else
  if [ -z "${HOME:-}" ]; then
    echo "error: \$HOME is not set, so the global install target is unknown." >&2
    echo "       Set HOME, or run with --local to install into ./.claude" >&2
    exit 1
  fi
  base="$HOME/.claude"
  scope_label="every project ($HOME/.claude)"
fi

skill_dir="$base/skills/$SKILL_NAME"
commands_dir="$base/commands"

# --------------------------------------------------------------------------- #
# Uninstall
# --------------------------------------------------------------------------- #

if [ "$mode" = "uninstall" ]; then
  removed=0
  if [ -d "$skill_dir" ]; then
    rm -rf "$skill_dir"
    echo "Removed $skill_dir"
    removed=1
  fi
  for command in "${COMMANDS[@]}"; do
    if [ -f "$commands_dir/$command" ]; then
      rm -f "$commands_dir/$command"
      echo "Removed $commands_dir/$command"
      removed=1
    fi
  done
  if [ "$removed" -eq 0 ]; then
    echo "Nothing to remove under $base"
  else
    echo ""
    echo "Uninstalled. Restart Claude Code (or run /doctor) to drop it from the session."
  fi
  exit 0
fi

# --------------------------------------------------------------------------- #
# Preflight
# --------------------------------------------------------------------------- #

if [ ! -d "$skill_source" ]; then
  echo "error: cannot find skills/$SKILL_NAME next to this script." >&2
  echo "       Expected: $skill_source" >&2
  echo "       Run install.sh from inside a clone of the repo:" >&2
  echo "         git clone https://github.com/rakymat-plugins/testing-coverage.git" >&2
  echo "         cd testing-coverage && ./install.sh" >&2
  exit 1
fi

for item in "${PAYLOAD[@]}"; do
  if [ ! -e "$skill_source/$item" ]; then
    echo "error: incomplete clone - missing skills/$SKILL_NAME/$item" >&2
    exit 1
  fi
done

for command in "${COMMANDS[@]}"; do
  if [ ! -f "$command_source/$command" ]; then
    echo "error: incomplete clone - missing commands/$command" >&2
    exit 1
  fi
done

# --------------------------------------------------------------------------- #
# Install
# --------------------------------------------------------------------------- #

if [ -d "$skill_dir" ]; then
  echo "Updating existing install at $skill_dir"
fi

# Replace rather than merge, so files removed upstream don't linger.
rm -rf "$skill_dir"
mkdir -p "$skill_dir" "$commands_dir"

for item in "${PAYLOAD[@]}"; do
  cp -R "$skill_source/$item" "$skill_dir/"
done
rm -rf "$skill_dir/scripts/__pycache__"
chmod +x "$skill_dir/scripts/"*.py 2>/dev/null || true

for command in "${COMMANDS[@]}"; do
  cp "$command_source/$command" "$commands_dir/$command"
done

# --------------------------------------------------------------------------- #
# Verify what actually landed
# --------------------------------------------------------------------------- #

failed=0

check() {
  if [ ! -e "$1" ]; then
    echo "  MISSING: $1" >&2
    failed=1
  fi
}

check "$skill_dir/SKILL.md"
check "$skill_dir/scripts/detect_stack.py"
for reference in anti-patterns gates harness interview layers stack-map writing-tests; do
  check "$skill_dir/references/$reference.md"
done
for template in TESTING-STRATEGY TESTING-PLAN TESTING-TASKS EVIDENCE-LOG; do
  check "$skill_dir/templates/$template.md"
done
for command in "${COMMANDS[@]}"; do
  check "$commands_dir/$command"
done

if [ "$failed" -ne 0 ]; then
  echo "" >&2
  echo "error: install incomplete - see MISSING lines above." >&2
  exit 1
fi

reference_count=$(find "$skill_dir/references" -name '*.md' | wc -l | tr -d ' ')
template_count=$(find "$skill_dir/templates" -name '*.md' | wc -l | tr -d ' ')

echo "Installed skill    -> $skill_dir"
echo "                      SKILL.md, ${reference_count} references, ${template_count} templates, 1 script"
echo "Installed commands -> $commands_dir"
for command in "${COMMANDS[@]}"; do
  echo "                      /${command%.md}"
done
echo "Scope              -> $scope_label"

# --------------------------------------------------------------------------- #
# Optional dependency
# --------------------------------------------------------------------------- #

python_bin=""
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
      python_bin="$candidate"
      break
    fi
  fi
done

echo ""
if [ -n "$python_bin" ]; then
  version="$("$python_bin" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null || echo "?")"
  if "$python_bin" "$skill_dir/scripts/detect_stack.py" "$skill_dir" >/dev/null 2>&1; then
    echo "Stack detector     -> OK ($python_bin $version, smoke-tested)"
  else
    echo "Stack detector     -> $python_bin $version found, but the smoke test failed."
    echo "                      The workflow still runs; detection falls back to manual inspection."
  fi
else
  echo "Stack detector     -> no Python 3.8+ on PATH (optional)."
  echo "                      The workflow still runs; detection falls back to manual inspection."
fi

cat <<'EOF'

Done. Run these in order, in any project:

  /testing-assess      decide which kinds of testing this project needs
  /testing-plan        write the plan + phased task list
  /testing-implement   build it, one layer at a time, green before moving on

Plain language works too, e.g. "what tests does this project need".
If the commands don't appear yet, restart Claude Code.
EOF
