# Vignette renderer inventory (row 6.40)

_2026-11-11. Read from the code on main at 17d2f7e0. Nothing was changed; this is the inventory the ruling asks for._

Ruling (Director Bible rule 40): "entirely replace the old vignette art style with the new pre-rendered 2.5D
footballer style". No stick figure or silhouette stays player-facing; inventory every renderer and fallback;
retire obsolete paths.

## Verdict

- **Footballers, coach and umpire: no old-style path is left.** Every one of them, in all seven scenes, is drawn
  from the pre-rendered sheet by one function, `StoppageVignette.draw_frame()`. Every fallback on that path lands
  on another pre-rendered strip (the average build, the base hair, a plain kit, the last frame). None lands on
  drawn art.
- **Drawn silhouette people are still player-facing in two scenes**, and they are not footballers: the awards
  night guests and the press pack. The crowd in the stands and the photographers behind the goals are also drawn
  in code. The ruling says "no stick figure or silhouette stays player-facing", so **row 6.40 is not closed by this
  document**. The list is under "What is left".
- **One obsolete path can be retired**: the earlier front-on speccy staging behind `OLD_FRONT_DURATION`. It cannot
  run today and it draws the new figures anyway (old staging, not old art).

## The one figure path

| Part | Where | Art |
| --- | --- | --- |
| Body | `StoppageVignette.draw_frame()` `scripts/ui/match/StoppageVignette.gd:577` | `assets/vignette/figures_shade.png` (drawn), recoloured by `figure.gdshader` from `figures_mask.png`, `figures_design.png`, `figures_digits.png` (`figure_material()` :197) |
| Layout | `VignetteFigures.BODIES` `scripts/ui/match/VignetteFigures.gd` (generated) | builds `average`, `small`, `ruck`, `coach` |
| Hair and face | `StoppageVignette.draw_hair()` :603, `_draw_look()` :629 | `look_*.png` (10 hair styles, `look_face_0..4.png`) through `VignetteLooks`; base `hair_*.png` (5 styles) through `VignetteFigures.hair_for()` |
| Tattoos | `VignetteInk.cell()` `scripts/ui/match/VignetteInk.gd:298` | `ink_1..3.png` |
| Ball | `VignetteBall` | `assets/vignette/ball.png` (rendered Sherrin) |
| Ground shadow | `draw_circle` ellipse, Stoppage :551-556, Broadcast :1397-1399 | drawn (a shadow, not a figure) |

The umpire is the same sheet in the umpire kit (`UMPIRE_GEAR`, `UMPIRE_LOOK`).

## Renderers

| Renderer | File | Opened from | Figures drawn by | Old-style figure path left? |
| --- | --- | --- | --- | --- |
| Stoppage | `scripts/ui/match/StoppageVignette.gd` | `MatchScene.gd:659`, `:2690` | `_draw_figure()` :526 -> `draw_frame()` | No |
| Decision | `scripts/ui/match/DecisionVignette.gd` | `MatchScene.gd:2693` | base `_draw_figure()`; moves from `_frame()` :229 | No |
| PreMatch | `scripts/ui/match/PreMatchVignette.gd` | `MatchKickoff.gd:100` (warmed `HubScene.gd:2137`) | base `_draw_figure()`; moves from `_frame()` :344 | No |
| Farewell | `scripts/ui/match/FarewellVignette.gd` | `MatchScene.gd:3841` | `_draw_figure()` :283, base for the rest | No |
| Broadcast | `scripts/ui/match/BroadcastVignette.gd` | `MatchScene.gd:3527` | `_figure()` :1379 -> `draw_frame()` :1404; extras `_draw_extras()` :351 | No |
| AwardWinner | `scripts/ui/match/AwardWinnerVignette.gd` | `SeasonAwards.gd:194`, `DraftScene.gd:1352` | winner: Broadcast `_figure()`. Guests: `_draw_audience()` :205, `_guest()` :232, drawn in code | Footballer: no. **Guests: yes, drawn silhouettes** |
| MediaConference | `scripts/ui/MediaConferenceVignette.gd` | `PressScene.gd:96`, `:107` | coach: `_coach()` :106, sheet build `coach`. Press: `_draw_press()` :194, drawn in code | Coach: no. **Press pack: yes, drawn silhouettes** |

