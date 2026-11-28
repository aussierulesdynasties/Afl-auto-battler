class_name Oval3D
extends Node3D
## PROTOTYPE (director, 2026-11-14: "True 3D oval"): the live oval as a real 3D scene, the
## players running where MatchDirector puts them. Looks only: it reads the director's tokens
## and ball every frame and never writes to them, so the match is the same match.
##
## Ground metres map straight to world metres: director (x, y) -> world (x, 0, y), +x towards
## the goal side 0 attacks. The players are the vignette footballer (MPFB body, the pipeline's
## own jog and idle), exported as assets/oval3d/player_average.glb, recoloured per club.

const PLAYER_GLB := "res://assets/oval3d/player_average.glb"
## Club Forge's hair styles on the same rig, one mesh per style on the head bone
## (tools/oval3d/export_hair_glb.py: the pipeline's own procedural shells, hair_lib.py).
const HAIR_GLB := "res://assets/oval3d/hair_styles.glb"
## The hair file in use (HAIR_GLB; a capture may point it at a candidate set). A style drawn
## from a downloaded asset (tools/oval3d/export_mh_hair_glb.py) has its strand texture, greyed
## to be tinted (grey_hair_tex.py), at hair_tex/<style>.png beside it.
static var hair_glb := HAIR_GLB
## The scalp under each style (oval3d_player.gdshader, scalp): 0 the body's own painted crop
## (no look), 1 bare skin (bald, and under every style's shell, which has its own hairline),
## 2 clippered (buzz, and under the cuts with clippered sides). Under the dreadlocks it is his
## hair colour (0): skin showed down the back between the locks.
const SCALP := {"bald": 1, "buzz": 2, "dreadlocks": 0, "undercut": 2, "curly_short": 2, "faux_hawk": 2,
		"tied_back": 2}
const SCALP_UNDER_SHELL := 1
## The boots' own material in the GLB (export_player_glb.py, the Tripo boot): drawn as modelled.
const BOOT_MATERIAL := "ARD_boot_real"
const HALF_LEN := MatchMotion.HALF_LEN
const HALF_WID := MatchMotion.HALF_WID
const GOAL_X := MatchMotion.GOAL_X
const GOAL_GAP := 6.4
const GOAL_H := 12.0
const BEHIND_H := 6.5
const FENCE := 6.0
const STAND_DEPTH := 34.0
const STAND_RISE := 24.0
## The jog's 17 keys at 24 fps are one stride cycle in 0.67 s, matched to about 6 m/s.
const LOOK_X := 78.0           # m: the camera follows the ball this far towards each goal
const LOOK_Z := 55.0           # ...and this far out to each wing (the man on the ball stays in view)
const BODY_GAP := 0.6         # m between two players' centres, drawn
## The digits the vignettes print numbers with (R fill, G outline), shared so both read alike.
const DIGITS := preload("res://assets/vignette/figures_digits.png")
## A Sherrin is about 0.29 m end to end and 0.18 m across.
const BALL_R := 0.09
const BALL_LONG := 1.6

var director: MatchDirector
var players: Array = []        # [{node, anim, ring}] in director.tokens order
var ball: MeshInstance3D
var camera: Camera3D
var anim: Oval3DAnim          # the animation session's controller (row 198)
var umpires: Array = []        # [{node, anim, ring, role, k}]: the vignettes' umpire set
var _look := Vector3.ZERO


