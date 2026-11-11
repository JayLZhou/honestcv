#!/usr/bin/env bash
# End-to-end demo: a fixture repository in, a verified resume out.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
root="$(dirname "$here")"
export PYTHONPATH="$root/src:${PYTHONPATH:-}"
hcv() { python3 -m honestcv "$@"; }

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cd "$work"

echo "== building a fixture repository =="
python3 "$here/make_demo_repo.py" "$work/orders" >/dev/null

echo "== 1. how legible is that history? =="
hcv --lang en audit "$work/orders" --author demo@example.com | head -20

echo "== 2. mine it =="
hcv --lang en init --name "Demo Candidate" --email demo@example.com
hcv --lang en mine "$work/orders" --author demo@example.com

echo "== 3. match against a JD =="
hcv --lang en match --jd "$here/jd-backend-en.txt" | head -30

echo "== 4. resume, letter, gap plans, practice =="
hcv --lang en resume   --jd "$here/jd-backend-en.txt" -o resume.md
hcv --lang en letter   --jd "$here/jd-backend-en.txt" -o letter.md
hcv --lang en plan     --jd "$here/jd-backend-en.txt" -o plan.md
hcv --lang en practice --jd "$here/jd-backend-en.txt" -o practice.md

echo "== 5. tamper with the resume, and watch verify catch it =="
printf -- '- Led a team of 12 engineers and cut latency by 90%%\n' >> resume.md
if hcv --lang en verify resume.md; then
  echo "FAIL: the verifier did not catch an invented claim" >&2
  exit 1
fi
echo
echo "The invented line was rejected. That is the whole product."
