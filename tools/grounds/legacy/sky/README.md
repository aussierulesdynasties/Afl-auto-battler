# Sky Stadium (Wellington), 2013-2015: measurements (in progress)

Legacy mode plays 3 matches here, one a season 2013-2015. The model on main (`tools/grounds/sky/model`, "first draft",
roof traced on satellite tiles, heights estimated) is what this checks.

## Sources

- **LINZ LiDAR, Wellington 2013-2014, 1 m DSM and DEM** (`s3://nz-elevation/wellington/wellington_2013-2014/`, tile
  BQ31_10000_0204, CC BY 4.0), flown in the Legacy years. A 400 x 400 m window round the ground is read straight from
  the public cloud-optimised GeoTIFF (`measure/lid.py`); the raster itself is not committed.
- Google Earth web historical imagery (`ge_history.js`, `LAT=-41.27301 LON=174.78587 R=950`): 40 dates, 15 Dec 2002
  to 4 Mar 2017 (`measure/dates.txt`). The roof's shadow covers part of the field edge in every frame and the lean
  differs between frames, so the turf edge traced from them (150 x 120 m, dates 2-3 m apart) is not used; the LiDAR
  is.

## Measured (2026-11-24)

| What | Result | How |
| --- | --- | --- |
| Field level | 3.14 m (NZVD2016) | median of the DSM over the middle 40 x 40 m |
| Field edge (fence or seat-front wall) | **166.5 m long (axis 11 deg off north, north end west) x 130.5 m wide**; polar Fourier K = 8 through 174 of 180 rays, 0.28 m rms | first point on each ray (every 2 deg) where the DSM stands 0.8 m above the field; six rays that stop on things on the field left out (`measure/lidar_profile.json`) |
| Roof inner edge | 72-90 m from the centre (round the ends to the sides), **19.2-21.6 m above the field** (5-95 %, median 20.6 m) | first DSM point 15 m above the field on each ray, height the median of three points from there |
| Roof top | **22.6-22.8 m** above the field over most of the ring (median 22.8 m) | highest DSM point across the roof on each ray, light towers left out of the percentiles that matter |
| Roof outer edge | 101.5-140.5 m out (the ring is wider on the south-west, over the concourse), 20-22.8 m up | last DSM point 15 m above the field |
| Light towers | four on the roof at about 50-51.6 m above the field (50.9, 49.9, 50.5, 51.6); a fifth patch reads 36.9 m | DSM patches above 40 m |

## Against the model on main

- Fence: model ellipse 163.3 x 127.5 m against 166.5 x 130.5 measured, so the model is about 3 m short each way; the
  measured edge is not an ellipse (K = 8 curve).
- Roof: model `z_roof` 27-29 m against 19.2-22.8 m measured, so **the model's roof is about 5-7 m too high**. Inner
  radii (model 70.2-95.0, measured 71.5-90.5 m) roughly agree; outer (99.7-126.5 against 101.5-140.5 m) do not on the
  south-west.
- Towers: the model has none; the DSM shows four on the roof, about 50 m above the field.

Bearings are degrees counter-clockwise from east round the field centre (0 east, 90 north).

## Not done yet

- Seat rows and tiers under the roof (the DSM sees only the roof there): photos or the 2019-2020 LiDAR's points.
- Rebuild the model to these numbers.
