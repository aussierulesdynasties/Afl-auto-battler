# Texture pass on archived ground models (row 202 2b)

Session local_85df280c, worktree `.claude/worktrees/kind-haslett-404e74`.

## Where the work is now

Saved: .claude/review/marvel/ (texture boards), .claude/review/texture_pass_boards/ (Engie, Manuka, WACA), .claude/review/texture_wip/ (Adelaide es2 e9e6c618, GMHBA tex2 cd2f8354, Optus roof11 f693bd05, Optus h50 build scripts). The 125 MB Optus h50 roof build glb is outside git at C:/Users/DANTE/Documents/AFL3D_archive/optus_bg/optus_h50_roofbuild.glb. The worktree's Oval3D.gd diff is stale against main and was not carried over.

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-kind-haslett-404e74.md)

# Handoff: kind-haslett-404e74 (texture session: archived grounds + background scenes)

### State
- 2026-11-21 Vic Park #1884: 52 ref photos in scratchpad/vpref/img (urls.txt, sheet0-4.jpg). Counts per part in side-session-notes/local_6e4c78c4.../vicpark_photo_counts_2026-11-21.md; no part reaches 10 (era). Asked lead whether post-2000 photos count. Next: matched-camera boards, then Windy Hill #1885, then Optus roof.

Norwood #1870, Albury #1875 (glb 5fc8cabb, worktree scratchpad/awt) auto-merge. Brighton #1877 (glb 54794e7c, worktree scratchpad/bwt, scripts in brightonhomes/texpass) auto-merge. Next: Whitten. Marvel bg v4 PASSED (orbit eefd5806, scene_bg b923708e); goes to lead local_a479dc03. Riverway bg failed 11-20 (plain boxes, flat river); 7 bg scenes have texture requests, await orbits.
Optus #1867 MERGED; seat colours follow-up PR #1880 auto-merge (render check scratchpad/oseat). GMHBA wall repainted: scratchpad/gmw/gmhba_tex.glb md5 35c677ab, sent to bg-gmhba local_3b7267ac-26d5-4ad5-993a-af5ee46bac47 for a rebuild + orbit. Whitten #1882 (glb 795d16bd, worktree scratchpad/wht) auto-merge. Victoria Park #1884 (glb 6791b6cb, worktree scratchpad/vpt; build.py chdir fixed to own folder) auto-merge, board sent. Windy Hill #1885 (glb b6a1fe14, worktree scratchpad/wht2) auto-merge, board sent. Football Park #1886 (glb A 44da3662, B b24d4dc4, worktree scratchpad/fpt) auto-merge, board sent. Suburban ovals: Fremantle #1888 (glb 78311e01) auto-merge, board sent. People First upper-tier seat grey 22%->8% measured vs photo: #1889 (glb 04f4f7d5: upper seats same shape as lower, 15% grey; v7 orbit failed speckle; awaiting bg v8; worktree scratchpad/pft, scripts/swap_image.py swaps one png in a glb), sent to bg-peoplefirst local_25ab6830 + plan. Director 11-20: models are verbatim copies of the photo; measure, never offer alternatives. Next: Leederville. Fremantle notes: then copy glb, board, PR (worktree scratchpad/fot, branch claude/fremantle-texture-pass from b4dea52f3; paint_fo.py mottle/stains cut, sponsor fascia+boards removed, texpaint.py + ground_fine.npy copied from old scratchpad fo; build: source/build/build.py -- close|glb build/tp). Machine RAM ~300 MB free (others' Blenders): paint with OPENBLAS_NUM_THREADS=1, ONLY=<maps>. Adelaide west stand back repainted: scratchpad/adw/adelaide_westback.glb md5 e1687b6a (paint.py, apply.py; arches are alpha-cut openings + 4 m concourse recess, UVs constant-radius fixed-metre after director caught strut kink + painted arches), sent to Adelaide bg local_a8ffb4e8 + plan local_a479dc03; review its orbit. Then Leederville, Bruce, Ikon Park, North Hobart, York Park. Gotcha: archived build scripts often chdir to the original builder's scratchpad or miss modules (copy from that scratchpad). Riverway bg failed ring sheet 11-20 (roofs white, river flat, lagoon bright): fixes sent.
WACA #1864, Manuka #1865, ENGIE #1866, Norwood #1870, Albury #1875 auto-merge (auto-merge enabled 06:09Z; merge queue: use `gh pr merge N --auto` with no strategy flag).

