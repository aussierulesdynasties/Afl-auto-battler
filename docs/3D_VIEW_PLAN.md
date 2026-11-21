# The 3D match view: the plan

_Director, 2026-11-16 (Director Bible 2.78). Every session working on the 3D view works from this file.
A step starts only when the steps it waits on are done. Work that is not on this plan does not start._

> "before we work out animations for every move. We need to prove the concept that the visual sim can
> behave like real football and adjust naturally to the way we coach the team"
>
> "i dont think we should make any more art before we settle on a visual direction and make a plan on
> how to address each asset and animation we need ... we are creating animations, but we havent even
> settled on what body we are going to animate"

## Why this plan exists

From 2026-11-14 to 11-16 the 3D oval grew one detail at a time: boots, hair, turf, a clip library of
123 retargeted moves, and a run of one-incident fixes to MatchDirector (free takers, loose balls,
leads, spills). Of the 43 clips baked into the game, only run, stand, carry and six tackle pairs play
in a match. Meanwhile nobody had checked the two things that matter first: does the team move like
real football, and does it change when the coach changes the plan? The body every clip is made for
was never chosen either (our MPFB average body, with a MetaHuman body mocked beside it).

## The freeze (from 2026-11-16)

- **No new art.** No clips, retargets, bakes, models, hair, boots, turf, stadium or crowd work, and no
  Tripo spend for the 3D view, until steps 2 and 3 are done, except the prototypes step 2's questions
  need. 3d view 2's clip-making from his Rokoko
  takes is paused (he chose "Pause it").
- **No one-incident choreography patches.** A fault seen in a film goes on the gap list (step 1) and is
  fixed as part of the system it belongs to.