func build(p_director: MatchDirector, home: String, away: String) -> void:
	director = p_director
	_environment()
	_ground()
	_posts()
	_stands(home, away)
	var scene: PackedScene = load(PLAYER_GLB)
	# Each club in its home guernsey, as the vignettes dress them (StoppageVignette._dress).
	var kits := [_kit(GameDB.club_guernsey(home)), _kit(GameDB.club_guernsey(away))]
	for t in director.tokens:
		var side := int(t.get("side", 0))
		var p := _player(scene, kits[side], GameDB.club_colours(home if side == 0 else away))
		_dress(p, t)
		players.append(p)
	anim = Oval3DAnim.new(director, players)
	director.want_contacts = true
	_add_umpires(scene)
	ball = MeshInstance3D.new()
	var bm := SphereMesh.new()
	bm.radius = BALL_R
	bm.height = BALL_R * 2.0
	ball.mesh = bm
	ball.scale = Vector3(1.0, 1.0, BALL_LONG)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.85, 0.12, 0.1)
	mat.roughness = 0.6
	ball.material_override = mat
	add_child(ball)
	camera = Camera3D.new()
	camera.fov = 30.0
	camera.far = 900.0
	# Placed in world space, so turning the ground for a change of ends (set_ends) leaves
	# the camera where the broadcast puts it.
	camera.top_level = true
	add_child(camera)
	sync(0.0)


## Copy the director's state onto the scene. The animations advance here, by dt, so the
## carrier's hands are where this frame puts them when the ball goes between them.
## A player touches the ball (or the man) this frame: kick, handball, ruck_tap, mark,
## gather, handball_receive, tackle, smother, spoil, bounce (i -1: the field umpire),
## goal_celebrate. `at` is where the ball goes, metres on the ground; `other` the man
## tackled or smothered. Called at the moment of contact (3d view 2, 2026-11-15).
func anim_event(i: int, kind: StringName, at: Vector2, other := -1) -> void:
	anim.event(i, kind, at, other)


func sync(dt: float) -> void:
	for c in director.contacts:
		anim_event(int(c["who"]), c["kind"], c["at"], int(c["other"]))
	director.contacts.clear()
	var mode := str(director.ball.get("mode", ""))
	var holder := int(director.ball.get("holder", -1)) if mode == "held" else -1
	var resting := false
	if mode == "dead":
		# A dead ball (a free kick or mark being set up) has no holder in the director but
		# keeps its hand height; drawn as it is, it would hang in the air. Within a metre of
		# a player it is in his hands; otherwise it lies on the turf.
		holder = _nearest(director.ball["pos"], 1.0)
		resting = holder < 0
	var at := _spaced()
	for i in range(players.size()):
		var t: Dictionary = director.tokens[i]
		var p: Dictionary = players[i]
		# An interchange puts another man in the slot: his own look and number.
		if str(t.get("pid", "")) != str(p.get("pid", "")):
			_dress(p, t)
		var pos: Vector2 = at[i]
		var vel: Vector2 = t["vel"]
		var node: Node3D = p["node"]
		node.position = Vector3(pos.x, 0.0, pos.y)
		anim.step(i, p, holder, pos, vel, dt)
	_move_umpires(dt)
	var bp: Vector2 = director.ball["pos"]
	var h := float(director.ball.get("h", 0.0))
	if holder >= 0 and holder < players.size():
		_hold_ball(players[holder])
	else:
		ball.position = Vector3(bp.x, BALL_R if resting else maxf(BALL_R, h), bp.y)
		ball.rotation = Vector3.ZERO
	# Followed to within a few metres of each goal line: a kick-in or a shot at the camera's own
	# end stays in view (aim_end stops looking ahead there).
	var target := Vector3(clampf(bp.x, -LOOK_X, LOOK_X), 0.0, clampf(bp.y, -LOOK_Z, LOOK_Z))
	_look = target if dt <= 0.0 else _look.lerp(target, clampf(dt * 1.5, 0.0, 1.0))


## Where each body is drawn: the director's spot, except that two bodies closer than BODY_GAP
## are eased apart along the line between them (drawn only; the tokens are not touched).
## A disc can sit on a disc; a body can't stand inside a body. About 2% of frames have such a
## pair (seed 31, 10 minutes: under 0.6 m in 0.7% same side, 1.2% opponents), most under 0.3 m apart.
func _spaced() -> Array:
	var at := []
	for t in director.tokens:
		at.append(t["pos"])
	for i in range(at.size()):
		for j in range(i + 1, at.size()):
			var gap: Vector2 = at[j] - at[i]
			var dist := gap.length()
			if dist < BODY_GAP:
				var dir := gap / dist if dist > 0.001 else Vector2.RIGHT.rotated(float(i))
				var push := dir * (BODY_GAP - dist) * 0.5
				at[i] -= push
				at[j] += push
	return at


