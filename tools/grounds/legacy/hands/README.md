# Hands Oval (Bunbury), measured

Legacy era: 2025-26 AFL matches, so the ground is built as it stands after the redevelopment.
Google Earth historical imagery, centre -33.346195, 115.6430106 (the model's origin), 950 m eye, straight down.
Captures are reference only and are not committed.

## Imagery

Six dates, 30 Jan 2021 to 30 Oct 2025 (`measure/dates.txt`). The March 2024 frame shows the redevelopment
under way; Nov 2024 and Oct 2025 show the finished ground. Only those two are used.
Both registered to the Oct 2025 frame (reg2.py, 303 inliers, 0.83 px rms).

## Scale

Google Earth status-bar readout on 9 screen points: 0.3044 m/px, times the 1.006 readout ratio found at the
other grounds = **0.3062 m/px, about ±0.5%**. No painted 50 m square was checked here.

## Turf edge (2024-25)

Greenness-drop trace on both frames, pooled, robust polar Fourier K=6 (`measure/comb.py`):
0.42 m rms, 1041 of 1356 points kept (the stand-shadow side and the SE light-tower shadow drop most).
- Along the goal axis: **184.4 m** (97.0 m north of the goal midpoint, 87.4 m south: the oval is not symmetric).
- Across: **147.5 m** (K=4 to 8 gives 146.4 to 148.5).
- Outline in metres east/north of the model origin: `measure/turf_2024_2025_enu.json`.

## Goals

From the four post shadows at each end, picked by hand on the Oct 2025 frame:
goal lines **171.6 m apart**, axis **59.2° anticlockwise from east**, goal midpoint 4.1 m west and 5.4 m south
of the model origin. Hand picking: about ±1 m and ±1°.

## Ring outside the turf

A bright concrete ring sits 0 to 5 m outside the turf edge (about 4.5 m in front of the grandstand), the
same on both dates to 0.5 m (`measure/ring.py`). It is not confirmed from imagery whether the boundary
fence stands on it; that needs a photo.

## Against the existing model (`tools/grounds/hands/model/hands.json`)

Its fence is an ellipse 185.0 x 156.2 m, long axis 61.7° from east. Centred on the measured goal midpoint:

| | north end | south end | across (two sides) |
| --- | --- | --- | --- |
| measured turf edge | 97.0 | 87.4 | 71.1 / 76.4 |
| model fence | 99.2 | 85.8 | 77.3 / 78.9 |

The model's fence lies 1.6 m inside the measured turf at the south end, which cannot be right, and its axis
is 2.5° off. The fence needs refitting to the measured outline plus the fence offset once the fence line is
confirmed.

## Not measured yet

Stand and roof heights, light towers (model guesses 35 m). Google Earth 3D here was probed (2,664 points,
700 m eye) but its mesh is dated 3/8/2022, before the redevelopment: it shows the old west stand at about 4 m
above the turf, so none of its heights apply to the 2025-26 ground and none are used. The new grandstand's
heights need photos or newer 3D data.

## Fence refit (2026-11-28)

The model's fence follows `measure/fence_line_enu.json`: the 2024-25 turf trace, corrected on the kit's satellite
mosaic (`tools/grounds/legacy/retrace_mosaic.py hands measure/turf_2024_2025_enu.json measure/fence_line_enu.json
green 0-250 335-360`). The PC's rebuild check found the Google Earth trace 2-4 m out behind the east benches
(bearings 100-160), so those points were moved in to the grass edge; elsewhere the two agree within about 1 m. The
west side (250-335) stays on the Google Earth trace: on the mosaic it is under the stand's shadow.
`tools/grounds/legacy/fence_fourier.py hands measure/fence_line_enu.json 6 --write` then fits it (+0.3 m to the rail
line, Blacktown's offset) as a K=6 Fourier fence (0.40 m rms to the line). The closest ellipse, now the plan's
`fence`, is 188.4 x 148.2 m, long axis 57.3 deg from east, centre (-0.88, -0.70), 1.46 m rms off the curve (the oval
is not symmetric end to end). The old ellipse ran from 6.0 m inside the edge to 2.3 m outside. Every stand front and
tower clears the new fence by 3.4 m or more. Checked by eye on zoomed mosaic boards at 12 bearings.