## Fallbacks on the figure path

All of these end in pre-rendered art.

| Fallback | File:line | When it fires | What shows |
| --- | --- | --- | --- |
| Average build | `StoppageVignette.gd:542-543` | A small or ruck man is asked for a move his build has no strip for (ruck: jog side-on, kick, clap; small: idle, tap, bounce, celebrate) | The average-build strip for that move |
| Average build | `BroadcastVignette.gd:1382-1383` (`_figure`) | A small featured player needs a move only the average build has (mark, brace, walk, celebrate, bounce) | The average-build strip |
| Average build | `BroadcastVignette.gd:664` | The marker's build has no back-on leap | Average leap |
| Average build (hand point) | `BroadcastVignette.gd:1038-1039`, `DecisionVignette.gd:390-391` | Same case, when finding the palm for the ball | Average strip's palm |
| Always average | `FarewellVignette.gd:290` | The chaired player and his carriers | Average strips `chaired`, `carrier`, `carrier_near` |
| Empty-strip guard | `FarewellVignette.gd:291-292` | Never: `VignetteFigures.strip()` (:3405) has no guard and the strips exist | Nothing (dead guard) |
| Build by height | `StoppageVignette.gd:670-674` | Height unknown, or the umpire | Average build |
| `ready_b` only if held | `StoppageVignette.gd:715` | Build lacks the back-on ready | Plain `ready` |
| Frame past the end | `StoppageVignette.gd:812` (`figure_frame`) | A move is asked for a frame it does not have | Its last frame (logged when `log_frames`) |
| Neutral look | `StoppageVignette.gd:559`; `BroadcastVignette.gd:36`, `:51`, `:121-122`; `AwardWinnerVignette.gd:37` | No player record (extras, umpire, a missing player) | `Appearance.UNCURATED`: base hair, no face |
| Base hair | `StoppageVignette.gd:562`, `draw_hair()` :603; `VignetteFigures.hair_for()` :3480 | `VignetteLooks.cell()` has no cell for this hair on this strip | Base `short_crop` (nothing for `buzz`) |
| No face | `StoppageVignette.gd:629` | The strip has no cell for this face (some strips carry only some faces) | Body shade only |
| No ink | `VignetteInk.gd:298` | No years of ink, or no cell for the strip | No tattoo |
| Plain kit | `StoppageVignette.gd:163-170`, `BroadcastVignette.gd:133-142` | Unknown club code | Kit from the two colours, grey trim, white base |
| Pad colour | `StoppageVignette.gd:521-523`, `BroadcastVignette.gd:580` | No club colour | Grey |
| No colours | `AwardWinnerVignette.gd:68-69` | Scene opened without club colours | Nothing drawn |
| Suit and room colours | `MediaConferenceVignette.gd:41`, `:123`, `:146` | No club colours | Neutral tie, wall, desk skirt |
| Coach strip | `MediaConferenceVignette.gd:106-114` | No guard: reads the `coach` strips directly | They exist in the sheet |

## The obsolete path: OLD_FRONT_DURATION

- `BroadcastVignette.gd:146` `OLD_FRONT_DURATION := 3.8`, returned by `duration_for()` :149-152 when the kind is
  the front-on speccy and `_sf_ready()` is false.
- `_sf_ready()` :730-731 is true when the sheet holds `mark_s` and `brace_s` (`side_q`) for the average build.
  It does today, and `tests/test_match_visual.gd:1251` fails if it ever does not. So the branch never runs.
