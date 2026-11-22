# Adelaide Oval: the director's fault list (2026-11-21)

Resumed 2026-11-21 evening to the MCG standard (Google Earth side-by-sides, seat rule, surrounds). Since #1949 grounds
play at their own size, so these positions now land a few metres from where he stood; the QA pass re-shot all of
them (`tools/grounds/adelaide/qa/faults.views`). Positions are as the ground inspector's C key
copies them ("x y z, facing, looking"); `godot ... GroundInspector.tscn -- --ground=adelaide --views=<file>`
re-shoots any list of them (one "name x y z facing looking" a line).

Generators: `.claude/review/adelaide/tools/gen.py` (stands, roofs, seats), `tools/hill.py` (the Hill),
`tools/hotel.py`; game export `tools/grounds/adelaide/paint.py` + `export.py` (README there).

| # | Where | What he saw | State |
| --- | --- | --- | --- |
| 1 | -1.3 62.1 169.6; -56.8 87.2 31.3; -117.0 116.8 -2.5 | Seats outside the stadium (behind the Riverbank roof, on the east stand's outer slope, behind the hotel deck) | Fixed: gen.py `seat_ok` places a seat only on a raked row, pitch-side of every roof or under one with 2.6 m headroom; a failing block-row goes whole. Riverbank stand ends at its roof, back glazed to the roof |
| 2, 5 | -53.7 15.4 27.6; -59.1 15.7 -28.8 | Gaps between the stands, chairs on the edge of the chasm with no barrier | Fixed: lower bowl runs round both south corners (spec `corner_se`, `corner_sw`; the Esri plan shows it continuous); a 1.1 m parapet on every raised stand end and back. The upper-tier gaps at the corners are real and stay |
| 3 | (lower bowl front) | Is this lip correct? | Fixed: the fence-front wall is now the dark wall of the photos (front_skin), not orange brick |
| 4 | -2.8 107.4 -114.1, facing 183, looking -70 | Is this (west) roof accurate? | Checked against Google Earth from eight directions: five petals, front and back lines within a few metres. The petals were puffier than the real membrane; their rise is now lower (west 3.9 m, east 5.7 m, was 4.9 and 8.8) |
| 6 | -3.1 32.4 -89.2; 7.3 63.3 -103.4 | Box building with two brick towers, flat slab overhanging, seats under it | Fixed: it is a real building (Esri plan, aerial photo: a flat-roofed block behind the petals between the towers). Now 17.45 m, its roof meeting the petals' back, towers 25 m, no seats in it |
| 7 | 75.7 6.0 -30.0, facing 60 | Hill seats were a painted slab | Fixed: 2,860 instanced seats on stepped treads (hill.py) |
| 8 | 86.3 17.2 -65.5, facing 2 | Oversized orange seats down the outside of the west stand's end wall; green roof underside | Fixed: the OSM notch at the stand's north end dropped (way_drop 20, 21). Roof underside green: global lighting fix in PR #1970 (MCG thread) |
| 9 | 37.8 18.1 -81.0; 19.4 17.5 -119.4 | Upper-tier rows uneven, running to the back where the roof crushes them | Fixed: west petals' back edge 24.5 m (back_west_2023), upper tier ends at the roof, the gap to the roof closed; flat decks never seated |
| 10 | 117.7 4.5 79.9, facing 327 | Scoreboard on a floating slab, flat black panel, paper-thin board on stilts | Fixed: the Hill is grassed down to the parkland all round; the amenities box sits on the mound; the screen is a 1.8 m solid cabinet with a bezel and back panels; the shelter roof is a solid slab |
| 11 | 85.1 35.8 26.9, facing 113 | Terrible texture work on the outer precinct | Fixed: the land round the ground is now the parklands from OpenStreetMap (paths, lawns, 4,600 trees, the Torrens, the CBD), and the precinct is the stadium's paved concourse (surrounds.py). The big screen's face is matte (it was glass and mirrored the sky purple); the heritage scoreboard's back has its green plinth, pilasters, trim and sash windows; the buildings round the ground take OSM's wall and roof colours |

Found in our own fly-through and fixed (2026-11-22): the pale rectangle inside the west upper tier at 37.8 18.1 -81.0
was the stand's raked underside (gen.py `open_back`) coming up through the tread where the tier's back steps in north
of the middle tower, so the seat check took out 70 seats there; the underside now meets the slab only where the tier
is clear of it, and the block is seated again (the seat check removes 14 seats in all, was 84). The big screen's ends,
the heritage scoreboard's window frames and the west stand's base read purple at a glancing angle: the stand light's
grass correction (oval3d_stand.gdshader) was mirrored at full strength on rough dark faces; it now rises only as far
as a rough face mirrors (Schlick with roughness). Painted steel and the roof membrane are matte (export.py). The land
next to the stands is a second map at 4 pixels a metre out to 254 m (`surrounds_near.webp`, paving slabs on the
concourse): the 1 m map smeared the concourse and paths seen from the stands. The flat deck behind the west upper
tier is concrete grey, not near-white. The east stand's back walls and north end exterior are grey precast.

The director's west-face notes (2026-11-22, from the Google Earth sheet): "are the dark archways painted on or not?
they shouldnt be"; "make the archways covered in green plants like in the Earth view"; the main entrance "isnt
accurate to real life at all". The arches were dark shapes 7 cm off the wall. Fixed (gen.py `arcade`): the brick face
up to the string course has real openings cut through it, 4 m wide, crowned at 6.4 m, with brick reveals 1.8 m deep,
a dark passage behind, stairs climbing inside and a sandstone beam across each opening (west_2019.jpg); the string
course is a moulding 0.18 m proud. Climbing plants cover the arcade face up to a ragged line about 10.6 m up, the
openings clear (their own part, `ivy.ply`, with a leaf texture, kind 14). The entrance between the towers (`entrance`,
spec `south_block.entrance`) is now a glazed ground floor standing 5 m out with a terrace on its roof inside an
orange-brick rim, three pale canopies leaning back from the rim to the facade, and a dark round-topped pod at each
end; planted stair cores stand out beside both towers (`green_walls`). The base wall's brick no longer stands in front
of the entrance building's recessed glass floor. The heritage scoreboard's arched door is cut 0.35 m into its brick
base, and its sash windows, pilasters, trim and louvres stand proud with real depth (hill.py); they were flat strips.

The stands' pitch-facing storeys and names (2026-11-22, from the 2026 photos chappell, edwinsmith, bradman, riverbank,
wanganeen_oatey and west_stands_2023; rows counted, heights in the photos' proportions under the fitted roofs): the west
is three tiers as built, a 7-row bottom tier, the brick wall, an 8-row middle tier, a glazed level with white columns,
the pale fascia with navy LED panels either side (blank: no ads), a 25-row upper tier and a panelled back wall up to the
roof (it was two even tiers with the whole upper tier red). The Bradman Pavilion is its own section: cream wall, red
middle tier, the cream facade with real window openings, a timber door and fanlight, cornice, the balcony with its
clock, the green glazed level, the ledge carrying the letters, red upper tier and the glass box under the roof. The east
and Riverbank stands have their stacked levels: LED ribbon, red middle tier, glazed level with columns, balcony slab
with its LED ribbon and glass rail, upper glazed level, fascia. Every name is solid raised letters (DejaVu Sans, spacing
and weight matched to each photo): CHAPPELL STAND, SIR EDWIN SMITH STAND, SIR DONALD BRADMAN PAVILION, GAVIN WANGANEEN
STAND, JACK OATEY STAND, MAX BASHEER STAND, FOS WILLIAMS STAND, RIVERBANK STAND (gen.py `tier_parts`, spec `fronts`,
`zones`). The west roof's back band keeps its old base (spec `back_z0`). The petals' front hems now arch up between
the valleys as in the photos (spec `lobet`: west full lobe height at the hem, east 0.7); they were nearly level.

Still short (2026-11-22): the entrance glass band's lettering is unreadable in Google Earth (plain glass, nothing
invented); the camera and media boxes cut into the upper tiers, the player benches in front of the Bradman, and the
V struts under the Riverbank's middle tier are not built yet; the east names' places along the stand are read from one
oblique photo (to within a few metres); the stands hold 38,200 seats plus the Hill's 2,900, short of the real ground,
and the photos' widths suggest the west stand may stand taller than its fitted roof allows (unresolved: Google Earth
views from the pitch do not frame like ours yet); the roof petals' valleys read softer than the real membrane;
parkland canopy is thinner; OSM's roof colours paint some nearby buildings salmon pink.

Found in the Google Earth pass (2026-11-21) and fixed: the Riverbank Stand's back was a dark navy drum (now storeys:
stone and glass at the street, a maroon band, glass, pale louvres with white struts to the roof); the lower bowl and
Riverbank top tier seats were blue (now grey-green and sage, from the photos); the Western Grandstand's brick was
dark maroon (now the photos' orange-red).
