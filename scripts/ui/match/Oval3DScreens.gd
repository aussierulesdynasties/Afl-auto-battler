class_name Oval3DScreens
extends Node3D
## The ground's big screens and its fence signs, live in the 3D match (row 202 2b).
##
## Screens: a ground model's screen faces (a surface whose material or node is named as a screen
## or scoreboard face, SCREEN_NAMES) are found when the match is built, and a flat face is laid
## over each, just in front, so the model's own UVs never matter. Every face shows
## the same picture: both clubs in their colours with goals, behinds and points, and the quarter
## and minute under them; after a goal, a GOAL card in the scorer's colours with his number and
## name, and while the TV replays the goal the replay itself plays on it (the camera the TV is
## using, drawn small). The picture is redrawn only when it changes, except during a replay.
##
## Fence signs: a ring of boards standing a metre in front of the boundary fence, round every
## ground, each board in one club's colours with its name, home and away in turn.
##
## How the club looks never changes a result (design bible): nothing here reads back into play.

## A surface whose material, or the node holding it, has one of these names is a screen face.
const SCREEN_NAMES := ["screen", "screen_off", "screens", "scorefront", "scoreboard",
		"scoreboard_n", "north_scoreboard_mat", "south_scoreboard_mat", "board_front", "sbface"]
## Faces smaller than this (m^2) are not screens (a sign, a sliver of the frame).
const MIN_AREA := 4.0
## Triangles more than this far (m) from a screen's first triangle belong to another screen.
const SCREEN_SPAN := 30.0
## The face is laid this far (m) in front of the model's screen, clear of its frame and posts.
const LIFT := 0.3
## The screen picture's height in pixels; its width follows the screen's shape.
const FACE_H := 320
## s (real time) the GOAL card stays up after a goal when no replay is shown.
const GOAL_HOLD := 10.0
## The replay drawn on the screens, in pixels.
const REPLAY_PX := Vector2i(320, 180)

## The boards: how far in front of the fence they stand, how tall, how long each is (m).
const SIGN_INSET := 1.0
const SIGN_H := 0.9
const SIGN_LEN := 9.0
const SIGN_LEAN := 0.12   # m the top sits back from the foot
const SIGN_PX := Vector2i(1152, 112)  # one board's picture

var home := ""
var away := ""
var faces: Array = []          # MeshInstance3D per screen
var signs: MeshInstance3D
## What the screens show: each club's goals and behinds, the clock line, and a goal's
## {side, who, num} while its card is up ({} otherwise).
var goals := [0, 0]
var behinds := [0, 0]
var clock := ""
var goal := {}
var replay: Texture2D = null   # the replay's picture while one plays
var _vps: Array = []           # each screen's picture (SubViewport), drawn by its _Face
var _sign_vp: SubViewport      # both clubs' boards, side by side
var _replay_vp: SubViewport    # the replay, drawn small for the screens
var _replay_cam: Camera3D
var _goal_left := 0.0          # s the GOAL card has left when no replay holds it
var _replaying := false


## Lays the faces over `ground`'s screens (a node already in the tree, under `oval`) and the
## ring of boards inside `fence` (half length and width of the boundary fence, m). With no
## clubs (the ground inspector) nothing is built: the model shows its own screens.
func build(oval: Node3D, ground: Node3D, fence: Vector2, p_home: String, p_away: String) -> void:
	home = p_home
	away = p_away
	name = "Screens"
	if home == "" or away == "":
		return
	if ground != null:
		for f in find_faces(oval, ground):
			_add_face(f)
	_make_signs(fence)


