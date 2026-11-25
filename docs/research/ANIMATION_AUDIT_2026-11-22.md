# Animation audit, 2026-11-22 (row 198)

Every clip the 3D match can play, where it came from, and how it compares with the real footage it was
made from. Each rating comes from comparing the clip side by side with its source footage. The
comparison sheets are the director's own `retargeted/videos/*.mp4`, stills at the same moments. The
Wired column says whether a match plays the clip yet.

Ratings:

- **Good:** reads as the real move at game distance.
- **Fair:** the right move, with a visible flaw.
- **Poor:** a viewer would notice something wrong.
- **Out:** not fit to play.

## Where the motion comes from

| Source | Clips | Licence position |
| --- | --- | --- |
| Rokoko Vision, from broadcast and Getty training footage (the director's footage, bible rule 2.74) | 21 AFL clips in `player_mh.glb`, 3 more on the PC (`rokoko new 2026-11-15`) | Rokoko claims no ownership of output. The footage's own rights are the grey area. The director accepted that risk on 2026-11-22. |
| Epic GASP (Game Animation Sample) | `jog`, `carry` and `idle` (every running and standing frame), plus 12 tackle pairs | Kept by the director's choice (2026-11-22). No replacement work. Never add new Epic animation. |
| Mixamo | 57 FBX on the PC (injuries, get-ups, cheering), none in the game | Mixamo allows use in games. Redistributing the standalone FBX is not allowed, so a clip ships only baked into our own GLB. |

## Clips matches play

| Clip | Use | Rating | Notes |
| --- | --- | --- | --- |
| `jog`, `carry` (GASP) | every run | Good | Generic Unreal motion. Reads well, but nothing about it is AFL. |
| `idle` (GASP) | every stand | Good | Generic. |
| `ground_ball_run_01`, `ground_ball_run_grimes_01` | scoops | Good | Already timed to the touch (#1989 and others). |
| 12 GASP tackle pairs | tackles | Fair | Two-man takes with real contact. They are soccer and NFL-style grabs, not an AFL wrap-and-sling. |
| `umpire_bounce_01` | centre bounce | Fair | The hips stay above 0.89 m all the way through (measured), so the umpire does not lie down. He leans far over in the follow-through. |
| `kick_on_run_03` | right-foot kick, on the run **(wired today)** | Fair | The body follows the source well. The follow-through leg stops lower than the real kicker's. |
| `kick_on_run_02_run` | left-foot kick **(wired today)** | Fair | Same: a short follow-through. |
| `drop_punt_02` | set-up kick, walking in **(wired today)** | Good | A high follow-through, matching the source. |
| `handball_on_run_01` | handball **(wired today)** | Poor | The punching fist barely travels. The source's punch is a hard drive, but the retarget turns it into a push. Needs a remake. |
| `chest_mark_02` | chest mark **(wired today)** | Fair | The arms and body match. The fingers are not modelled, so the hands look flat round the ball. |
| `overhead_mark_01` | overhead mark **(wired today)** | Good | Hands overhead, a good stretch. |

## Clips not wired yet

| Clip | Rating against source | Next step |
| --- | --- | --- |
| `ruck_jump_01` | Fair: feet 0.7 m off the turf | Wire to the ruck tap (needs a two-ruck contest, not one man) |
| `ruck_centre_nicnat_01`, `ruck_ump_nicnat_01` (PC) | Poor: the source is a wide broadcast shot, the leap barely leaves the ground | Remake from a closer source |
| `spoil_rance_01`, `spoil_rance_02` | Fair: the fist goes up and through | Wire to the spoil contact |
| `bump_contest_01`, `bump_finals_01` | Fair: shoulder-in, low centre | Wire as one-man shepherds and bumps |
| `dive_finals_01` | Poor: wide shot, the body twists oddly at the ground | Remake |
| `banana_ablett_01/02`, `snap_ablett_01` | Fair | Goal-kick variants: wire after kicks settle |
| `run_bounce_01`, `run_with_ball_01/03` | Fair | Run-and-bounce needs a ball path off the turf |
| `dribble_ablett_01`, `ground_ball_01/04`, `dont_argue_01`, `mark_and_kick_jog_01`, `drop_punt_ablett_side`, `kick_on_run_01/02/04` | Fair to Poor | `kick_on_run_04` starts with his hands apart, so the ball would hover. Keep it out. |

## What wiring did today

`tools/oval3d/clip_markers.py` reads each move's contact frame off the motion: the fastest boot, the
palms closest together, or the hands highest. The match then starts the clip so that this frame lands
on the director's touch. Measured with `tools/visual/measure_oval3d_moves.gd` over 120 s, seed 31:

| Move | With the clip | Ball to boot or palms at the touch | Picture behind the touch |
| --- | --- | --- | --- |
| Kick | 40 of 40 | 0.000 m | median 0.017 s |
| Handball | 12 of 12 | 0.000 m | median 0.017 s |
| Mark | 9 of 11 | 0.000 m | median 0.017 s |

The 2 marks without a clip are one taken inside a ground-ball scoop (correct as drawn) and one mark
the director gives with no warning. A no-warning mark needs a catch-up clip; that is open.

Faults found and fixed on the way:

- A tackle cut a kick off mid-swing, and the ball left with no boot on it. A tackle now waits until
  the contact.
- A free kick paid to the man already holding the ball was drawn as a kick. It is no longer a kick.
- A marker whose director run-in was late stood frozen with his hands up for up to 1.2 s. He now takes
  the ball as it arrives and keeps it.

## Sourcing plan for the gaps

The director ruled out filming (2026-11-22: "yeah nah, thats not feasible"). Every route below needs
nothing physical from him. Licences were checked first. The terms are quoted from each source's own
page, as read on 2026-11-22.

| Gap | Route | Licence (quoted) | Cost |
| --- | --- | --- | --- |
| AFL moves: remakes (handball, ruck), new tackles, umpire signals, the helped-off injury | Broadcast clip → Rokoko Vision → MetaHuman retarget (the existing pipeline) | Rokoko terms 3.1/6.3: "we do not claim ownership over any User Content". Footage risk accepted by the director. | Free tier 30 s a month. Basic is $12 a month for 600 s, which needs the director's yes. |
| The same, without the per-second limit | Our own video-to-motion: MediaPipe pose → MetaHuman skeleton bake, in the cloud. Proved by a round trip on our own rendered clips before it is trusted. | MediaPipe: Apache-2.0 | None |
| Extra general motion | CMU motion capture database | CMU FAQ: "may be copied, modified, or redistributed without permission" | None |
| Injuries, get-ups, crowd and bench reactions | Mixamo, baked into our own GLB | "royalty free for personal, commercial, and non-profit projects including... Create video games". No standalone FBX in the repo. | None |

Ruled out:

- Move One: its EULA 7.1.2 makes Move AI the owner of the output.
- GVHMR, the SMPL-based models and opencap-monocular: non-commercial licences.

## Reel feedback fixes (2026-11-22, evening)

The director watched the moves reel: "some of the animations create some strange model contortion",
"the ball drop from hand to foot when they kick is very floaty", "the players are holding the ball
horizontally like a dinner plate", and "the tackler is standing by idly waiting for the tackle".
Every fix below was measured, not judged by eye.

**The kick's ball.** The footage (kick_on_run_03, drop_punt_02) shows the ball guided down in the
kicking-side hand alone, at about hip height, while the other arm swings up and away. The clips do
the same: the palms are about 1 m apart in the run-in, and the kicking-side hand is at 0.87-0.92 m.
We had drawn the ball between both palms, in mid-air at about 1.2 m, lying flat across them, and let it
go from there. Now:

- As the palms part, the ball moves over to the kicking-side palm.
- In that hand the ball leans about 42 deg off the flat along his run, as the footage measures.
- It falls near upright, 0-10 deg off vertical as in drop_punt_02 side-on, under real gravity in real seconds.

Measured over 120 s, seed 31:

| | Before | After |
| --- | --- | --- |
| Release height (median) | 0.92 m | 0.76 m |
| Implied g (median) | 7.1 m/s² | 9.4 m/s² |

A touch that comes earlier than planned re-times the rest of the fall from where the ball is. It
never falls slower than gravity.

**The idle tackler.** A tackler who slowed below running pace as he arrived stood in the idle clip
until the take started. A man within 6 m of the carrier now keeps running up to 0.6 s longer, and the
take starts well inside that. Over 4 of 4 takes he stood 0.00 s.

**Contortions.** `tools/oval3d/dump_clip_joints.gd` and `tools/oval3d/joint_audit.py` split every
joint's rotation into twist and bend, and a hinge's bend into the part on the hinge and the part off
it. The Epic GASP clips are the baseline: their elbows stay within ~32 deg off the hinge. The worst
broadcast-made clips:

| Clip | Joint | Fault |
| --- | --- | --- |
| umpire_bounce_01 | Right elbow | 21 deg backwards past straight |
| umpire_bounce_01 | Left elbow | 63 deg off its hinge |
| kick_on_run_02_run, ground_ball_run_01, run_bounce_01, ground_ball_01, dont_argue_01 | Elbows | 40-59 deg off the hinge |
| spoil_rance_01 | Ankle | 79 deg |

`ClipLimits` holds the broadcast clips inside a real body's limits as a match loads them:

- Elbow: 35 deg off the hinge and 10 deg past straight.
- Knee: 20 deg off the hinge and 5 deg past straight.
- Wrist: 70 deg of twist and 70 deg of bend.
- Ankle and neck: limited the same way.

The GASP clips are untouched. After the limits, the worst broadcast joint is 37 deg (the audit's own
rounding), against 63. `tools/oval3d/pose_stills.gd` renders any clip frame with and without the
limits to check them.
