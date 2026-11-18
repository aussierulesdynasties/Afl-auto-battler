---
name: afl-head-pipeline
description: Every step of putting a real player's head into the 3D game - Tripo head from his portrait, Blender clean (detach at the collar), Unreal MetaHuman conform, colour and shape transfer, fit onto the body's neck, self-check renders and the in-game film for the director. Use it whenever you make, remake, fix or film a player head (assets/oval3d/heads/, D:/AflMH, row 202 2d), even for "just one head". Extends afl-art-pipeline (the director's appearance gate) for the 3D heads.
---

# Player heads: the MetaHuman method (row 202 2d)

Director: "if we are going to do hundreds of players it needs to be as efficient and recreatable as possible".
One head = one Tripo model + one command + one film. Every step below is one he approved. Do not add, skip or
reorder a step, and do not invent a fix, rule or formula without explaining it in plain words with a worked
example and getting his OK in the question box.

## Rules that apply to every head

- **Systems, never per-head fixes.** If a head fails, find the class of fault and fix the script so the whole class
  cannot happen again, then rerun. Never hand-edit one head, never add a per-player setting.
- **Read every log line the chain prints** (step 2 below). A STOP, a missing line or an odd number means the head is
  not done. Chandler's first run shipped his jumper because nobody read "clothing faces 28".
- **Look before you send.** Check the clean board, the look board and every film frame yourself. Never send a head
  with a visible fault (jumper left on, crack across the face, bald patch, hair turned to skin, floating pieces).
- **Video, not stills, for the director.** He judges heads in motion: an mp4 at real speed from the game camera.
- **Only the head he named.** Other heads in a film are controls; don't chase their faults.
- Two failed fixes of the same fault = research the industry practice before the third.

## Step 0: what must be open

| Thing | Where |
| --- | --- |
| Raw Tripo head | `D:/AflMH/Heads/<name>_head.glb` |
| His portrait | `D:/AflMH/Refs/portraits/<club>_2026_fifa_portraits/NN_name.png` |
| Blender 5.2 | `C:/Program Files/Blender Foundation/Blender 5.2/blender.exe` (ignore the "unregister_class" Traceback the BlenderMCP addon prints in every log) |
| Unreal 5.8 + MCP | `"D:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" D:/AflMH/AflMH.uproject -ModelContextProtocolStartServer -ModelContextProtocolPort=8010 -nosplash` (~105 s to start). Session id in `D:/AflMH/Work/mcp/mcp_sid.txt`; if calls fail, re-initialise it (see the handoff's Unreal MCP notes). If the Unreal console shows "Select", ask the director to press Esc. |
| Godot 4.7.2 | windowed only through `bash C:/kt/gpu_slot.sh`; never kill another session's Godot |
| Python | run with `python -P` (D:/AflMH/Scripts/inspect.py shadows the stdlib) |

## Step 1: make the Tripo head (Chrome, his account)

Read Usage History (click the credit balance) before and after. About 130 credits a head.
1. Image panel -> More Templates -> **Head Extraction**, upload his portrait (the real photo, never a text prompt),
   Generate Image (free).
2. Hover the result -> cube icon = **multi-view** (free) -> **Multi-View to 3D**.
3. Model panel -> **Smart Mesh** tab (never HD), Generate (100) -> Texture (30) -> Export GLB 4k.
4. It lands in `C:/Users/DANTE/Documents/Downloads/tripo_convert_<uuid>.glb`; move it to `D:/AflMH/Heads/<name>_head.glb`.
5. Close the Chrome tabs you opened.

## Step 2: the one command

```
bash D:/AflMH/Scripts/make_head.sh <name> <player id> D:/AflMH/Heads/<name>_head.glb
# e.g. bash D:/AflMH/Scripts/make_head.sh chandler MEL_37 D:/AflMH/Heads/chandler_head.glb
```

Run it in the background (about 5 minutes). Back up `assets/oval3d/heads/<pid>.glb` and `heads.json` first: it
overwrites them. Logs and times go to `D:/AflMH/Work/<name>/` (`times.txt`, `1_clean.log` ... `7_look.log`).

What each step does, and the line you must read:

| # | Step (script) | What it does | Read this |
| --- | --- | --- | --- |
| 1 | clean (`clean_head.py`, Blender) | The director's four: deletes junk inside the neck; **detaches the head**: finds the clothing (any colour unlike his skin, dark or light), grows it up the collar, deletes it so the cut follows the collar, peels collar-coloured rims, drops loose collar scraps; keeps the face below the line just above the eyes; rebuilds the hair above it as one closed surface | `clothing faces N cut at X of height` (N in the hundreds or more; X roughly 0.25-0.5), `eye pieces` or `eye whites N`, `cap line`. A `STOP:` line ends the run on purpose: shoulders still on, or eyes not found. Fix the script, not the head. |
| 2 | conform (Unreal p5, p7, p8, p9, p10) | Imports the clean head, tracks the face, conforms a MetaHuman head to it, exports MH head + scan | Any `Traceback` in `2_p*.log` stops the run |
| 3 | transfer (`transfer2.py`) | Copies the scan's shape (along normals) and colour onto the MetaHuman head | `3_transfer.log` ends without error |
| 4 | despeck (`despeck.py`) | Removes light specks and skin shards from the hair, dark specks and isolated dots from the skin | count lines in `4_despeck.log` |
| 5 | source (`mh_head_src.py`) | One mesh, one material, the scan's eye colours, MetaHuman UV2 for the pore maps | `game/<pid>.glb` and `<pid>_scan.glb` exist |
| 6 | fit (`tools/oval3d/heads/fit_head.py`) | Puts the head on the body's neck socket: 6 cm shape join, 2 cm colour join | `CHECK scale ... LOOK: neck width ..., neck stretched ...` (Chandler: scale 1.890, width x0.69-0.93, stretched 4.2 cm) |
| 7 | look (`look_game2.py`) | Flat-lit renders: front, three-quarter, eye level, back, back-left | `D:/AflMH/Work/<name>/look_*.png` |

## Step 3: self-check (before anything reaches the director)

1. **Clean board** (after step 1): render the clean head with `D:/AflMH/Work/clean/show.py` (back, front, side,
   under). Red = a loose piece, yellow = an open edge (neck ring, eyes, lips are expected). Check: no jumper or
   collar left, the neck kept all the way round (not chopped at the chin at the back), the face whole, no crack
   across the nose, hair one surface.
2. **Look board** (after step 7): no red wedges at the neck, no crack or smear across the face, eyes in place, hair
   all round with no bald patches, the nape hair still hair (not skin).
3. Compare the front render with his portrait side by side: same face, same hairline.

## Step 4: in game, then the film

1. `godot --headless --path . --import` after every head rebuild. Without it Godot films the OLD import of the glb.
2. Film him jogging (needs the local FOLLOW/CLIP edits in `tools/visual/capture_builds3d.gd`, never committed):
   ```
   G=/c/Users/DANTE/Desktop/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe
   OUT=<scratchpad>/<film>; mkdir -p $OUT
   FOLLOW=<pid> GPU_SLOT_OWNER=heads-<name> bash C:/kt/gpu_slot.sh $G --path . --script tools/visual/capture_builds3d.gd -- $OUT match heads > $OUT/log.txt 2>&1
   ```
   The log must say `FOLLOW <pid>` and `SHOT ... done`.
3. Make the mp4 with `bash D:/AflMH/Scripts/mkmp4.sh <film dir> <out.mp4>` (three views side by side, 30 fps, real speed).
4. Look at every frame yourself, running and standing still: does the head belong to the body, any line at the
   jaw or neck, hair reads as hair, nothing floating or clipping. Fix the class of fault and refilm before sending.
5. Send the mp4 with a one-line caption and the step times from `times.txt`.

## Known faults and where they come from

| You see | Cause | Fixed in |
| --- | --- | --- |
| Jumper wedges on the neck, crack across the nose | Clothing not cut (dark jumper), and the eye line fell to the nose because no eye pieces were found | `clean_head.py`: clothing test no longer needs a light colour; eye line from the eye whites; STOP checks |
| Neck chopped at the chin at the back | A flat cut at the front collar's height | `clean_head.py`: the cut follows the collar |
| Nape hair turned to skin | A 6 cm colour fade | `fit_head.py`: colour join only 2 cm (shape join stays 6 cm) |
| Old head still in the film | Godot used the stale import | `--import` before filming |
| Hard line under the jaw when he stands still | Lighting, not texture (the Mobile renderer ignores skin scattering) | Not fixed: proposed to the director, no OK yet |
| Hair looks smooth at game distance | Not found yet (the shine test changed nothing) | Open |

## Never commit

Media, `.import` noise, stray `.uid`, the handoff, `wrap_head.py`, the TEMP edits (`capture_builds3d.gd`
FOLLOW/CLIP/SUN_ANGLE/SHADOW_DIST, `Oval3D.gd` HEAD_SSS) or a TEMP `socket.json`. Python edits use `newline=''`.