## Every screen face under `ground`, in `oval`'s own space: [{centre, normal, right, up, w, h}],
## facing the middle of the ground.
static func find_faces(oval: Node3D, ground: Node3D) -> Array:
	var tris := []  # [a, b, c, normal toward the middle, area]
	var to_oval := oval.global_transform.affine_inverse()
	for mi in _meshes(ground):
		var m: Mesh = mi.mesh
		if m == null:
			continue
		var node_hit := _is_screen_name(str(mi.name)) or _is_screen_name(str(mi.get_parent().name))
		var xf: Transform3D = to_oval * mi.global_transform
		# A screens node that names its face by material (the MCG's "screens" holds the face, its
		# frame, glass and housing) gives only that face: the rest is not screen.
		var by_mat := false
		for s in m.get_surface_count():
			var sm: Material = mi.get_surface_override_material(s)
			if sm == null:
				sm = m.surface_get_material(s)
			if sm != null and _is_screen_name(sm.resource_name):
				by_mat = true
		for s in m.get_surface_count():
			var mat: Material = mi.get_surface_override_material(s)
			if mat == null:
				mat = m.surface_get_material(s)
			var hit := (node_hit and not by_mat) or (mat != null and _is_screen_name(mat.resource_name))
			if not hit:
				continue
			var arr: Array = m.surface_get_arrays(s)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			var n := idx.size() if not idx.is_empty() else v.size()
			for i in range(0, n - 2, 3):
				var a: Vector3 = xf * v[idx[i] if not idx.is_empty() else i]
				var b: Vector3 = xf * v[idx[i + 1] if not idx.is_empty() else i + 1]
				var c: Vector3 = xf * v[idx[i + 2] if not idx.is_empty() else i + 2]
				var cr := (b - a).cross(c - a)
				var area := cr.length() * 0.5
				if area < 0.01:
					continue
				var nrm := cr.normalized()
				var mid := (a + b + c) / 3.0
				var inward := Vector3(-mid.x, 0.0, -mid.z).normalized()
				if nrm.dot(inward) < 0.0:
					nrm = -nrm
				# Upright, and turned to the ground (a screen's sides and top are not its face).
				if absf(nrm.y) > 0.35 or nrm.dot(inward) < 0.4:
					continue
				tris.append([a, b, c, nrm, area, mid])
	# Group into screens: a triangle joins the first screen it lies near.
	var groups := []
	for t in tris:
		var put := false
		for g in groups:
			if (g["first"] as Vector3).distance_to(t[5]) < SCREEN_SPAN:
				g["tris"].append(t)
				put = true
				break
		if not put:
			groups.append({"first": t[5], "tris": [t]})
	var out := []
	for g in groups:
		var area := 0.0
		var nsum := Vector3.ZERO
		for t in g["tris"]:
			area += float(t[4])
			nsum += (t[3] as Vector3) * float(t[4])
		if area < MIN_AREA:
			continue
		var nrm := Vector3(nsum.x, 0.0, nsum.z).normalized()
		var right := (-nrm).cross(Vector3.UP).normalized()
		var lo := Vector2(INF, INF)
		var hi := Vector2(-INF, -INF)
		var front := -INF
		for t in g["tris"]:
			for k in 3:
				var p: Vector3 = t[k]
				var q := Vector2(p.dot(right), p.y)
				lo = Vector2(minf(lo.x, q.x), minf(lo.y, q.y))
				hi = Vector2(maxf(hi.x, q.x), maxf(hi.y, q.y))
				front = maxf(front, p.dot(nrm))
		var w := hi.x - lo.x
		var h := hi.y - lo.y
		if w < 2.0 or h < 1.0:
			continue
		var mid2 := (lo + hi) * 0.5
		# The centre: across and up from the rectangle, out to the screen's front plane.
		var centre := right * mid2.x + Vector3.UP * mid2.y
		var c0 := centre - nrm * centre.dot(nrm) + nrm * (front + LIFT)
		out.append({"centre": c0, "normal": nrm, "right": right, "up": Vector3.UP, "w": w, "h": h})
	# A piece of a screen found apart from it (its side panel, a second strip of its face) is
	# not a screen of its own: a face whose middle lies on a bigger face is dropped.
	out.sort_custom(func(p, q): return float(p["w"]) * float(p["h"]) > float(q["w"]) * float(q["h"]))
	var kept := []
	for f in out:
		var inside := false
		for k in kept:
			var d: Vector3 = f["centre"] - k["centre"]
			if absf(d.dot(k["right"])) < float(k["w"]) * 0.5 + 1.0 and absf(d.y) < float(k["h"]) * 0.5 + 1.0 \
					and absf(d.dot(k["normal"])) < 4.0:
				inside = true
				break
		if not inside:
			kept.append(f)
	return kept


