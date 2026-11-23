# The 3D match day trailer: storyboard and production plan

_Started 2026-11-22 by the thread "Storyboard the 3D trailer". Planning only._

The director, 2026-11-22: "I also want a trailer for the 3d mode, complete with fly throughs of the
major stadiums and some exciting player animations (a goal on the run and celebration, a specky, a
run down tackle), crowd reactions, some shots of the cities/backgrounds"; a Legacy section where
"the screen could wipe between different decades showing the same scene in different eras
(something simple that will show the guernseys and MCG perhaps)"; "i also wanna see some Club Forge
stuff in the trailer"; "including post-effects and graphics and sounds, and music". And: "I dont
want work to begin before the 3d stuff is polished and release quality".

## What this page is, and what it is not

- **A plan, not a start.** No footage is captured, no tool installed, no music made, no title card
  rendered and no cut assembled until the 3D 1.0 release bar ([3D_1_0_RELEASE.md](3D_1_0_RELEASE.md),
  PR #2033) is passed and the director says go. This follows his word above and the trailer gate
  in the Director Bible (rule 98, ARD-M8-010): before his go, plan only.
- **Today nothing in the shot list can be filmed to standard.** On 2026-11-22 no 1.0 item is
  passed. Each shot below names the 1.0 work it waits on.
- **Trailer honesty (Director Bible rule 39).** Every frame is the real game: a seeded match or
  screen the game actually produces, the real match engine deciding what happens. No staged
  outcomes the game cannot produce, no debug UI, no placeholder art, audio only if cleared. The
  in-engine trailer tools below only choose the camera, the speed and which real moment to film.
- **Tools are free (rules 98 and 111).** Free software only, open source preferred; paid software,
  subscriptions and paid music need his explicit approval first.

## Limits, stated up front

1. **The speccy has no animation yet.** No two-man speccy clip exists (animation thread, 2026-11-23:
   it needs new motion copied from broadcast footage). The shot waits on that clip being made,
   played in matches, and the engine producing a speccy we can find in a seeded match.
2. **Goal celebrations do not exist yet.** "A few gestures only", and nobody owns it (release page,
   Animations). The goal-on-the-run shot waits on it.
3. **A run-down tackle from behind is not built.** Tackles play (12 two-man clips), but a chase that
   ends in a tackle from behind with the crowd's "BALL!" is an open animation ask.
4. **The MCG only exists as it is today.** A real 1990s MCG had the old Southern Stand (the Great
   Southern Stand opened in 1992) and the old Ponsford, Members' and Olympic stands (rebuilt
   2003-2006). Wiping from 1990 to 2026 at today's MCG would put 1990 guernseys in a 2006 stadium.
   Which way to go is the director's call (decision card in the thread; options under Act 3).
5. **Most Club Forge home grounds have no 3D model.** Of the 53 Forge places, only the ones whose
   ground is also a 3D ground (Bellerive, York Park, North Hobart, Norwood, Traeger Park, Cazaly's,
   Marrara/TIO) can be filmed at home. The Forge shots use one of those, or the Forge club away at
   a big ground.
6. **Faces are not in a match yet.** Close-ups (ruck at the bounce, the celebration) wait on the
   faces work reaching matches.
7. **Music is not chosen.** Options and their terms are below; the pick is his.
8. **Sound is judged by ears, his.** A machine can check levels, peaks and sync; it cannot say the
   mix sounds right. No audio is ever played aloud on his PC by us.
9. **Real players and stadium names in an advert.** A trailer is advertising, which is a different
   use from the game itself. Real players' names and faces, club names and naming-rights stadium
   names (Marvel, Optus, GMHBA, People First, ENGIE) carry more risk there than in play. No AFL,
   club or broadcaster logos appear in the trailer. How far to lean on real names is his call;
   this plan flags it and does not decide it.

## Shape

- **Main cut:** about 1 min 50 s, 16:9, 3840 x 2160 at 60 fps master, exported 4K and 1080p for
  YouTube and the itch.io page.
- **Phone cut:** about 30 s, 9:16 portrait (the game is portrait first): the 3D picture as the game
  shows it on a phone, for Shorts, TikTok and Reels.