### Task
1. Background scenes: People First PASSED 11-20 (orbit a3302bb3, model 3bd42451 #1868), told to land; GMHBA orbit 16 (3ade3ef9) PASSED, to lead; stadium 'wall' speckle reported to lead local_a479dc03, asked owner; Optus PASSED; Marvel (local_8b52d5c6-9bd8-460b-9163-4aa8e02a12d5) FAILED 11-20, fixing 5 points (orbits sent to director, sessions told to land).
   Adelaide (local_a8ffb4e8) rebuilding against my 7-point list (water meshes, courts, road meshes, pavers, roofs,
   ground detail repeat-break + distance fade, Oval No.2). Review its orbit + ring sheet; give verdict same turn.
2. Archived ground texture pass, in order: WACA (now), Manuka, ENGIE, Norwood, Albury, Brighton, Whitten, Victoria
   Park, Windy Hill, Football Park, suburban ovals. Per ground: branch from latest commit, stddev table, hand repaint,
   own signs (no sponsors/nets/crowd/field), rebuild glb, re-render proofs, board, self-check, commit, push, report.

### Where things are
- WACA worktree: D:/Temp/claude/2117a0e07442304a/b457f311-.../scratchpad/wwt (branch claude/waca-texture-pass,
  model commit a2dec673b). New tools/grounds/waca/paint_tex.py (glass sky-gradient panes, white/concrete faint
  streaks), run after `python tex.py tex`. Build: `WACA_TEX=1 blender -b -P build.py -- out/waca_tex.glb out/r92t.png`;
  close-ups `blender -b -P turn.py -- out/close 0` (absolute paths). WACA DONE: PR #1864 (glass, even concrete, paved apron, sponsors removed,
  WACA signs). Car-park land still flat colour.
- Background textures: scratchpad/bgtex (mk_*.py): road_asphalt_v2 (8 m), roof_far (24 m), roof_corrugated, city_far,
  mv_plaza_pavers (6 m), mv_harbour_water_soft, adl_bluestone, adl_torrens_water, perth_*.

### Gotchas
- Repeat break that passed everywhere: 2nd sample 0.37x, rot 36.87 deg, 50/50, contrast x1.414; distance fade
  150-400 m. Blender-node versions need a Godot shader note in each scene's handoff.
- Director: no blotchy mottle on seats/steel; keep surfaces even like the photo.
- ffmpeg not on PATH: use imageio (imageio.v3.imread(video, index=n)).
- Give each session its verdict in the same turn I review it. Open EVERY orbit frame at full size before any verdict (lead 11-20).
- GMHBA orbit 20 FAILED (plain white outer wall). Wall repainted as fin cladding (paint2.py, Populous Gate 1 photo in scratchpad/gmref): gmw/gmhba_tex2.glb md5 cd2f8354, sent to local_3b7267ac; gate orbit 21.
- Riverway set j (c06b8df4) PASSED 11-20, told to land via plan session.
- GMHBA orbit 21 (cd2f8354) PASSED 11-20, told to land via plan session.
- PF speckle = 3D seat_grey mesh (36k tris random grey in upper tier), not texture. Recoloured to seat_red: glb 3e5c537f pushed to #1889 (commit 3d41e0167), sent to local_25ab6830; v9 full orbit (mp4 6dafffce) PASSED 11-20, all 8 frames30; sent to bg + plan.
- (old) PF v8 (8a0267cc) FAILED: upper seats are white pixel noise vs photo (light 52% vs 39%), cause = no mipmaps on seat textures; asked bg for frames 1/91/181 with linear-mipmap filtering; if still off, fix texture myself. Plan session is holding v8.
- Mars bg (local_1ff67e2e) orbit on 4801ab51 FAILED 11-20: roof tile grid, blurry near verges, rock-like tree crowns, west wall on grass, car-park blotch; await next orbit + newest stadium md5.
- Cazaly's bg (local_4821b85c) v10 fe0bc1c4 FAILED: rock-like trees/disc palms, diagonal checker grass, water outside creek (ring_180), sawtooth bank (ring_225); await v11.
- Adelaide orbit dde77e8f (westback e1687b6a) FAILED 11-20: bg swapped only 'stands', not 'west_concourse' (green in arches); Oval No.2 dirt; blotchy east field; plain white east wall/end slabs. Then plan asked east/south outer faces repainted: scratchpad/adw/adelaide_es2.glb md5 e9e6c618 (paint_es.py, paint_hotel.py, apply_es.py then apply_hotel.py; hotel wings copper fins, East Gate glass az 2-20, stands outer walls es_facade); sent to bg + plan. Gate the next orbit.
- PR bodies need a line 'Part of row 202' (stadium work) or CI plan job fails.
- Optus roof: director rejected 5f441917 and f2f2080d. Now scratchpad/oroof/optus_roof7.glb md5 1278690b (apply.py..apply7.py chain: flat membrane + 0.3 m rib lines per sat, top trusses removed, rings smoothed, seats outside glass trimmed, gutter flush). Sent to Optus bg local_3b624783 + plan; gate its orbit (denoised).

