# The 3D view's phone budget

_2026-11-21. Measured in the cloud on every ground the match view plays in, at each graphics level.
The phone run that settles the frame rate is still to come (below). This page is evidence; the
director sets the budget (rule 94: "the director sets the numbers once he has seen the phone")._

## How it was measured

`tools/perf/Oval3DPhone.tscn` builds the match view exactly as a match does (Oval3D with the ground's
model, the crowd on its seats, a fine day) and plays a seeded Fremantle v St Kilda match at 4x under
the broadcast camera (Oval3DBroadcast), at the phone's picture size (1080 x 1240). For each ground
and graphics level it records the triangles and draw calls each frame draws, the memory in use,
the time to build the scene and the renderer's own time.

- Triangles, draw calls and memory are the same on any device, so they carry straight over to a phone.
- The renderer times here come from a software GPU in the cloud, so only their ratios between grounds
  and levels mean anything. They are given relative to the plain stand on High.
- The same scene is the main scene of a separate measuring APK (export preset "Android 3D probe",
  package `...aussierulesdynasties.probe`, installs beside the game). On a phone it measures real
  frame times; see "What needs a phone" below.

Run it again with:

    godot --path . --rendering-method mobile tools/perf/Oval3DPhone.tscn -- \
        levels=high,medium,low measure=1 size=1080x1240 out=rows.json [grounds=mcg,marvel] [shots=DIR] quit

## What was too heavy, and what changed

| Problem | Before | Fix | After (High) |
|---|---|---|---|
| A ground's seats were one batch per colour: every seat in the ground drawn every frame, wherever the camera looked, and drawn again into each of the four shadow bands | MCG: 15.2 million triangles a frame | Seats drawn in 48 slices round the bowl (GroundModels.SEAT_SECTORS); the camera draws only the slices in view | MCG: 3.6 million |
| Marvel's seats are two meshes of a million triangles each; Moorabbin's Huggins Stand 550,000; People First two halves of 340,000. A mesh that big is always "near", so neither the view nor the detail levels ever cut it | Marvel: 11.9 million | Any model mesh over 200,000 triangles is cut into 32 pieces round the bowl when the ground loads (GroundModels.slice_big_meshes). Same triangles, same look; costs about 1.5 s more to load Marvel here | Marvel: 3.1 million |

## The graphics levels (Settings > Graphics)

High is the look as built and ruled, and stays the default. Medium and Low are for weaker phones.
Every level plays the same match; only the picture changes (scripts/ui/match/Oval3DQuality.gd).

| | High | Medium | Low |
|---|---|---|---|
| Sun shadow map | 4096, soft (best) | 2048, soft (cheapest) | 2048, soft (cheapest) |
| Shadow bands by distance | 4 | 4 | 2 |
| Each seat casts a shadow | yes | no | no |
| Supporters as 3D people | within 55 m (rule 2.92) | within 30 m | none: every supporter a card |
| Mesh detail threshold | 1 | 2 | 4 |
| Picture drawn at | full size | full size | three-quarter size, stretched |
| Grass blades round the ball | yes | yes | no |
| A late game's plain stand shades the wing | yes | yes | no |

Low keeps the soft shadow filter: the hard filter was tried first and lost the roof's shade on the
stands, so Marvel's seats showed bright under the roof. Low keeps the ground's own shadows for the
same reason (its roofs shade the stands and the wing).

## Every ground, every level

Triangles in thousands a frame (the mean over the measured frames, broadcast camera); draw calls a frame;
the renderer's time against the plain stand on High (software GPU, so ratios only); video memory in use
(textures, meshes and buffers, MB). "(stand)" is the plain stand a ground with no model plays in.