- **Audience:** AFL fans who play management games; the hook is "your club, every great ground, real
  footy you can see".
- **Arc:** a city wakes to match day, the grounds, the game itself, the history (Legacy), your own
  club (Club Forge), the big finish under lights.

## Shot list

Times are the main cut. "Waits on" names the 1.0 area from [3D_1_0_RELEASE.md](3D_1_0_RELEASE.md):
Grounds, Players (incl. faces), Animations, Presentation, plus Lighting (night lights, sun, sky).

### Act 1: Match day in the city (0:00-0:12)

| # | Time | Shot | Camera and tool | Sound | Waits on |
|---|---|---|---|---|---|
| 1 | 0:00-0:05 | Black. Then dawn over Melbourne: the CBD skyline, the Yarra, the MCG's light towers catching first sun | Slow push across the skyline toward the MCG (flight path camera) | Low city air, then the crowd murmur fades up | Grounds: MCG surrounds past 2 km (horizon empty today), Lighting: dawn sky |
| 2 | 0:05-0:09 | Yarra Park, fans walking in under the elms toward the MCG | Low drone glide over the park to the gates | Murmur builds | Grounds: Yarra Park real (OSM today); Presentation: fans walking in is an after-1.0 idea (game hub), so this shot is the park only unless that is built |
| 3 | 0:09-0:12 | Title card 1: "Every great ground." | Text over shot 2's last frames | First music hit | Title cards (below) |

### Act 2: The grounds (0:12-0:36)

Fly-throughs of the big grounds, each about 4 s, each ending on a lower-third with the ground's name
in the scoreboard face.

