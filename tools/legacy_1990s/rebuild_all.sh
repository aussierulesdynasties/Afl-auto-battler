#!/usr/bin/env bash
# Rebuild every Legacy start and the rollovers from the committed data (no
# web cache: the staff files are kept). Run from the repo root.
set -euo pipefail
python tools/legacy_1990s/build_start.py --report
python tools/legacy_2000s/build_start_2000.py --no-staff --report
python tools/legacy_2010s/build_start.py --report
python tools/legacy_1990s/build_start_2020.py --no-staff --report
python tools/legacy_1990s/build_rollovers.py
