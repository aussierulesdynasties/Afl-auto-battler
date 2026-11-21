extends Node3D
## The ground inspector (row 202 2b, director 2026-11-20: "fly around the map very fast in first
## person"): every stadium model in the checkout, and in its local worktrees on request, flown
## through with a free camera so the director can inspect it closely and write his fault list.
##
## A ground the match loads (assets/grounds/<dir>) is shown as the match shows it: Oval3D's light,
## turf, goalposts, model and seats. Any other .glb (tools/grounds, .claude/review, a worktree) is
## read straight off disk onto the same light, turf and goalposts, as authored (not moved). Pieces split for GitHub (<name>_part1.glb, _part2 ...)
## load together as one ground.
##
## Launch: tools/inspect/inspect_ground.bat (Windows) or tools/inspect/inspect_ground.sh, or open
## this scene in the editor and press F6. Arguments after "--": --ground=<text> opens the first
## ground whose name contains it, --glb=<path> opens one file, --worktrees lists the worktrees too,
## --check loads every ground in turn (those --ground names, if given), saves its start view to
## user://inspection/check and quits.
## Controls are on screen (F1 hides them). Looks only: nothing here touches a match.

const OVAL3D := preload("res://scripts/ui/match/Oval3D.gd")

## Where models are looked for, from the project folder; the game's own grounds come first.
const MATCH_ROOT := "assets/grounds"
const REVIEW_ROOTS := ["tools/grounds", ".claude/review"]
const WORKTREES := ".claude/worktrees"
const SKIP_DIRS := [".git", ".godot", "node_modules", "__pycache__"]

const SPEED_START := 25.0     # m/s
const SPEED_MIN := 1.0
const SPEED_MAX := 600.0
const BOOST := 5.0            # Shift
const CRAWL := 0.2            # Alt
const LOOK := 0.0025          # rad per pixel of mouse
const EYE := 1.75             # m: a man standing
const SHOTS := "user://inspection"

var grounds: Array = []       # [{name, kind, paths: [abs .glb], dir, base}]
var current := -1
var stage: Node3D             # the ground on show, rebuilt on each load
var oval                      # its Oval3D, when it is one
var camera: Camera3D
var ball_marker: MeshInstance3D       # the point under the camera: the turf's standing blades follow it
var start_view := Transform3D.IDENTITY
var speed := SPEED_START
var yaw := 0.0
var pitch := 0.0
var velocity := Vector3.ZERO
var hud: Label
var help: Label
var note: Label
var list: ItemList
var list_panel: PanelContainer
var _note_t := 0.0
var _loading := false
var _failed := false
var _show_oval := true
var _match_parts: Array = []
var _project := ""


func _ready() -> void:
	_project = ProjectSettings.globalize_path("res://").trim_suffix("/")
	OS.low_processor_usage_mode = false
	AudioServer.set_bus_mute(0, true)
	camera = Camera3D.new()
	camera.fov = 70.0
	camera.near = 0.05
	camera.far = 6000.0
	add_child(camera)
	camera.make_current()
	_build_ui()
	get_window().files_dropped.connect(_on_files_dropped)
	var args := _args()
	_scan(args.has("worktrees"))
	if args.has("glb"):
		_add_file(str(args["glb"]))
		_load(grounds.size() - 1)
		return
	var pick := 0
	if args.has("ground"):
		var want := str(args["ground"]).to_lower()
		for i in grounds.size():
			if want in str(grounds[i]["name"]).to_lower():
				pick = i
				break
	if grounds.is_empty():
		_say("No stadium models found under %s." % _project)
		_show_list(true)
		return
	if args.has("check"):
		_check.call_deferred(str(args.get("ground", "")).to_lower())
		return
	_load(pick)


