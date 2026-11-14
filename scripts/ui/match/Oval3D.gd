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
		_number(p, int(t.get("num", -1)))
		players.append(p)
	anim = Oval3DAnim.new(director, players)
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
	add_child(camera)
	sync(0.0)


## Copy the director's state onto the scene. The animations advance here, by dt, so the
## carrier's hands are where this frame puts them when the ball goes between them.
func sync(dt: float) -> void:
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
		var pos: Vector2 = at[i]
		var vel: Vector2 = t["vel"]
		var node: Node3D = p["node"]
		node.position = Vector3(pos.x, 0.0, pos.y)
		anim.step(i, p, holder, pos, vel, dt)
	var bp: Vector2 = director.ball["pos"]
	var h := float(director.ball.get("h", 0.0))
	if holder >= 0 and holder < players.size():
		_hold_ball(players[holder])
	else:
		ball.position = Vector3(bp.x, BALL_R if resting else maxf(BALL_R, h), bp.y)
		ball.rotation = Vector3.ZERO
	var target := Vector3(clampf(bp.x, -60.0, 60.0), 0.0, clampf(bp.y, -25.0, 25.0))
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


## The broadcast camera: up in the stand on the wing, following the ball along the ground.
func aim_wing(height: float, back: float) -> void:
	camera.position = Vector3(_look.x * 0.9, height, _look.z * 0.4 + back)
	camera.look_at(Vector3(_look.x, 0.0, _look.z), Vector3.UP)


## Behind the play, high: the length of the ground runs up a portrait screen.
func aim_end(height: float, back: float) -> void:
	camera.position = Vector3(_look.x - back, height, _look.z * 0.6)
	camera.look_at(Vector3(_look.x + 12.0, 0.0, _look.z), Vector3.UP)


## Close on the ball, from the wing side and a little behind: the body check.
func aim_close() -> void:
	var bp: Vector2 = director.ball["pos"]
	camera.position = Vector3(bp.x - 9.0, 4.5, bp.y + 11.0)
	camera.look_at(Vector3(bp.x, 1.0, bp.y), Vector3.UP)


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
		if (mi as MeshInstance3D).material_override is ShaderMaterial:
			(mi as GeometryInstance3D).set_instance_shader_parameter("number", clampi(n, -1, 99))


func _player(scene: PackedScene, kit: ShaderMaterial, cols: Array) -> Dictionary:
	var node: Node3D = scene.instantiate()
	add_child(node)
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).material_override = kit
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


func _mat(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = 0.85
	return m
