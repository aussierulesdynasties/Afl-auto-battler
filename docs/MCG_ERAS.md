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

- 2026-11-23: eras settled from published history; Google Earth historical aerials found for
  2000-2004; capture of every dated aerial under way.
