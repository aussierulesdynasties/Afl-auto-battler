# Fix Cazaly's west club building

Session local_c57fc1a0, worktree `.claude/worktrees/cazalys-west`.

## Where the work is now

All commits are on main (branch diff against main is empty). Open question is in stadium_lead.md.

---

## The session's handoff file (verbatim, C-Users-DANTE-Documents-GitHub-Afl-auto-battler-claude-worktrees-cazalys-west.md)

# Handoff: cazalys-west worktree

### State
available (WIP pushed, not READY). PR #1898: auto-merge OFF, keep it off until the lead passes it.

### Latest (2026-11-21)
- c2d5f5173 pushed: club h 5.75 (+0.5 parapet = 6.25 top, wvEC ray-cast 6.11-6.35 at NW face s2-6); NW return past box wrap + wall above low strip = render_white.
- Aerial wrap (wrap_board.png): roof slab 1.2-10.8 m along NW face, wall hidden under eave; model box wrap 2.0 m (photo). 4.1 m was wvEC projection, not aerial. Reported to lead.
- Now: earth commit pushed (glb 00345ce0): red earth behind bldg_w done. Raised block open: lower roof flat (v1 4.4-4.5 both edges); face v1 1.6 m vs v4 2.4 m, DA 1.64 m; v4 band may include cast shadow. Awaiting lead ruling. Auto-merge off.


### Task
Make the Cazaly's club entrance (on bldg_s, "club" in cazalys.json, Mulgrave Rd SE corner) a verbatim copy of Commons photo 12. Fix the lead's 9 faults. Also copy bldg_w as the real shed and the rest of bldg_s's Mulgrave Rd front. Brief from the lead, local_6e4c78c4; the lead confirmed I own bldg_s and bldg_w.

