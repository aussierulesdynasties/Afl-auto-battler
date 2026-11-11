class_name MediaConferenceVignette
extends Control
## A short post-match media-room scene in the vignettes' style: the coach, a
## pre-rendered figure in a suit with a tie in the club's colour, walks in behind
## the desk and sits down at the microphones; the room is the club's media wall,
## the press in front of him with phones up, a TV camera, the odd flash. The
## question/answers remain authoritative UI layered over it.

signal ready_for_question
const CUT_IN := 0.35
const FREEZE := 1.55
## The coach walks in to his chair, then sits.
const WALK_END := 1.05
const SIT_END := 1.45
## The coach's outfit and look: one for now, swappable when coaches get their own
## appearance (roadmap "coach appearance").
const COACH_SUIT := Color(0.16, 0.17, 0.2)
const COACH_SHIRT := Color(0.93, 0.93, 0.95)
const COACH_LOOK := {"skin": 1, "hair": 2, "hair_style": "short_crop"}
const BODY := "coach"
## The press-room camera creeps in from ZOOM_IN to ZOOM_MAX through the questions.
const ZOOM_IN := 1.12
const ZOOM_MAX := 1.24
var club := ""
## 0 (the press conference): the scene is drawn to its frame. Above 0 (the
## appointment interview): the camera sits tight on the desk, and the coach is
## drawn from the close-up sheets (CoachCloseUp: the same coach rendered at 3x,
## director 2026-11-12 "Re-render sharper"), never larger than this many screen
## units per sheet pixel, even at the camera's closest; a frame bigger than that
## gets more room around him (the media wall above and beside, the press pack in
## front), never a blown-up coach.
var figure_cap := 0.0
## The close-up coach's share of the frame's height, head to desk, at the camera's
## closest (the cap may hold him smaller).
const CLOSE_FILL := 0.30
## The desk top above his feet, metres: 0.2 of the scene's height (see _draw), where
## he stands 0.62 of it at 1.84 m.
const DESK_M := 0.2 * 1.84 / 0.62
## The close-up sheets, loaded only while an interview's room is up (CoachCloseUp).
const CLOSE_SHEETS := {"shade": "res://assets/vignette/coach_hd_shade.png",
		"mask": "res://assets/vignette/coach_hd_mask.png", "design": "res://assets/vignette/coach_hd_design.png"}
var _close := {}
## With figure_cap: how far down the frame (in screen units) the front of the
## press pack lands. Below it the nearest reporters' backs fill to the foot.
## Below 0: the foot of the frame.
var scene_bottom := -1.0
var _bottom_now := -1.0
var _colours := []
var _t := 0.0
var _ready := false
var _view := Transform2D.IDENTITY   # the camera this frame (VignetteCamera)

static func open(host: Node, club_code: String) -> MediaConferenceVignette:
	var v := MediaConferenceVignette.new()
	v.name = "MediaConferenceVignette"
	v.club = club_code
	var db := host.get_tree().root.get_node("GameDB")
	v._colours = db.club_colours(club_code)
	v.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	v.mouse_filter = Control.MOUSE_FILTER_STOP
	host.add_child(v)
	v._dress()
	return v

## His suit, shirt and a tie in the club's first colour, on the figure material.
func _dress() -> void:
	var tie: Color = _colours[0] if not _colours.is_empty() else Color(0.5, 0.1, 0.1)
	material = StoppageVignette.figure_material([{"design": "suit", "base": COACH_SUIT,
			"pattern": COACH_SHIRT, "pattern2": tie, "shorts": COACH_SUIT}])

func _process(delta: float) -> void:
	_t += delta
	# A new scene_bottom: the camera tilts there (the first one it simply starts at).
	if scene_bottom >= 0.0:
		_bottom_now = scene_bottom if _bottom_now < 0.0 else lerpf(_bottom_now, scene_bottom, 1.0 - exp(-delta * 6.0))
	if not _ready and _t >= FREEZE:
		_ready = true
		ready_for_question.emit()
	# The room carries on behind the question: flashes, the coach shifting.
	queue_redraw()

