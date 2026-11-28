# Summit Park (Mount Barker), measured

No AFL premiership match yet (none in `data/legacy/fixtures.csv`), so the ground is built as it stands now.
Google Earth historical imagery, centre -35.0779788, 138.8934415 (the model's origin), 950 m eye, straight
down. Captures are reference only and are not committed.

## Imagery and scale

Four dates, 20 Oct 2024 to 23 Jan 2026 (`measure/dates.txt`). The three from Dec 2024 on are used, registered
to the Jan 2026 frame (59 to 109 inliers, 1.2 px rms). The ground sits about 320 m above sea level, so the
scale is finer than at the coastal grounds: readout 0.2049 m/px, times 1.006 = **0.2062 m/px, about ±0.5%**.

## Turf edge

Greenness-drop trace on the three frames, pooled, robust polar Fourier K=6: 0.30 m rms, 1965 of 2435
points kept. **175.3 m x 145.3 m** (K=4 to 8: 173.5-175.3 x 145.5-145.6). The Oct 2024 frame alone gives
171.2 x 147.9 m; its registration is weak and it is left out.

## Goals

From the post bases (where each post's shadow meets the post), picked by hand on the Jan 2026 frame: goal
lines **161.9 m apart**, axis **74.0° anticlockwise from east**; outer posts 19.9 and 20.2 m apart (19.2 m
expected, so the picks are good to about ±1 m). Goal midpoint 6.1 m west and 2.9 m south of the model origin.
Turf runs 89.1 m north and 86.2 m south of the goal midpoint along the axis, 70.6 and 74.6 m across.

The published size, 160 x 141 m (data/grounds.json, from Wikipedia), is the boundary line, which sits inside
the turf; the line itself is not visible on these frames and is not measured.

## Against the existing model (`tools/grounds/summit/model/summit.json`)

Its fence ellipse (172.7 x 152.3 m, long axis 83.6° from east) measured from the goal midpoint along the
measured axis: 89.3 north, 82.9 south, 73.0 and 79.9 across. Its south end lies 3.3 m inside the measured
turf, which cannot be right, and its axis is about 10° off the goals. It needs refitting to this outline.

## Not measured

The grey fence or path ring outside the turf (the brightness search was not consistent between dates),
stand and tower heights.

## Fence refit (2026-11-28)

`tools/grounds/legacy/fence_fourier.py summit measure/turf_2024_2026_enu.json 6 --write` puts the model's fence on
the measured turf edge pushed out 0.3 m to the rail line (Blacktown's offset), as a K=6 Fourier curve (`fence_fourier`
in `summit/model/summit.json`, 0.02 m rms to the offset trace). The old ellipse ran from 5.4 m inside the turf to
3.5 m outside it, its axis about 8° off. The closest ellipse, now the plan's `fence`, is 175.6 x 146.1 m, long axis
75.9° from east, centre (-3.38, -1.79), 0.34 m rms off the curve. Every building and tower clears it by 3.1 m or more.