func _nearest(at: Vector2, within: float) -> int:
	var best := -1
	var best_d := within
	for i in range(director.tokens.size()):
		var d := (director.tokens[i]["pos"] as Vector2).distance_to(at)
		if d < best_d:
			best_d = d
			best = i
	return best


## The ball sits between the carrier's palms, its long axis across his body as the carry pose
## holds it. A palm is 60% along the hand bone, the point the sprite pipeline uses
## (build_sprites.hands_px), so the 3D ball and the sprite ball sit in the same place.
func _hold_ball(p: Dictionary) -> void:
	var skel: Skeleton3D = p["skel"]
	var hands: Array = p["hands"]
	var gt := skel.global_transform
	var palms := []
	for k in range(2):
		var pose := skel.get_bone_global_pose(hands[k])
		palms.append(gt * (pose.origin + pose.basis.y.normalized() * float(p["hand_len"][k]) * 0.6))
	var l: Vector3 = palms[0]
	var r: Vector3 = palms[1]
	ball.position = (l + r) * 0.5
	var across := r - l
	if across.length() > 0.01:
		ball.look_at(ball.position + across, Vector3.UP)


## The sides change ends: +1 when the home side kicks to the far end of the camera's ground
## (periods 1 and 3), -1 the other way. The ground and everyone on it turn half a turn; the
## camera stays put, so the home side then attacks the other way up the screen.
func set_ends(sign: float) -> void:
	rotation.y = 0.0 if sign > 0.0 else PI


func _world(v: Vector3) -> Vector3:
	return global_transform * v


## The broadcast camera: up in the stand on the wing, following the ball along the ground.
func aim_wing(height: float, back: float) -> void:
	var at := _world(_look)
	camera.global_position = Vector3(at.x * 0.9, height, at.z * 0.4 + back)
	camera.look_at(at, Vector3.UP)


## Behind the play, high: the length of the ground runs up a portrait screen.
func aim_end(height: float, back: float) -> void:
	var at := _world(_look)
	# In the last 20 m before the camera's own goal the camera climbs to the high
	# behind-the-goals angle: from the usual height the goal posts stand in front of the play;
	# from above they are short uprights at its edge. (A wing camera loses the ball off a
	# portrait screen's narrow width.)
	var near := clampf((-at.x - (LOOK_X - 20.0)) / 20.0, 0.0, 1.0)
	camera.global_position = Vector3(at.x - back * lerpf(1.0, 0.55, near),
			height * lerpf(1.0, 2.4, near), at.z * 0.6)
	# 12 m ahead of the ball up the ground; none from the high angle.
	camera.look_at(at + Vector3(12.0 * (1.0 - near), 0.0, 0.0), Vector3.UP)


## Close on the ball, from the wing side and a little behind: the body check.
func aim_close() -> void:
	var bp: Vector2 = director.ball["pos"]
	var at := _world(Vector3(bp.x, 0.0, bp.y))
	camera.global_position = at + Vector3(-9.0, 4.5, 11.0)
	camera.look_at(at + Vector3(0.0, 1.0, 0.0), Vector3.UP)


# ---------------------------------------------------------------------------
func _environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.55, 0.7, 0.86)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.62, 0.66, 0.72)
	env.ambient_light_energy = 0.4
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-52.0, -35.0, 0.0)
	sun.light_energy = 1.25
	sun.shadow_enabled = true
	# Shadows only as far as the broadcast camera needs them, softened and lifted off the body
	# so the shorts and arms don't speckle the thighs and ribs with shadow-map steps.
	# The default soft-shadow filter draws the shade under the shorts as a dotted pattern; more
	# filter samples and a finer map make it a smooth band (a phone cost to measure).
	sun.directional_shadow_max_distance = 160.0
	sun.shadow_normal_bias = 2.0
	RenderingServer.directional_shadow_atlas_set_size(4096, true)
	RenderingServer.directional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_HIGH)
	add_child(sun)


