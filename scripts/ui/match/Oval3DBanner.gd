class_name Oval3DBanner
extends Node3D
## Through the banner on the 3D ground (row 202; asked for 2026-11-21: "a 'running through the
## banners' scene, similar to our existing vignette but in the new 3d view"). Before the first
## bounce the cheer squad holds your club's banner up on the far wing, in front of the race; your
## side bursts through it, the crepe paper tears into strips that hang from the rope or fall to the
## grass, the crowd rises, and the picture cuts as the TV coverage does: the wide,
## low and front-on as they burst through, then alongside as they run onto the ground.
## The words are PreMatchVignette.banner_text's (Banners.pick): milestones, else the club's name.
## Looks only: nothing here is read by the match. Built by PitchView, driven by frame(dt).

signal burst   # the first man is through the paper: the crowd's roar
signal done

## A run-through banner is a great sheet of crepe paper, 18 m by 6.5 m (PreMatchVignette.BANNER_W),
## taped from strips of crepe hung from a rope between two poles.
const W := 18.0
const LOW := 0.5               # m: the paper's bottom edge
const TOP := 7.0               # m: the rope
## The squad hold the bottom corners this far out from the middle (the paper's own grid is
## Oval3DBannerCloth's).
const HELD_FROM := 6.2
## Where it stands: this far inside the boundary on the far wing (the camera's wing is +z, rule
## 2.93), BANNER_X up the ground, the printed face toward the middle of the ground.
const IN_FROM_BOUNDARY := 13.0
const BANNER_X := -6.0
const RACE_BACK := 13.0        # m: they come from this far behind the paper (the race's mouth)
const RUN_SPEED := 7.2         # m/s: a run-out is quicker than the jog loop's pace
const RUN_AFTER := 26.0        # m: how far onto the ground each runs past the paper
const FIRST_GO := 1.2          # s: the first man leaves the race
const ROW_GAP := 0.32          # s: each rank of the pack behind the one in front
## The cuts, from the moment the first man is through: the wide until CUT_FRONT before it,
## front-on until CUT_BACK after it, then from the race behind them until the end.
const CUT_FRONT := 1.1
const CUT_BACK := 2.0
const LAST_SHOT := 2.4
## Where the ground has a pre-game shot (GroundModels.PREGAME_VIEW, set by the director in the ground
## inspector), the scene opens on it for PREGAME_HOLD seconds, at the inspector's lens, before the wide.
const PREGAME_HOLD := 3.0
const PREGAME_FOV := 70.0
const PAPER_FACE := "res://scripts/ui/match/oval3d_banner.gdshader"

var oval: Oval3D
var side := 0
var t := 0.0
var finished := false
var _centre := Vector3.ZERO    # the paper's foot, middle (world)
var _runners: Array = []       # [{p, i, path: [a, b, c], go, len, cross}]
var _others: Array = []        # every other body on the ground: their stand loop runs on
var _squad: Array = []         # the cheer squad: [{p, pose}]
var _paper: MultiMeshInstance3D
var cloth: Oval3DBannerCloth   # the paper (it tears as the men go through)
var _burst_at := INF
var cut_front := 0.0           # s: the cuts (CUT_FRONT, CUT_BACK), worked out from the first man through
var cut_back := 0.0
var length := 0.0
var _mat: ShaderMaterial
var _face_vp: SubViewport
var _rng := RandomNumberGenerator.new()
var _hidden: Array = []        # nodes shown again at the end (the rings, the ball)
var _opening := Transform3D.IDENTITY   # the pre-game shot, world (the scene runs from -PREGAME_HOLD)
var _has_opening := false