func finish_now() -> void:
	if _ready:
		return
	_t = FREEZE
	_ready = true
	ready_for_question.emit()
	queue_redraw()

func _gui_input(event: InputEvent) -> void:
	if not _ready and ((event is InputEventMouseButton and event.pressed) or (event is InputEventScreenTouch and event.pressed)):
		finish_now()

## The part of the frame the scene (wall grid, desk, coach, press pack) is laid
## out in: the whole frame, or with figure_cap the size that keeps the coach at
## or under the cap, centred across, its press pack ending at scene_bottom.
func scene_box() -> Rect2:
	if figure_cap <= 0.0:
		return Rect2(Vector2.ZERO, size)
	# Close up: head to desk takes CLOSE_FILL of the frame at ZOOM_MAX, or less where
	# the cap holds him. Standing he is 0.62 of the scene's height (see _draw).
	var cap := figure_cap * CoachCloseUp.PX_PER_M
	var px_m := minf(size.y * CLOSE_FILL / (_seated_reach() - DESK_M), cap)
	var hs := px_m / ZOOM_MAX * 1.84 / 0.62
	return Rect2(Vector2.ZERO, Vector2(hs * 1.6, hs))


## The seated coach's head above his feet, metres (the close-up sheet's strip).
func _seated_reach() -> float:
	return CoachCloseUp.reach(CoachCloseUp.strip(BODY, "coach_seated", "front"), 0)


## The part of the scene the frame shows now, in scene units.
func _frame_local() -> Rect2:
	if figure_cap <= 0.0:
		return Rect2(-scene_box().position, size)
	var inv := _view.affine_inverse()
	var a := inv * Vector2.ZERO
	return Rect2(a, inv * size - a)


## The camera's zoom now: in on him through the questions.
func _zoom() -> float:
	return VignetteCamera.glide(ZOOM_IN, ZOOM_MAX, _t, SIT_END, SIT_END + 9.0)


## Screen units per figure-sheet pixel at the camera's closest (what the cap holds).
func figure_scale() -> float:
	var ppm := CoachCloseUp.PX_PER_M if figure_cap > 0.0 else VignetteFigures.PX_PER_M
	return scene_box().size.y * 0.62 / 1.84 / ppm * ZOOM_MAX


## Fixed-size details (lines, mic heads, the bottle) scaled with a close-up's scene,
## so they keep their proportion to the coach; 1 in the press conference.
func _unit(h: float) -> float:
	return 1.0 if figure_cap <= 0.0 else h / 240.0


