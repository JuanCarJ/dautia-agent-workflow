#!/usr/bin/env bash
set -euo pipefail

skill_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash -n "$skill_root/scripts/audit_workspace.sh"
python3 "$skill_root/tests/run_tests.py"