## Every ground loaded in turn: a line each, OK or not, and its start view saved.
func _check(only := "") -> void:
	var dir := SHOTS + "/check"
	DirAccess.make_dir_recursive_absolute(dir)
	var bad := 0
	var tried := 0
	var headless := DisplayServer.get_name() == "headless"
	print("ground inspector check: %d grounds" % grounds.size())
	for i in grounds.size():
		if only != "" and not only in str(grounds[i]["name"]).to_lower():
			continue
		tried += 1
		var t0 := Time.get_ticks_msec()
		await _load(i)
		for _f in 3:
			await get_tree().process_frame
		if not headless:
			await RenderingServer.frame_post_draw
		var meshes := stage.find_children("*", "MeshInstance3D", true, false).size()
		var ok := meshes > 0 and not _failed
		bad += 0 if ok else 1
		if not headless:
			var shot := "%s/%02d_%s.png" % [dir, i, str(grounds[i]["paths"][0]).get_file().get_basename()]
			get_viewport().get_texture().get_image().save_png(shot)
		print("%s  %s  meshes %d  size %s m  %.1f s" % ["OK  " if ok else "FAIL", grounds[i]["name"],
				meshes, str(_bounds(stage).size.round()), (Time.get_ticks_msec() - t0) / 1000.0])
		if tried == 1:
			bad += 0 if await _fly_check(dir, headless) else 1
	print("ground inspector check: %d of %d grounds loaded; views in %s" % [tried - bad, tried, ProjectSettings.globalize_path(dir)])
	get_tree().quit(1 if bad > 0 else 0)


## The controls driven as a player's keys and mouse drive them (input events, not the handlers):
## a click to fly, Shift+W held for a second, then T to the centre square, its view saved.
func _fly_check(dir: String, headless: bool) -> bool:
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = get_viewport().get_visible_rect().size * 0.5
	Input.parse_input_event(click)
	await get_tree().process_frame
	var from := camera.global_position
	var forward := -camera.global_basis.z
	for k in [KEY_SHIFT, KEY_W]:
		Input.parse_input_event(_key_event(k, true))
	var t0 := Time.get_ticks_msec()
	var top := 0.0
	var frames := 0
	while Time.get_ticks_msec() - t0 < 1000 or frames < 4:
		await get_tree().process_frame
		frames += 1
		top = maxf(top, velocity.length())
	for k in [KEY_W, KEY_SHIFT]:
		Input.parse_input_event(_key_event(k, false))
	var moved := (camera.global_position - from).dot(forward)
	var secs := (Time.get_ticks_msec() - t0) / 1000.0
	Input.parse_input_event(_key_event(KEY_T, true))
	Input.parse_input_event(_key_event(KEY_T, false))
	for _f in 3:
		await get_tree().process_frame
	var at_centre := camera.global_position.distance_to(Vector3(0, EYE, 0)) < 0.5
	if not headless:
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(dir + "/eye_centre_square.png")
	# Shift is x5 the cruise speed. A slow software renderer draws few frames, so the test is the
	# speed reached and the way it went, not the distance.
	var ok := top > speed * BOOST * 0.8 and moved > 1.0 and at_centre
	print("%s  flying: Shift+W reached %.0f m/s, %.0f m forward in %.1f s; T to the centre square %s" % [
			"OK  " if ok else "FAIL", top, moved, secs, "yes" if at_centre else "no"])
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	return ok


func _key_event(k: Key, down: bool) -> InputEventKey:
	var e := InputEventKey.new()
	e.keycode = k
	e.physical_keycode = k
	e.pressed = down
	return e


func _args() -> Dictionary:
	var out := {}
	for a in OS.get_cmdline_user_args():
		var s := str(a).trim_prefix("--")
		var eq := s.find("=")
		if eq < 0:
			out[s] = true
		else:
			out[s.substr(0, eq)] = s.substr(eq + 1)
	return out


# --- Finding the models ---------------------------------------------------------------------

func _scan(worktrees: bool) -> void:
	grounds.clear()
	var seen := {}
	_scan_checkout(_project, "", seen)
	if worktrees:
		var wt := _project.path_join(WORKTREES)
		for d: String in _subdirs(wt):
			_scan_checkout(wt.path_join(d), d, seen)
	_fill_list()