func _draw() -> void:
	if size.x < 8.0 or size.y < 8.0:
		return
	var box := scene_box()
	var w := box.size.x
	var h := box.size.y
	var fade := clampf(_t / CUT_IN, 0.0, 1.0)
	var desk_y := h * 0.66
	var feet_y := h * 0.86                  # behind the desk: his chair's on the floor there
	var pm := h * 0.62 / 1.84               # pixels per metre: standing, he's about 0.62 of the scene
	# The coach: in from the left behind the desk, sits at the middle microphones.
	var k := 1.0 - pow(1.0 - clampf(_t / WALK_END, 0.0, 1.0), 3.0)
	var x := lerpf(w * 0.08, w * 0.5, k)
	# The camera at the back of the room: following him in, then creeping in on him
	# through the questions, the way the press-room camera does (VignetteCamera).
	var G := VignetteCamera
	var zoom := _zoom()
	var focus := box.position + Vector2(x, desk_y - h * 0.12) + G.breathe(_t, size, 0.006)
	if figure_cap > 0.0:
		# Tight on the desk: his head held at one height on the screen, head and desk
		# centred in the room above the page (scene_bottom), the press pack's heads
		# under the desk. Walking in he stands taller; the camera rides his head down
		# as he sits, so he is never cut off at the top.
		var vb := size.y if _bottom_now < 0.0 else _bottom_now
		var block := (_seated_reach() - DESK_M) * pm * ZOOM_MAX
		var head_y := maxf(vb * 0.05, (vb - block * 1.4) * 0.5)
		var walk_reach := CoachCloseUp.reach(CoachCloseUp.strip(BODY, "coach_walk", "front_r"), 0)
		var reach: float = G.glide(walk_reach, _seated_reach(), _t, WALK_END * 0.6, SIT_END)
		var head := Vector2(x, feet_y - reach * pm)
		_view = Transform2D(0.0, Vector2(zoom, zoom), 0.0,
				Vector2(size.x * 0.5, head_y) - head * zoom + G.breathe(_t, size, 0.006) * zoom)
	else:
		_view = G.view(size, focus, zoom) * Transform2D(0.0, box.position)
	draw_set_transform_matrix(_view)
	_draw_wall(w, h, desk_y)
	_draw_camera_rig(w, h)
	if _t < WALK_END:
		_coach(Vector2(x, feet_y), pm, "coach_walk", "front_r", int(_t * 7.0) % 8)
	elif _t < SIT_END:
		_coach(Vector2(x, feet_y), pm, "coach_sit", "front", mini(2, int((_t - WALK_END) / (SIT_END - WALK_END) * 3.0)))
	else:
		# Settled; now and then a hand comes up as he makes a point.
		var talking := _t > FREEZE + 0.6 and fmod(_t - FREEZE, 3.4) < 1.1
		_coach(Vector2(x, feet_y), pm, "coach_seated", "front", 1 if talking else 0)
	_draw_desk(w, h, desk_y)
	_draw_press(w, h)
	draw_set_transform_matrix(Transform2D.IDENTITY)
	# A camera flash now and then from the pack.
	var f := fmod(_t + 0.3, 1.9)
	if _t > 0.5 and f < 0.07:
		draw_rect(Rect2(Vector2.ZERO, size), Color(1, 1, 1, 0.18 * (1.0 - f / 0.07)), true)
	# No letterbox and no caption: the room fills its frame edge to edge (the black
	# bands, director's question), and the screen's own title already names it.
	if fade < 1.0:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 1.0 - fade), true)

## The coach figure, feet at feet (hidden behind the desk), pm pixels per metre.
func _coach(feet: Vector2, pm: float, anim: String, facing: String, frame: int) -> void:
	var look := Color(0.0, int(COACH_LOOK["skin"]) / 8.0, int(COACH_LOOK["hair"]) / 8.0, 1.0)
	if figure_cap > 0.0:
		_close_up(feet, pm, anim, facing, frame, look)
		return
	var info := VignetteFigures.strip(BODY, anim, facing)
	frame = StoppageVignette.figure_frame(info, frame, anim, facing)
	var k := pm / VignetteFigures.PX_PER_M
	var origin := feet - Vector2(info["pivot"][0], info["pivot"][1]) * k
	draw_texture_rect_region(StoppageVignette.FIGURE_SHADE, Rect2(origin, VignetteFigures.frame_size(info) * k),
			VignetteFigures.source(info, frame), look)
	StoppageVignette.draw_hair(self, origin, info, frame, k, look, str(COACH_LOOK["hair_style"]))


## The coach from the close-up sheets (CoachCloseUp), his hair from its own atlas.
func _close_up(feet: Vector2, pm: float, anim: String, facing: String, frame: int, look: Color) -> void:
	_bind_close_up()
	var CU := CoachCloseUp
	var info := CU.strip(BODY, anim, facing)
	frame = StoppageVignette.figure_frame(info, frame, anim, facing)
	var k := pm / CU.PX_PER_M
	var origin := feet - Vector2(info["pivot"][0], info["pivot"][1]) * k
	draw_texture_rect_region(_close["shade"], Rect2(origin, CU.frame_size(info) * k), CU.source(info, frame), look)
	var hair := CU.hair_for(info, str(COACH_LOOK["hair_style"]))
	if not hair.is_empty():
		draw_texture_rect_region(CU.hair_texture(hair), Rect2(origin + CU.hair_offset(hair) * k,
				Vector2(hair["size"][0], hair["size"][1]) * k), CU.hair_source(hair, frame), look)


