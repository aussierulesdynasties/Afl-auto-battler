# The 3D oval in the match screen: self-check

Captured with tools/visual/capture_match3d.gd: a 1080x2400 window, Fremantle v GWS in round 1 at 4x, and Settings > Match view on "3D oval". The frames were taken at 4, 10, 12 and 24 s (quarter 1) and at 95 s (quarter 2, after the change of ends).

## Objects
- scoreboard and feed: PASS - unchanged above and below the oval; the goal and behind lines name the same players as the flat oval would
- players: PASS - every token is a footballer, in a Dockers purple or Giants orange-and-charcoal guernsey with its number, with a ring in the club colour
- umpires: PASS - the field umpire is in lime and runs with the play; the goal umpire stands on the goal line in match3d_2
- ball: PASS - the red ball is in the carrier's hands in match3d_3 (pack) and on the turf in match3d_0; it never floats away from a player
- camera at the far end and midfield: PASS - from behind the play, high, with the ground running up the screen and the ball in the middle third
- camera at its own end: PASS - match3d_2: a kick-in seen from the high angle behind the goals; the posts are short uprights at the edge, not standing in front of the play
- change of ends: PASS - match3d_4 is quarter 2; the ground turned half a turn and the camera stayed behind the play
- bench button: PASS - drawn over the 3D picture, bottom left, as on the flat oval
- ground lines: PASS - the boundary, 50 m arcs, centre square and goal squares are white and unbroken

## Seams
- carrier, ball between the hands, legs clear of the ring: PASS - C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/game-visuals-feasibility-a3eeac/docs/captures/oval3d_match/crop_pack.png
- goal end from the high camera: PASS - C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/game-visuals-feasibility-a3eeac/docs/captures/oval3d_match/crop_goal_end.png
- two players at game size, guernsey numbers and shorts: PASS - C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/game-visuals-feasibility-a3eeac/docs/captures/oval3d_match/crop_pair.png

## Not in the 3D view yet
The flat oval's overlays are missing from the 3D view: the caption over a scorer, the press zones, the marks on the ground, the role labels, and the long-press tips. The match plays the same either way.