## One checkout's grounds: the match's own first, then the review models. A copy identical in
## name and size to one already listed (the same file in another worktree) is left out.
func _scan_checkout(root: String, label: String, seen: Dictionary) -> void:
	var tag := "" if label == "" else "  [%s]" % label
	var names := {}
	for n in GroundModels.grounds():
		names[GroundModels.slug_for(n)] = n
	for d: String in _subdirs(root.path_join(MATCH_ROOT)):
		var base := root.path_join(MATCH_ROOT).path_join(d) + "/"
		# <slug>.glb or its pieces <slug>_part1.glb ... (GroundModels.files), as the match finds them.
		var glbs := Array(GroundModels.files(d, base))
		if glbs.is_empty() or _seen(seen, glbs):
			continue
		var res_base := "" if label == "" else base
		var title := str(names.get(d, d.to_upper()))
		grounds.append({"name": "%s  (in the match)%s" % [title, tag], "kind": "match",
				"paths": glbs, "dir": d, "base": res_base})
	for r in REVIEW_ROOTS:
		var found: Array = []
		_find_glbs(root.path_join(r), found)
		for g in _group_parts(found):
			if _seen(seen, g["paths"]):
				continue
			var rel: String = str(g["paths"][0]).trim_prefix(root + "/")
			g["name"] = "%s%s  (%s)%s" % [g["stem"], g["parts_note"], rel.get_base_dir(), tag]
			g["kind"] = "model"
			# A draft with its seats beside it (seat_tmpl.bin, seats_<colour>.bin) is built the way a
			# match builds a ground, seats and all.
			var folder := str(g["paths"][0]).get_base_dir() + "/"
			if g["paths"].size() == 1 and FileAccess.file_exists(folder + "seat_tmpl.bin"):
				g["kind"] = "seated"
				g["dir"] = g["stem"]
				g["base"] = folder
			grounds.append(g)


func _seen(seen: Dictionary, paths: Array) -> bool:
	var key := ""
	for p in paths:
		var f := FileAccess.open(p, FileAccess.READ)
		key += "%s:%d;" % [str(p).get_file(), f.get_length() if f else -1]
	if seen.has(key):
		return true
	seen[key] = true
	return false


func _subdirs(path: String) -> Array:
	var out: Array = []
	var d := DirAccess.open(path)
	if d == null:
		return out
	d.include_hidden = true
	for s in d.get_directories():
		out.append(s)
	out.sort()
	return out


func _find_glbs(path: String, out: Array) -> void:
	var d := DirAccess.open(path)
	if d == null:
		return
	d.include_hidden = true
	for f in d.get_files():
		if f.get_extension().to_lower() == "glb":
			out.append(path.path_join(f))
	for s in d.get_directories():
		if not s in SKIP_DIRS:
			_find_glbs(path.path_join(s), out)


## <stem>_part<N>.glb files in one folder are one ground; every other .glb is its own.
func _group_parts(files: Array) -> Array:
	var re := RegEx.create_from_string("^(.*)_part(\\d+)\\.glb$")
	var parts := {}
	var out: Array = []
	for f in files:
		var m := re.search(str(f).get_file())
		if m == null:
			out.append({"stem": str(f).get_file().get_basename(), "parts_note": "", "paths": [f]})
			continue
		var key := str(f).get_base_dir().path_join(m.get_string(1))
		if not parts.has(key):
			parts[key] = []
		parts[key].append([int(m.get_string(2)), f])
	for key in parts:
		var ps: Array = parts[key]
		ps.sort_custom(func(a, b): return a[0] < b[0])
		var paths: Array = []
		for p in ps:
			paths.append(p[1])
		out.append({"stem": str(key).get_file(), "parts_note": " (%d pieces)" % paths.size(), "paths": paths})
	out.sort_custom(func(a, b): return str(a["paths"][0]) < str(b["paths"][0]))
	return out


func _add_file(path: String) -> void:
	var p := path.replace("\\", "/")
	grounds.append({"name": "%s  (%s)" % [p.get_file().get_basename(), p.get_base_dir()],
			"kind": "model", "paths": [p], "stem": p.get_file().get_basename()})
	_fill_list()


func _on_files_dropped(files: PackedStringArray) -> void:
	for f in files:
		if f.get_extension().to_lower() == "glb":
			_add_file(f)
			_load(grounds.size() - 1)
			return
	_say("Drop a .glb file to open it.")


# --- Loading a ground -----------------------------------------------------------------------