- If it did run, `_draw()` :278-281 would send the front-on speccy to `_draw_speccy()` :599, the earlier staging.
  That function still draws the pre-rendered figures, and it is the live path for the side-on and defensive
  speccies. So this is old staging, not old-style art.
- `_sf_ready()` is tested at :263, :278, :409, :436, :493, :578, :589.
- Not removed here: it is not old-style art, and removing it touches a live scene and its suite. Retiring it is a
  small code row: delete the constant, make the seven tests of `_sf_ready()` unconditional, keep the test at
  `test_match_visual.gd:1251` as the guard that the strips exist.
- Two functions in `BroadcastVignette.gd` have no caller in scripts, tests or tools: `_sf_blend()` :834 and
  `_ready_figure()` :1413. Both draw pre-rendered figures. They can go in the same row.

## What is left (drawn people, player-facing)

| Who | File:line | How they are drawn | Seen in |
| --- | --- | --- | --- |
| Awards night guests | `AwardWinnerVignette.gd:205-244` (`_draw_audience`, `_guest`) | Head-and-shoulders silhouettes: polygon, circle, rim arc; clapping hands as circles. Comment :202-204: "all in silhouette against the stage light" | Season awards, draft night |
| Press pack | `MediaConferenceVignette.gd:194-225` (`_draw_press`) | Six head-and-shoulders silhouettes with phones and recorders | Press conference |
| Crowd in the stands | `VignetteCrowd.gd:23` (`seats`), `:79` (`stand`), `:131` (`draw`) | Rows of heads and shoulders painted into a texture, arms up as rectangles. "No faces, no likenesses: a crowd at a distance" | Every on-ground scene, and `PitchView.gd:2161` |
| Photographers | `VignetteGround.gd:236-250` (`_photographers`) | A dark rectangle, a circle head, a lens rectangle | Behind the goals |

Rule 40 itself names the first case: "Awards ceremony currently reuses BroadcastVignette silhouettes and must be
replaced." The winner has been replaced; the guests around him have not. The rooms these people sit in (awards
stage, press room, stands) are also drawn in code; row 6.42 replaces those with rendered plates, and rule 42 keeps
drawn rooms "only as fallbacks".

## Helpers

| Helper | Draws people? | Notes |
| --- | --- | --- |
| `VignetteFigures.gd` | Data only | Sheet layout and base hair |
| `VignetteLooks.gd` | Data only | Hair and face cells. Header :5-8 says "Shown only with Features 'player_looks' on": stale, there is no such gate |
| `VignetteInk.gd` | Data only | Tattoo cells |
| `VignetteBall.gd` | No | Rendered ball |
| `VignetteCamera.gd` | No | Transform only |
| `VignetteGrade.gd` | No | Colour grade pass (`grade.gdshader`) |
| `VignetteAtmos.gd` | No | Haze and lights |
| `VignetteWeather.gd` | No | Rain, wind, flags |
| `VignetteCrowd.gd` | Yes, drawn | See "What is left" |
| `VignetteGround.gd` | Photographers, drawn | Ground and stands drawn in code |

## Neighbours on the same figure path

- `scripts/ui/PitchView.gd:170-185`: the small figures on the oval use `draw_frame()`. Always the average build
  (:2092, :2119); a missing move falls back to `idle` front (:2116-2118).
- `scripts/ui/PlayerPreview.gd`: build from height (:36-39), `ready` falls back to `idle` (:59), `draw_frame()` :68.

## Stale wording to fix when the code is next touched

- `BroadcastVignette.gd:43-46`: "sized as the old drawn figures were".
- `BroadcastVignette.gd:19`: the note about `OLD_FRONT_DURATION`.
- `VignetteLooks.gd:5-8`: the `player_looks` feature gate that does not exist.

## Question for the director

Do the drawn silhouette guests, press pack, crowd and photographers count under rule 40 (replace them with
pre-rendered people now), or do they go with the rendered plates of row 6.42?