func _ground() -> void:
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(2.0 * (HALF_LEN + FENCE + 1.0), 2.0 * (HALF_WID + FENCE + 1.0))
	mi.mesh = pm
	var sm := ShaderMaterial.new()
	sm.shader = load("res://scripts/ui/match/oval3d_ground.gdshader")
	sm.set_shader_parameter("half_size", Vector2(HALF_LEN, HALF_WID))
	sm.set_shader_parameter("goal_x", GOAL_X)
	mi.material_override = sm
	add_child(mi)


func _posts() -> void:
	var white := StandardMaterial3D.new()
	white.albedo_color = Color(0.96, 0.96, 0.94)
	var pad := StandardMaterial3D.new()
	pad.albedo_color = Color(0.85, 0.15, 0.12)
	for end in [-1.0, 1.0]:
		for k in [-1.5, -0.5, 0.5, 1.5]:
			var goal: bool = absf(k) < 1.0
			var post := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 0.17
			cm.bottom_radius = 0.17
			cm.height = GOAL_H if goal else BEHIND_H
			post.mesh = cm
			post.material_override = white
			post.position = Vector3(end * GOAL_X, cm.height * 0.5, k * GOAL_GAP)
			add_child(post)
			var p := MeshInstance3D.new()
			var pc := CylinderMesh.new()
			pc.top_radius = 0.36
			pc.bottom_radius = 0.36
			pc.height = 2.8
			p.mesh = pc
			p.material_override = pad
			p.position = Vector3(end * GOAL_X, 1.4, k * GOAL_GAP)
			add_child(p)


## A raked stand all the way round, the crowd painted by its shader in both clubs' colours.
func _stands(home: String, away: String) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var seg := 160
	for i in range(seg):
		var a0 := TAU * float(i) / seg
		var a1 := TAU * float(i + 1) / seg
		var ring := []
		for a in [a0, a1]:
			var d := Vector2(cos(a), sin(a))
			var inner := Vector3(d.x * (HALF_LEN + FENCE), 1.2, d.y * (HALF_WID + FENCE))
			var outer := Vector3(d.x * (HALF_LEN + FENCE + STAND_DEPTH), STAND_RISE,
					d.y * (HALF_WID + FENCE + STAND_DEPTH))
			ring.append([inner, outer, a / TAU])
		var u0: float = ring[0][2] * 160.0
		var u1: float = ring[1][2] * 160.0
		var quad := [[ring[0][0], Vector2(u0, 0)], [ring[0][1], Vector2(u0, 1)],
				[ring[1][1], Vector2(u1, 1)], [ring[1][0], Vector2(u1, 0)]]
		for idx in [0, 1, 2, 0, 2, 3]:
			st.set_uv(quad[idx][1])
			st.add_vertex(quad[idx][0])
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var sm := ShaderMaterial.new()
	sm.shader = load("res://scripts/ui/match/oval3d_crowd.gdshader")
	var hc: Array = GameDB.club_colours(home)
	var ac: Array = GameDB.club_colours(away)
	sm.set_shader_parameter("home_a", hc[0])
	sm.set_shader_parameter("home_b", hc[1])
	sm.set_shader_parameter("away_a", ac[0])
	sm.set_shader_parameter("away_b", ac[1])
	mi.material_override = sm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	# The fence: a low white wall at the foot of the stand.
	var fence := MeshInstance3D.new()
	var fm := CylinderMesh.new()
	fm.top_radius = 1.0
	fm.bottom_radius = 1.0
	fm.height = 1.2
	fm.radial_segments = 128
	fm.cap_top = false
	fm.cap_bottom = false
	fence.mesh = fm
	fence.scale = Vector3(HALF_LEN + FENCE, 1.0, HALF_WID + FENCE)
	fence.position.y = 0.6
	var fmat := StandardMaterial3D.new()
	fmat.albedo_color = Color(0.92, 0.92, 0.9)
	fmat.cull_mode = BaseMaterial3D.CULL_DISABLED
	fence.material_override = fmat
	add_child(fence)