static func _is_screen_name(s: String) -> bool:
	var k := s.to_lower()
	# Godot suffixes duplicate node names ("screen2", "screen_001"): ignore a trailing count.
	while k.length() > 0 and (k[-1].is_valid_int() or k[-1] == "_" or k[-1] == "."):
		k = k.substr(0, k.length() - 1)
	return SCREEN_NAMES.has(k)


static func _meshes(n: Node) -> Array:
	var out := []
	if n is MeshInstance3D:
		out.append(n)
	for c in n.get_children():
		out.append_array(_meshes(c))
	return out


func _add_face(f: Dictionary) -> void:
	var w := float(f["w"])
	var h := float(f["h"])
	var vp := SubViewport.new()
	vp.name = "Picture%d" % faces.size()
	vp.size = Vector2i(int(FACE_H * clampf(w / h, 0.8, 4.0)), FACE_H)
	vp.disable_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	add_child(vp)
	var board := _Face.new()
	board.screens = self
	board.size = Vector2(vp.size)
	vp.add_child(board)
	_vps.append(vp)
	var q := QuadMesh.new()
	q.size = Vector2(w, h)
	var mi := MeshInstance3D.new()
	mi.name = "Face%d" % faces.size()
	mi.mesh = q
	mi.transform = Transform3D(Basis(f["right"], f["up"], f["normal"]), f["centre"])
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_texture = vp.get_texture()
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	faces.append(mi)


## The score as the scoreboard shows it: goals and behinds each side, and the clock line
## ("Q2 14'", or a break's name).
func show_score(p_goals: Array, p_behinds: Array, p_clock: String) -> void:
	goals = [int(p_goals[0]), int(p_goals[1])]
	behinds = [int(p_behinds[0]), int(p_behinds[1])]
	clock = p_clock
	_redraw()


## A goal: the GOAL card in the scorer's colours, his number and name.
func show_goal(side: int, who: String, num: int) -> void:
	goal = {"side": side, "who": who, "num": num}
	_goal_left = GOAL_HOLD
	_redraw()


## Each frame: the GOAL card's time, and the replay while the TV shows one (`tv_cam`, the
## camera filming it).
func frame(wall: float, replaying: bool, tv_cam: Camera3D) -> void:
	if faces.is_empty():
		return
	if replaying:
		if _replay_vp == null:
			_make_replay()
		_replay_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		_replay_cam.global_transform = tv_cam.global_transform
		_replay_cam.fov = tv_cam.fov
		if not _replaying:
			replay = _replay_vp.get_texture()
			for vp: SubViewport in _vps:
				vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
				vp.get_child(0).queue_redraw()
		_replaying = true
		return
	if _replaying:
		# The replay is over: the GOAL card a little longer, then the score.
		_replaying = false
		replay = null
		_replay_vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		_goal_left = minf(_goal_left, 3.0)
		_redraw()
	if not goal.is_empty():
		_goal_left -= wall
		if _goal_left <= 0.0:
			goal = {}
			_redraw()


func _redraw() -> void:
	for vp: SubViewport in _vps:
		vp.get_child(0).queue_redraw()
		if not _replaying:
			vp.render_target_update_mode = SubViewport.UPDATE_ONCE