## The figure material on the close-up sheets: their mask and design, their size
## (how the shader tells a figure draw), and their hair atlas among the hair sizes.
func _bind_close_up() -> void:
	if not _close.is_empty():
		return
	for key in CLOSE_SHEETS:
		_close[key] = load(CLOSE_SHEETS[key])
	var mat := material as ShaderMaterial
	mat.set_shader_parameter("mask_tex", _close["mask"])
	mat.set_shader_parameter("design_tex", _close["design"])
	mat.set_shader_parameter("sheet_size", CoachCloseUp.SHEET_SIZE)
	var sizes: Array = Array(mat.get_shader_parameter("hair_sizes"))
	var count := int(mat.get_shader_parameter("hair_count"))
	for tex in CoachCloseUp.HAIR_TEXTURES:
		var sz := Vector2i((tex as Texture2D).get_size())
		if not sz in sizes.slice(0, count) and count < sizes.size():
			sizes[count] = sz
			count += 1
	mat.set_shader_parameter("hair_sizes", sizes)
	mat.set_shader_parameter("hair_count", count)

## The media wall: a step-and-repeat of plain club-colour tiles (no invented logos),
## lit from the front, and the room's dark edges.
func _draw_wall(w: float, h: float, desk_y: float) -> void:
	# The wall runs to every edge of the frame, so no dark strip shows as the camera moves.
	# Scene coordinates: the frame starts at -at (wider and taller with figure_cap).
	var fr := _frame_local()
	var at := -fr.position
	draw_rect(fr, Color(0.12, 0.12, 0.14), true)
	var grid := Rect2(w * 0.04, h * 0.1, w * 0.92, desk_y - h * 0.06)
	var wall := Rect2(fr.position.x, fr.position.y, fr.size.x, grid.end.y - fr.position.y)
	var a: Color = _colours[0] if not _colours.is_empty() else Color(0.3, 0.3, 0.32)
	var b: Color = _colours[1] if _colours.size() > 1 else a.lightened(0.3)
	var tw := grid.size.x / 7.0
	var th := grid.size.y / 3.5
	for row in range(mini(-1, floori((fr.position.y - grid.position.y) / th) - 1), 4):
		for col in range(mini(-1, floori((fr.position.x - grid.position.x) / tw) - 1),
				maxi(9, ceili((fr.end.x - grid.position.x) / tw) + 2)):
			var off := tw * 0.5 if posmod(row, 2) == 1 else 0.0
			var r := Rect2(grid.position + Vector2(col * tw - off + tw * 0.12, row * th + th * 0.18), Vector2(tw * 0.76, th * 0.64))
			r = r.intersection(wall)
			if r.size.x <= 1.0 or r.size.y <= 1.0:
				continue
			# Muted, so a white or yellow club doesn't glare over the coach.
			var c := (a if posmod(row + col, 2) == 0 else b).darkened(0.55)
			draw_rect(r, Color(c, 0.55), true)
			draw_rect(Rect2(r.position + r.size * Vector2(0.3, 0.42), r.size * Vector2(0.4, 0.16)), Color(1, 1, 1, 0.07), true)
	# A frame taller than the scene shows the ceiling: a lighting truss and its
	# lamps, their beams down the wall onto the desk.
	if at.y > h * 0.25:
		var c := minf(at.y * 0.5, h * 0.3)
		var top := -at.y
		draw_rect(Rect2(-at.x, top, fr.size.x, c), Color(0.06, 0.06, 0.07), true)
		draw_rect(Rect2(-at.x, top + c - 1.5, fr.size.x, 1.5), Color(1, 1, 1, 0.06), true)
		var ty := top + c * 0.55
		var steel := Color(0.2, 0.2, 0.22)
		draw_line(Vector2(-at.x, ty), Vector2(fr.size.x - at.x, ty), steel, 2.0, true)
		draw_line(Vector2(-at.x, ty + 7.0), Vector2(fr.size.x - at.x, ty + 7.0), steel, 2.0, true)
		var step := 14.0
		var bx := -at.x
		while bx < fr.size.x - at.x:
			draw_line(Vector2(bx, ty), Vector2(bx + step * 0.5, ty + 7.0), steel, 1.0, true)
			draw_line(Vector2(bx + step * 0.5, ty + 7.0), Vector2(bx + step, ty), steel, 1.0, true)
			bx += step
		var lamps := 2 + 2 * ceili(maxf(0.0, at.x) / w)
		for i in range(-lamps, lamps + 2):
			var lx := w * (0.5 + 0.22 * (i - 0.5))
			if lx < -at.x - 10.0 or lx > fr.size.x - at.x + 10.0:
				continue
			var can := Vector2(lx, ty + 9.0)
			# The beam: soft, aimed in at the desk.
			var aim := Vector2(lerpf(lx, w * 0.5, 0.6), desk_y)
			var spread := w * 0.11
			draw_colored_polygon(PackedVector2Array([can + Vector2(-4, 6), can + Vector2(4, 6),
					aim + Vector2(spread, 0), aim - Vector2(spread, 0)]), Color(1.0, 0.95, 0.85, 0.035))
			draw_line(Vector2(lx, ty + 7.0), can, steel, 1.5, true)
			draw_set_transform_matrix(_view * Transform2D((aim - can).angle() - PI * 0.5, can))
			draw_rect(Rect2(-5, -2, 10, 10), Color(0.13, 0.13, 0.15), true)
			draw_rect(Rect2(-4, 7, 8, 2), Color(1.0, 0.93, 0.78, 0.9), true)
			draw_set_transform_matrix(_view)
	# Key light on the wall behind his chair.
	for i in range(5):
		draw_circle(Vector2(w * 0.5, desk_y - h * 0.12), w * (0.12 + 0.06 * i), Color(1.0, 0.95, 0.85, 0.035))

