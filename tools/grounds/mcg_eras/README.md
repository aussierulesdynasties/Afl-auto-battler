# MCG of each era: measuring tools

See [docs/MCG_ERAS.md](../../../docs/MCG_ERAS.md) for the seasons and the plan. These tools measure the
old stands from Google Earth's dated aerials. The captures are reference only: they stay in the
project's private files (`/mnt/project-files/mcg-eras/private-imagery/`), never in the repo or a
shipped texture.

- `ge_history.js`: Google Earth web in headless Chromium (Playwright, swiftshader). Turns on Historical
  Imagery, steps back to the oldest date, then forward one date at a time and saves a straight-down
  capture of each (`node ge_history.js <dates forward> <steps back>`, env `R` = camera range in m,
  `W`/`H` viewport). At R=950 and a 2000x2000 viewport a pixel is 0.3019 m on the ground (read off
  Google Earth's own pointer coordinates at seven points, 2026-11-23); capture centre lat -37.81990,
  lon 144.98330.
- `arena_edge.py` + `arena_fit.py`: the arena's edge found along 720 rays from the field centre (the
  first sustained break from the turf's colour), then a robust ellipse fit; prints centre, axes and
  rms in metres.
- `polar2.py`: unwraps a capture round the field centre (x = bearing, y = distance), so roof and tier
  edges become curves that can be compared between dates.
- `crop.py`: a zoomed crop with a pixel grid, for reading points by eye.

Dates available at the MCG (Google Earth web, 2026-11-23): 23 Mar 2000, 15 Nov 2000, 18 Nov 2000,
19 Feb 2001, 20 Jun 2001, 4 Jul 2001, 29 Apr 2002, 11 Oct 2002, 16 Aug 2004, 21 Oct 2004,
12 Nov 2004, then 2006 on. Nothing between 1985 (Landsat) and 2000, and nothing in 2003 or 2005.

Heights from shadows (2026-11-23):

- `sun.py`: sun elevation from the date and a measured azimuth (`python3 sun.py <day of year> <azimuth>`).
- `regfix.py`: registers a capture by fitting March 2000's arena ellipse to its sunlit edge only.
- `shadow.py` (`F=<capture>`): radial brightness steps (roof edges, shadow edges); `tedge.py`: sustained
  shadow edge on the turf; `pview.py` / `pover.py`: polar strips with a labelled grid and traced points.
- `fwd.py`: draws the roof front's shadow on the turf for given heights and fits the heights to the
  traced shadow edge; `hsolve.py`: the simpler per-bearing version (only valid where the sun shines
  straight across the stand).
- `measure/`: traced edges, registered centres and the results (`heights_2026-11-23.json`).
