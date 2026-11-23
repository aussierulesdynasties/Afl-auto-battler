# Ikon Park (Princes Park / Optus Oval), 1997-2005 bowl: measurements (in progress)

Legacy mode plays 242 matches here, 1990-2005. Facts and sources: [FACTS.md](FACTS.md). Imagery: Google Earth web
historical, captured headless with `tools/grounds/legacy/ge_history.js` (56 dates, 23 Mar 2000 to 30 Jan 2016).
Reference only: never committed, never in a texture. The measuring scripts are the Football Park ones
(`../football_park/measure/`: turf2, refine2, linereg, fourier) run with `CX=1112 CY=909 MPP=0.2948`.

## Measured so far (2026-11-23)

| What | Result | How |
| --- | --- | --- |
| Scale | 0.2948 m a pixel | the painted 50 m centre square, 14 Mar 2014 (the square sits 5.4 deg off the image axes) |
| Fence line (2009-2014) | polar Fourier curve, K = 10, **0.40 m rms** (546 of 569 points), 167.4 m along the goal line axis x 147.6 m across | turf edge traced on five dates (30 Jun 2009, 1 Feb 2010, 10 and 31 Jan 2014, 14 Mar 2014), each registered to 14 Mar 2014 on the painted lines; per 0.5 deg the median of the dates that see the edge (at least three); `measure/comb.py`, `measure/fence_fit.json` |
| How far the dates agree | single dates sit 0.4-0.9 m (median spread per 30 deg sector) from each other; one date's sector is off by up to 2.1 m where a stand shadow hides the edge | same traces |
| Goal lines | the 50 m arc apexes put the goal lines about 158.6 m apart, 4 m inside the fence at each end (by eye on the arcs, +-1 m) | 14 Mar 2014 |

Bearings are degrees counter-clockwise from image east round the field centre at pixel (1112, 909) of the 14 Mar 2014
capture; north is up in the captures.

## Not settled

- **Fence before 2006.** The 2000-2005 frames are soft and lack painted lines. Of 29 May 2002, 4 Mar 2004 and
  24 Jan 2005 only 4 Mar 2004 registers, and it comes out 6 % short in one axis, so it cannot confirm the 2009-2014
  fence to better than 2-3 m; by eye its turf edge follows the fitted curve. The two western stands came down after
  2005; the fitted fence is used for 1997-2005 until a period photo pins the west side.
- **1990-1996.** No aerial predates 2000; the east end before the Legends Stand (1995-97) comes from photos only.
- No published field size was found (see FACTS.md), so the fence has no published cross-check yet.
