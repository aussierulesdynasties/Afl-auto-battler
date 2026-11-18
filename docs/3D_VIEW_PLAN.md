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
| 4 | No squeeze on a loose ball | 36-47 m wide (Alexander 2019) | 62-67 m | A loose-ball shape: none exists; loose balls use the open-play spots |
| 5 | Stoppages around the ground are thin | 23 players in the ball's quarter in either 50, 17 in midfield (Alexander 2021) | 13.4 | Stoppage set-ups (`_centre_spot`, `_centre_setup`, the ball-up and throw-in spots) |
| 6 | Kicks are short and gain little ground | 25.0 m average, ±11.8 (Spencer 2019); 25-30 m gained | 20.0 m, ±11.6; 11.2 m gained | MatchSim kick events (balance-gated) |
| 7 | Too many kicks | 213 a team-game (Wheelo 2026) | 309 | MatchSim event count (balance-gated) |
| 8 | Calls do not change how the side kicks | Attacking: no switch; Controlled and Slow it down: shorter, across and back (rule 2.45) | Attacking: switches stay 6%; Controlled: kicks 0.5 m longer; Slow it down: 0.2 m longer, 3 points fewer backward | MatchSim kick choice by plan (balance-gated) |
| 9 | A tagger does not shadow his man | a tag is permanent and goes where his man goes (2.44, 2.58); no published distance | 21.7 m apart on average, within 5 m 15.6% of the time (off: 27.0 m, 6.9%) | Man-on-man pull in `_structure_spot`: only inside 35 m, at most 85% of the way |
| 10 | A switched defender drifts off his forward | everyone has an opponent (2.44) | 25.3 m apart, within 5 m 15.7% (off: 28.9 m, 13.5%) | Man-on-man pull (as 9) |
| 11 | Fumble then gather: the gatherer runs 3.9 m past and the ball lies alone ~0.7 s (seed 31, FRE v STK) | the nearest man scoops it | as stated (row 197 inbox) | Loose-ball pickup; the WIP on `claude/oval3d-loose-ball-wip` fails 8 match_visual checks |
| 12 | No clean gather (down for it, picks it up) in the shipped game | | the first man knocks it on toward MatchSim's winner | Loose-ball pickup (as 11) |
| 13 | A dead stop at the fence: 4-5 m/s to 1.1 m/s in one step, twice in four seeds | | as stated (row 197 inbox) | MatchMotion fence clamp |
| 14 | Throw numbers at it does not put more men at the ball; it moves the team forward like Push | more of our men around the ball wherever it is (the call's own words) | men within 20 m of the ball +0.9 at most (+0.1 at stoppages); team centre 7-19 m further forward, as Push's 8-14 m | Call shape: `_structure_spot` lifts the lines forward for Surge and Push alike (`_surge_ref`); no pull toward the ball |

What the calls already do (no gap): Attacking narrows the side 26-34 m in attack (about 39%; rule 2.45 asks about
45%); Controlled widens it 13-24 m and shortens it 35-44 m; Defensive shortens it 29 m in midfield; Win Contest
narrows it 18-25 m and puts 1.9 more men within 10 m of a stoppage. Flood pulls the team 10-13 m back with 2.2 more men behind the ball in our half;
Push moves it 8-14 m forward with 2.5-2.9 fewer behind; Slow it down spreads it 16-27 m wider; Stack sets the
lines 51 m shorter at the centre bounce (still 6-6-6, no extra men in the square). Not yet measured: what each position does
(marks, tackles, kicks per role), which the harness does not count.

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
part by part (kept, reworked or replaced).

   What a stadium needs, part by part, as the real grounds have it (2026-11-17), against today's (row 202
   2c's stand, seen from the 2.93 main camera):

   | Part | What the real grounds have | Today's 3D view | Verdict |
   | --- | --- | --- | --- |
   | Stands | Each ground's own tiers (the MCG three, most two, small grounds one), concourses between them | One ring stand, 34 m deep, 24 m high, the same at every ground | Replaced: each ground's tiers from data/grounds.json |
   | Crowd | Sits on those tiers | 41,127 on the one ring (2.92 mix) | Kept, seated on each ground's tiers |
   | Roof | Edge lip, canopy over the top tier, or a closed roof (Marvel) | None | New, from the data's roof kind |
   | Outer facade | Each ground its own: "the outer facades are all very different" (director, 2026-11-17) | One plain grey wall round every ground | Replaced: each ground's own facade |
   | Light towers | MCG's tubular masts, plain masts, or lights on the roof (Marvel, Optus: 2.91) | None | New, from the data |
   | Scoreboards | One or two big screens at the ends; heritage boards (SCG) | None | New, from the data |
   | Fence | Advertising boards at the boundary's edge | A plain white wall | Reworked: plain board panels, no sponsor's mark |
   | Goal ends | Nets raised behind the goals | Posts only | New |
   | Main camera | A camera platform with a clear view (2.93's spot) | The eye sits among the seats: near heads fill the wide view | New: a platform on each wing, no seats in front of the lens |
   | Field size | Each ground its own size | One size for every ground | Open: whether size affects play is the director's open question (bible items 26 and 51) |

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
  game (the game stays in Godot); one is shown in our match before anything is built on it. Shown and approved (2.89). Builds, heads and faces next.
- 2e the main camera (rule 2.93): the real AFL main camera (OP-33: centre line, 15 m up, 25 m back from the boundary; it pans, tilts and zooms to follow the ball, about a third of the ground across), in a 16:9 TV picture across the phone ("A TV shape"). Prototype: `tools/visual/capture_cameras3d.gd`. Sources: Free TV Australia OP-33 (2015); ABC News (2020).
- 2e after a goal (rule 2.96): one skippable replay (B: the camera behind the goals, half speed) while the players go back to their 6-6-6 spots, sped up; a skip brings the picture back live and shows the rest of the walk back fast, then the bounce. Prototype: `tools/visual/capture_cameras3d.gd` (cuts, replays, slow and fast cuts). Sources: Tom Ryan, Substack (9 and 23 Sep 2026); SEN (18 Jun 2020).

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

## Status

| Step | State |
|---|---|
| Freeze | in force from 2026-11-16 |
| 1. Football proof | harness in `tools/balance.sh shape`; spec checked (rule 2.86); gap list above; fixes next (row 201) |
| 2. The world and the look | under way (row 202): 2a daylight, tone, night lighting and wet games chosen, skies chosen (rules 2.80-2.84); 2d body chosen: MetaHuman (2.85), shown in our match and approved (2.89); 2b every AFL ground since 1990 and Macquarie Point get their own stadium (2.90), roofed grounds lit from their roofs (2.91); 2c crowd chosen: a mix of 3D people and cards (2.92), built into the 3D view; 2e main camera chosen: the real AFL main camera in a 16:9 TV picture (2.93), after a goal one skippable replay while the players go back (2.96); next 2b building the grounds, 2d builds and faces, 2e the other cameras and cuts in play |
| 3. Asset and animation plan | done (#1707) |
| 4. Build | after 1 and 3 (rows 197, 198) |
