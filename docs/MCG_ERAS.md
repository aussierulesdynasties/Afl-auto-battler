# The MCG of each era

The director chose (decision card, 2026-11-22) to build the MCG as it stood in each season, for
Legacy matches played there before 2006 and for the trailer's decade wipe
([3D_TRAILER_PLAN.md](3D_TRAILER_PLAN.md), shot 21). Today's model (2006 on) is the reference ground
([MCG_STANDARD.md](MCG_STANDARD.md)); each older MCG is built to the same standard. Looks only:
nothing here reaches the match sim.

## The seasons and what stood

Legacy mode starts in 1990. The MCG changed twice in that time, and each rebuild was done in stages
around the football, so some seasons were played beside a building site.

| Seasons | South side | North side (west to east) | Screens | Model |
| --- | --- | --- | --- | --- |
| 1990 | Southern Stand (1937) | Ponsford Stand (1968), Members' Pavilion (1928), Olympic Stand (1956) | one, on the Ponsford Stand | `mcg_1990` |
| 1991 | Southern Stand coming down, Great Southern Stand going up | as 1990 | as 1990 | `mcg_1991` |
| 1992-2002 | Great Southern Stand (1992) | as 1990 | Ponsford Stand; a second on the Olympic Stand from 1994 | `mcg_1992` |
| 2003 | Great Southern Stand | new Ponsford Stand rising; Members' Pavilion and Olympic Stand still standing | Olympic Stand | `mcg_2003` |
| 2004 | Great Southern Stand | new Ponsford Stand open; Members' Pavilion gone (site); Olympic Stand's east half only | Olympic Stand, then the new Ponsford Stand from April | `mcg_2004` |
| 2005 | Great Southern Stand | new Ponsford Stand; new Members' rising; Olympic Stand gone (site) | new Ponsford Stand | `mcg_2005` |
| 2006 on | Great Southern Stand (Shane Warne Stand from 2022) | today's northern stand | today's two boards (late 2013 on; smaller boards in the same places 2006-2013) | `mcg` (today's) |

The light towers stand in every season: six towers finished in December 1984, about 75 m with the
head frames 10 m higher, angled in at 15 degrees (MCG, Light Towers). They are the same towers
today's model already has, which makes them fixed points for measuring old photos.

### The dates behind the table

- Southern Stand opened at the end of 1936, "spanned almost half of the field's circumference"
  (Wikipedia, MCG). Concrete cancer found in 1988.
- Great Southern Stand: "staged demolition of the old stand", "completed within 13 months", in time
  for the 1992 Cricket World Cup; 324 m long and 45 m high, a seven-level core cantilevering four
  tiers, a steel cantilevered roof (John Holland). The 1991 Grand Final went to Waverley Park because
  the building work cut the MCG's capacity (Wikipedia, MCG; MCG, Grandstands).
- Western Stand built 1967-68, renamed the W.H. Ponsford Stand in 1986. Its Level 4 carried the 1982
  colour video screen, which caught fire on 27 August 1999 and was replaced in 2000. A second screen
  went on Level 4 of the Olympic Stand in 1994 (Wikipedia, MCG).
- Olympic (Northern) Stand built 1955-56 for the Olympics; corporate suites from 1984 (MCG,
  Grandstands).
- Members' Pavilion completed 1928 (MCG, Grandstands).
- Northern redevelopment: Ponsford Stand demolition began September 2002, after the Grand Final, "in
  five stages" (Austadiums, 25 April 2006; 2004 news). February 2004: Members' Pavilion "completely
  torn down", demolition of the western half of the Olympic Stand begun, "the second part to be torn
  down after this year's AFL Grand Final"; MCC members in the new Ponsford Stand for 2004; a second
  big screen in the new Ponsford Stand in April 2004 (Austadiums, 11 February 2004). Football
  returned to the finished ground on Anzac Day 2006 after the Commonwealth Games (Austadiums, April
  2006).

## References and what each may be used for

Measuring from imagery is allowed; raw imagery is never committed or baked into shipped textures
([MCG_STANDARD.md](MCG_STANDARD.md), "Where shipped data may come from").

| Source | What it shows | Use |
| --- | --- | --- |
| Google Earth historical aerials: 23 Mar 2000, 15 and 18 Nov 2000, 19 Feb 2001, 20 Jun 2001, 4 Jul 2001, 29 Apr 2002, 11 Oct 2002, 16 Aug 2004, 21 Oct 2004 (and more being read) | straight down: the Great Southern Stand and the old Ponsford, Members' and Olympic stands; the 2002-2004 building sites | plan shapes, roof outlines, tier edges, shadow lengths for heights; registered on the Great Southern Stand and light towers, which have not moved |
| MCC Museum images on Google Arts & Culture (aerials 1936, 1956, 1961, 1985 at night) | the Southern Stand and northern stands from the air | heights and profiles by solving each photo's camera on the light towers (1985) or the northern stands' measured plan |
| Wikimedia Commons (free licences): MCG99 (1998), MCG 2004 Panorama (public domain), New Ponsford Stand Construction (2003), renovations August 2005 | ground-level views of each era | facades, tiers, roofs, colours |
| Published figures (above) | lengths, heights, tiers, dates | checks on every measurement |

## Method

1. Register each historical aerial to today's model: the Great Southern Stand's roof edge and the
   six light-tower bases have not moved since 1992, so each aerial gets a best-fit scale, rotation
   and offset, with the fit error in metres.
2. Trace each old stand's plan (back wall, roof edge, tier edges, front wall) as smooth fitted curves
   in the model's frame; report the trace error in metres.
3. Heights from the oblique photos, by solving each photo's camera against points already fixed in
   3D (light towers, the Great Southern Stand, the measured northern stands), and from shadow lengths
   in the dated aerials (sun position from the date and time).
4. Build each stand as its own part, so a season's MCG is a set of parts: today's model cut into
   its Great Southern Stand and its northern stand, plus each old stand and each building site.
5. QA each era from the same cameras as its references before anyone sees it.

## Limits, stated up front

- **No overhead photo of the old Southern Stand.** Google Earth's oldest sharp aerial of the MCG is
  March 2000, eight years after it came down. It is measured from the oblique MCC Museum aerials and
  any free-licence photos, solved against the light towers and the northern stands, so its errors
  will be larger than the other stands'. They will be reported in metres, not hidden.
- **The 1991 building site has few references.** The MCC Museum's demolition photos (c1990-91) sit
  behind a bot check the cloud cannot pass. If no usable view is found, 1991 is reported as not yet
  buildable rather than drawn from guesswork.
- **Wikimedia Commons is rate-limiting the cloud** (2026-11-23); its photos are fetched when it
  allows.

## Status

- 2026-11-23: eras settled from published history. Every dated Google Earth aerial of the MCG
  captured (11, March 2000 to November 2004; none in 2003 or 2005, so those seasons rely on
  photos). Captures pinned to map coordinates at 0.3019 m a pixel from Google Earth's own pointer
  readout. Arena edge fitted in the three sharpest (23 Mar 2000: rms 0.46 m; 29 Apr 2002: 0.64 m;
  15 Nov 2000: 1.14 m); the others are too soft or shadowed for a clean fit. Roof edges of the old
  stands shift between dates by up to about 13 m (each flight leaned differently), so plan
  positions and heights are solved together from several dates, not traced from one. Tools in
  `tools/grounds/mcg_eras/`.
- 2026-11-23, later: heights from shadows. The sun in each aerial is fixed from a light tower's
  shadow (direction), with the elevation from the date; in March 2000 the tower's head shadow gives
  the same elevation to 0.2 degrees. Roof fronts of the old northern stands traced from March 2000
  (Ponsford about 104-108 m from the field centre, Members' a curve from 101 to 93 m, Olympic 116-123
  m). Results (`tools/grounds/mcg_eras/measure/heights_2026-11-23.json`):
  - Olympic Stand roof front: 24-25 m above the turf from 20 June 2001, 21-23 m from 4 July 2001
    (fit rms 3.5 m). The two dates disagree by about 2.5 m; not settled yet.
  - Ponsford Stand roof back: about 26 m (25-28) above the ground west of it, from its shadow in
    March 2000 (fit rms 1.5 m); that ground is near plaza level, so about 30 m above the turf.
  - Members' Pavilion: not measurable from these shadows (they fall on the west seats); needs photos.
  - Check on today's model: the Great Southern Stand's roof front casts its March 2000 shadow as if
    it were 35.6-36.6 m above the turf (fit rms 0.2 m). Today's model has it 35.7 m above the turf
    (31.5 m above its plaza datum, turf at -4.2 m): it agrees. Google Earth's 3D readout across the
    east stand agrees too (turf 8 m, roof 42-46 m above sea level).
- 2026-11-23, today's model checked against Google Earth's 3D heights (pointer readout, 1,045 points
  every 10 degrees, then 1,008 points at 1 m steps every 5 degrees across the roof's back edge;
  `tools/grounds/mcg_eras/measure/ge3d_*.json`). Roof heights agree within Google Earth's 1 m readout:
  Great Southern Stand 36 m above the turf (model 35.4-35.7), northern stand 42-43 m (model 42.7-43.7).
  The Great Southern Stand's roof back edge was too far out: by 1.6-4.4 m at 95-115 degrees and up
  to 7 m at 125-140 degrees (Google Earth shows the 36 m roof ending there, with a 24-30 m deck behind
  it). `roof_outer` corrected from 65 to 222 degrees (each point within about 1.5 m). Bearings on a
  truss line are left out (the masts read as roof). A second sweep (2.5 degrees, 2.5 m steps) over the
  northern stand's ends found 46 m tops at 55-67.5 and 235-247.5 degrees, front edge 107-111 m and
  back edge about 125-127 m from the centre. These were first read as raised end roofs; they are the
  two video screens (46 m above the turf is the screen boxes' top, and Google Earth shows no roof in
  front of them). The raised-roof change is withdrawn. The screen boxes themselves sit wrong: the
  east box ended at 65.5 degrees where Google Earth's runs to about 69, and both boxes reached 134 m
  where the top ends at about 127. Remeasured at 0.5 degree and 2.5 m steps (495 points,
  `ge3d_screens.json`): east screen 54.25-69 degrees, west 234.75-249.75 (each end to about 0.25
  degrees, 0.5-1 m at that radius); front 110.5 m (east) and 109 m (west) from the centre; flat top
  46 m above the turf out to 127 m, then a clad back sloping down to about 30 m by 131.5 m (to about
  1-1.5 m). Google Earth shows no roof in front of either screen. The roof height now steps at the
  screens' ends (`roof_steps`) with vertical end walls, not a ramp hidden in the old box: northern
  stand 38.9 m above the plaza (43 m above the turf) beside the east screen's north end and 38.3 m
  beside the west screen's north end, Great Southern Stand 31.2-31.5 m. Not yet measured: what sits
  under each screen's sloped back (the model leaves the box's underside open where the stand's back
  wall stops short of it, at the west screen).
- 2026-11-23, the rear of the Great Southern Stand against Google Earth 3D (1,960 points,
  `ge3d_gss_rear.json`). The "gaps" the PC flagged were places where the model dropped to the plaza
  behind the roof or stuck out where Google Earth has nothing. Stair and balcony blocks at 158-168 and
  198-208 degrees reached 132-135 m from the centre where the real structure ends at 126-129 m, at
  the wrong heights (Google Earth: 23 m balconies and 10-11 m podiums above the turf); they are
  re-placed. The plant deck at 131-149 degrees is 29 m above the turf out to 131 m (was 31 m to
  128.5 m). From 210 to 228 degrees a lower outer band of roof, 31-34 m above the turf, runs past the
  36 m roof's back edge out to 126-128 m; the model had nothing there (`roof_skirt`). The outer edge
  of everything behind the roof now agrees with Google Earth to a median of 1.35 m (mean 1.8 m, was
  2.35 m and 3.3 m) over 86 bearings. The worst remaining misses are block edges that fall between
  the 1 degree samples, the light tower at 182 degrees and the stair towers at 118-125 degrees (up to
  4-8 m, sparse data there).
