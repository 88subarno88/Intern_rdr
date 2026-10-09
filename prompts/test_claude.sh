#!/usr/bin/env bash
# Runs the exact Claude command n8n will use, on sample_items.json.
# Expect three scored items; the fake promo one should be "skip" with a low score.
set -euo pipefail
P="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
cd "$WORK"

cat "$P/sample_items.json" | claude -p --model haiku --tools "" --strict-mcp-config \
  --no-session-persistence --output-format json \
  --system-prompt-file "$P/score_prompt.md" \
  --json-schema "$(cat "$P/score_schema.json")" \
  | python3 -c 'import sys, json; print(json.dumps(json.load(sys.stdin)["structured_output"], indent=2))'