## One kit material per club: the region fields in the mesh pick skin, hair, guernsey,
## shorts, socks and boots per pixel, and the guernsey wears the club's design
## (oval3d_player.gdshader). kit is GameDB.club_guernsey's {design, base, pattern, pattern2,
## shorts, pattern3, kit_cell}, set as StoppageVignette.figure_material sets it.
func _kit(kit: Dictionary) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://scripts/ui/match/oval3d_player.gdshader")
	m.set_shader_parameter("kit_base", [kit["base"]])
	m.set_shader_parameter("kit_pattern", [kit.get("pattern", kit["base"])])
	m.set_shader_parameter("kit_pattern2", [kit.get("pattern2", kit["base"])])
	m.set_shader_parameter("kit_pattern3", [kit.get("pattern3", kit.get("pattern2", kit["base"]))])
	var cell := int(kit.get("kit_cell", -1))
	m.set_shader_parameter("kit_design", [float(100 + cell) if cell >= 0
			else float(maxi(0, GameDB.GUERNSEY_DESIGNS.find(str(kit.get("design", "plain")))))])
	m.set_shader_parameter("shorts", kit.get("shorts", Color(0.94, 0.94, 0.92)))
	m.set_shader_parameter("digits_tex", DIGITS)
	m.set_shader_parameter("kit_atlas", GameDB.kit_atlas())
	m.set_shader_parameter("kit_grid", GameDB.kit_grid())
	return m


## His number on the back of his guernsey (0-99; -1 for none), per figure.
func _number(p: Dictionary, n: int) -> void:
	for mi in (p["node"] as Node3D).find_children("*", "MeshInstance3D", true, false):
		if (mi as MeshInstance3D).has_meta("kit"):
			(mi as GeometryInstance3D).set_instance_shader_parameter("number", clampi(n, -1, 99))


## The man in token t's slot as he looks: his number, skin, hair colour and hair style
## (GameDB.figure_look: what he chose in Club Forge, a generated player's own variety, a real
## player's curated look). Looks only, as the vignettes draw him.
func _dress(p: Dictionary, t: Dictionary) -> void:
	var pid := str(t.get("pid", ""))
	p["pid"] = pid
	_number(p, int(t.get("num", -1)))
	var who = GameDB.player_by_id(pid) if pid != "" else null
	look(p, GameDB.figure_look(who) if who != null else StoppageVignette.UMPIRE_LOOK)


## Skin, hair colour and hair style on one figure. l: {"skin", "hair"} palette indices
## (Appearance.SKIN, HAIR) and "hair_style" (Appearance.HAIR_STYLES; none: the base crop).
## any_shell: also a shell id of a candidate set (hair_glb) that is no Club Forge style yet (captures).
func look(p: Dictionary, l: Dictionary, any_shell := false) -> void:
	var skin: Color = Appearance.SKIN[clampi(int(l.get("skin", 1)), 0, Appearance.SKIN.size() - 1)]
	var hair_i := clampi(int(l.get("hair", 1)), 0, Appearance.HAIR.size() - 1)
	var style := str(l.get("hair_style", VignetteFigures.HAIR_BASE))
	if not Appearance.HAIR_STYLES.has(style) and not (any_shell and hair_shells().has(style)):
		style = VignetteFigures.HAIR_BASE
	for mi in (p["node"] as Node3D).find_children("*", "MeshInstance3D", true, false):
		if (mi as MeshInstance3D).has_meta("kit"):
			var g := mi as GeometryInstance3D
			g.set_instance_shader_parameter("skin", skin)
			g.set_instance_shader_parameter("hair", Appearance.HAIR[hair_i])
			g.set_instance_shader_parameter("scalp", scalp_for(style))
	p["hair_style"] = style
	if p.get("hair_node") is Node:
		(p["hair_node"] as Node).free()
	p.erase("hair_node")
	var shell: Dictionary = hair_shells().get(style, {})
	if shell.is_empty():
		return
	var skel: Skeleton3D = p["skel"]
	var on := BoneAttachment3D.new()
	on.name = "Hair"
	on.bone_name = str(shell["bone"])
	skel.add_child(on)
	var mi := MeshInstance3D.new()
	mi.name = "hair_" + style
	mi.mesh = shell["mesh"]
	mi.transform = shell["at"]
	mi.material_override = _hair_material(hair_i, shell.get("tex"))
	on.add_child(mi)
	p["hair_node"] = on


