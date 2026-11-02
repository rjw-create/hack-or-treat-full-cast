#!/usr/bin/env bash
# Verify command for this repo (Core role). Spends no credits: it only checks local files.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python}"
# --fast skips the ffmpeg work (placeholder stems and audio-check tests), the slow part under CPU load.
fast=0; [ "${1:-}" = "--fast" ] && fast=1

echo "== Interface check on the sample files"
"$PY" -m core.interface core/fixtures/sample

echo "== Interface check on the real adaptation"
"$PY" -m core.interface core/adaptation/script.json

if [ $fast -eq 0 ]; then
  echo "== Placeholder stems generate and still pass the interface check"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  "$PY" -m core.placeholders --out "$tmp/placeholder"
  "$PY" -m core.interface "$tmp/placeholder"
fi

echo "== Core pipeline tests (fake ElevenLabs client: no credits, keys or network)"
"$PY" -m unittest discover -s core/tests -t .

echo "== Proof eval tests"
if [ $fast -eq 1 ]; then
  "$PY" -m unittest $(grep -L "ffmpeg" evals/test_*.py | sed 's#/#.#; s#\.py$##')
else
  "$PY" -m unittest discover -s evals -t .
fi

echo "== Surface mixer tests (timing and filter graph only, no ffmpeg needed)"
"$PY" -m unittest web.test_mix

if [ $fast -eq 1 ]; then echo "check.sh --fast: passed (ffmpeg checks skipped; run without --fast before a PR)"; else echo "check.sh: all checks passed"; fi