## The table across the front: its club-colour skirt, top, the microphones bunched in
## front of his chair (broadcasters' blank flags), a bottle and a glass, a name card.
func _draw_desk(w: float, h: float, desk_y: float) -> void:
	# The skirt in the club's colour, lit from above, its folds catching the light.
	var skirt: Color = (_colours[0] if not _colours.is_empty() else Color(0.2, 0.2, 0.22)).darkened(0.3)
	if skirt.get_luminance() < 0.06:
		skirt = skirt.lightened(0.12)          # a black club's skirt still reads as cloth
	# To the floor: in a frame taller than the scene it runs on down behind the press.
	var u := _unit(h)
	var drop := h * 0.24 if figure_cap <= 0.0 else maxf(h * 0.24, _frame_local().end.y - desk_y)
	draw_rect(Rect2(w * 0.1, desk_y, w * 0.8, drop), skirt, true)
	for i in range(9):
		var fx := w * (0.13 + 0.093 * i)
		draw_line(Vector2(fx, desk_y + 2.0), Vector2(fx, desk_y + drop), skirt.darkened(0.3), 1.5 * u, true)
	draw_rect(Rect2(w * 0.1, desk_y, w * 0.8, h * 0.035), Color(1, 1, 1, 0.08), true)
	var trim: Color = _colours[1] if _colours.size() > 1 else skirt.lightened(0.4)
	draw_rect(Rect2(w * 0.1, desk_y + h * 0.05, w * 0.8, 2.0 * u), Color(trim, 0.6), true)
	draw_rect(Rect2(w * 0.08, desk_y - h * 0.018, w * 0.84, h * 0.03), Color(0.22, 0.2, 0.19), true)
	draw_rect(Rect2(w * 0.08, desk_y - h * 0.018, w * 0.84, 1.5 * u), Color(1, 1, 1, 0.18), true)
	# Name card in front of his place, blank.
	draw_rect(Rect2(w * 0.43, desk_y - h * 0.05, w * 0.14, h * 0.035), Color(0.88, 0.88, 0.86), true)
	var flags := [Color(0.75, 0.12, 0.12), Color(0.12, 0.3, 0.7), Color(0.9, 0.9, 0.9), Color(0.1, 0.55, 0.3), Color(0.95, 0.65, 0.1)]
	# Short desk microphones angled up at him; tips at his chest, clear of his face.
	var mic_h := h * 0.07
	# Close up, mic heads and flags at their real size against him (a ~6 cm head, a
	# ~7 cm flag): the press-conference scale would make each head half his face.
	var mu := u * (0.6 if figure_cap > 0.0 else 1.0)
	for i in range(flags.size()):
		var bx := w * (0.4 + 0.05 * i) + (i % 2) * 3.0 * u
		var tip := Vector2(w * 0.5 + (bx - w * 0.5) * 0.55, desk_y - mic_h - (i % 3) * 2.0 * u)
		var base := Vector2(bx, desk_y - h * 0.012)
		draw_line(base, tip, Color(0.18, 0.18, 0.2), 2.0 * u, true)
		draw_rect(Rect2(base + Vector2(-4, -4) * u, Vector2(8, 4) * u), Color(0.1, 0.1, 0.11), true)
		var flag := Rect2(tip.lerp(base, 0.28) - Vector2(5, 4) * mu, Vector2(10, 8) * mu)
		draw_rect(flag, flags[i], true)
		draw_circle(tip, 4.0 * mu, Color(0.06, 0.06, 0.07), true, -1.0, true)
	# A bottle and a glass of water at his elbow.
	var bottle := Vector2(w * 0.66, desk_y - h * 0.012)
	draw_rect(Rect2(bottle - Vector2(4 * u, h * 0.08), Vector2(8 * u, h * 0.08)), Color(0.6, 0.75, 0.85, 0.75), true)
	draw_rect(Rect2(bottle - Vector2(2 * u, h * 0.095), Vector2(4 * u, h * 0.015)), Color(0.2, 0.4, 0.8), true)
	draw_rect(Rect2(bottle + Vector2(10 * u, -h * 0.04), Vector2(7 * u, h * 0.04)), Color(0.8, 0.88, 0.95, 0.5), true)

