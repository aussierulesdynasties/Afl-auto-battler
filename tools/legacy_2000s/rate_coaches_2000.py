"""Rate each 2000 senior coach from his real senior record before 2000 (director 2026-11-13,
"Rate from records"), with the 1990 start's rules: tools/legacy_1990s/rate_coaches.py, run on
data/legacy/2000s/coaches_2000.csv, writing data/legacy/2000s/coach_ratings_2000.csv beside it
(Coaches._era_ratings reads coach_ratings_<start year>.csv next to the staff file).

    python tools/legacy_2000s/rate_coaches_2000.py            # fetch missing pages, write the CSV
    python tools/legacy_2000s/rate_coaches_2000.py --offline  # cache only
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "legacy_1990s"))
import rate_coaches as R  # noqa: E402

R.BEFORE = 2000
R.COACHES = ROOT / "data/legacy/2000s/coaches_2000.csv"
R.OUT = ROOT / "data/legacy/2000s/coach_ratings_2000.csv"
R.CACHE = ROOT / "data/cache/legacy_2000s/coaches"
# AFL Tables' page names where they differ from the name the club record uses.
R.PAGE_NAME = dict(R.PAGE_NAME, **{"Mark Williams": "Mark_Williams2"})

if __name__ == "__main__":
    R.main()
