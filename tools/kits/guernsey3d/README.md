# Guernsey copied from its photo, onto the 3D player

Director, 2026-11-18: "copy the real guernsey EXACTLY ... THE ENTIRE GUERNSEY ... only remove the sponsors".

Each club's guernsey is cut to its own photo's outline (hem, width, armholes, neck) and wears the
photo's design as a picture. Run from a work folder holding `ref/CODE_front.png`, `ref/CODE_back.png`
(the shop photos) and `orig_mh.glb` (the uncut body: `git show 24541c278:assets/oval3d/player_mh.glb`).

1. Trace the photo into a flat design, sponsors filled with the colour round them
   (palette = the cloth colours; boxes = x0,y0,x1,y1 of each sponsor or logo on the 2000 px photo):

       python trace.py ESS front "#271F25,#F4062F" "930,500,1070,610;690,590,920,730;1050,600,1330,700;1110,1430,1320,1580;840,200,1170,250" design_ESS_front.png
       python trace.py ESS back "#291F26,#F4082F" "790,320,1200,450;520,1585,610,1635" design_ESS_back.png

2. Cut the body's guernsey to that outline (smoothed below the chest, holes filled, the hem panel
   skinned to the shorts, front/back split on the guernsey's depth-middle as Oval3D._depth_middle):

       python recut5.py orig_mh.glb wrap5_ESS.glb ESS

3. Put the design into the atlas cell (outside the outline each pixel takes its nearest clean
   inside pixel, so no edge streaks): `python fillcell.py ESS 4 kits_today.png`

4. Capture (`tools/visual/capture_guernseys3d.gd -- OUT ESS [rest|idle]`) and board it:
   `python board.py ESS OUT board_ESS.png` (photo | model | 50% overlay, front and back).

Done for: ESS. The game still loads one body (player_mh.glb) for every club; a per-club guernsey
in the game is not built yet.