static var _shells := {}
static var _hair_mats := {}


## Each style's shell from HAIR_GLB, read once: {style: {"mesh", "bone", "at"}}, "at" being
## the mesh's place relative to its bone, so it sits the same on every player's head.
static func hair_shells() -> Dictionary:
	if not _shells.is_empty() or not ResourceLoader.exists(hair_glb):
		return _shells
	var root: Node = (load(hair_glb) as PackedScene).instantiate()
	for n in root.find_children("hair_*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var parent := mi.get_parent()
		if not parent is BoneAttachment3D:
			push_error("Oval3D: %s is not on a bone in %s" % [mi.name, hair_glb])
			continue
		var style := str(mi.name).trim_prefix("hair_")
		_shells[style] = {"mesh": mi.mesh, "bone": (parent as BoneAttachment3D).bone_name, "at": mi.transform}
		var tex := hair_glb.get_base_dir().path_join("hair_tex/%s.png" % style)
		if ResourceLoader.exists(tex):
			_shells[style]["tex"] = load(tex)
	root.free()
	return _shells


## How far the pipeline pushed the scalp out for the old painted crop (ard_body.OFFSET["hair"],
## metres). Every style now sits on his skull as hair_lib fitted it, so the lift comes off.
const SCALP_LIFT := 0.010
## The body's hair region, a surface of its own in the GLB (ard_body.REGIONS).
const HAIR_SURFACE := "ARD_hair"
static var _skulls := {}


## The body mesh with the scalp back on his skull: every vertex at a hair-region corner (the
## pipeline lifted exactly those, in every surface they share) drawn in by SCALP_LIFT, and the
## normals round it recomputed, welded across surfaces, so the old ledge's light goes with it.
## Once per mesh; every player shares the copy.
static func _skull(m: Mesh) -> Mesh:
	if _skulls.has(m):
		return _skulls[m]
	var am := m as ArrayMesh
	var hair := -1
	if am != null:
		for s in range(am.get_surface_count()):
			var mat := am.surface_get_material(s)
			if mat != null and mat.resource_name == HAIR_SURFACE:
				hair = s
	if hair < 0:
		_skulls[m] = m
		return m
	var surfs := []
	for s in range(am.get_surface_count()):
		surfs.append(am.surface_get_arrays(s))
	var key := func(v: Vector3) -> Vector3i:
		return Vector3i((v * 1e5).round())
	# The lift's direction per corner: the normal of the hair region's own faces round it. They
	# all moved out together, so they lie parallel to the skull; the stored normals were baked
	# after the lift and tip up along the old ledge.
	var lift := {}
	var hv: PackedVector3Array = surfs[hair][Mesh.ARRAY_VERTEX]
	var hi: PackedInt32Array = surfs[hair][Mesh.ARRAY_INDEX]
	for f in range(0, hi.size(), 3):
		var fn := _face_normal(hv[hi[f]], hv[hi[f + 1]], hv[hi[f + 2]])
		for c in range(3):
			var k: Vector3i = key.call(hv[hi[f + c]])
			lift[k] = lift.get(k, Vector3.ZERO) + fn
	for k in lift:
		lift[k] = (lift[k] as Vector3).normalized()
	# Draw them in, and note every corner of a face that touches one: its normal changes.
	var keys := []
	var near := {}
	for a in surfs:
		var vs: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
		var k := []
		k.resize(vs.size())
		for i in range(vs.size()):
			k[i] = key.call(vs[i])
			if lift.has(k[i]):
				vs[i] -= lift[k[i]] * SCALP_LIFT
		a[Mesh.ARRAY_VERTEX] = vs
		var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
		for f in range(0, idx.size(), 3):
			if lift.has(k[idx[f]]) or lift.has(k[idx[f + 1]]) or lift.has(k[idx[f + 2]]):
				for c in range(3):
					near[k[idx[f + c]]] = Vector3.ZERO
		keys.append(k)
	# Area-weighted face normals, summed per corner across all surfaces.
	for s in range(surfs.size()):
		var vs: PackedVector3Array = surfs[s][Mesh.ARRAY_VERTEX]
		var idx: PackedInt32Array = surfs[s][Mesh.ARRAY_INDEX]
		var k: Array = keys[s]
		for f in range(0, idx.size(), 3):
			var c0: Vector3i = k[idx[f]]
			var c1: Vector3i = k[idx[f + 1]]
			var c2: Vector3i = k[idx[f + 2]]
			if not (near.has(c0) or near.has(c1) or near.has(c2)):
				continue
			var fn := _face_normal(vs[idx[f]], vs[idx[f + 1]], vs[idx[f + 2]])
			for c in [c0, c1, c2]:
				if near.has(c):
					near[c] += fn
	var out := ArrayMesh.new()
	for s in range(surfs.size()):
		var a: Array = surfs[s]
		var ns: PackedVector3Array = a[Mesh.ARRAY_NORMAL]
		var k: Array = keys[s]
		for i in range(ns.size()):
			var n: Vector3 = near.get(k[i], Vector3.ZERO)
			if n.length_squared() > 0.0:
				ns[i] = n.normalized()
		a[Mesh.ARRAY_NORMAL] = ns
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a)
		out.surface_set_material(s, am.surface_get_material(s))
		out.surface_set_name(s, am.surface_get_name(s))
	_skulls[m] = out
	return out