| Ground | Triangles (H / M / L) | Draw calls (H / M / L) | Renderer time (H / M / L) | Video MB (H / L) |
|---|---|---|---|---|
| optus | 3839 / 2985 / 1948 | 311 / 261 / 238 | 1.31 / 0.95 / 0.73 | 878 / 843 |
| mcg | 3593 / 2559 / 1880 | 237 / 219 / 206 | 1.36 / 1.02 / 0.76 | 821 / 785 |
| scg | 3446 / 2538 / 2181 | 216 / 201 / 209 | 1.37 / 1.04 / 0.85 | 887 / 853 |
| marvel | 3123 / 2134 / 1910 | 172 / 159 / 166 | 1.43 / 0.97 / 0.75 | 865 / 834 |
| macpoint | 2859 / 1985 / 1683 | 386 / 371 / 376 | 1.15 / 0.96 / 0.72 | 783 / 750 |
| york_park | 2257 / 1795 / 1592 | 300 / 292 / 300 | 0.95 / 0.77 / 0.65 | 836 / 803 |
| moorabbin | 2227 / 2015 / 1793 | 239 / 235 / 243 | 0.98 / 0.83 / 0.68 | 794 / 762 |
| sky | 2173 / 1727 / 1487 | 353 / 339 / 343 | 1.00 / 0.77 / 0.59 | 785 / 752 |
| bruce | 2087 / 1423 / 1380 | 435 / 425 / 433 | 0.83 / 0.72 / 0.56 | 759 / 727 |
| cazalys | 1940 / 1771 / 1231 | 350 / 324 / 313 | 0.85 / 0.71 / 0.52 | 808 / 776 |
| (stand) | 1906 / 1696 / 1122 | 177 / 171 / 156 | 1.00 / 0.81 / 0.58 | 751 / 717 |
| ikon_park | 1771 / 1758 / 1464 | 186 / 188 / 195 | 0.75 / 0.73 / 0.56 | 793 / 762 |
| people_first | 1764 / 1752 / 1568 | 180 / 182 / 194 | 0.91 / 0.73 / 0.59 | 790 / 758 |
| football_park | 1585 / 1396 / 1280 | 233 / 233 / 241 | 0.83 / 0.70 / 0.53 | 814 / 782 |
| gmhba | 1548 / 1536 / 1328 | 132 / 134 / 141 | 0.88 / 0.70 / 0.58 | 840 / 809 |
| waverley_park | 1367 / 1355 / 1286 | 194 / 196 / 207 | 0.80 / 0.72 / 0.57 | 815 / 784 |
| blacktown | 1353 / 1230 / 1162 | 285 / 287 / 296 | 0.77 / 0.64 / 0.50 | 783 / 752 |
| jiangwan | 1260 / 1248 / 1160 | 264 / 266 / 274 | 0.73 / 0.64 / 0.53 | 750 / 719 |
| windy_hill | 1245 / 1233 / 1147 | 193 / 195 / 203 | 0.74 / 0.65 / 0.50 | 784 / 752 |
| bellerive | 1112 / 1100 / 1069 | 158 / 160 / 167 | 0.75 / 0.64 / 0.56 | 775 / 743 |
| hands | 1111 / 1090 / 1070 | 284 / 284 / 292 | 0.71 / 0.64 / 0.52 | 786 / 754 |
| engie | 1110 / 1098 / 1065 | 144 / 146 / 153 | 0.71 / 0.62 / 0.51 | 734 / 703 |
| whitten | 1108 / 1090 / 1068 | 209 / 211 / 219 | 0.71 / 0.61 / 0.48 | 1189 / 1157 |
| barossa | 1101 / 1079 / 1060 | 257 / 258 / 266 | 0.73 / 0.65 / 0.49 | 790 / 758 |
| norwood | 1097 / 1085 / 1059 | 184 / 186 / 198 | 0.70 / 0.59 / 0.49 | 751 / 720 |
| riverway | 1091 / 1078 / 1060 | 259 / 261 / 268 | 0.67 / 0.65 / 0.48 | 799 / 767 |
| summit | 1089 / 1077 / 1059 | 282 / 284 / 291 | 0.74 / 0.62 / 0.47 | 764 / 732 |
| waca | 1088 / 1075 / 1054 | 241 / 243 / 250 | 0.67 / 0.62 / 0.47 | 854 / 822 |
| subiaco | 1087 / 1075 / 1054 | 204 / 206 / 213 | 0.70 / 0.63 / 0.46 | 738 / 707 |
| north_hobart | 1063 / 1051 / 1042 | 246 / 248 / 259 | 0.69 / 0.61 / 0.51 | 805 / 773 |
| manuka | 1057 / 1045 / 1035 | 248 / 249 / 259 | 0.71 / 0.63 / 0.48 | 761 / 729 |