## A TV camera on its tripod at the side, shooting the desk.
func _draw_camera_rig(w: float, h: float) -> void:
	var u := _unit(h)
	var head := Vector2(w * 0.9, h * 0.5)
	var leg := Color(0.09, 0.09, 0.1)
	for dx in [-0.05, 0.0, 0.05]:
		draw_line(head + Vector2(0, h * 0.04), Vector2(head.x + w * dx, h * 0.93), leg, 2.0 * u, true)
	var body := Rect2(head - Vector2(w * 0.07, h * 0.06), Vector2(w * 0.12, h * 0.1))
	draw_rect(body, Color(0.15, 0.15, 0.17), true)
	draw_rect(Rect2(body.position, Vector2(body.size.x, 2.0 * u)), Color(1, 1, 1, 0.15), true)   # rim light
	draw_rect(Rect2(head - Vector2(w * 0.12, h * 0.035), Vector2(w * 0.055, h * 0.055)), Color(0.1, 0.1, 0.11), true)
	draw_circle(head - Vector2(w * 0.12, h * 0.0075), h * 0.02, Color(0.25, 0.32, 0.45))     # lens
	draw_rect(Rect2(head + Vector2(-w * 0.03, -h * 0.09), Vector2(w * 0.05, h * 0.03)), Color(0.12, 0.12, 0.13), true)   # handle
	draw_circle(head + Vector2(w * 0.04, -h * 0.045), 2.0 * u, Color(0.9, 0.15, 0.15))   # tally light

