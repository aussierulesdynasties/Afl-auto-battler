# Riverway Stadium (Townsville), measured

Legacy era: one AFL match, 15 June 2019 (Gold Coast v St Kilda, `data/legacy/fixtures.csv`).
Google Earth historical imagery, centre -19.317618, 146.731540, 950 m eye, straight down. Captures are
reference only and are not committed.

## Imagery

16 dates, Aug 2017 to Feb 2026 (`measure/dates.txt`). No frame falls in 2019; the five frames from
21 Sep 2018 to 23 Jun 2020 bracket the match and are used. The west grandstand is already there in Sep 2018.
Registered to the 12 Jan 2020 frame (reg2.py, 38 to 178 inliers, 1.2 px rms).

## Scale

Google Earth status-bar readout on 9 points: 0.2998 m/px, times the 1.006 readout ratio = **0.3016 m/px,
about ±0.5%**.

## Mown oval (2018-20)

Greenness-drop trace on the five frames, pooled, robust polar Fourier K=6: 0.79 m rms, 3242 of 3549 points kept.
**171.6 m north-south x 146.7 m east-west**, axis 88.5° from east (K=4 to 8: 171.6-172.3 x 146.2-146.7).
Outline in metres from the model origin (-19.317618, 146.731873): `measure/turf_2018_2020_enu.json`.

This is the edge of the mown oval. No frame shows the AFL boundary line painted for the match, so the
boundary itself is not measured; a photo of the 2019 match is needed for it. No published AFL size was found
(data/grounds.json uses the default).

## Against the existing model (`tools/grounds/riverway/work/fence.json`)

The model's fence ellipse (145.5 x 172.1 m, fitted to the grass edge on a 2024 Esri tile) matches the
2018-20 outline: radius difference median +0.1 m, 5-95% from -2.2 to +1.9 m, worst 2.4 m; centres within
2.3 m. So the model's plan holds for 2019.

The Feb 2026 frame traced alone gives 168.9 x 154.0 m; that single frame was not checked further and is not
used.

## Not measured

Stand and roof heights for 2019 (the model's were fitted to 2024 Google Earth views; whether anything changed
between 2019 and 2024 is not checked).