- What exists stays in the game as a placeholder: the MPFB body, the mocap run, stand and carry loops
  (#1689, approved), the tackle pairs, kits, hair, boots and turf. None of it is the settled look.

## Step 1. The football proof (code only; runs beside step 2)

The 3D oval, on the placeholder body with run, stand, carry and tackles only, must play like real
football and answer the coach.

1. **What real footy looks like, in numbers.** For each phase (centre bounce, stoppage around the
   ground, kick-in, their ball in our half, our ball going forward, set shot): where the 36 men stand,
   each team's length and width, men behind the ball, spacing to the nearest opponent, how far and how
   often the ball is kicked and switched. Then, for every call (the four plans, Stack, Flood, Push,
   Throw numbers at it, tags and switches): what a coach would see change. Sources: his footage and
   published AFL tracking studies, each number with its source. He checked the spec on 2026-11-17: real
   footy is the target everywhere, and a number passes within 10% of the real one (rule 2.86).
2. **Measure.** A harness in the style of `tools/balance.sh` logs every man's position over many
   matches and marks each number IN, NEAR or OUT of the spec. Paired runs (same seed, call on and
   off) give each call's change with its standard error. Where the sim's own events are not footy
   (where the ball is won, kick lengths), that is a MatchSim change and goes through the balance screen.
3. **The gap list.** Every OUT number and every fault seen in a film, each named to the system that
   owns it (a phase's shape, a call's shape, leads, the press, stoppage set-ups, the sim's events).
4. **Fix the systems.** One shape model per phase and call, not a patch per incident.
5. **The proof.** Paired films of each call (same match, call on and off) from a high whole-ground
   camera and the broadcast camera, at game speed. It passes when the numbers are IN and he watches
   and says it reads as footy and he can see his coaching (he chose "Numbers and your watch").

### The gap list (row 201, 2026-11-16)

Measured with `tools/balance.sh shape` (README: tools/balance), 153 matches per arm on GitHub (run 43859090677; the five burst calls re-run in run 43869053009, held all match). Real numbers and their sources
are in `tools/balance/afl_shape_rates.json`; the spec page puts them to him. Each line names the system that owns
it; step 4 fixes the system, not the incident.

Lengths and widths are metres, end to end of the 18; "in the ball's zone" counts both sides in the ball's quarter
of the ground. Calls are paired runs (same seed, call on and off), the change on the side that made the call.

| # | Gap | Real | Oval now | Owner |
|---|---|---|---|---|
| 1 | The team is too long in open play | 74-94 m with the ball, 75-87 m without, 65-97 m loose (Alexander 2019) | 107-127 m everywhere | Phase shape: `MatchDirector._structure_spot` moves each line only 15-78% of the ball's travel, so the lines stay spread |
| 2 | The team does not follow the ball to either end | team centre 29-33 m past halfway when attacking in the forward 50; 43-47 m back defending in the back 50 | 15 m; 18 m | Phase shape (`_structure_spot`, as 1) |
| 3 | Too few men near the ball | 15.5-19.5 of the 36 in the ball's quarter (Alexander 2021) | 11.6-15.4 | Phase shape (as 1) |
| 4 | No squeeze on a loose ball | 36-47 m wide (Alexander 2019) | 62-67 m. Held 2026-11-21, no change: the reference cannot be the widest pair (see below); length, area and team centre on a loose ball are IN or NEAR, and the 10th-90th percentile width (37-41 m) sits on the paper's figure | A loose-ball shape: none exists; loose balls use the open-play spots |
| 5 | Stoppages around the ground are thin | 23 players in the ball's quarter in either 50, 17 in midfield (Alexander 2021) | 13.4 | Stoppage set-ups (`_centre_spot`, `_centre_setup`, the ball-up and throw-in spots) |
| 6 | Kicks are short and gain little ground | 25.0 m average, ±11.8 (Spencer 2019); 25-30 m gained | 20.0 m, ±11.6; 11.2 m gained | MatchSim kick events (balance-gated) |
| 7 | Too many kicks | 213 a team-game (Wheelo 2026) | 309 | MatchSim event count (balance-gated) |
| 8 | Calls do not change how the side kicks | Attacking: no switch; Controlled and Slow it down: shorter, across and back (rule 2.45) | Attacking: switches stay 6%; Controlled: kicks 0.5 m longer; Slow it down: 0.2 m longer, 3 points fewer backward | MatchSim kick choice by plan (balance-gated) |
| 9 | A tagger does not shadow his man | a tag is permanent and goes where his man goes (2.44, 2.58); no published distance | 21.7 m apart on average, within 5 m 15.6% of the time (off: 27.0 m, 6.9%). Re-measured on main 2026-11-20 (153 matches): 9.0 m, 45%; only while his side defends, the same. Now 8.4 m, 49%: a tagger keeps up at a run | Man-on-man pull in `_structure_spot`: only inside 35 m, at most 85% of the way |
| 10 | A switched defender drifts off his forward | everyone has an opponent (2.44) | 25.3 m apart, within 5 m 15.7% (off: 28.9 m, 13.5%). Re-measured on main 2026-11-20: 17.7 m, 25%. Explained 2026-11-21: while his side defends and the match-up is on, 10.5 m and 48% within 5 m; the rest of the 17 m is the ball in his side's hands and the forward rotated out of the forward line (handed over until he is back, by design) | Man-on-man pull (as 9) |
| 11 | Fumble then gather: the gatherer runs 3.9 m past and the ball lies alone ~0.7 s (seed 31, FRE v STK) | the nearest man scoops it | as stated (row 197 inbox). Fixed on main by #1838: over 4 matches the gatherer is 0.6 m from the ball when he takes it and it never lies alone over 0.5 s | Loose-ball pickup; the WIP on `claude/oval3d-loose-ball-wip` fails 8 match_visual checks |
| 12 | No clean gather (down for it, picks it up) in the shipped game | | the first man knocks it on toward MatchSim's winner. Fixed by #1838 (as 11) | Loose-ball pickup (as 11) |
| 13 | A dead stop at the fence: 4-5 m/s to 1.1 m/s in one step, twice in four seeds | | Fixed 2026-11-20: he pulls up within his braking limit and slides along the fence (`_test_fence_pull_up`) | MatchMotion fence clamp |
| 14 | Throw numbers at it does not put more men at the ball; it moves the team forward like Push | more of our men around the ball wherever it is (the call's own words) | men within 20 m of the ball +0.9 at most (+0.1 at stoppages); team centre 7-19 m further forward, as Push's 8-14 m. Fixed 2026-11-21: the midfield and half-back line ring the ball with it and without it, +1.8 to +3.4 men within 20 m in open play and +2.6 at stoppages; the team centre moves 3-5 m | Call shape: `_structure_spot` lifts the lines forward for Surge and Push alike (`_surge_ref`); no pull toward the ball |

What the calls already do (no gap): Attacking narrows the side 26-34 m in attack (about 39%; rule 2.45 asks about
45%); Controlled widens it 13-24 m and shortens it 35-44 m; Defensive shortens it 29 m in midfield; Win Contest
narrows it 18-25 m and puts 1.9 more men within 10 m of a stoppage. Flood pulls the team 10-13 m back with 2.2 more men behind the ball in our half;
Push moves it 8-14 m forward with 2.5-2.9 fewer behind; Slow it down spreads it 16-27 m wider; Stack sets the
lines 51 m shorter at the centre bounce (still 6-6-6, no extra men in the square). Not yet measured: what each position does
(marks, tackles, kicks per role), which the harness does not count.

**Re-measured on main, 2026-11-20** (24 matches, local): gaps 1-3 are mostly closed since the list was written: the
team's length is IN in 10 of 12 open-play zones, its centre IN at both ends, and the men in the ball's quarter IN.
Still OUT: the team centre in the two midfield zones (8-11 m short of real), every hull area (35-40% under), and the
loose-ball width (gap 4, 52-63 m against 36-47 m). The harness now splits stoppages by zone (gap 5): 20.9 men in the
ball's quarter at a stoppage in either 50 (real 23, IN) and 19.6 in midfield (real 17, NEAR). The paper's loose-ball
width and area do not fit together (an area of 4,440 m2 cannot sit inside 89 by 40 m), so gap 4's reference is being
checked against the paper before the sim is pushed to it.

**Gap 4 assumption, 2026-11-21** (nobody on the project has the paper, so this is a reading, not a check): the loose-ball
widths read off Alexander 2019's Fig 2 cannot be the widest pair across, because in every zone the same figure's area
is larger than its length times that width allows (a loose ball in their half: 4,785-5,120 m2 inside at most 97 by 44 m).
The likelier reading is a narrower spread measure; the sim's 10th-90th percentile width on a loose ball (36.7, 37.4,
38.3, 40.8 m by zone) sits inside or next to the paper's 35.6-47.1 m. Squeezing the widest pair to 36-47 m would push the
hull areas, already under real, further away, so the loose-ball shape is left as it is until someone can read the paper.

## Step 2. The world and the look (runs beside step 1; before anything that draws the game)

> "we should also first make sure our stadium art is sorted, and figure out how to do crowds cheaply
> figure out shaders, lighting, post-processing, weather systems, times of day etc before we start
> drawing the actual game"

The world the game is drawn in is settled first; the players are drawn into it after. Each part is
researched, prototyped as options on the 3D oval, put to him as captures from the game's cameras (one
question at a time), and costed on the phone once, when the foundation is together. Today's world is a
placeholder: one raked ring of stands with a shader-painted crowd, a flat background colour, no sky,
one sun and filmic tonemapping; the turf of #1658 already varies with weather and time of day.

**2a. The rendering foundation.**
1. **Shaders.** One material model for everything on screen (turf, stands, crowd, players, kit),
   so the whole picture sits in the same light.
2. **Lighting.** Sun and sky, ambient and bounce light, shadows (their quality and phone cost),
   stadium lights at night.
3. **Post-processing.** Tonemapping and exposure, colour grade, anti-aliasing, ambient occlusion,
   bloom, haze: what each adds against what it costs on the phone.
4. **Weather and time of day as one system.** Day, twilight and night; dry, overcast, rain and a wet
   ground; one setting drives the sky, light, turf, post-processing and crowd. (How weather affects
   play stays a separate, open question in the design bible; this is its look only.)

**2b. The stadium.** What the grounds are (real AFL venues or one stadium for every match), their
stands, roofs, light towers, scoreboards, fences, signage and goal-end details, at the detail the
cameras actually see. The stadium we have "is ok, but it was just thrown together, it wasnt borne from a
plan" (2026-11-16): the plan first sets what a stadium needs, then today's is assessed against it,
part by part (kept, reworked or replaced). No ground's look is approved yet (director, 2026-11-20): a
finished ground is flown through by the director in the ground inspector (`tools/inspect/README.md`:
any model, in first person, very fast), he writes its fault list, the faults are fixed, then he approves it.

**2c. The crowd, cheaply.** Methods compared on looks and phone cost before any is chosen: shader-
painted seats (today), instanced cards of baked figures (impostors), animated low-poly instances, and
a mix by distance. Cheer squads, banners and reactions to goals are part of the choice. Chosen 2026-11-17: a mix, 3D people within 55 m of the camera and cards beyond (rule 2.92).

**2d. The players' look.** After 2a: the world's light decides how a body reads.
1. **The body.** Our MPFB average body, the MetaHuman body, or another source; how many builds
   (heights, frames); how heads and faces vary. Shown in a match, from the broadcast camera and close.
2. **The look.** How realistic: skin, kit cloth, boots and hair detail at the distances the game is seen.

**2e. The cameras.** Which views a match uses (broadcast wing, high whole ground, behind the goals,
close-ups at a stoppage or a set shot).

The answers are recorded in the Director Bible and summarised here.

**Answers so far.**
- 2a lighting, daylight (rule 2.80): sky light for every match (ambient and reflections from a sky
  with the stands round its foot and the grass below); late-afternoon games add a low sun and the
  stands' shade across the ground. Prototype: `tools/visual/capture_look3d.gd`.
- 2a post-processing, tone (rule 2.81): AgX tonemapping with a footy-TV grade (contrast 1.1,
  saturation 1.2), exposure set by the brightness of open grass; club rings keep their exact colour.
- 2a lighting, night (rule 2.82): four light towers, one to each corner, each casting a shadow;
  a roofed venue's lighting is settled with the stadium (2b). The crowd needs almost no shine.
- 2a weather, wet (rule 2.83): cloud light (no sun, soft shadows) and rain falling on screen
  (fine streaks from 15 m out). A distance haze barely shows at the match cameras' range.
- 2a skies (rule 2.84): the world has designed skies, one for each weather and time of day ("i 100% want skies"; "a world design decision"); the seven prototype skies approved ("Theyre gorgeous").
- 2b the grounds (rule 2.90): every ground with an AFL premiership match since 1990 (36) gets its own 3D stadium, the 8 Legacy
  grounds as they were in the 1990s included, plus Macquarie Point (Hobart) from its concept design; all 37 are in data/grounds.json, with their sources.
- 2b roofed grounds at night (rule 2.91): as in real life, Marvel and Optus are lit from floodlights on their roofs, all the way round; the open grounds keep four towers (2.82).
- 2d the body (rule 2.85): MetaHuman, made in Unreal 5.6+ used as a tool only and exported into the Godot
  game (the game stays in Godot); one is shown in our match before anything is built on it. Shown and approved (2.89).
- 2d builds (rule 2.97): every man at his own height and weight, blended between four MetaHuman bodies (168 cm, 211 cm,
  light and heavy at 188 cm); `scripts/ui/match/Oval3DBuild.gd`. No weight on record: a real 2026 man's weight at his
  height (2.98). Prototype: `tools/visual/capture_builds3d.gd`.
- 2d faces (rule 2.99): Tripo heads for the best 23 of every 2026 list, which the director generates (list and spec in
  `tools/oval3d/heads/`); everyone else recognisable features only (facial hair, skin tone, size, hair); invented
  players from pre-made modular pieces, tested together, which later feed a character creator.
- 2e the main camera (rule 2.93): the real AFL main camera (OP-33: centre line, 15 m up, 25 m back from the boundary; it pans, tilts and zooms to follow the ball, about a third of the ground across), in a 16:9 TV picture across the phone ("A TV shape"). Prototype: `tools/visual/capture_cameras3d.gd`. Sources: Free TV Australia OP-33 (2015); ABC News (2020).
- 2e after a goal (rule 2.96): one skippable replay (B: the camera behind the goals, half speed) while the players go back to their 6-6-6 spots, sped up; a skip brings the picture back live and shows the rest of the walk back fast, then the bounce. No replay after a behind, except the deciding one: a behind that ends up the last score and wins or levels the game, replayed after the siren. Prototype: `tools/visual/capture_cameras3d.gd` (cuts, replays, slow and fast cuts). Sources: Tom Ryan, Substack (9 and 23 Sep 2026); SEN (18 Jun 2020).
- Parked as a stretch goal (director 2026-11-18: "lets park all bespoke supporter work as a stretch goal"; TODO stretch goal, special crowd characters). Close-up supporters (rule 2.100): bespoke supporters for close-ups in breaks (the woman, a face-painted fan for each team, the cheer squad with signs and banners, the poncho stalwart in the rain) are MetaHumans ("A MetaHuman"); no kid ("nix kids"). Prototype shot: `tools/visual/capture_closeup3d.gd`.
- The woman supporter (rule 2.104): early-to-mid-twenties blonde, the MetaHuman Vivian face with long straight blonde hair and a fringe ("A Vivian").
- Supporter knitwear (rule 2.108): scarves and beanies take any club's colours at run time, Forge clubs too ("the colours need to be completely switchable"); `scripts/ui/match/SupporterMerch.gd` and `assets/oval3d/supporters/merch_knit.gdshader`.
- 2e supporters (rule 2.101): the gameplay cameras draw nobody within 20 m of the lens, so no supporter blocks the picture; supporter shots are for breaks (stretch goal).
- 2e set shots (rule 2.102): "do what happens IRL": the live picture cuts to the camera behind the goals for the kick, then back to the main camera.
- 2e ball-ups (rule 2.103): "B: ruckmen close-ups": in the wait before a ball-up the picture cuts to about a second on each ruckman, then back to the main camera just before the bounce.
- 2e ball-up close-ups at speed (rule 2.109): "B: Sped up with the match": the close-ups run at the match's speed like everything else.
- 2e skipping a replay (rule 2.110): "B: Tap the picture": a tap anywhere on the 3D picture skips a goal's replay; a "Replay: tap to skip" tag sits top left while it plays.
- 2e TV framing (rule 2.111): "B: real TV top/bottom": the main camera keeps a 16:9 TV picture's top and bottom on the tall phone picture; the wide shot (with sky) on "Long kicks, After a goal, Start of each quarter"; "zoom needs to be quick but not jarringly so". Set shots are filmed from behind the kicker, as real TV does.
- 2e the picture on the phone (rule 2.105): "A but the stats part is very ugly": the main picture fills the screen between the scoreboard and the controls, taller than a TV picture at the same zoom; team stats under it as split bars in club colours (rule 2.106: "A: bars"): disposals, marks, clearances and hit-outs ("Keep those four"). The scoreboard panel goes (rule 2.107): "we can put an on screen scoreboard like in ss2" (a TV score bug on the picture), "use the extra new space for more 3d view", and "the momentum bar stays, make it unobtrusive": a thin line along the bottom edge of the picture ("C: bottom of picture").

The freeze allows only the
prototypes each question needs; nothing from step 2 is the settled look until he has chosen it.

## Step 3. The asset and animation plan ([3D_ASSET_PLAN.md](3D_ASSET_PLAN.md); the rig waits on step 2's body)

One inventory of every asset and animation the 3D view needs, written once the body is chosen. For
each: what it is, where it comes from (his Rokoko takes, a free library, made by us), what it is made
on (the chosen body's rig), how it is checked, and its order. Families:

- bodies, heads, hair, kits, boots, umpires;
- getting around (cycles, starts, stops, turns), with and without the ball;
- actions with their failures (kicks, handballs, gathers, marks, bounces), contests and ruck;
- idles, reactions, umpire signals, stoppage set-ups;
- the ground, stadium, crowd and cameras;
- the 3D scenes that replace the vignettes (rule 2.76).

The existing 123-clip library is assessed against the plan: kept, re-made on the chosen body, or cut.
`docs/research/AFL2004_ANIMATION_STUDY.md` stays the method for animation (warping to the sim's spot
and time, entry and exit, paired contests, live layers and IK, detail levels).

## Step 4. Build (after steps 1 and 3)

In the order the asset plan sets: the action layer and the proof passage (TODO rows 197 and 198), then
full-match coverage, then the phone check at that milestone, then the 3D scenes that replace the
vignettes. Nothing in step 4 starts before the football proof has passed and the asset plan exists.

## Status (as of 2026-11-20)

_Update this section whenever 3D work merges. It is the one place 3D progress is tracked; TODO.md rows hold the detail._

| Step | TODO row | State | Next |
|---|---|---|---|
| Freeze (no new player art, no one-incident patches) | | in force since 2026-11-16 | lifts when steps 2 and 3 are done |
| 1. Football proof | 201 | harness built (#1695), spec checked (2.86), gap list of 14 written | fix the systems on the gap list; none fixed yet |
| 2a. Light, tone, weather, skies | 202 | chosen and built (2.80-2.84, #1693 #1694 #1696 #1701); film look over the picture (2.112, #1839) | phone costing: every ground measured at three graphics levels in the cloud ([PHONE_3D_BUDGET.md](PHONE_3D_BUDGET.md), Settings > Graphics); the real phone run (the "Android 3D probe" APK) is next |
| 2b. The 37 grounds | 202 | 23 of 37 have a model merged, 2 more in open PRs, 4 under way locally (table below) | land Victoria Park, Riverway, Mars and Accor; confirm the other 8; background scenes (#1878 #1892 #1897) |
| 2c. Crowd | 202 | chosen: 3D people within 55 m, cards beyond (2.92), built; seated on the MCG model's own seats (he chose "Seat the crowd in the MCG", 2026-11-20, #1929) | measure its cost on a phone; each other ground gets it once it loads in a match |
| 2d. Players' look | 202 | body: MetaHuman (2.85, 2.89); builds by height and weight (2.97, 2.98); faces ruled (2.99) | the Tripo heads (director generates) and the features for everyone else |
| 2e. Cameras | 202 | main camera, goal replay, set shots, ball-up close-ups, tap to skip, TV framing, picture layout, stat bars, score bug all ruled and built (2.93-2.111, #1818) | the other cameras and cuts in play |
| Broadcast popups | 207 | stat card ruled (2.94, 2.95) | ask: when a card shows and for how long; the journalists' posts |
| 3. Asset and animation plan | 203 | done (#1707), docs/3D_ASSET_PLAN.md | |
| 4a. Proof passage | 197 | runtime in the match screen (#1601 and on); waits on 201 and 203 | after step 1 passes |
| 4b. Animation | 198 | paused (2.78) | the clips 203 lists, on the MetaHuman body |
| Parked | stretch | bespoke close-up supporters (2.100, parked 2026-11-18) | |

### 2b: the grounds (rule 2.90)

"Model" means a ground model landed on main. Work that is still in a local worktree counts too: a ground session adds its row here when it starts, not only when it merges.

| Ground | State | PRs |
|---|---|---|
| MCG | model, instanced seats | #1843 |
| Marvel Stadium | model | #1911 |
| Adelaide Oval | model, 3D seats; plays in a match (exported for the game by tools/grounds/adelaide) | #1856 |
| Optus Stadium | model, roof, seats | #1867 #1880; background scene open #1897 |
| SCG | model | #1909 |
| GMHBA Stadium | exterior model | #1903; open: roof #1899, background scene #1878 |
| People First Stadium | model, roof | #1853 #1860 #1868 #1889; background scene open #1892 |
| ENGIE Stadium | texture pass | #1866 |
| Bellerive Oval | model | #1900 |
| Manuka Oval | model | #1865 |
| Norwood Oval | model, textures | #1870 |
| Waverley Park | model | #1902 |
| Victoria Park | texture pass open | #1884 |
| Windy Hill | model | #1885 |
| Moorabbin Oval | model | #1910 |
| Ikon Park | exterior model | #1852 |
| Whitten Oval | model, textures | #1882 |
| Football Park | model | #1886 |
| Subiaco Oval | both era models | #1901 |
| York Park | exterior model | #1855 |
| WACA | model | #1864 |
| Cazaly's Stadium | model, textures | #1891; open: west building #1898 |
| North Hobart Oval | 1991-92 model | #1854 |
| Bruce Stadium | model, 3D seats | #1848 |
| Riverway Stadium | model open | #1896 |
| Mars Stadium | model built, not yet pushed (local worktree, 2026-11-20) | |
| Accor Stadium | model built, not yet pushed (local worktree, 2026-11-20) | |
| Marrara Oval (TIO Darwin) | under way, not yet pushed (site data and roof scripts, 2026-11-19) | |
| The Gabba | model, 3D seats; plays in a match (built 2026-11-19/20 on a branch that never merged; brought in from the PC) | |
| Barossa Park, Traeger Park, Sky Stadium, Jiangwan Stadium, Hands Oval, Blacktown, Summit Park, Macquarie Point | to confirm: no work found in the repo or its local worktrees | |

Machine pre-inspection of the 30 match grounds, before the director's fly-through (2026-11-21, #1950):
[3D_PREINSPECTION.md](3D_PREINSPECTION.md). Its fixes are in; its open faults are listed there.

Each ground's turf (2026-11-21, asked for by the director as part of 2b): its own mowing cut (stripes across or
along the ground, checkerboard, diagonal or diamonds, 10-14 m bands) and grass (couch at the warm-climate grounds,
rye in the south), `Oval3DTurf.MOWING`; the AFL markings are drawn from the ground's own size. A first draft for his
fly-through review like the rest of the ground: curators cut a new pattern each week, so the cut is a house style.

### Open questions for the director (3D only)

- Row 207: when a stat card appears and for how long; the journalists' posts (who, what, when, where).
- Row 202 2e: the other cameras and cuts in play.
- Design bible: how weather affects a match (its look is settled; its effect on play is not).