## The banner for `p_side` (0 home, 1 away) with `text` (lines split on "\n"), in `club`'s colours.
func build(p_oval: Oval3D, p_side: int, text: String, club: String, seed := 0) -> void:
	oval = p_oval
	side = p_side
	top_level = true
	_rng.seed = hash([seed, club, text])
	# The far wing is world -z whichever way round the ground is (Oval3D.set_ends turns the ground).
	_centre = Vector3(BANNER_X, 0.0, -(MatchMotion.HALF_WID - IN_FROM_BOUNDARY))
	global_transform = Transform3D(Basis.IDENTITY, _centre)
	var cols := GameDB.club_colours(club)
	_face(text, cols)
	_build_paper()
	_build_poles()
	_build_squad(club, cols)
	_build_runners()
	_plan_tear()
	var slug := GroundModels.slug_for(oval.ground) if oval.ground != "" else ""
	if GroundModels.has_pregame_view(slug):
		# In the ground's own frame, so it turns with the ground when the ends change.
		_opening = oval.global_transform * GroundModels.pregame_view(slug)
		_has_opening = true
		t = -PREGAME_HOLD
	for n in [oval.ball]:
		if n != null and n.visible:
			n.visible = false
			_hidden.append(n)
	for p in oval.players + oval.umpires:
		var ring: Node3D = p.get("ring")
		if ring != null and ring.visible:
			ring.visible = false
			_hidden.append(ring)
	frame(0.0)


