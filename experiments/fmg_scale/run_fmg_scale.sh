#!/usr/bin/env bash
# Run the complete FMG scale/structure measurement against the canonical
# exports committed under examples/, writing one timestamped raw-results file.
#
# Invoke from anywhere inside the Worldloom repository with:
#   bash experiments/fmg_scale/run_fmg_scale.sh

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "ERROR: run this from inside the Worldloom git repository." >&2
  exit 1
}
cd "$ROOT"

BRANCH="$(git branch --show-current)"
EXPECTED_BRANCH="experiments/fmg-scale-measurement"
if [[ "$BRANCH" != "$EXPECTED_BRANCH" ]]; then
  echo "ERROR: expected branch '$EXPECTED_BRANCH', found '$BRANCH'." >&2
  echo "Checkout the experiment branch before running measurements." >&2
  exit 1
fi

PYTHON="${PYTHON:-python3}"
VENV="$ROOT/.venv"

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Creating Python virtual environment at $VENV"
  "$PYTHON" -m venv "$VENV"
fi

# The project has no runtime dependencies. Put src/ directly on the
# interpreter path so H8 uses the checked-out WorldState implementation
# without requiring a package download or editable install.
source "$VENV/bin/activate"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

INPUTS=(
  "$ROOT/examples/Thimaland Full 2026-10-02-14-17.json"
  "$ROOT/examples/Viveria Full 2026-10-02-11-31.json"
  "$ROOT/examples/Pithigy Full 2026-10-02-11-35.json"
)

for input in "${INPUTS[@]}"; do
  if [[ ! -f "$input" ]]; then
    echo "ERROR: missing FMG export: $input" >&2
    exit 1
  fi
done

RESULT_DIR="$ROOT/experiments/fmg_scale/results"
mkdir -p "$RESULT_DIR"
TIMESTAMP="$(date -u '+%Y-%m-%dT%H-%M-%SZ')"
OUTPUT="$RESULT_DIR/fmg_scale_$TIMESTAMP.json"

echo "Running FMG measurements on the three canonical examples..."
python "$ROOT/experiments/fmg_scale/measure_fmg.py" \
  "${INPUTS[@]}" \
  --output "$OUTPUT"

echo
echo "Raw results written to:"
echo "  $OUTPUT"
echo
echo "To stage exactly this result:"
echo "  git add -- '$OUTPUT'"
echo
echo "No FMG input files are copied or modified by this script."
