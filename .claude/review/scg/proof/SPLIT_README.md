# scg.glb, split into pieces under 45 MB

The original scg.glb (commit f812cef, 57584408 bytes, md5 3ccb3dd1aeb657ed4005de38a8b5062b) is over GitHub's 50 MB limit, so it is stored as the pieces below. Load all of them together to get the whole ground. Vertex, index, instance and texture bytes are copied unchanged by split/split_glb.py.

| Piece | Bytes | md5 |
|---|---|---|
| scg_part1.glb | 45015024 | 79d86a1e5e5d3583882dd299dddf6382 |
| scg_part2.glb | 12570088 | dd7e39988961095541433c0f07e2531f |

Original and pieces together, loaded in Blender 5.2: 3,151,834 vertices, 1,579,811 triangles, 55 materials (same names) in both. Renders from 4 cameras (3/4 high, field level, stand close-up, roof edge) differ by at most 2/255 per pixel.