# ---------------------------------------------------------------------------
# The printed face: drawn once in a small viewport, then kept as a texture with mipmaps.
# ---------------------------------------------------------------------------
class Face extends Control:
	var text := ""
	var cols: Array = []

	func _draw() -> void:
		var bg: Color = cols[0]
		var band: Color = cols[1]
		# The paint: whichever of the club's second colour and white stands out more on the paper.
		var ink: Color = cols[1] if _contrast(cols[1], bg) >= _contrast(Color.WHITE, bg) else Color.WHITE
		if _contrast(band, bg) < 1.6:
			band = ink
		draw_rect(Rect2(Vector2.ZERO, size), bg)
		var bh := size.y * 0.085
		draw_rect(Rect2(0, 0, size.x, bh), band)
		draw_rect(Rect2(0, size.y - bh, size.x, bh), band)
		var lines := text.to_upper().split("\n", false)
		if lines.is_empty():
			return
		var font: Font = UiKit.BOLD
		var widest := 1.0
		for l in lines:
			widest = maxf(widest, font.get_string_size(l, HORIZONTAL_ALIGNMENT_LEFT, -1, 100).x)
		# As big as the paper takes: the widest line across 92% of it, the lines' capitals
		# (about 0.72 of the font's ascent) filling the room between the bands with a gap between.
		var room := size.y - 2.0 * bh - size.y * 0.1
		var cap_k := font.get_ascent(100) * 0.72 / 100.0
		var n := lines.size()
		var fs := int(minf(100.0 * size.x * 0.92 / widest, room / ((n + (n - 1) * 0.3) * cap_k)))
		var cap := font.get_ascent(fs) * 0.72
		var lh := cap * 1.3
		var y := bh + size.y * 0.05 + (room - (lh * n - cap * 0.3)) * 0.5 + cap
		for l in lines:
			var w := font.get_string_size(l, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			var at := Vector2((size.x - w) * 0.5, y)
			# A painted letter's dark edge, as a signwriter's brush leaves it.
			draw_string_outline(font, at, l, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, maxi(2, fs / 14), Color(0, 0, 0, 0.35))
			draw_string(font, at, l, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, ink)
			y += lh

	static func _contrast(a: Color, b: Color) -> float:
		var la := a.get_luminance() + 0.05
		var lb := b.get_luminance() + 0.05
		return maxf(la, lb) / minf(la, lb)


func _face(text: String, cols: Array) -> void:
	_face_vp = SubViewport.new()
	_face_vp.size = Vector2i(1536, 556)
	_face_vp.transparent_bg = false
	_face_vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	_face_vp.disable_3d = true
	var f := Face.new()
	f.text = text
	f.cols = cols
	f.size = Vector2(_face_vp.size)
	_face_vp.add_child(f)
	add_child(_face_vp)
	_mat = ShaderMaterial.new()
	_mat.shader = load(PAPER_FACE)
	_mat.set_shader_parameter("face", _face_vp.get_texture())
	_mat.set_shader_parameter("paper_w", W)
	_keep_face.call_deferred()


## The face as a texture with mipmaps (a viewport's has none, and shimmers far off).
func _keep_face() -> void:
	await RenderingServer.frame_post_draw
	if not is_instance_valid(_face_vp):
		return
	var img := _face_vp.get_texture().get_image()
	if img == null or img.is_empty():
		return
	img.generate_mipmaps()
	_mat.set_shader_parameter("face", ImageTexture.create_from_image(img))
	_face_vp.queue_free()
	_face_vp = null


# ---------------------------------------------------------------------------
# The paper, the poles and the rope
# ---------------------------------------------------------------------------
func _build_paper() -> void:
	cloth = Oval3DBannerCloth.new(W, LOW, TOP, HELD_FROM, _rng.randi())
	if oval.quality == Oval3DQuality.LOW:
		cloth.substeps = 1     # Graphics: Low: half the work, a little stiffer
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = QuadMesh.new()   # 1 x 1: each cell's own transform stretches it between its points
	mm.instance_count = Oval3DBannerCloth.NX * Oval3DBannerCloth.NY
	_mat.set_shader_parameter("cells", Vector2(Oval3DBannerCloth.NX, Oval3DBannerCloth.NY))
	cloth.draw(mm)
	_paper = MultiMeshInstance3D.new()
	_paper.multimesh = mm
	_paper.material_override = _mat
	_paper.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	_paper.extra_cull_margin = 30.0
	add_child(_paper)


func _build_poles() -> void:
	var metal := StandardMaterial3D.new()
	metal.albedo_color = Color(0.72, 0.73, 0.75)
	metal.metallic = 0.6
	metal.roughness = 0.4
	for sx in [-1.0, 1.0]:
		var pole := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.035
		cm.bottom_radius = 0.035
		cm.height = TOP + 0.6
		cm.radial_segments = 8
		pole.mesh = cm
		pole.material_override = metal
		pole.position = Vector3(sx * (W * 0.5 + 0.06), cm.height * 0.5, 0.0)
		add_child(pole)
	var rope := MeshInstance3D.new()
	var rm := CylinderMesh.new()
	rm.top_radius = 0.015
	rm.bottom_radius = 0.015
	rm.height = W + 0.12
	rm.radial_segments = 6
	rope.mesh = rm
	var rmat := StandardMaterial3D.new()
	rmat.albedo_color = Color(0.9, 0.9, 0.86)
	rope.material_override = rmat
	rope.rotation.z = PI * 0.5
	rope.position = Vector3(0.0, TOP + 0.02, 0.0)
	add_child(rope)


# ---------------------------------------------------------------------------
# The cheer squad: two at each pole, a few holding each end of the paper up from behind, and
# a few more beside it, in plain tops of the club's colour.
# ---------------------------------------------------------------------------
const SQUAD_SPOTS := [
	# [x from the middle, z (+: the ground side), facing (0: the ground), pose]
	[-9.45, -0.55, 0.0, "pole"], [-9.0, -0.75, 0.0, "pole"], [9.45, -0.55, 0.0, "pole"], [9.0, -0.75, 0.0, "pole"],
	[-8.2, -0.9, 0.0, "hold"], [-7.3, -0.95, 0.0, "hold"], [-6.4, -0.9, 0.0, "hold"],
	[8.2, -0.9, 0.0, "hold"], [7.3, -0.95, 0.0, "hold"], [6.4, -0.9, 0.0, "hold"],
	[-10.6, 0.7, -0.5, "cheer"], [-11.4, -0.4, -0.3, "cheer"], [10.6, 0.7, 0.5, "cheer"], [11.5, -0.3, 0.3, "cheer"],
]


const SQUAD_LEGS := [Color(0.16, 0.21, 0.32), Color(0.2, 0.26, 0.38), Color(0.07, 0.07, 0.08), Color(0.33, 0.34, 0.36)]
const SQUAD_HAIR := ["short_crop", "crew", "long", "tied_back", "curly_short", "shaggy", "shoulder_length", "buzz"]


func _build_squad(club: String, cols: Array) -> void:
	var scene: PackedScene = load(Oval3D.player_glb)
	if scene == null:
		return
	# Supporters' clothes: half in the club's guernsey, half in a plain top of its colour, with
	# jeans, black or grey trackpants and white shoes (oval3d_player.gdshader's trousers).
	var top: Color = cols[0]
	var kits := [oval._kit(GameDB.club_guernsey(club)), oval._kit({"base": top, "design": "plain", "shorts": Color(0.1, 0.1, 0.12)})]
	for i in range(SQUAD_SPOTS.size()):
		var s: Array = SQUAD_SPOTS[i]
		if str(s[3]) == "cheer" and oval.quality == Oval3DQuality.LOW:
			continue     # Graphics: Low: those holding it up only (the phone budget)
		var p: Dictionary = oval._player(scene, kits[i % 2], cols, "")
		oval._number(p, -1)
		var legs: Color = SQUAD_LEGS[_rng.randi() % SQUAD_LEGS.size()]
		for mi in (p["node"] as Node3D).find_children("*", "MeshInstance3D", true, false):
			if (mi as MeshInstance3D).has_meta("kit"):
				(mi as GeometryInstance3D).set_instance_shader_parameter("trousers", legs)
		oval.look(p, {"skin": _rng.randi_range(0, 4), "hair": _rng.randi_range(0, 5),
				"hair_style": SQUAD_HAIR[_rng.randi() % SQUAD_HAIR.size()]})
		var ring: Node3D = p["ring"]
		ring.visible = false
		var node: Node3D = p["node"]
		node.global_transform = Transform3D(Basis(Vector3.UP, float(s[2])), global_transform * Vector3(float(s[0]), 0.0, float(s[1])))
		var ap: AnimationPlayer = p["anim"]
		ap.play("idle")
		ap.seek(_rng.randf() * 8.0, true)
		_squad.append({"p": p, "pose": str(s[3]), "k": _rng.randf() * TAU})


## Arms up: the bones turned after the stand loop has set them, toward where his hands go (the
## body's own frame: +z ahead, +x his left). A pole or the paper's edge held at about head height;
## a cheer, both arms high and pumping.
func _pose(sq: Dictionary) -> void:
	var p: Dictionary = sq["p"]
	var skel: Skeleton3D = p["skel"]
	var pose := str(sq["pose"])
	var k := float(sq["k"])
	for s in [0, 1]:
		var out := 1.0 if s == 0 else -1.0
		var up := 1.05
		if pose == "pole":
			up = 0.75 if s == 0 else 1.35
		elif pose == "cheer":
			up = 2.35 + 0.3 * sin(t * 7.0 + k + s * 1.3)
		var arm := Vector3(out * 0.3, sin(up - PI * 0.5) , cos(up - PI * 0.5)).normalized()
		_aim(skel, ["upperarm_l", "upperarm_r"][s], ["lowerarm_l", "lowerarm_r"][s], arm)
		var fore := Vector3(out * 0.1, sin(up - PI * 0.5 + 0.5), cos(up - PI * 0.5 + 0.5)).normalized()
		_aim(skel, ["lowerarm_l", "lowerarm_r"][s], ["hand_l", "hand_r"][s], fore)


## Turn bone `name` so that its child `tip` lies along `dir` from it (the skeleton's own frame).
static func _aim(skel: Skeleton3D, name: String, tip: String, dir: Vector3) -> void:
	var b := skel.find_bone(name)
	var c := skel.find_bone(tip)
	if b < 0 or c < 0:
		return
	var g := skel.get_bone_global_pose(b)
	var now := skel.get_bone_global_pose(c).origin - g.origin
	if now.length() < 0.001:
		return
	var turn := Quaternion(now.normalized(), dir.normalized())
	var want := Basis(turn) * g.basis
	var parent := skel.get_bone_parent(b)
	var pg := skel.get_bone_global_pose(parent).basis if parent >= 0 else Basis.IDENTITY
	skel.set_bone_pose_rotation(b, (pg.inverse() * want).get_rotation_quaternion())


# ---------------------------------------------------------------------------
# The runners: your 18 from the race, in a pack, through the paper and on to the ground.
# ---------------------------------------------------------------------------
func _build_runners() -> void:
	var mine := []
	var dir: Array = oval.director.tokens
	for i in range(oval.players.size()):
		if int((dir[i] as Dictionary).get("side", 0)) == side:
			mine.append(i)
		else:
			_others.append(oval.players[i])
	_others.append_array(oval.umpires)
	# The pack: one in front (the captain's spot), then ranks of three to five.
	var ranks := [1, 3, 4, 5, 5]
	var n := 0
	for rank in range(ranks.size()):
		var w: int = ranks[rank]
		for j in range(w):
			if n >= mine.size():
				break
			var lane := (float(j) - (w - 1) * 0.5) * 1.35 + _rng.randf_range(-0.3, 0.3)
			var from := Vector3(lane * 0.7, 0.0, -RACE_BACK - rank * 1.7 - _rng.randf_range(0.0, 0.6))
			var cross := Vector3(lane * 1.15, 0.0, 0.0)
			# Out the other side they fan out toward the middle of the ground.
			var out := Vector3(lane * 3.2 + _rng.randf_range(-1.5, 1.5) + 4.0, 0.0, RUN_AFTER + rank * 1.2)
			var a := global_transform * from
			var b := global_transform * cross
			var c := global_transform * out
			var length := _bez_len(a, b, c)
			var go := FIRST_GO + rank * ROW_GAP + _rng.randf_range(0.0, 0.12)
			var r := {"p": oval.players[mine[n]], "path": [a, b, c], "go": go, "len": length,
					"speed": RUN_SPEED * _rng.randf_range(0.94, 1.04)}
			r["cross"] = go + _bez_find(a, b, c, _centre.z) * length / float(r["speed"])
			r["x"] = cross.x
			_runners.append(r)
			n += 1


static func _bez(a: Vector3, b: Vector3, c: Vector3, u: float) -> Vector3:
	return a.lerp(b, u).lerp(b.lerp(c, u), u)


static func _bez_len(a: Vector3, b: Vector3, c: Vector3) -> float:
	var sum := 0.0
	var last := a
	for i in range(1, 33):
		var q := _bez(a, b, c, i / 32.0)
		sum += last.distance_to(q)
		last = q
	return sum


## The share of the path's length at which it reaches z (it runs toward +z).
static func _bez_find(a: Vector3, b: Vector3, c: Vector3, z: float) -> float:
	for i in range(1, 129):
		if _bez(a, b, c, i / 128.0).z >= z:
			return i / 128.0
	return 1.0


func _runner_at(r: Dictionary, at: float) -> Array:
	var s := clampf((at - float(r["go"])) * float(r["speed"]) / float(r["len"]), 0.0, 1.0)
	var path: Array = r["path"]
	var pos := _bez(path[0], path[1], path[2], s)
	var ahead := _bez(path[0], path[1], path[2], minf(1.0, s + 0.02))
	if s >= 1.0:
		ahead = pos + (pos - _bez(path[0], path[1], path[2], 0.98))
	return [pos, ahead - pos, s]


## When the first man reaches the paper, and the cuts from it.
func _plan_tear() -> void:
	var first := INF
	for r in _runners:
		first = minf(first, float(r["cross"]))
	_burst_at = first
	# Each man's own tear up from where he hits it; the first man's splits the sheet open.
	# A few long tears, not a shredding: a man where the paper has already gone goes through the gap.
	var order := _runners.duplicate()
	order.sort_custom(func(a, b): return float(a["cross"]) < float(b["cross"]))
	var lines := []
	for r in order:
		var x := float(r["x"]) + _rng.randf_range(-0.25, 0.25)
		var clear := true
		for l in lines:
			if absf(x - float(l)) < 1.6:
				clear = false
		if not clear:
			continue
		lines.append(x)
		cloth.rip(x, float(r["cross"]) - 0.05, _rng.randf_range(0.55, 0.95), lines.size() == 1)
	cut_front = first - CUT_FRONT
	cut_back = first + CUT_BACK
	length = cut_back + LAST_SHOT


# ---------------------------------------------------------------------------
# Each frame
# ---------------------------------------------------------------------------
## Advance by dt (seconds of wall time); true once the scene has played out.
func frame(dt: float) -> bool:
	if finished:
		return true
	var was := t
	t += dt
	if was < _burst_at and t >= _burst_at:
		burst.emit()
		if oval.crowd != null:
			oval.crowd.cheer(side, oval._crowd_t)
	oval._crowd_t += dt
	if oval.crowd != null:
		oval.crowd.set_now(oval._crowd_t)
	_mat.set_shader_parameter("now", t)
	_move_runners(dt)
	for p in _others:
		(p["anim"] as AnimationPlayer).advance(dt)
	for sq in _squad:
		((sq["p"] as Dictionary)["anim"] as AnimationPlayer).advance(dt)
		_pose(sq)
	_move_paper(dt)
	_camera()
	if t >= length:
		finish()
	return finished


func _move_runners(dt: float) -> void:
	for r in _runners:
		var p: Dictionary = r["p"]
		var node: Node3D = p["node"]
		var ap: AnimationPlayer = p["anim"]
		var at := _runner_at(r, t)
		var pos: Vector3 = at[0]
		var way: Vector3 = at[1]
		var moving := t >= float(r["go"]) and float(at[2]) < 1.0
		var yaw := atan2(way.x, way.z) if way.length() > 0.001 else 0.0
		node.global_transform = Transform3D(Basis(Vector3.UP, yaw), pos)
		var want := "jog" if moving or t >= float(r["go"]) else "idle"
		if ap.current_animation != want:
			ap.play(want, 0.15)
		# The jog loop played up to a run-out's pace (Oval3DAnim's rate, as in the match).
		var rate := float(r["speed"]) / Oval3D.LOOP_SPEED if want == "jog" else 1.0
		ap.advance(dt * rate)


func _move_paper(dt: float) -> void:
	# The men at the paper, in its own frame: where each one's chest is and which way he runs.
	var men := []
	var inv := global_transform.affine_inverse()
	for r in _runners:
		if t < float(r["go"]):
			continue
		var at := _runner_at(r, t)
		var c: Vector3 = inv * (at[0] as Vector3)
		if c.z > -1.5 and c.z < 3.0:
			men.append([c, inv.basis * (at[1] as Vector3)])
	cloth.step(dt, men, t)
	cloth.draw(_paper.multimesh)


# ---------------------------------------------------------------------------
# The TV cuts. Each shot: where the camera is and where it looks, in the banner's own frame
# (x along the paper, z toward the ground), and its lens.
# ---------------------------------------------------------------------------
func _camera() -> void:
	var cam: Camera3D = oval.camera
	var eye: Vector3
	var at: Vector3
	var fov: float
	if _has_opening and t < 0.0:
		# The pre-game shot: the ground and the crowd, the squad on the far wing with the banner up.
		cam.global_transform = _opening
		cam.fov = PREGAME_FOV
		return
	if t < cut_front:
		# The wide: from up the wing on the ground side, the squad, the paper and the stand behind.
		var k := t / maxf(0.1, cut_front)
		eye = Vector3(-34.0 + 4.0 * k, 9.0, 46.0)
		at = Vector3(0.0, 3.4, 0.0)
		fov = 30.0 - 2.0 * k
	elif t < cut_back:
		# Low and front-on, a little off the middle: the words fill the picture; they burst out at us.
		var k := (t - cut_front) / (cut_back - cut_front)
		eye = Vector3(5.5, 1.5, 19.0 - 1.5 * k)
		at = Vector3(0.0, 3.2, 0.0)
		fov = 44.0
	else:
		# From the race: their backs as they run on, through what is left of the paper, the
		# ground and the crowd beyond; the camera eases after them.
		var k := (t - cut_back) / LAST_SHOT
		eye = Vector3(-1.5, 4.4 - 0.6 * k, -12.0 + 3.0 * k)
		at = Vector3(2.0, 1.2, 24.0)
		fov = 52.0
	cam.global_position = global_transform * eye
	cam.look_at(global_transform * at, Vector3.UP)
	cam.fov = fov


## The scene is over (its end, or a tap): the ground handed back to the match as it was.
func finish() -> void:
	if finished:
		return
	finished = true
	for n in _hidden:
		if is_instance_valid(n):
			(n as Node3D).visible = true
	for sq in _squad:
		var node: Node3D = (sq["p"] as Dictionary)["node"]
		if is_instance_valid(node):
			node.queue_free()
	_squad.clear()
	done.emit()
