"""Rate each 2020 senior coach from his real senior record before 2020 (director 2026-11-13, "Rate from records").

The 1990 rater (rate_coaches.py) with 2020's files: reads data/legacy/2020s/coaches_2020.csv and one
AFL Tables coach page per name (cached under data/cache/legacy_2020s/coaches/, fetched once when
missing), writes data/legacy/2020s/coach_ratings_2020.csv. Same scale and rules as 1990.

    python tools/legacy_1990s/rate_coaches_2020.py            # fetch missing pages, write the CSV
    python tools/legacy_1990s/rate_coaches_2020.py --offline  # cache only
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rate_coaches as R  # noqa: E402

R.BEFORE = 2020
R.COACHES = R.ROOT / "data/legacy/2020s/coaches_2020.csv"
R.OUT = R.ROOT / "data/legacy/2020s/coach_ratings_2020.csv"
R.CACHE = R.ROOT / "data/cache/legacy_2020s/coaches"
R.PAGE_NAME = {}

if __name__ == "__main__":
    R.main()
