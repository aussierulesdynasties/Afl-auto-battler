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
   published AFL tracking studies, each number with its source. He checks the spec.
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

**2c. The crowd, cheaply.** Methods compared on looks and phone cost before any is chosen: shader-
painted seats (today), instanced cards of baked figures (impostors), animated low-poly instances, and
a mix by distance. Cheer squads, banners and reactions to goals are part of the choice.

**2d. The players' look.** After 2a: the world's light decides how a body reads.
1. **The body.** Our MPFB average body, the MetaHuman body, or another source; how many builds
   (heights, frames); how heads and faces vary. Shown in a match, from the broadcast camera and close.
2. **The look.** How realistic: skin, kit cloth, boots and hair detail at the distances the game is seen.

**2e. The cameras.** Which views a match uses (broadcast wing, high whole ground, behind the goals,
close-ups at a stoppage or a set shot).

The answers are recorded in the Director Bible and summarised here. The freeze allows only the
prototypes each question needs; nothing from step 2 is the settled look until he has chosen it.

## Step 3. The asset and animation plan (after step 2)

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
| 1. Football proof | not started (row 201) |
| 2. The world and the look | not started (row 202: 2a foundation, 2b stadium, 2c crowd, 2d players' look, 2e cameras) |
| 3. Asset and animation plan | after step 2 (row 203) |
| 4. Build | after 1 and 3 (rows 197, 198) |