### Where things are
- Worktree .claude/worktrees/cazalys-west, branch claude/cazalys-west-bldg, HEAD see git log (pushed WIP)
- build.py: front_path() and club_front(); building() supports 'replace' (a satellite-traced edge)
- cazalys.json: club_front block (canopy [-0.5,12.9,7.5,5.0,0.45], posts, sign, bays, bollards, drive, garden, lobby h 5.3)
- paint.py: soffit_white, conc_drive, mulch, shrub, palm_trunk, palm_frond (RGBA; mb.py alpha list now includes palm_frond)
- Refs: ref/aw2013/*.jpg (Andrew Watson 2013), ref/entrance_2018_01.jpg; scratch thumbnails p12.jpg and e18.jpg plus renders r7-r9 in the session scratchpad
- Re-traced from the satellite (scratchpad ent2b.png, 14 px/m, x=10 at px 0, y=-95 at py 0): the real SE corner is at x 33.2, y -137.9; the white canopy roof spans x 25.4-36.8, y -130.4 to -140.7; the shopfront notch runs (35.7,-123.6) to (39.6,-111); the garden island is at x 29-44, y -142 to -151. Photo 12 is taken from the NE of the corner looking SW (the island is at the left).

### Unfinished (open faults vs photo 12)
- The canopy is now a wedge (canopy_poly). Still wrong: the fascia band reads too thick, and the ground under the front is missing since the drive was removed.
- Glazing is now smoothed (Catmull-Rom); its height and lean still need fixing per (b).
- Drive, garden, palms and car park were handed to bg-cazalys (outside the fence); data in side-session-notes cazalys_outside_fence_drive_garden.json.
- Camera: the PnP fit failed twice, so I switched to the vanishing-point method (work/vp.py, vp2.py; gitignored scratch copies). With a horizon at y 361 (800x600 frame), the shopfront vanishing point at (-9,361) and f 582, the post bases land on x 36.1-36.5 at y -136.4, -133.4 and -130.5 (about 3 m apart), which matches the satellite canopy edge (x 36.8). The eye is about 45.0,-124.9,1.6, target 33.3,-134.0,3.2.
  Full-res reads (1920x1440 frame, scratchpad z1.jpg). R post base (1106,1089). Bollards b1-b5, top/base: x 1132 (1022.5/1098.5), 1216 (1027.5/1109), 1294 (1034/1121.5), 1368 (1040/1135), 1442 (1048.5/1150). The bollard top and base lines meet at VP (206,945), so the horizon is at about y 945.
  work/vp3.py jointly fits f, eye, yaw, cy, bollard spacing and the R post: 7 px mean error, but the results are implausible (0.8 m bollard spacing, eye pinned at the height bound). So the assumed kerb line (3 m off the notch face) is probably wrong: the poster face right of the entrance runs (33,-131) to (35.7,-123.6). Next: count the bollards on the satellite / a 2018 photo to get the real spacing, fix it, and refit with the eye height 1.5-1.7 m.
- bldg_w is still a plain prism: copy the real shed from the satellite and photos.
- Rest of the bldg_s front: copy from aw2013.
- Measured table: both buildings, 10 photos per part, a side-by-side per part.
- GLB rebuild with proofs.py, md5, then READY (HEAD == ls-remote). Tell bg session local_4821b85c the md5.

### Street View (lead: main side-by-sides; photo 12 is the cross-check)
- Pano 1 (Feb 2025), panoid dxiQEa8tBLbzx8OQGPV1oA, at -16.9370524,145.7494604 = local (42.44,-154.87). Eye z 2.5; viewport 1024x768, 75y = hfov 75.
- The g01 render fails: the light towers line up, but bldg_s's front is wrong. The real Mulgrave Rd front is a two-storey pavilion: a glazed ground floor under a continuous white awning (~4 m), a grey-glazed upper floor with sloped white struts and "Cairns Football League" lettering, and a white box (~11 m) by the entrance. The model has a uniform 9 m block. Next: rebuild it as storeys, then 10+ panos with a side-by-side per part.
- DONE c9d6f6aac (pushed WIP): south_front() in build.py plus a cazalys.json south_front block (path on the real wall from (25.4,-141.3) to (33.2,-137.9); eave 6.7; box 7.4/8.6; club h 6.7).
- Solved pano camera (the URL position is wrong): eye (44.52,-166.93,3.0), target (32.09,-158.53,3.0), vfov 67.45 (f 449, heading +4.0). The c02.jpg overlay now lines up the eave, awning and ends. Left to do: the box is a little short and narrow, the struts' spacing, the "Cazalys" logo and "Cairns Football League" lettering, then the remaining Street View frames (10+ per part), bldg_w, GLB/md5, READY.
- Scratchpad sv/: sv01.jpg, sv02_h300.jpg, g01.jpg. Browser tab "seed" is still open: close it when done.

### Latest (2026-11-21, commit 39cdf736a pushed)
- Box measured 8.9-9.4 m (not ~11); lettering really reads "CAIRNS AUSTRALIAN FOOTBALL LEAGUE"; both modelled hand-made (paint.py sign_cafl, sign_clublogo). Tell the lead both points in the READY.
- Pano poses: p1 eye (44.52,-166.93) H 304.03; p2 eye (-13.68,-180.48) H 328.11; p3 eye (-9.95,-179.6) H 1.58. scratchpad amap.py maps pixel x -> a (wall offset -2.3).
- CONFLICT: the same features land 7-12 m apart between panos (logo p1 32.8-39.1 vs p3 20.5-24.9). Agreed: recess/step at a 55-56 (= satellite bend 55.1). TESTED: p1 and p3 agree on the logo only if its plane is ~+4.5 m (road side) of the path line (logo a ~26-31.5); negative setbacks diverge. So either the traced path sits ~4.5 m north of the real upper facade, or a pano heading is off. Check the path against the satellite roof edge next. Was: test whether the upper wall offset differs from -2.3 (setback) by solving the offset that makes p1 and p3 agree, then re-render all three boards.
- Satellite check: the traced path IS the awning roof's road edge, so a +4.5 m facade is impossible; pano 3's heading is the bad one. Decision: east features from p1 (MATCH), west from p2 (frontal); drop p3 for positions.
- 9a9f3e2c1 pushed: posts = json list (measured to 37.4; 41.3-53.0 extrapolated at 3.9 m, verify on p2). Overlay c09.jpg.
- 86c031a2b pushed: west wing first pass (json south_front.west: recess 51.5-56.7 rust wall + cream mullions, glass 56.7-66.7, plain logo2 67.5-72.5, west box 72.5-81.7 raised roof, awning +0.5 west of recess). Board scratchpad w01b.jpg (pano 2 pose). Logo position and awning W end MATCH. FAIL: raised west skillion (photo: deep overhang rising west, glass band under it), recess reads dark not red, struts (photo x 155/205/540/645 in 800 frame), no posts west of a 53 (photo posts every ~55 px), upper glass runs too long east of the recess.
- 03f0c82e8 pushed: west wing placed from pano 2 (posts list now includes 53.6-79.9, struts 51.9/56.6/66.2/73.4/78.4, recess 51.6-56.2 drawn on the wall face because the club prism hid it, logo2 67.9-72.2, west box 73.0-80.9 with low glass band + white above, rust (122,60,46)). Board w05b.jpg: logo, upper glass, recess, struts, posts, raised roof MATCH. FAIL: the club prism west of the path end (OSM corner -48.55,-166.18 then NW to -64.55,-148) shows a 6.7 m glass/white block where the photo shows only trees; the satellite (trusting-edison .claude/review/cazalys_bldg_w_sat19.png, bottom right) shows a lower white NW wing set back. Lower/trim it next.
- 09915e581 pushed: building() takes "low": [X, Y, h] and splits the footprint (clip(), prism_cap()); club SW corner x<-42.6, y<-140 is 4.3 m. Board w06b.jpg. Its height (4.3) is estimated from frame sv/sv07_wvEC_h25.jpg (pano wvECTXtTb2HgTQPZfHvKjw at -16.9373867,145.7485185, h25 30y): measure it properly from that frame. That frame also shows the west box's fan of cream raking struts on the white wall and a PARKING P2 sign: compare.
- Browser tab "seed" still open on that pano.
- Lead asked: aerial before trimming. Done: scratchpad nw.py/nw.png/nwc.png (Esri z19) show roof over the whole SW corner, so it is kept (low, not trimmed). Board nw_board.jpg sent to lead. Open FAIL: west box has ~6 cream struts fanned on its white wall (model 2): solve the wvEC camera, measure struts + low wing height.
- 2026-11-21: triangulated the box from pano 2 and the solved wvECTX camera (scratchpad tri.py; held-out logo W check 72.1 vs 72.2 PASS). Box face E edge (-39.0,-160.6), a 75.7, setback 2.5; W wall (-49.2,-159.9), a 85, setback 6.5. The model has it at 73-80.9 on the wall line, which is WRONG. Next: give the box its own face line in build.py; place 9 V-struts (wvEC feet x 147,183,225,270,317,330,352,373,393; heads 128,162,203,250,297,357,380,402,420); measure the low-wing height with a held-out check point. Lead told.
- SUPERSEDED: the aerial (scratchpad box_aerial.png) rejects the 15° face; the box is flush with the wall line (zoomed z7.png; old x107 was a power pole). From wvEC on the wall line (tri2.py): box E end a 78.5 vs pano 2's 73.0 (CONFLICT); box W end a 90.6, past the path end, so the box wraps the SW corner. SETTLED 578f4728a: box 78.5-86.5 (aerial roof break at a 80, box_aerial2.png); the path now starts at the OSM SW corner (-48.55,-166.18). Board box_b1.jpg (wvEC render: vfov 26.7, eye -57.46,-198.35,2.5, target -20.6,-120.6,5.5). 224b9d56d pushed: 'render_white' (paint.py), box roof 7.75/7.15 (0.46 m drop), west.fan = 9 [foot, head] struts (build.py beam), "low" now takes a 4th entry for the wall material. Board box_b3.jpg. aa9a67bae pushed: the path now starts with the wrap point (-51.26,-163.1) (aerial corner_opts.png: the wrap follows the roof edge; straight does not); box 78.5-90.6; strut heads at box_o*0.8 out. Board box_b5.jpg. 661263501 pushed: roof follows runs, struts on the wall (o 0.3) foot->head at measured a, no eave over the box (runs from A(box c0)), awning fascia render_white, strut 78.4 removed. Board box_b7.jpg: box MATCH. Open FAIL: a full-height white block at the far left of the wvEC view (club prism north of y -140, west of the wrap) where the photo shows the low wing roof. Next: fix it with the aerial, measure the low wing height (held-out check), then bldg_w, GLB/md5, READY.
- 61a27b9c0 pushed: box wrap 2.0 m (box 78.5-88.5); the far-left 65 px block was the box roof wrapping too far (rc.py ray-cast: wvEC rays enter bldg_s at ~36 m on the NW face; the photo parapet y212 = z 6.3-6.7 = the main block). Board box_b9.jpg. Table: low strip 4.3 m = upper bound, not measured (pano 2, p2b.py). Open FAIL: the main block's NW wall renders dark 'club' (photo white) and its top is ~18 px high (the 0.5 m parapet?). Next: give the NW face a white wall, then bldg_w, GLB/md5, READY.
- 233eff911 pushed: "low" = [p0, p1, depth 4.0, h 4.3, wall] along the NW face (hclip in build.py). Pano 2 bound: nothing above ~4.3-4.5 m within 8 m of the corner (p2b.py, rays at 68-85° to wvEC). Open FAIL (box_b8.jpg): the far-left render block tops out ~65 px above the photo parapet y212; a taller part further back. Next: ray-cast that pixel in Blender to find the piece, size it to y212, check against the aerial.
- (older) Wing height: the wvEC frame alone can't fix depth (wingz.png: parapet at y212 = 6.3 m if on the NW face, 4.3 m if 17 m back). The aerial lowY.png shows a ~4 m low strip along the NW face from the box to y ~-122, not the axis-aligned split. Next: triangulate the parapet corner from sv04 + wvEC (wing.py has zat()); held-out check = awning top 3.3 m (wvEC reads 3.4-3.5, PASS); then rebuild "low" as a strip along the NW face (needs a half-plane clip in build.py).
- Still to do (posts done): posts as explicit list (0.8, 6.35, 10.1, 13.9, 17.8, 21.7, 25.6, 29.7, 34.0, 37.4), west wing, 10+ frames/part with boards, bldg_w, GLB md5, READY.

### Gotchas
- tex/, ref/ and ge/ are gitignored: run `python paint.py` before Blender.
- Render: blender -b --python model/shot.py -- outdir name:ex,ey,ez:tx,ty,tz:fov
- Keep CRLF in .py files. Write scripts with the Write tool (heredocs with ''' break).
