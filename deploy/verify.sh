#!/usr/bin/env bash
# Structural checks use Python's standard library, matching the build toolchain.
set -euo pipefail
exec python3 "$(dirname "$0")/verify.py"