func _load(i: int) -> void:
	if _loading or i < 0 or i >= grounds.size():
		return
	_loading = true
	current = i
	var g: Dictionary = grounds[i]
	list.select(i)
	_say("Loading %s ..." % g["name"], 60.0)
	# Two frames so the note is on screen before a big file holds the window.
	await get_tree().process_frame
	await get_tree().process_frame
	if stage != null:
		stage.queue_free()
		oval = null
	stage = Node3D.new()
	stage.name = "Stage"
	add_child(stage)
	var ok := true
	# The match's world under every ground: its light, turf and goalposts (Oval3D), so a model not
	# yet in the match is seen against the oval it will sit on (O hides the turf and posts).
	# At the ground's own size, as a match there is played (GroundModels.field: its fence less
	# the run-off), so its model sits unstretched on the turf; any other model on the standard oval.
	var own := GroundModels.field(str(g.get("dir", ""))) if g["kind"] in ["match", "seated"] else Vector2.ZERO
	MatchMotion.use_field(own)
	oval = OVAL3D.new()
	oval.name = "Oval"
	stage.add_child(oval)
	oval._environment()
	oval._ground()
	oval._posts()
	oval.camera = camera
	ball_marker = MeshInstance3D.new()
	oval.add_child(ball_marker)
	oval.ball = ball_marker
	_match_parts = oval.get_children().filter(func(n): return n is MeshInstance3D and n != ball_marker)
	if g["kind"] in ["match", "seated"]:
		oval._ground_model(str(g["dir"]), str(g["base"]))
		ok = oval.get_node("Ground").get_child_count() > 0
	else:
		for p in g["paths"]:
			var n: Node3D = OVAL3D.load_glb(p)
			if n == null:
				ok = false
				continue
			stage.add_child(n)
	_set_match_parts(_show_oval)
	_failed = not ok
	if not ok:
		_say("Could not read %s" % ", ".join(g["paths"]), 8.0)
	else:
		_say("%s  (%d of %d)" % [g["name"], i + 1, grounds.size()], 4.0)
	_frame_start()
	_loading = false


## The match's turf, goalposts and standing blades shown or hidden.
func _set_match_parts(on: bool) -> void:
	for n in _match_parts:
		if is_instance_valid(n) and n is Node3D:
			n.visible = on
	if oval != null and oval.turf != null:
		var b = oval.turf.get("blades")
		if b is Node3D:
			b.visible = on


## The start view: high over a wing, looking across the ground to its centre.
func _frame_start() -> void:
	var box := _bounds(stage)
	var c := box.get_center()
	var r := maxf(box.size.x, box.size.z) * 0.5
	if r < 1.0:
		c = Vector3.ZERO
		r = 120.0
	if grounds[current]["kind"] in ["match", "seated"]:
		# Centred on the fence; framed on the stands, not on a wide terrain disc round them.
		c = Vector3.ZERO
		r = minf(r, 190.0)
	# Off the middle of the wing, so a light tower on the axis does not stand in the way.
	var at := c + Vector3(r * 0.4, r * 0.45, r * 1.0)
	start_view = Transform3D(Basis.IDENTITY, at).looking_at(c, Vector3.UP)
	_go(start_view)


func _go(t: Transform3D) -> void:
	camera.global_transform = t
	var f := -t.basis.z
	yaw = atan2(-f.x, -f.z)
	pitch = asin(clampf(f.y, -1.0, 1.0))
	velocity = Vector3.ZERO
	_apply_look()


func _bounds(n: Node) -> AABB:
	var box := AABB()
	var first := true
	for c in n.find_children("*", "VisualInstance3D", true, false):
		var vi := c as VisualInstance3D
		if vi is Light3D:
			continue
		var b := vi.global_transform * vi.get_aabb()
		if b.size.length() > 20000.0:
			continue   # a sky dome or a stray huge plane would hide the ground's own size
		box = b if first else box.merge(b)
		first = false
	return box


# --- Flying ---------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	var flying := Input.mouse_mode == Input.MOUSE_MODE_CAPTURED
	if event is InputEventMouseMotion and flying:
		yaw -= event.relative.x * LOOK
		pitch = clampf(pitch - event.relative.y * LOOK, deg_to_rad(-89.0), deg_to_rad(89.0))
		_apply_look()
	elif event is InputEventMouseButton and event.pressed:
		match event.button_index:
			MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT:
				if not flying:
					_show_list(false)
					Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
			MOUSE_BUTTON_WHEEL_UP:
				speed = minf(speed * 1.25, SPEED_MAX)
			MOUSE_BUTTON_WHEEL_DOWN:
				speed = maxf(speed / 1.25, SPEED_MIN)
	elif event is InputEventKey and event.pressed and not event.echo:
		_key(event)


