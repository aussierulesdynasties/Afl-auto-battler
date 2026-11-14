# How AFL Live 2004 animated its footballers, and what we take from it

_Study of 2026-11-14. Director: "i dont want to use their anims, i want you to learn how they did
it though, so we can improve it". None of their motion data is used or shipped. This note records
how their system is organised and measures its data; our clips still come from owned or licensed
sources ([pipeline proposal §9](ANIMATION_PIPELINE_PROPOSAL.md))._

## What was looked at

- `GRAPHICS/ACTOR/ANIMATIONS/ANIMS_TEN_BIT.FLAT` (4.8 MB): every animation in one binary bank.
- `GRAPHICS/ACTOR/MESHES/PLAYER_LOD_1.DFF`: the player model (RenderWare), for the skeleton.
- `AFL2004.exe`: its text strings, which list 310 clip names and the animation class names.

## The data (measured)

| Fact | Value | How measured |
|---|---|---|
| Clips | 310 (299 full body, 9 upper body, 2 head) | clip paths in the program |
| Skeleton | 31 bones | the model's bone table (RenderWare HAnim) |
| Key rate | 25 a second (keys 0.04 s apart) | key times in the bank |
| Bone keys | ~363,000, 12 bytes each: link to the previous key, time, rotation | record scan |
| Rotation | 32 bits: three 10-bit parts, the fourth rebuilt (the "ten bit" in the name) | 99.8% of keys drop the same part; all but 10 of 363k fit a unit rotation |
| Rotation precision | ~0.16 degrees a step | 10 bits over ±0.71 |
| Root (hips) | full floats: position, rotation and time each frame | 32-byte records |
| Key thinning | a bone that holds still gets no key: frames carry 30, 23 or fewer bone keys | keys per time step |
| Longest clip | 12.3 s | largest key time |

Their size problem was memory on a 2004 console, so they stored rotations only (bone lengths never
change), packed small, and left out keys for still bones. Our footballers are pre-rendered sprites
(ARD-M8-007), so none of this packing carries over. What carries over is how the motion was organised.

## How the moves were organised

| Family | Clips | Pattern |
|---|---|---|
| Tackles | 75 | 5 approach directions (front, front-left, left, rear, rear-left) × tackler and tackled player × the outcome |
| Getting around | 64 | stand, walk, jog, run, sprint, side-step, walk back, run back, each with and without the ball |
| Marks | 38 | 7 specky takes, each with a dropped version; chest, diving, leading, turning 180 |
| Ruck and contests | 30 | tap left, tap behind, tap forward, grab, jostle and wrestle with the opponent |
| Idle, reactions, ceremony | 24 | 8 idle variants, fist pump, head shake, disappointment, coin toss, bench |
| Umpires | 23 | every signal, bounce, throw-up, ball-up |
| Kicks | 14 | quick, medium, long, torpedo, snap, banana, soccer, set shot run-up loop |
| Gathers | 12 | stand and run, with turns of 90 and 180 |
| Handballs | 10 | quick, long, fake |
| Bumps and spoils | 10 | bump, fall front, back, side; punch the ball away |
| Upper body and head layers | 7 | reach for the ball high or chest-high, square or side-on; twist the trunk; turn the head |

Four ideas run through the whole list:

1. **A move is named by where it starts and where it ends.** 91 clips read `start_move_end`:
   `stand_k_long_stand`, `run_k_long_run`, `run_gather_run`, `stand_pickup_t90_run`. A kick from
   a standstill and a kick on the run are different clips, so legs never pop from one gait to another.
2. **Turns are animated, not snapped.** 32 clips turn the player 30, 90 or 180 degrees (`run_t180_run`,
   `stand_t90_jog`). The body plants and turns; it never just spins round.
3. **The tackle is a pair, and it branches on the result.** Both players start together (`_start`),
   then play the result the match decided: tackled and caught, shrugged off, ball spilled, disposed of
   in the tackle, taken to ground, then the recovery. The animation shows what the match engine decided.
4. **Every mark has a miss.** `m_spec_a_01` to `07` and `m_spec_a_miss_01` to `06`; `run_m_chest_run`
   and `run_m_chest_miss_run`. A dropped mark looks like a drop.

Smaller ideas: the hands reach for the ball as an upper-body layer while the legs keep running
(`receive_high90`); the head turns towards the ball as its own layer; 8 idle variants stop a stoppage
looking like clones; locomotion clips exist both with the ball and without.

## What we can do better, on our sprite pipeline

Mapped onto the open [animation pipeline proposal](ANIMATION_PIPELINE_PROPOSAL.md) (its §12 decisions
are still the director's):

| Their idea | Where we are | Improvement for us |
|---|---|---|
| Start and end state in every move | `kick`, `snap`, `gather` are standing moves; `gather_run` is proposed (§8) | Give every one-shot strip a run version: `run_kick_run`, `run_handball_run`, `run_gather_run`. The proposed `gather_run` is the first; the same marker contract (foot plant, contact) covers the rest |
| Animated turns | facing snaps to the nearest rendered direction plus a mirror | A 90 and a 180 turn strip for stand and run; the scene plays it when a player's direction changes that much |
| Tackle branches on the result | one tackle pair proposed (§8) | Render the pair's start once, then one ending per tackle result MatchSim already decides (holding the ball, held to a ball-up, a fend-off, stepped out of it: `scripts/sim/MatchSim.gd`). Bible principle 3: the game shows what each decision led to |
| A miss for every mark | `mark_f`, `mark_s` only | A dropped version of each mark, for the marking contests MatchSim already spills to the ground |
| Run back and side-step | `jog`, `walk`, `carry` | A backpedal for defenders tracking the ball's flight and a side-step for the tackles MatchSim already marks as stepped out of |
| Idle variety | `ready`, `ready_b` | 3-4 ready variants with a different start frame per player, for a believable broadcast stoppage (row 6.38) |
| 25 keys a second | strips of 4-8 frames | More frames only where the eye reads contact (the ball drop, the hands at the gather); markers stay the source of truth, as §3 proposes |
| Upper-body and head layers | not possible on one sprite | Not worth it on sprites; the run versions above cover the case where it shows most |

Where we can beat them: their motion is 2004 motion capture with one skeleton for every player. Ours
can have three body sizes (§1) and right- and left-footers kept apart when mirroring (§5), neither of
which their list shows.