## A triangle's outward normal, scaled by its area (Godot winds front faces clockwise).
static func _face_normal(a: Vector3, b: Vector3, c: Vector3) -> Vector3:
	return (c - a).cross(b - a)


## Hair colour i on a shell; tex: a downloaded style's greyed strands (alpha cut), tinted i.
static func _hair_material(i: int, tex: Texture2D = null) -> StandardMaterial3D:
	var key := [i, tex]
	if not _hair_mats.has(key):
		var m := StandardMaterial3D.new()
		m.albedo_color = Appearance.HAIR[i]
		m.roughness = 0.9
		# Strand cards are one face thick: draw both sides, or the long styles show slits.
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		if tex != null:
			m.albedo_texture = tex
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			m.alpha_scissor_threshold = 0.5
			m.alpha_antialiasing_mode = BaseMaterial3D.ALPHA_ANTIALIASING_ALPHA_TO_COVERAGE
		_hair_mats[key] = m
	return _hair_mats[key]


## The scalp under style (oval3d_player.gdshader, scalp): bald and buzz their own; under any
## style's hair bare skin, as the hair has its own hairline (the body's painted crop would show
## as a band under it); no hair, the painted crop.
static func scalp_for(style: String) -> int:
	return int(SCALP.get(style, SCALP_UNDER_SHELL if hair_shells().has(style) else 0))


func _player(scene: PackedScene, kit: ShaderMaterial, cols: Array) -> Dictionary:
	var node: Node3D = scene.instantiate()
	add_child(node)
	# Every surface wears the kit except the boots, which keep their own textured material.
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		m.mesh = _skull(m.mesh)
		for s in range(m.mesh.get_surface_count()):
			var own := m.mesh.surface_get_material(s)
			if own == null or own.resource_name != BOOT_MATERIAL:
				m.set_surface_override_material(s, kit)
		m.set_meta("kit", true)
	var skel: Skeleton3D = node.find_children("*", "Skeleton3D", true, false)[0]
	var hands := [skel.find_bone("hand_l"), skel.find_bone("hand_r")]
	# A hand bone's length: its head to its fingers' roots (the children's rest offsets).
	var hand_len := []
	for hb in hands:
		var sum := 0.0
		var kids := skel.get_bone_children(hb)
		for c in kids:
			sum += skel.get_bone_rest(c).origin.length()
		hand_len.append(sum / maxf(1.0, kids.size()) if kids.size() > 0 else 0.1)
	var ap: AnimationPlayer = node.find_children("*", "AnimationPlayer", true, false)[0]
	for n in ["jog", "carry"]:
		var a: Animation = ap.get_animation(n)
		if a:
			a.loop_mode = Animation.LOOP_LINEAR
	ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	ap.play("idle")
	# The club ring at his feet: allegiance and a thumb target from any angle.
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.55
	tm.outer_radius = 0.72
	ring.mesh = tm
	ring.scale = Vector3(1.0, 0.05, 1.0)
	ring.position.y = 0.03
	var rm := StandardMaterial3D.new()
	rm.albedo_color = cols[0]
	rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	ring.material_override = rm
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	node.add_child(ring)
	return {"node": node, "anim": ap, "ring": ring, "skel": skel, "hands": hands, "hand_len": hand_len}