| # | Time | Shot | Camera and tool | Waits on |
|---|---|---|---|---|
| 4 | 0:12-0:16 | Adelaide Oval from the Riverbank footbridge, over the Torrens, the petal roofs, St Peter's | Flight path from the footbridge, rising over the western stand | Grounds: Adelaide rebuild and surrounds (#2010, #2015) |
| 5 | 0:16-0:20 | Optus Stadium at dusk across the Swan, the bronze facade, the Matagarup bridge | Wide arc from the river | Grounds: Optus shape and surrounds (shape still wrong 2026-11-23), Lighting: dusk |
| 6 | 0:20-0:24 | The Gabba under lights, Woolloongabba around it | Down through the lights to the centre square | Grounds: Gabba (#2020), Lighting: Gabba night towers (MCG only today) |
| 7 | 0:24-0:27 | Marvel Stadium, roof closing over Docklands | Locked high shot, roof shut timed to the cut | Grounds: Marvel (#2011) |
| 8 | 0:27-0:30 | SCG, Moore Park, the members' pavilion | Low past the pavilion onto the ground | Grounds: SCG (#2017) |
| 9 | 0:30-0:33 | Bellerive with kunanyi behind, Derwent glittering | Across the river toward the ground | Grounds: Bellerive (#2018) |
| 10 | 0:33-0:36 | Title card 2: "Real footy." Cut to the MCG full house, wide from the top deck | Static, crowd alive | Grounds: MCG; Presentation: crowd |

### Act 3: The game (0:36-1:08)

Every moment here comes from a seeded match the engine played, found by the event finder (tools,
below). No result is staged.

| # | Time | Shot | Camera and tool | Sound | Waits on |
|---|---|---|---|---|---|
| 11 | 0:36-0:40 | The banner run-through: the team bursts through, the paper tears | Ground-level in front of the banner | The roar as the home side runs out (#2012) | Presentation: banner run-through (#2004) |
| 12 | 0:40-0:43 | The first bounce, ruckmen go up, close on the faces | Ruck close-up camera (exists), slowed to half speed | Umpire's whistle, a hush, the thud | Players: faces in a match (ruckmen head to knees); Animations: ruck contest |
| 13 | 0:43-0:49 | **Goal on the run**: a mid breaks from the pack, bounces, kicks from 40 m on the run, it sails through | Main AFL camera live, then the goal replay from behind the goals at half speed | Crowd rises with the run, roar on the goal | Animations: run, bounce, kick on the run; Presentation: goal replay (#2022) |
| 14 | 0:49-0:52 | **The celebration**: teammates mob him, he points to the crowd | Tight shot, low | Roar holds | Animations: celebrations (nobody owns yet); Players: faces |
| 15 | 0:52-0:53 | The goal kicker's TV stat card over the picture | As the game shows it (#1990) | | Presentation: stat card |
| 16 | 0:53-0:58 | **Run-down tackle**: a forward breaks clear, a defender chases him 30 m, tackles from behind, the umpire pays holding the ball | Wide, then the close tackle cut (#1985) | Building crowd, then "BALL!", the whistle, the roar | Animations: chase-down from behind (not built); Presentation: close tackle cut |
| 17 | 0:58-1:03 | **The speccy**: a forward climbs over a pack in the goal square and holds it | Replay camera, quarter speed (slow motion) | The crowd's gasp, then the eruption | Animations: speccy (no clip yet) |
| 18 | 1:03-1:05 | Crowd reactions: the cheer squad up on its feet, hands on heads at the other end | Crowd close shot (cheer squad bays) | Roar | Presentation: crowd reactions (built); Grounds: crowd on the ground's seats |
| 19 | 1:05-1:08 | Rain at night: a pack spills the slippery ball, the lights catch the rain | Main camera, rain on | Rain, crowd | Presentation: wet matches (on main), Lighting: night |

### Act 4: Legacy mode (1:08-1:26)

| # | Time | Shot | Camera and tool | Sound | Waits on |
|---|---|---|---|---|---|
| 20 | 1:08-1:10 | Title card 3: "Start in 1990." | Text on black | Music drops to a single line | |
| 21 | 1:10-1:22 | **The decade wipe.** One scene, one locked camera: two clubs lined up at the centre bounce at the MCG. The picture wipes left to right through 1990, 2000, 2010 and 2026, each about 3 s: the guernseys of that year, the scoreboard's ground name and year, the crowd's clothes | Locked camera; the same seed in four Legacy starts; the wipe edge follows a goalpost or a light tower so it reads as one place in four times | Crowd bed only; one siren blast on the last wipe | Players: Legacy guernseys on the MetaHuman body (1990-2025 designs exist, not yet checked on the new body); Grounds: the MCG of each era (see below) |
| 22 | 1:22-1:26 | The old grounds: two 2 s glimpses, Waverley Park in the 1990s and Victoria Park | Fly-in on each | | Grounds: the 24 Legacy grounds (no owner for Waverley Park and Victoria Park yet) |

**The MCG through the decades (his call).** Options:

- **A. Build the MCG of each era.** 1990s (old Southern Stand before 1992; old Ponsford, Members'
  and Olympic stands) and the early 2000s (Great Southern Stand, old northern stands); 2006 on is
  today's model with smaller changes. A real modelling job to the MCG standard, and it also puts
  the right MCG under Legacy matches played there before 2006, which today show the modern one.
- **B. Only the decades today's MCG fits.** 2006, 2016, 2026. No new model; no 1990s.
- **C. Each era at its own ground.** The same moment at Waverley Park (1990s), Docklands as Colonial
  Stadium (2000s), the MCG (2010s, 2020s). Less of "the same scene".

### Act 5: Club Forge (1:26-1:40)

Club Forge is the main menu's creative space: create a club from a real football place (its name,
ground, colours and guernsey, painted part by part) and create a player prospect (position, height,
play style, foot, number and look) who enters a new career's draft. Every mode hosts both.

| # | Time | Shot | Camera and tool | Sound | Waits on |
|---|---|---|---|---|---|
| 23 | 1:26-1:29 | Title card 4: "Build your own club." | | Music builds again | |
| 24 | 1:29-1:33 | The Club Forge screen on a phone: a colour picked, the guernsey's body painted, then the pattern; the crest and name fill in | Screen capture of the real screen (portrait), real taps | UI taps (game's own) | Club Forge UI as it ships |
| 25 | 1:33-1:35 | The Forge prospect turns on the 3D preview, then his hair cut changes | The PlayerPreview turntable | | Players: MetaHuman body and Forge hair (#1976) |
| 26 | 1:35-1:40 | Match cut: the same guernsey runs out in 3D, the Forge club through the banner at its home ground (a Forge place with a 3D ground, e.g. Launceston at York Park), then the prospect kicks a goal | Banner camera, then main camera | Roar | Players: Forge guernsey drawn on the MetaHuman body (drawn by the shader from its design, not checked against the standard yet); Grounds: that ground finished |

### Act 6: The finish (1:40-1:50)

| # | Time | Shot | Camera and tool | Sound | Waits on |
|---|---|---|---|---|---|
| 27 | 1:40-1:45 | Night at the MCG, last seconds of a close match, a set shot after the siren from behind the kicker, the ball in the air, cut to black before it lands | Set shot camera from behind (on main) | The siren (#2012), silence, one heartbeat of crowd, cut | Lighting: MCG night (#1996); Presentation: set shot camera |
| 28 | 1:45-1:50 | End card: game name, "3D match day", where to get it, date | Static | Final music note, then silence | Title cards |

**Phone cut (30 s):** shots 1 (2 s), 11, 13, 16, 17, 21 (two eras), 26, 28, reframed to 9:16 the way
the game draws the TV picture on a phone, end card in portrait.

## How it gets made (after his go)

### In-engine trailer tools (to build in `tools/trailer/`)

1. **Offline capture with Godot's Movie Maker** (built into Godot, MIT). `--write-movie` with
   `--fixed-fps` renders every frame at full quality regardless of how slow the PC runs, with
   perfect frame pacing, at a resolution above the screen's. Output as PNG frames plus a WAV of the
   game's sound, or OGV. Rendered on his PC's GPU (RTX 4070 SUPER), never in the cloud: the cloud's
   software GPU shades materials wrongly (project rule).
2. **A shot file per shot** (`tools/trailer/shots/<n>.json`): ground, date and era, weather, time
   of day, seed, which moment, camera, speed, length. A shot re-renders the same every time.
3. **Flight path camera** for the fly-throughs: a Path3D with eased speed and look-at targets,
   keyframed in the ground inspector (tools/inspect, which already flies every ground). The paths
   are checked against Google Earth views of the same spots, like the grounds are.
4. **The event finder.** Plays seeded matches headless and lists the moments the engine produced:
   goals on the run from 35 m+, chase-down tackles paid as holding the ball, contested marks over a
   pack in the forward 50. Builds on the cameras prototype `scan_marks.gd`
   (project files, cameras-2e/prototype). The trailer picks from what the engine really did.
5. **Slow motion.** Lower `Engine.time_scale` while Movie Maker keeps its fixed frame rate, so a
   quarter-speed replay gets four real frames for each one, not stretched frames.
6. **Motion blur.** Render the fast shots at 240 fps and blend every four frames down to 60 (the
   method Godot's own docs give for Movie Maker motion blur).
7. **Clean UI layers.** Each shot renders twice where it shows game graphics: with and without the
   score bug and stat card, so the edit can choose. Never a debug overlay.
8. **The decade wipe.** The same seed in four Legacy starts (1990, 2000, 2010, 2026), the same
   locked camera, rendered as four full shots; the wipe is made in the edit along a line in the
   picture (a goalpost or light tower), with a short soft edge.

### Edit, post-effects and graphics

- **Edit:** Kdenlive (GPL, free) for the cut; Blender (GPL, free) for the title animation and any
  compositing. DaVinci Resolve's free version is free for commercial work (Blackmagic support,
  forum, 2018 and 2022) but not open source, so it is the second choice.
- **Encode:** FFmpeg (LGPL/GPL).
- **Post-effects:** a light grade matched to the broadcast colour the turf already uses (#2014); a
  touch of depth of field on close-ups (Godot's camera attributes); motion blur as above; a very
  light grain. No lens flares or effects the game does not show.
- **Title cards and lower-thirds:** the game's own faces: ARD Signwriter (drawn for this game, owned
  by the project, `assets/fonts/ARDSignwriter-LICENSE.txt`) for titles, Barlow and Barlow Condensed
  (SIL Open Font Licence, `assets/fonts/*-OFL.txt`) for small text. Both cleared for a trailer. The
  cards use the editorial dark look of the game. Copy: short and in plain footy words; final title
  copy goes to him.
- **Readable on a phone and a desktop:** cards checked at phone size before export (rule 98).

### Sound design

- **Crowd and siren:** from PR #2012. The siren is ours, rebuilt from measurements of real AFL
  sirens (no recording in the repo); the crowd takes are ElevenLabs Sound Effects made on the
  director's account. Mixed as stems in the edit, not taken from the game's mixed output, so the
  roar can be shaped to the cut: murmur bed, goal roar, behind groan, "BALL!", quarter-end swell,
  banner roar.
- **ElevenLabs terms:** paid plans include a commercial licence and content made during a paid
  subscription can be used commercially "indefinitely"; the free plan cannot be used commercially
  (ElevenLabs help centre, read 2026-11-22). **To confirm before release:** the account was on a
  paid plan when the #2012 takes were made.
- **Game sounds:** kick thud, whistle, umpire, from the game's own sounds only where they are ours
  or cleared; any missing one is listed, not invented with a stand-in.
- **Levels:** mastered to about -14 LUFS integrated for YouTube, peaks under -1 dBTP, checked by
  machine; how it sounds is his to judge. Nothing played aloud on his PC by us.

### Music

The trailer needs one piece about 1 min 50 s long, cut to the picture: a quiet start, a lift at
the grounds, a drive through the game, a drop for Legacy, a build for Club Forge, a big final hit.
Options, with terms (read 2026-11-22; not legal advice):

| Option | Cost | Terms | Notes |
|---|---|---|---|
| **His own original track** | Free | His own work: no licence needed | Fits Director Bible rule 66 (his originals replace generated music in the game) and rule 98 (free only). Can be written to the cut once the edit is locked |
| **Kevin MacLeod (incompetech.com)** | Free | Creative Commons Attribution 4.0: credit "Title Kevin MacLeod (incompetech.com), Licensed under Creative Commons: By Attribution 4.0" in the video description; YouTube use and monetising allowed | Well-known tracks, heard in many videos; not written to our cut. A false Content ID claim can happen; incompetech says add the credit, then dispute |
| **A commissioned composer** | Paid (his approval needed, rule 98) | A written agreement giving the project the rights for the trailer, online ads and the game | Written to the picture |
| **ElevenLabs Music on his paid account** | His existing plan | Paid plans: commercial use, no attribution, rights kept after the subscription; "Indie Game" (under $500,000 revenue) is not excluded; Starter plan forbids streaming distribution, so Creator or above for YouTube; prompts cannot name artists or songs | AI-made music, which he removed from the game in October (rule 66) |

Ruled out: Artlist (its help centre: "If you are creating a game, then you need an Enterprise
plan"), Epidemic Sound (a subscription: Pro covers online ads but only content published while
subscribed; needs his approval under rule 98), and any commercial song, club song recording,
broadcaster theme or "Up There Cazaly" recording.

## Order of work, after the go

1. He says go (1.0 bar passed).
2. This plan refreshed against what shipped; any shot whose feature changed is redrawn.
3. Trailer tools built and checked on one shot (shot 10, MCG full house).
4. The event finder run; candidate moments sent to him as short clips to pick from.
5. Fly-through paths keyed and checked against Google Earth.
6. Every shot rendered on his PC; each checked frame by frame for art faults before he sees it.
7. Music: his chosen route.
8. Edit, grade, titles, sound mix.
9. He reviews the full cut; fixes; exports (4K, 1080p, 9:16).

## Sources

- Godot Movie Maker: docs.godotengine.org, tutorials/animation/creating_movies.
- ElevenLabs: elevenlabs.io/music-terms (updated 2026-10-09); help centre "Can I publish the content
  I generate on the platform?".
- Incompetech: incompetech.com/music/royalty-free/faq.html and its Content ID page.
- Artlist: help centre article 43000659339; artlist.io/help-center/privacy-terms/artlist-license.
- Epidemic Sound: epidemicsound.com/our-plans.
- DaVinci Resolve free for commercial work: forum.blackmagicdesign.com (Blackmagic support, 2018,
  2022).
- MCG history: Great Southern Stand opened 1992; northern stands rebuilt 2003-2006 for the 2006
  Commonwealth Games (en.wikipedia.org/wiki/Melbourne_Cricket_Ground).