func _make_replay() -> void:
	_replay_vp = SubViewport.new()
	_replay_vp.name = "ScreenReplay"
	_replay_vp.size = REPLAY_PX
	_replay_vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	add_child(_replay_vp)
	_replay_cam = Camera3D.new()
	_replay_cam.top_level = true
	_replay_cam.far = 900.0
	# The screens are not drawn in the replay they show (no picture inside the picture).
	_replay_cam.cull_mask = 1
	_replay_vp.add_child(_replay_cam)
	_replay_cam.current = true
	for f in faces:
		(f as MeshInstance3D).layers = 2


# --- Fence signs ---------------------------------------------------------------------------

func _make_signs(fence: Vector2) -> void:
	_sign_vp = SubViewport.new()
	_sign_vp.name = "SignPicture"
	_sign_vp.size = Vector2i(SIGN_PX.x * 2, SIGN_PX.y)
	_sign_vp.disable_3d = true
	_sign_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	add_child(_sign_vp)
	var art := _Signs.new()
	art.home = home
	art.away = away
	art.size = Vector2(_sign_vp.size)
	_sign_vp.add_child(art)
	var a := fence.x - SIGN_INSET
	var b := fence.y - SIGN_INSET
	# Board ends spaced evenly along the ellipse (by arc length).
	var ring := PackedVector2Array()
	var steps := 2048
	var lens := PackedFloat32Array([0.0])
	for i in steps + 1:
		var t := TAU * float(i) / steps
		ring.append(Vector2(a * cos(t), b * sin(t)))
		if i > 0:
			lens.append(lens[i - 1] + ring[i].distance_to(ring[i - 1]))
	var total := lens[steps]
	var count := maxi(2, int(round(total / SIGN_LEN / 2.0)) * 2)  # even: home and away in turn
	var front := SurfaceTool.new()
	front.begin(Mesh.PRIMITIVE_TRIANGLES)
	var back := SurfaceTool.new()
	back.begin(Mesh.PRIMITIVE_TRIANGLES)
	var j := 0
	var seg := 6  # pieces per board, so it follows the curve
	for k in count:
		var u0 := 0.0 if k % 2 == 0 else 0.5
		var pts := []
		for s in seg + 1:
			var want := total * (float(k) + float(s) / seg) / count
			while j < steps - 1 and lens[j + 1] < want:
				j += 1
			var f := (want - lens[j]) / maxf(0.0001, lens[j + 1] - lens[j])
			pts.append(ring[j].lerp(ring[j + 1], f))
		for s in seg:
			var p0: Vector2 = pts[s]
			var p1: Vector2 = pts[s + 1]
			var o0 := p0.normalized() * SIGN_LEAN
			var o1 := p1.normalized() * SIGN_LEAN
			var a0 := Vector3(p0.x, 0.0, p0.y)
			var a1 := Vector3(p1.x, 0.0, p1.y)
			var t0 := Vector3(p0.x + o0.x, SIGN_H, p0.y + o0.y)
			var t1 := Vector3(p1.x + o1.x, SIGN_H, p1.y + o1.y)
			var ua := u0 + 0.5 * float(s) / seg
			var ub := u0 + 0.5 * float(s + 1) / seg
			var inward := -Vector3(p0.x + p1.x, 0.0, p0.y + p1.y).normalized()
			_quad(front, a0, a1, t1, t0, inward, Vector2(ua, 1.0), Vector2(ub, 1.0), Vector2(ub, 0.0), Vector2(ua, 0.0))
			var d0 := -inward * 0.04
			_quad(back, a0 + d0, a1 + d0, t1 + d0, t0 + d0, -inward, Vector2.ZERO, Vector2.ZERO, Vector2.ZERO, Vector2.ZERO)
	var mesh := front.commit()
	back.commit(mesh)
	signs = MeshInstance3D.new()
	signs.name = "FenceSigns"
	signs.mesh = mesh
	var fm := StandardMaterial3D.new()
	fm.albedo_texture = _sign_vp.get_texture()
	fm.emission_enabled = true
	fm.emission_texture = _sign_vp.get_texture()
	fm.emission_energy_multiplier = 0.35
	fm.roughness = 0.7
	fm.cull_mode = BaseMaterial3D.CULL_DISABLED
	fm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	signs.set_surface_override_material(0, fm)
	var bm := StandardMaterial3D.new()
	bm.albedo_color = Color(0.13, 0.14, 0.15)
	bm.roughness = 0.9
	bm.cull_mode = BaseMaterial3D.CULL_DISABLED
	signs.set_surface_override_material(1, bm)
	add_child(signs)