## What the numbers say

- The heaviest grounds on High draw 3 to 4 million triangles a frame (Optus, MCG, SCG, Marvel);
  most grounds about 1.1 to 2 million. Low saves most at the big grounds (Optus 3.8 to 1.9 million)
  and cuts the renderer's time by a third to a half everywhere: a quarter fewer pixels, no 3D
  people in the crowd. It keeps the ground's own shadows, so its triangles fall less than its time.
- The floor, about 1 million triangles at any ground and any level, is the 36 players and 7 umpires
  drawn and drawn again into the shadow map, not the ground. Players' detail levels (row 197's
  level-of-detail bodies) are the lever there, outside this page.
- Draw calls stay under about 440 everywhere. Bruce Stadium (825 separate meshes in its model) and
  Macquarie Point are the most; merging Bruce's meshes would take it under 200.
- Memory was the bigger risk on a cheap phone, and is now compressed. The 3D view held about 750 MB
  of video memory before any ground loaded, most of it textures stored uncompressed: the guernsey
  atlas (assets/oval3d/kits_today.png, 8192 x 5120, about 210 MB with its mipmaps) and the Tripo head
  photos. Every ground's model kept its textures uncompressed too (embedded_image_handling=3, #1931);
  Whitten Oval's added about 440 MB. Now the atlas and heads are GPU-compressed (ASTC on a phone,
  high quality) and the grounds' textures are stored as Basis Universal. Measured on High:

  | | Before | After |
  |---|---|---|
  | Plain stand | 751 MB | 591 MB |
  | MCG | 821 MB | 661 MB |
  | Marvel | 865 MB | 640 MB |
  | Optus | 878 MB | 640 MB |
  | Whitten | 1,189 MB | 719 MB |

  The guernseys filmed close at chest height (capture_guernseys3d.gd: Collingwood, West Coast,
  Richmond, Hawthorn) differ by about 3 levels in 255 on average and look the same side by side; the
  grounds from the broadcast camera are indistinguishable. The table above was measured before the
  compression, so its video memory column is the old figure.

## The budget (proposed, for the director)

Nothing here is settled until the director has seen the phone (rule 94). Working numbers, from
published guidance for low-end Android GPUs (Mali-G52 and Adreno 610 class):

- Low holds 30 frames a second on a low-end phone: under about 1 million triangles and 300 draw
  calls a frame, and the whole game under 1.5 GB of memory.
- Medium and High hold 60 frames a second on a mid-range or better phone (the 60 cap of rule 94).
- The open question O19 (match view worst 5% of frames under 33 ms) is the frame-time target.

Against that, Low is at or just over the triangle line at most grounds (1.0 to 1.2 million, the
players' floor) and up to 2.2 million at the eight heaviest; with the textures compressed every
ground's video memory is 590 to 720 MB. The phone run decides whether that is enough.

## What needs a phone

The cloud gives counts and memory, not frame times. To measure a real phone:

1. In the Godot editor on the PC: Project > Export > "Android 3D probe" > Export Project (debug),
   or `godot --headless --export-debug "Android 3D probe" builds/android/ard-3d-probe.apk`.
2. Install it beside the game (`adb install builds/android/ard-3d-probe.apk`), open "ARD 3D probe"
   and leave it: it walks every ground at High, Medium and Low (about 15 minutes), the table on
   screen. Screenshot it, or `adb pull` its user://oval3d_phone.txt.

That run gives each ground's real frame time and worst 5%, and says which level each phone needs.