func _key(e: InputEventKey) -> void:
	match e.keycode:
		KEY_ESCAPE:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		KEY_TAB:
			_load(wrapi(current + (-1 if e.shift_pressed else 1), 0, grounds.size()))
		KEY_PAGEDOWN:
			_load(wrapi(current + 1, 0, grounds.size()))
		KEY_PAGEUP:
			_load(wrapi(current - 1, 0, grounds.size()))
		KEY_L:
			_show_list(not list_panel.visible)
		KEY_R:
			_go(start_view)
		KEY_T:
			# The centre square at a man's height, looking down the ground.
			_go(Transform3D(Basis.IDENTITY, Vector3(0, EYE, 0)).looking_at(Vector3(-50, EYE, 0), Vector3.UP))
		KEY_G:
			var p := camera.global_position
			_go(Transform3D(Basis.IDENTITY, Vector3(p.x, _floor_under(p) + EYE, p.z)).looking_at(
					Vector3(p.x, _floor_under(p) + EYE, p.z) + Vector3(-sin(yaw), 0, -cos(yaw)), Vector3.UP))
		KEY_EQUAL, KEY_KP_ADD:
			speed = minf(speed * 1.25, SPEED_MAX)
		KEY_MINUS, KEY_KP_SUBTRACT:
			speed = maxf(speed / 1.25, SPEED_MIN)
		KEY_C:
			DisplayServer.clipboard_set(_where())
			_say("Copied: " + _where())
		KEY_F12, KEY_P:
			_screenshot()
		KEY_O:
			_show_oval = not _show_oval
			_set_match_parts(_show_oval)
			_say("Match turf and goalposts " + ("shown" if _show_oval else "hidden"))
		KEY_F1:
			help.visible = not help.visible
		KEY_F11:
			var full := DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_MAXIMIZED if full
					else DisplayServer.WINDOW_MODE_FULLSCREEN)


## The height of whatever is under p, from the ground's own faces (no colliders: a ray down
## through the meshes); 0, the turf, when nothing is.
func _floor_under(p: Vector3) -> float:
	var best := -INF
	for c in stage.find_children("*", "MeshInstance3D", true, false):
		var mi := c as MeshInstance3D
		if mi.mesh == null:
			continue
		var box := mi.global_transform * mi.get_aabb()
		if p.x < box.position.x or p.x > box.end.x or p.z < box.position.z or p.z > box.end.z:
			continue
		var tm := mi.mesh.generate_triangle_mesh()
		if tm == null:
			continue
		var inv := mi.global_transform.affine_inverse()
		var hit: Dictionary = tm.intersect_ray(inv * Vector3(p.x, p.y + 0.5, p.z), inv.basis * Vector3.DOWN)
		if hit.is_empty():
			continue
		var y: float = (mi.global_transform * Vector3(hit["position"])).y
		if y <= p.y + 0.5 and y > best:
			best = y
	return best if best > -INF else 0.0


func _apply_look() -> void:
	camera.global_basis = Basis.from_euler(Vector3(pitch, yaw, 0.0))


func _process(dt: float) -> void:
	# The keys fly whether or not the mouse is held for looking; not while the list is open.
	var want := Vector3.ZERO
	if not list_panel.visible:
		var b := camera.global_basis
		if Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP):
			want -= b.z
		if Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN):
			want += b.z
		if Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT):
			want -= b.x
		if Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT):
			want += b.x
		if Input.is_physical_key_pressed(KEY_E) or Input.is_physical_key_pressed(KEY_SPACE):
			want += Vector3.UP
		if Input.is_physical_key_pressed(KEY_Q) or Input.is_physical_key_pressed(KEY_CTRL):
			want -= Vector3.UP
		if want != Vector3.ZERO:
			want = want.normalized() * speed
			if Input.is_physical_key_pressed(KEY_SHIFT):
				want *= BOOST
			if Input.is_physical_key_pressed(KEY_ALT):
				want *= CRAWL
	# Quick to start and stop, never a lurch: most of the way to the wanted speed in a tenth of a second.
	velocity = velocity.lerp(want, 1.0 - exp(-dt * 18.0))
	camera.global_position += velocity * dt
	if ball_marker != null and is_instance_valid(ball_marker):
		var p := camera.global_position
		ball_marker.global_position = Vector3(p.x, 0.0, p.z)
	_hud(dt)