static func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, n: Vector3,
		ua: Vector2, ub: Vector2, uc: Vector2, ud: Vector2) -> void:
	for pair in [[a, ua], [c, uc], [b, ub], [a, ua], [d, ud], [c, uc]]:
		st.set_normal(n)
		st.set_uv(pair[1])
		st.add_vertex(pair[0])


## The text colour that reads on `bg`: the club's other colour when it stands out, else white
## or near-black.
static func ink_on(bg: Color, other: Color) -> Color:
	if _contrast(bg, other) >= 3.0:
		return other
	return Color.WHITE if _contrast(bg, Color.WHITE) >= _contrast(bg, Color(0.07, 0.07, 0.08)) else Color(0.07, 0.07, 0.08)


static func _contrast(a: Color, b: Color) -> float:
	var la := a.get_luminance() + 0.05
	var lb := b.get_luminance() + 0.05
	return maxf(la, lb) / minf(la, lb)


## The screen picture: the scoreboard, or the GOAL card (with the replay under it while one plays).
class _Face:
	extends Control
	var screens: Oval3DScreens
	const BG := Color(0.035, 0.04, 0.05)

	func _draw() -> void:
		var home := screens.home
		var away := screens.away
		var goals: Array = screens.goals
		var behinds: Array = screens.behinds
		var clock := screens.clock
		var font: Font = UiKit.BOLD
		var w := size.x
		var h := size.y
		draw_rect(Rect2(Vector2.ZERO, size), BG)
		if not screens.goal.is_empty():
			_draw_goal(font, w, h)
			return
		# Two club rows, then the clock.
		var row_h := h * 0.36
		for side in 2:
			var code := home if side == 0 else away
			var cols: Array = GameDB.club_colours(code)
			var y := h * 0.06 + side * (row_h + h * 0.04)
			var band := Rect2(w * 0.03, y, w * 0.94, row_h)
			draw_rect(band, cols[0])
			var ink: Color = Oval3DScreens.ink_on(cols[0], cols[1])
			# The score on the right, then the name in the room left of it: the club's short
			# name on a narrow screen, shrinking only if even that will not fit.
			var line := "%d.%d" % [goals[side], behinds[side]]
			var pts := str(int(goals[side]) * 6 + int(behinds[side]))
			var sfs := int(row_h * 0.62)
			var gap := w * 0.035
			while sfs > 12 and font.get_string_size(pts, HORIZONTAL_ALIGNMENT_LEFT, -1, sfs).x \
					+ font.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, int(sfs * 0.8)).x + gap > w * 0.52:
				sfs -= 2
			var pts_w := font.get_string_size(pts, HORIZONTAL_ALIGNMENT_LEFT, -1, sfs).x
			var line_w := font.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, int(sfs * 0.8)).x
			var pts_x := w * 0.95 - pts_w
			var line_x := pts_x - gap - line_w
			var sb := y + row_h * 0.5 + font.get_ascent(sfs) * 0.36
			draw_string(font, Vector2(line_x, sb), line, HORIZONTAL_ALIGNMENT_LEFT, -1, int(sfs * 0.8), ink)
			draw_string(font, Vector2(pts_x, sb), pts, HORIZONTAL_ALIGNMENT_LEFT, -1, sfs, ink)
			var room := line_x - gap - w * 0.06
			var fs := int(row_h * 0.52)
			var nm := GameDB.club_name(code).to_upper()
			if font.get_string_size(nm, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > room:
				nm = GameDB.club_short(code).to_upper()
			while fs > 12 and font.get_string_size(nm, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > room:
				fs -= 2
			var base := y + row_h * 0.5 + font.get_ascent(fs) * 0.36
			draw_string(font, Vector2(w * 0.06, base), nm, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, ink)
		var cfs := int(h * 0.13)
		while cfs > 12 and font.get_string_size(clock, HORIZONTAL_ALIGNMENT_LEFT, -1, cfs).x > w * 0.92:
			cfs -= 2
		draw_string(font, Vector2(0, h * 0.96), clock, HORIZONTAL_ALIGNMENT_CENTER, w, cfs, Color(0.95, 0.95, 0.92))

	func _draw_goal(font: Font, w: float, h: float) -> void:
		var goal: Dictionary = screens.goal
		var replay: Texture2D = screens.replay
		var home := screens.home
		var away := screens.away
		var side := int(goal.get("side", 0))
		var code := home if side == 0 else away
		var cols: Array = GameDB.club_colours(code)
		draw_rect(Rect2(Vector2.ZERO, size), cols[0])
		var ink: Color = Oval3DScreens.ink_on(cols[0], cols[1])
		if replay != null:
			# The replay fills the screen; GOAL and the scorer on a band of his colours at its foot.
			draw_texture_rect(replay, Rect2(Vector2.ZERO, size), false)
			var band := Rect2(0, h * 0.74, w, h * 0.26)
			draw_rect(band, cols[0])
			var fs := int(h * 0.15)
			var who := str(goal.get("who", ""))
			var line := "GOAL  #%d %s" % [int(goal.get("num", 0)), who.to_upper()] if who != "" else "GOAL"
			while fs > 12 and font.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > w * 0.92:
				fs -= 2
			draw_string(font, Vector2(0, band.position.y + band.size.y * 0.5 + font.get_ascent(fs) * 0.36),
					line, HORIZONTAL_ALIGNMENT_CENTER, w, fs, ink)
			return
		var gfs := int(h * 0.46)
		while gfs > 12 and font.get_string_size("GOAL", HORIZONTAL_ALIGNMENT_LEFT, -1, gfs).x > w * 0.9:
			gfs -= 2
		draw_string(font, Vector2(0, h * 0.55), "GOAL", HORIZONTAL_ALIGNMENT_CENTER, w, gfs, ink)
		var who := str(goal.get("who", ""))
		if who != "":
			var line := "#%d  %s" % [int(goal.get("num", 0)), who.to_upper()]
			var fs := int(h * 0.15)
			while fs > 12 and font.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > w * 0.92:
				fs -= 2
			draw_string(font, Vector2(0, h * 0.84), line, HORIZONTAL_ALIGNMENT_CENTER, w, fs, ink)


## The two boards' picture: the home club's on the left half, the away club's on the right.
class _Signs:
	extends Control
	var home := ""
	var away := ""

	func _draw() -> void:
		var font: Font = UiKit.BOLD
		var half := size.x * 0.5
		for side in 2:
			var code := home if side == 0 else away
			var cols: Array = GameDB.club_colours(code)
			var r := Rect2(side * half, 0, half, size.y)
			draw_rect(r, cols[0])
			# A thin stripe of the second colour along the top and the foot.
			var ink: Color = Oval3DScreens.ink_on(cols[0], cols[1])
			draw_rect(Rect2(r.position.x, 0, half, size.y * 0.08), ink)
			draw_rect(Rect2(r.position.x, size.y * 0.92, half, size.y * 0.08), ink)
			var nm := GameDB.club_name(code).to_upper()
			var fs := int(size.y * 0.62)
			while fs > 12 and font.get_string_size(nm, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > half * 0.86:
				fs -= 2
			draw_string(font, Vector2(r.position.x, size.y * 0.5 + font.get_ascent(fs) * 0.36), nm,
					HORIZONTAL_ALIGNMENT_CENTER, half, fs, ink)