## The umpires, as the vignettes place them (VignetteExtras.umpires): three field umpires,
## a boundary umpire on each wing, a goal umpire on each goal line, in the umpires' lime
## (StoppageVignette.UMPIRE_GEAR). No club ring: they belong to neither side.
func _add_umpires(scene: PackedScene) -> void:
	var kit := _kit(StoppageVignette.UMPIRE_GEAR)
	var spots := _umpire_spots()
	for k in range(spots.size()):
		var u := _player(scene, kit, [StoppageVignette.UMPIRE])
		look(u, StoppageVignette.UMPIRE_LOOK)
		(u["ring"] as Node3D).visible = false
		u["role"] = str(spots[k][0])
		u["k"] = k
		var at: Vector2 = spots[k][1]
		(u["node"] as Node3D).position = Vector3(at.x, 0.0, at.y)
		umpires.append(u)


## [role, director metres] for each umpire with the ball at its current spot. VignetteExtras
## works in the vignette ground (x across, y along, half-lengths A x L); the director's x runs
## along the ground and y across it, so the axes swap and scale to MatchMotion's half-lengths.
func _umpire_spots() -> Array:
	var bp: Vector2 = director.ball["pos"]
	var sx := HALF_LEN / VignetteGround.L
	var sy := HALF_WID / VignetteGround.A
	var out := []
	for u in VignetteExtras.umpires(Vector2(bp.y / sy, bp.x / sx)):
		var v: Vector2 = u["oval"]
		out.append([u["ump"], Vector2(v.y * sx, v.x * sy)])
	return out


## Each umpire runs toward his spot for where the ball is now (at most UMP_SPEED), jogging
## while he moves and facing the ball when he stands. Goal umpires stay on their lines.
const UMP_SPEED := 7.0
const UMP_RUN_FROM := 1.4


func _move_umpires(dt: float) -> void:
	if umpires.is_empty():
		return
	var spots := _umpire_spots()
	var bp: Vector2 = director.ball["pos"]
	for u in umpires:
		var node: Node3D = u["node"]
		var ap: AnimationPlayer = u["anim"]
		var at := Vector2(node.position.x, node.position.z)
		var want: Vector2 = spots[int(u["k"])][1]
		var step := want - at
		var vel := Vector2.ZERO
		if dt > 0.0 and step.length() > 0.05:
			var move := step.limit_length(UMP_SPEED * dt)
			at += move
			vel = move / dt
		node.position = Vector3(at.x, 0.0, at.y)
		var speed := vel.length()
		var clip := "idle"
		var rate := 1.0
		if speed > UMP_RUN_FROM:
			node.rotation.y = atan2(vel.x, vel.y)
			clip = "jog"
			rate = clampf(speed / 6.0, 0.45, 2.3)
		else:
			var to := bp - at
			if to.length() > 0.5:
				node.rotation.y = atan2(to.x, to.y)
		if ap.current_animation != clip:
			ap.play(clip)
			ap.seek(fmod(float(u["k"]) * 0.137, ap.current_animation_length), false)
		ap.advance(maxf(dt * rate, 1e-4))


func _mat(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = 0.85
	return m