# --- On screen ------------------------------------------------------------------------------

func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	hud = _label(18)
	hud.position = Vector2(14, 10)
	layer.add_child(hud)
	help = _label(15)
	help.text = "\n".join([
		"Click: fly (mouse looks)    Esc: free the mouse",
		"W A S D: move    Space or E: up    Ctrl or Q: down",
		"Shift: x%d fast    Alt: slow    Wheel or + -: cruise speed" % int(BOOST),
		"Tab / Shift+Tab: next / previous ground    L: list of grounds",
		"R: start view    T: centre square at eye height    G: drop to the floor below",
		"C: copy where you are (for the fault list)    P or F12: screenshot",
		"O: show or hide the match's turf and goalposts (to check the model sits on them)",
		"F11: full screen    F1: hide this    Drop a .glb on the window to open it",
	])
	help.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	help.position = Vector2(14, -10)
	help.grow_vertical = Control.GROW_DIRECTION_BEGIN
	layer.add_child(help)
	note = _label(20)
	note.set_anchors_preset(Control.PRESET_CENTER_TOP)
	note.grow_horizontal = Control.GROW_DIRECTION_BOTH
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	note.position.y = 110
	layer.add_child(note)
	list_panel = PanelContainer.new()
	list_panel.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	list_panel.custom_minimum_size = Vector2(560, 0)
	list_panel.offset_left = -580
	list_panel.offset_right = -10
	list_panel.offset_top = 10
	list_panel.offset_bottom = -10
	layer.add_child(list_panel)
	var box := VBoxContainer.new()
	list_panel.add_child(box)
	var title := _label(18)
	title.text = "Grounds (click one to load it)"
	box.add_child(title)
	list = ItemList.new()
	list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	list.item_clicked.connect(func(i, _at, _button): _load(i))
	box.add_child(list)
	var wt := Button.new()
	wt.text = "Also list the models in local worktrees (.claude/worktrees)"
	wt.pressed.connect(func(): _scan(true); _say("%d grounds listed" % grounds.size()))
	box.add_child(wt)
	list_panel.visible = false


func _label(size: int) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 6)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _fill_list() -> void:
	list.clear()
	for g in grounds:
		list.add_item(str(g["name"]))
	if current >= 0 and current < grounds.size():
		list.select(current)


func _show_list(on: bool) -> void:
	list_panel.visible = on
	if on:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _say(text: String, secs := 3.0) -> void:
	note.text = text
	_note_t = secs


func _hud(dt: float) -> void:
	_note_t -= dt
	if _note_t <= 0.0:
		note.text = ""
	var title := "" if current < 0 else str(grounds[current]["name"])
	var mv := velocity.length()
	hud.text = "%s\n%s    speed %d m/s (cruise %d)    %d fps" % [title, _where(), roundi(mv),
			roundi(speed), Engine.get_frames_per_second()]


## Where the camera is, in the match's metres when it is a match ground: x along the ground
## (+x the end the home side kicks to), y height above the turf, z across it.
func _where() -> String:
	var p := camera.global_position
	var heading := wrapf(rad_to_deg(-yaw), 0.0, 360.0)
	var g := "" if current < 0 else str(grounds[current].get("dir", grounds[current].get("stem", "model")))
	return "%s at x %.1f  y %.1f  z %.1f, facing %d deg, looking %+d deg" % [g, p.x, p.y, p.z,
			roundi(heading), roundi(rad_to_deg(pitch))]


func _screenshot() -> void:
	DirAccess.make_dir_recursive_absolute(SHOTS)
	var g := "ground" if current < 0 else str(grounds[current].get("dir", grounds[current].get("stem", "model")))
	var stamp := Time.get_datetime_string_from_system().replace(":", "-")
	var path := "%s/%s_%s.png" % [SHOTS, g.validate_filename(), stamp]
	help.visible = false
	hud.visible = false
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(path)
	hud.visible = true
	help.visible = true
	DisplayServer.clipboard_set(_where())
	_say("Saved %s (and copied where you are)" % ProjectSettings.globalize_path(path), 6.0)