### Optus roof (2026-11-20 late)
roof11 f693bd05 FAILS truss count: real 50 (Arup/MakMax; sat 7.2 deg spacing), model 52. Next: rebuild roof at 50 bays + 3 arches per bay (LSAA barrel vault), keep bowl NB=52 (obuild/build.py NB drives bowl too). Scripts in scratchpad/oroof (ribline.json, ribprof.npy). Plan + bg-optus told to hold renders.
Progress: obuild/build.py patched to NR=50 roof (RF2/IN2/DR02 resampled 400 pts; backup build52.py); test build OK -> obuild/h50/optus.glb (147k tris). Still to do: (1) truss phase vs satellite (ribprof.npy), (2) X cable lines under overhang (o4), (3) ship step: hout/optus.glb + seats -> optus_stadium.glb (find script: seatbin/split/ship.blend), (4) rerun oroof apply.py..apply11 chain with u = arc/(L/50) instead of i/K, (5) edges p90<=0.75 m (plan ask), (6) overlay 4 quadrant crops + table + md5 to plan local_a479dc03-8848-4245-9544-2b0221533a84 and bg-optus local_3b624783. Arch rise unmeasured: needs low oblique top photo; truss depth 3 m published.
Truss count settled 50 on Google z19 (scratchpad/gsat/g19.png, centre ~px 1180,1070, unroll*.png): 13/13/12/12 per quadrant; 2 under HALO ~186,195 deg. Next: register g19 to model frame (fit roof outline), detect 50 tip dots at outer edge, place each truss there (build.py NR roof), then chain + table (target per-truss max <0.5 m at rim, edges p90<=0.75 m).
Plan also asks: build HALO walkway loop (west roof, ~186-195 deg; path/width from Esri+Google, frame/rail/height from HALO photos, in table); confirm the 2 trusses under it from an on-roof HALO photo; report registration error + per-truss rim error with the build.

### Optus 2026-11-21 progress
- Registration done: scratchpad gsat/reg.py -> gsat/reg.json (cx 1286.7, cy 1033.3, 0.25285 m/px, rot 0.858 deg), overlay gsat/reg_ov.png. Fit is visually tight; edge residuals (outer mean 1.14 / p90 3.4 m, inner 1.0 / 2.65 m) are mostly model edge faults (west inner jag ~170-200 deg, HALO), not registration.
- Next: detect 50 truss-tip dots on g19 using reg.json transform; place trusses per rib in obuild/build.py; then arches, X cables, HALO, edges p90<=0.75.
- Truss tips detected: gsat/tips.py -> gsat/tips.json (50 indices on a 4000-pt resample of roof ring, angles). Exactly 50: 50th peak strength 122 vs 51st -32. Rim bay spacing mean 16.81 m (min 12.8, max 22.2, sd 2.05) -> real trusses are uneven, place per tip. Overlay gsat/tips_ov.png: outer ends land on tip dots.
- Next: measure each truss's INNER end separately (lines currently join same ring index; some NE ones lean off the rib), then write the per-truss rim/inner positions into build.py (replace even RF2 spacing).
- 2026-11-21: inner ends measured (gsat/inner.py -> gsat/truss.json, copied to obuild/truss.json; line-darkness search, inner shift up to +-52 samples, none at search limit). Overlays gsat/truss_q0-3.png: all 50 lie on ribs by eye.
- build.py now places trusses from truss.json (_bays: K steps per bay between measured trusses; membrane UV arcs2 = real RF2 arc). Truss depth 3.0 m (top 3.2, bottom chord +0.2). Rebuilt h50/optus.glb md5 7372fc47...; chk.py: model truss ends sit 0.00 m from measured points.
- Still to do: arches (3/bay), X cables, HALO, edges p90<=0.75, ship merge + apply chain with u=arc/bay, renders, camera-matched overlays, table.
- Ruling 2026-11-21: READY table must list >=10 reference photos per part (roof, HALO, arches, cables, stand, etc.) from Google Images/Street View; <10 = gate fail.
- 2026-11-21: 30 roof refs downloaded to scratchpad opt/refs2 (r01-r30, INDEX.md has per-part counts). Short of 10: trusses 8, X cables 5. Next: 2 truss + 5 cable photos, then measure arch rise/sag (r12, r05 scaled by 3 m truss), build arches + cables.
- Ruling 2026-11-21: READY needs per-part side-by-side boards (render from photo camera vs photo, filename on it) with MATCH/FAIL per region; photos without boards = unchecked = fail. Adelaide bg told es2 e9e6c618 is current (build16).
