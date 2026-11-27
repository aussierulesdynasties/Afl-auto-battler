# Ground inspector

Fly through any stadium model in first person, fast, to inspect it closely and write its fault list
(row 202 2b; director, 2026-11-20: "fly around the map very fast in first person").

## Open it

- **Windows:** double-click `tools/inspect/inspect_ground.bat`, or run `tools\inspect\inspect_ground.bat scg`
  to open the first ground whose name has "scg" in it. If Godot is not on PATH, set it once:
  `setx GODOT "C:\path\to\Godot_v4.7.2-stable_win64.exe"` and open a new terminal.
- **Linux/macOS:** `tools/inspect/inspect_ground.sh [name]` (`GODOT=/path/to/godot` if needed).
- **Editor:** open `tools/inspect/GroundInspector.tscn` and press F6 (Run Current Scene).

It opens on the MCG. Press **L** for the list of every ground and click one, or **Tab** to step through them.

## Controls

| Key | Does |
|---|---|
| Click | Fly: the mouse looks around. **Esc** frees the mouse |
| W A S D | Move (also the arrow keys) |
| Space or E / Ctrl or Q | Up / down |
| Shift | x5 fast (125 m/s at the starting cruise) |
| Alt | Slow, for close looks |
| Wheel, + or - | Cruise speed (1 to 600 m/s) |
| Tab / Shift+Tab, PgDn / PgUp | Next / previous ground |
| L | The list of grounds |
| R | Back to the start view |
| T | The centre square at a man's eye height |
| G | Drop to the floor below you at eye height (a stand, a concourse) |
| O | Show or hide the match's turf and goalposts |
| H | The aerial orbit: the camera circles outside the ground as from a helicopter (`Oval3DOrbit`); H or any move key stops it |
| C | Copy where you are to the clipboard, for the fault list |
| P or F12 | Screenshot (and copy where you are); the saved path shows on screen |
| F11 | Full screen or window |
| F1 | Hide the help |

Drop any `.glb` file onto the window to open it.

## What it shows

- **In the match** (`assets/grounds/<slug>/`): the ground exactly as a match builds it (Oval3D and
  GroundModels: light, turf, goalposts, the model laid on the match fence, and its seats), listed by
  its ground name. Every ground in `GroundModels.grounds()` appears here, pieces and all.
- **Models not in the match yet** (`tools/grounds/`, `.claude/review/`): read straight off disk, as
  authored, on the match's light, turf and goalposts. A model split for GitHub (`<name>_part1.glb`,
  `_part2` ...) loads as one ground.
- **Local worktrees:** the button under the list also scans `.claude/worktrees/*` for the same folders,
  so unpushed work can be inspected. Copies identical to one already listed are left out.

Screenshots go to `%APPDATA%\Godot\app_userdata\Aussie Rules Dynasties\inspection\` on Windows.

## Check it

`godot --path . res://tools/inspect/GroundInspector.tscn -- --check` loads every ground in turn, prints
OK or FAIL for each, drives the controls on the first (a click, Shift+W held, T) and saves each start
view to `user://inspection/check/`. `--ground=<name>` limits it to matching grounds. Without a GPU, run it
under `xvfb-run` with the lavapipe Vulkan driver.

Looks only: nothing here changes a match.