## The press in the foreground, from behind: heads and shoulders, each one different
## (size, place, tilt), phones and a recorder held up to the desk.
func _draw_press(w: float, h: float) -> void:
	var body := Color(0.035, 0.035, 0.04)
	var rim := Color(0.7, 0.66, 0.6, 0.7)
	# [x, y, size, tilt, holds: 0 nothing, 1 phone, 2 recorder]
	var row := [[0.04, 0.82, 1.1, -0.10, 0], [0.2, 0.87, 1.0, 0.06, 1], [0.37, 0.92, 1.2, -0.04, 0],
			[0.63, 0.87, 0.95, 0.12, 1], [0.8, 0.93, 1.25, -0.08, 2], [0.97, 0.84, 1.05, 0.05, 0]]
	var people := row.duplicate()
	# A frame wider than the scene: the same pack carries on to each side.
	var fr := _frame_local()
	for side in range(1, ceili(maxf(maxf(0.0, -fr.position.x), fr.end.x - w) / w) + 1):
		for p in row:
			people.append([float(p[0]) - side, p[1], p[2], -float(p[3]), p[4]])
			people.append([float(p[0]) + side, p[1], p[2], -float(p[3]), 0])
	# A frame taller than the scene: their backs run down to its foot (under the page).
	var foot := fr.end.y
	for i in range(people.size()):
		var p: Array = people[i]
		var r: float = h * 0.085 * float(p[2])
		var at := Vector2(w * float(p[0]), h * float(p[1]))
		var low := at.y + r * 1.6 if figure_cap <= 0.0 else maxf(at.y + r * 1.6, foot)
		var sway := sin(_t * (0.9 + 0.17 * i) + i * 1.3) * r * 0.04
		var tilt: float = p[3]
		var hold := int(p[4])
		if hold > 0:
			# Arm up holding a phone or recorder towards the desk, screen lit.
			var hand := at + Vector2(r * (0.9 if tilt >= 0.0 else -0.9), -r * 1.9 + sway)
			draw_line(at + Vector2(r * 0.6 * signf(hand.x - at.x), -r * 0.2), hand, body, r * 0.32, true)
			if hold == 1:
				draw_rect(Rect2(hand - Vector2(r * 0.3, r * 0.55), Vector2(r * 0.6, r * 1.0)), body, true)
				draw_rect(Rect2(hand - Vector2(r * 0.24, r * 0.48), Vector2(r * 0.48, r * 0.86)), Color(0.55, 0.65, 0.8, 0.55), true)
			else:
				draw_rect(Rect2(hand - Vector2(r * 0.18, r * 0.5), Vector2(r * 0.36, r * 0.8)), Color(0.12, 0.12, 0.13), true)
				draw_circle(hand + Vector2(0, -r * 0.5), r * 0.2, Color(0.2, 0.2, 0.22))
		var shoulders := PackedVector2Array([Vector2(at.x - r * 1.6, low), at + Vector2(-r * 1.3, -r * 0.1),
				at + Vector2(-r * 0.5, -r * 0.45), at + Vector2(r * 0.5, -r * 0.45), at + Vector2(r * 1.3, -r * 0.1),
				Vector2(at.x + r * 1.6, low)])
		draw_colored_polygon(shoulders, body)
		var head := at + Vector2(tilt * r * 2.0, -r * 1.0 + sway)
		draw_set_transform_matrix(_view * Transform2D(tilt, Vector2(0.86, 1.0), 0.0, head))
		draw_circle(Vector2.ZERO, r * 0.62, body)
		draw_arc(Vector2.ZERO, r * 0.62, PI * 1.15, PI * 1.85, 10, rim, maxf(1.0, r * 0.1), true)
		draw_set_transform_matrix(_view)
