# The 3D view: asset and animation plan

_Step 3 of [the 3D view plan](3D_VIEW_PLAN.md) (TODO row 203, Director Bible 2.78). Written 2026-11-16, ahead of
step 2's body choice, on the director's word: "may as well make the /plan now". Where an answer depends on the
body (row 202, 2d), it says so; nothing here is made until that body is chosen. Chosen 2026-11-17: MetaHuman (rule 2.85)._

## What drives the list

Every animation exists because the sim asks for it. MatchDirector turns MatchSim's event log into these moments
(`scripts/ui/match/MatchDirector.gd`): kick, handball, mark, pass, receive, inside 50, rebound, clanger, goal,
behind, tackle, pressure, smother, spoil, pack, ball-up, throw-in, free, fifty, last disposal, out on the full,
kick-in, sub, injury, quarter, with outcomes inside them (ruck tap, ground ball, fumble, spill, bounce, set shot).
A move the sim never produces is not made. A sim event with no animation is a gap and goes on this list.

## How every item is made and checked

1. **Source** (in this order of preference):
   - his Rokoko takes, of himself or of real footage studied frame by frame: the AFL moves no library has;
   - a library whose licence allows a Godot game sold on itch and Android (CC0, CC BY, Mixamo's terms);
   - made by us in Blender: poses, fixes, blends, never a whole move invented from nothing.

   **The licence is read before a source is proposed** (director, 2026-11-17: "make a rule you have to check
   fucking licenses before sending me to download any fucking asset"). On the source's own page: allowed in a
   Godot game, sold commercially, on itch and Android, attribution or not, what is forbidden, and the URL read.
   Engine-locked (Unreal-only, Unity-only), non-commercial, editorial-only or unread means not proposed.
2. **Retarget** onto the chosen body's rig (2d: MetaHuman, rule 2.85), names unchanged, one GLB action per clip.
3. **Contact pass**: feet pinned while planted, hands on the ball, mesh clip check on every frame (the tools of
   3d view 2: contact3.py, meshlow.py, trim.py).
4. **Markers**: foot plants, ball contact, release, mark secured, tackle contact, so the clip can be warped to
   MatchSim's spot and moment (study §2.1).
5. **Self-check before he sees it**: every frame from the game camera and the front. Humanoid, every pose possible,
   ball held and never hovering, no limb in the body or through the jumper, no foot sliding.
6. **Shown to him as video at game speed** (mp4 or GIF, never stills), in a real match where it plays.

## The inventory

"Have" names what exists today. Order: **A** the proof passage (rows 197 and 198), **B** everything a normal match
needs, **C** ceremony, reactions and the 3D scenes. Counts are estimates to plan with.

### Bodies and the things they wear

| Item | Needed for | Have | Source | Order |
|---|---|---|---|---|
| The body, with 2-3 builds (key position, midfielder, small) | every player | MPFB average (placeholder) | MetaHuman (2.85) | A |
| Heads and faces that vary | "they look like clones" | one head | MetaHuman (2.85) | B |
| Hair | identity | 31 styles (rule 2.77, passed) | kept; refit to the chosen head | A |
| Guernseys, shorts, socks, 18+ clubs and clash | every match | passed on MPFB (2.75) | refit to the chosen body | A |
| Boots | every player | one boot | refit | A |
| Umpires: field (passed, 2.75), boundary, goal (coat, hat, flags) | stoppages, scores | field umpire | refit; boundary and goal umpire kits made | A field, B the rest |
| The ball (Sherrin) | every touch | ball mesh | kept | A |
| Trainers, runners, water carriers | injuries, breaks | none | made on the same body | C |

### Getting around (everyone, every second of the match)

| Item | Have | Source | Order |
|---|---|---|---|
| Stand idle loop and 6-12 idle breaks, two moods | neutral and relaxed sets (36 clips, GASP) | Rokoko | A |
| Walk, jog, run, sprint loops, without and with the ball | mocap jog, run, carry loops (#1689, approved) | his Rokoko | A |
| Backpedal and side-step loops | none | Rokoko | A |
| Starts, stops, plant-and-turn 90 and 180 at walk, jog and run | stand turns 45-180 (16 clips) | Rokoko for the running turns | A |
| Sidestep a man at pace | 12 avoid clips (GASP) | Rokoko | B |
| Bounce on the run | run_bounce_01 | kept on MPFB, else re-made | B |

### The ball: actions and their failures

Each success has its failure (study §2.5). Left-footers use a mirror that swaps the kicking leg.

| Sim event | Success clips | Failure clips | Have | Order |
|---|---|---|---|---|
| kick (pass, inside 50, rebound) | drop punt from a run and from a stand, long and short | shank, kicked off the side | kick_on_run 01-04, drop_punt_02, drop_punt_ablett_side, mark_and_kick_jog_01 | A |
| set shot (goal, behind) | walk back, run-up, drop punt | miss wide | none | B |
| snap, banana, torpedo, grubber, soccer off the ground | one each | | snap_ablett_01, banana_ablett_01-02, dribble_ablett_01 | B |
| handball | from a stand, on the run, receiving one | fumbled | handball_on_run_01 | A |
| ground ball, gather | standing, running, turning 90 | knock-on, fumble | ground_ball_01, _04, _run_01, _run_grimes_01 | A |
| mark | chest, overhead, on the lead, intercept | dropped chest, dropped overhead | chest_mark_02, overhead_mark_01, dive_finals_01 | A |
| pack (contested mark) | pack of 3-4 going up together, one marks | spilled to the ground | none | A |
| speccy | a ride on a back, front and side | spilled speccy | none | C |
| smother | arms over a kick | | none | B |
| spoil | punched from behind | | spoil_rance_01 | B |
| kick-in | from the square, play on and short | | none | B |

### Contests: pairs that branch on the result

| Sim event | Pairs and branches | Have | Order |
|---|---|---|---|
| tackle | front, side, behind × lead foot; branches: holding the ball, held to a ball-up, ball knocked loose, fended off | 12 tackle clips (6 pairs: behind, left, right; GASP) | A |
| pressure | chase, arms out, a corralling run | none | B |
| bump, shepherd | bump, shepherd for a teammate | bump_contest_01, bump_finals_01 | B |
| ruck (centre bounce, ball-up, throw-in) | run-up and leap, tap forward, to either side, grab, jostle before the bounce | ruck_jump_01 | A |
| stoppage set-up | mids jostling at the drop, wrestles, blocks | none | A |
| get up | from a tackle, roll left and right | getup_roll_l, _r (GASP) | A |

### Umpires and stoppages

| Item | Have | Order |
|---|---|---|
| Field umpire: run, bounce, ball-up, every signal (holding the ball, free, 50, play on, advantage, ball-up call) | umpire_bounce_01, played at every centre bounce (the ball from his hands to the turf on the director's bounce); its lift of the ball stands in for the ball-up throw | A bounce, B the rest |
| Boundary umpire: run the line, throw-in over the head, out on the full signal | none (he goes to the line and holds the ball, his back to the play; the bounce clip's lift stands in for the throw) | B |
| Goal umpire: goal (two fingers, two flags), behind (one), touched, flag waving | none | B |
| Man on the mark (arms up, standing still), walk back, protected zone | none | B |

### Breaks, the bench and reactions

| Item | Have | Order |
|---|---|---|
| Interchange: run to the bench, sit, run out | 14 bench clips (GASP) | B |
| Quarter breaks: walk to the huddle, the huddle, three-quarter-time circle | none | C |
| After a goal: celebrate, hug, point to the passer; the scored-on side's dejection | gesture_come_on_in, gesture_agree_v2, gesture_disagree_v2 (GASP), dont_argue_01 | B |
| Injury: down, holding a limb, helped off | 14 poses (GASP) | C |

### The world (step 2 decides the look; listed so the plan is whole)

| Item | Decided by | Have |
|---|---|---|
| Sky, light, tone, weather, time of day | 2a (rules 2.80 sky light, 2.81 TV tone; night and wet open) | in progress |
| Ground: turf, lines, goal and behind posts, padding | 2a/2b | turf (#1658) |
| Stadium: stands, roof, light towers, scoreboard, fence, signage | 2b | one raked ring (placeholder) |
| Crowd, cheer squads, banners, reactions | 2c | shader crowd (placeholder) |
| Cameras: broadcast wing, high whole ground, behind the goals, close-ups | 2e | broadcast and high |

### The 3D scenes that replace the vignettes (rule 2.76)

Each is a scene on the same bodies and stadium. Order C, after full-match coverage.

| Vignette today | 3D scene needs |
|---|---|
| Broadcast moments: speccy front, side, defensive; goal line; boundary snap; after the siren | the clips above plus a close camera |
| Stoppage and decision vignettes | stoppage set-ups, a held still at the gate |
| Pre-match: warm-up, huddle, run-through | warm-up drills, the huddle, the banner and the run-through |
| Farewell: guard of honour, chaired off | two lines clapping, a man carried on shoulders |
| Award winner (Brownlow and others) | a room, a walk to the stage, a speech |
| Media conference | a room, a seated coach, journalists |

## The 123 clips we have

| Group | Clips | If MPFB stays | If another body |
|---|---|---|---|
| AFL actions (kicks, marks, gathers, handball, ruck, bumps, spoil, bounce, umpire bounce) | 29 | keep the ones he passed; re-make the rest to the checks above | re-target from the same takes, redo the contact pass |
| Tackle pairs (GASP) | 12 | placeholder until re-made from Rokoko pair takes | re-made from Rokoko pair takes |
| Stand idles, breaks and turns (GASP) | 36 | placeholder until re-made | re-made |
| Sidesteps, bench, gestures, get-ups (GASP) | 31 | placeholder until re-made | re-made |
| Held poses: injured, on the ground, rolling (GASP) | 14 | placeholder until re-made (order C) | re-made |
| Placeholder loops in the game (jog, idle, carry; #1689) | 3 | keep | re-target from his takes |

The body is MetaHuman (2.85), so the "If another body" column applies. Cut today: nothing. A clip no sim event calls stays out of the game build until its row needs it.

## The licence question

93 of the 123 clips came from Epic's Game Animation Sample (GASP): the 36 stand idles and turns, the 31 sidesteps,
bench clips, gestures and get-ups, the 14 held poses, and the 12 tackle clips that play in the game now. Epic
licenses GASP for Unreal Engine projects only, and our game is Godot
([CG Channel on the release](https://www.cgchannel.com/2024/06/get-500-free-game-ready-animations-for-use-in-unreal-engine);
[Epic forum](https://forums.unrealengine.com/t/what-can-i-do-with-game-animation-sample-that-recently-was-at-100-off/1903980)).
Using them outside Unreal at all is outside that licence, so they are placeholders until replaced.

### Replacements found (licences read 2026-11-17)

| Source | Licence, read on its own page | Cost |
|---|---|---|
| Mixamo ([FAQ](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html)) | "royalty free for personal, commercial, and non-profit projects including... video games"; no engine named; needs an Adobe ID | free |
| CMU mocap ([home](http://mocap.cs.cmu.edu/), [FAQ](http://mocap.cs.cmu.edu/faqs.php)) | may be included in commercially sold products; no reselling the data itself | free |
| Quaternius Universal Animation Library 1 and 2 ([1](https://quaternius.com/packs/universalanimationlibrary.html), [2](https://quaternius.com/packs/universalanimationlibrary2.html)) | CC0; Godot listed | Standard free, Pro $9.99 |
| Tomasi Studios football mocap ([RenderHub](https://www.renderhub.com/tomasi-studios/18-football-motion-capture-animations-for-blender3d)) | Extended Use: "computer/web/mobile games" allowed ([terms](https://www.renderhub.com/info/3d-content-licensing)) | $15.50 |

The bodies (2d's choice) are licensed for us too. Our MPFB average body: MakeHuman's core assets are CC0, "no restrictions" and no credit needed
([licence page](https://static.makehumancommunity.org/about/license.html)). The MetaHuman body:
Epic's [licence page](https://www.metahuman.com/license?lang=en-US), read 2026-11-17, says "MetaHumans can be used
with any engine or creative software"; outside Unreal they are Non-Engine Products, so a Godot game pays no royalty;
free under US$1M a year in revenue, an Unreal seat licence above it; never used to train AI. The raw MetaHuman files may leave our hands only inside a built game, so they live in a private
repo, never this public one ([EPIC_ASSETS.md](EPIC_ASSETS.md), 2026-11-23). Unreal's own mannequins
(Manny and Quinn, which GASP plays on) are Unreal-only and were never in our game.

| GASP group | Replacement (Mixamo clip names, searched on mixamo.com) | Covered |
|---|---|---|
| Stand idles and breaks | Standing Idle, Weight Shift Idle, Breathing Idle, Neutral Idle, Happy Idle, looking-around idles (507 idle results) | yes |
| Turns in place | 45, 90, 135 and 180 degree turns each way, quick 90 and 180, walking turns 90 and 180 | yes |
| Sidesteps (12) | walking and running strafes left and right, Soccer Strafe, boxing dodges | partly: an evasive step past a man at pace is AFL-specific, his Rokoko |
| Bench (14) | Sitting Down, seated idles (elbows on knees, leaning forward), Sitting To Standing, clapping and cheering while seated | yes |
| Gestures (3) | Agreeing Yes, Celebrating After A Win, fist pumps, Rallying The Crowd | agree yes; disagree and come-on to find |
| Get-ups (2) | Getting Up From Back, Getting Up From Stomach, Getting Up From Being Knocked Down | yes |
| Held poses (14) | Injured Holding Hurt Leg Idle, Hurt Ground Idle From A Soccer Fall, Knocked Out Falling To Back and To Stomach, Sitting Against A Wall Dazed | yes (holds taken from these) |
| Tackle pairs (12) | Running To Tackle, Receiving A Football While Getting Tackled To The Ground, Falling Flat On Face From A Hit To The Back While Running, Getting Feet Swept Out | partly: one-man clips, not one take of two men; front, side and lead-foot variants missing. CMU's two-person takes are pulls and a stumble, no tackle |

The tackle pairs are the gap: a real tackle needs both men in one take, which his Rokoko pair takes give.

### Downloaded 2026-11-17

57 Mixamo clips are in `Desktop/footy assets/mixamo/`, saved as FBX Binary, Without Skin, 30 fps, no keyframe
reduction. Each one was imported in Blender and every file opened with the 65-bone Mixamo rig and an action.

| GASP group | Downloaded (Mixamo title) |
|---|---|
| Stand idles and breaks | Standing Idle, Neutral Idle, Happy Idle, Breathing Idle, Unarmed Idle, Weight Shift, Looking Around |
| Turns | Left Turn, Right Turn, Left Turn 45, Left Turn 90, Right Turn 90, Turn Left 45 Degrees, Turning Right 45 Degrees, Turning Right, Standing Turn Left 90, Standing Turn Right 90, Quick 180 Turn, Walking Turn 180 |
| Sidesteps | Left Strafe, Right Strafe, Walk Strafe Left, Walk Strafe Right, Jog Strafe Left, Jog Strafe Right, Dodging Right |
| Bench | Sitting Idle, Stand To Sit, Sit To Stand, Standing Up, Sitting Clap, Cheering While Sitting, Sitting Fist Pump, Sitting Victory |
| Gestures and reactions | Agreeing, Shaking Head No, Annoyed Head Shake, Beckoning (come on), Dismissing Gesture, Standing Arguing, Rallying, Cheering, Clapping, Victory, Waving |
| Get-ups | Getting Up |
| Held poses and falls | Injured Idle, Injured Hurting Idle, Injured Stumble Idle, Knocked Out, Sitting Dazed, Fallen Idle, Fall Flat, Falling Flat Impact, Falling Down, Sweep Fall |
| Tackles (one man) | Defender (running to tackle) |

Not on Mixamo under the searched titles: Receiving A Football While Getting Tackled To The Ground and Running Tackle.
Those tackles come from his Rokoko pair takes.

## Order of work (step 4 follows it)

Director, 2026-11-17, asked this order directly: he chose "A, then B, then C".

1. 2d chose the body, MetaHuman (2.85); heads, hair, kits and boots refit to it.
2. **A**: getting around, the proof passage's actions (centre bounce, ruck tap, gather, handball, kick, contested
   mark), the tackle pairs, the field umpire. Row 198 makes them; row 197 plays them; phone check.
3. **B**: every other sim event, its failures, boundary and goal umpires, the bench, reactions.
4. **C**: injuries, breaks, speckies, then the 3D scenes that replace the vignettes.
