# Optus Stadium survey

The measurements the Optus model is built from. Every ring of the stadium is an offset of one fitted
curve, the roof's outer edge (`shape.py`). No Google Earth imagery is stored here, only numbers read
off it: the hard data rule in docs/MCG_STANDARD.md.

## Method

**Calibrated Google Earth views.**
- The URL form is `@lat,lon,{a}a,{d}d,35y,{h}h,{t}t,0r` in a 1280x1000 window, cropped to 1280x720 (rows 140-860).
- The 720 crop has a vertical field of view of 25.58° (F = 1584 px).
- Google Earth's turf is 5 m above sea level. Heights here are above the turf.
- Low cameras are lifted by Google Earth, by about 14 m for cameras 20 m above the turf. Cameras are therefore solved from hover points (`solve_obl.py` in the build notes), not taken from the URL.

**Hovers.**
- `ge_hover.js` moves the mouse to a pixel and screenshots the status bar.
- `ocr.py` reads latitude and longitude (to 0.01", about 0.3 m) and the height (1 m steps).
- Each hover is a direct 3D point on Google Earth's mesh.
- Model frame: x east, y north, metres. Model (-30.38, -8.78) = (-31.95115518870997, 115.88899235343283). north = Δlat·110574, east = Δlon·111320·cos(lat0).

**Tracing.** `gtrace.py` walks rays at a known height through six straight-down 350 m shots. It finds the
roof edge as a sustained brightness drop, at sub-pixel precision. The shots are combined by median.

## Files

| File | What | Fit |
|---|---|---|
| outer2_c10.json | Roof outer edge, polar Fourier N=10 about OC | 0.09 m rms, 0.72 m max; shots agree to 0.16 m |
| roofz_c4.json | Roof edge height, 4 harmonics | 0.61 m rms (1 m readouts), 40.9-42.8 m |
| inner_c.json, inner_z.json | Roof inner edge (12 harmonics) and its height | 0.37 m rms; 41 m |
| truss_model.json | 50 truss positions along the edge, 2-harmonic drift | 0.6 m rms |
| hover_res.json | Roof-edge height hovers | |
| fac_rows.npy, fac_coef.npy | 1,025 facade hovers on 12 oblique views: [view, u, v, θ, offset d, h]. Fit d(θ,h) uses hat functions in h × Fourier NH=3 | 0.55 m rms |
| bronze_top.json | Top of the bronze cladding, 60 readings, 5 harmonics (facade.json `top`) | 0.98 m rms |
| pod_d.npy | Podium deck edge as an offset of the roof edge. It came from OpenStreetMap, smoothed. It is being replaced by the podium hover survey because it is 4-7 m too far in on the south | 0.55 m rms vs OSM |
| halo.json | HALO rooftop platform, digitised off the straight-down shot g_-75_+0 (0.20 m a pixel) | about ±1 m |

## Checks against the build

- **Top down.** The same gradient tracer runs on our render and on Google Earth at all six straight-down cameras. Roof outer edge: 0.77 m rms over 697 bearings.
- **Oblique.** Each Google Earth hover ray is cast into our glb (trimesh). The difference in depth along the ray is the error in metres. Facade at 15-35 m: median 0.6 m.

## Published dimensions

- 42 m high, five tiers, 165 m x 130 m field: worldconstructionnetwork.com (New Perth Stadium and Sports Precinct).
- 50 triangular truss cantilevers, about 35 m (44 m long overall); each bay is a barrel vault on three arches: LSAA, New Perth Stadium tensile membrane roof.
- Bronze facade of anodised aluminium: architectureau.com.

Imagery for measurement: Google Earth (© Google, Airbus, Maxar, CNES), measured only, never stored or shipped.
