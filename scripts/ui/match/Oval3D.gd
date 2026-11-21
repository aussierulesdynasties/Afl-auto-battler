class_name Oval3D
extends Node3D
## PROTOTYPE (director, 2026-11-14: "True 3D oval"): the live oval as a real 3D scene, the
## players running where MatchDirector puts them. Looks only: it reads the director's tokens
## and ball every frame and never writes to them, so the match is the same match.
##
## Ground metres map straight to world metres: director (x, y) -> world (x, 0, y), +x towards
## the goal side 0 attacks. The players are the vignette footballer (MPFB body, the pipeline's
## own body), exported as assets/oval3d/player_average.glb, recoloured per club.

const PLAYER_GLB := "res://assets/oval3d/player_average.glb"
## The run, the stand and the run with the ball, from motion capture on the same rig, replacing
## the GLB's hand-posed jog, idle and carry: a neutral run loop (frame 75 = frame 0, the travel
## taken out), a stand-idle loop, and the run's arms swapped for a ball carrier's two-handed hold.
const LOOPS_GLB := "res://assets/oval3d/player_loops.glb"
## The player and loop files in use (PLAYER_GLB, LOOPS_GLB); a capture may point them at a
## candidate body (row 202 2d: the MetaHuman footballer, which carries its own loops).
static var player_glb := PLAYER_GLB
static var loops_glb := LOOPS_GLB
## m/s the jog loop covers at rate 1 (14.6 m in its 2.5 s): the rate scales from this.
const LOOP_SPEED := 5.83
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
## The eyes' material name in the GLB (a MetaHuman body's eyeballs, coloured by their vertex
## colour): drawn as modelled, never in the kit.
const EYE_MATERIAL := "ARD_eye"
const HALF_LEN := MatchMotion.HALF_LEN
const HALF_WID := MatchMotion.HALF_WID
const GOAL_X := MatchMotion.GOAL_X
const GOAL_GAP := 6.4
const GOAL_H := 12.0
const BEHIND_H := 6.5
const FENCE := 6.0
const STAND_DEPTH := 34.0
const STAND_RISE := 24.0
const LOOK_X := 78.0           # m: the camera follows the ball this far towards each goal
const LOOK_Z := 55.0           # ...and this far out to each wing (the man on the ball stays in view)
const BODY_GAP := 0.6         # m between two players' centres, drawn
const UMP_BODY_GAP := 0.7     # m from an umpire's hips to a player's centre, drawn
## The digits the vignettes print numbers with (R fill, G outline), shared so both read alike.
const DIGITS := preload("res://assets/vignette/figures_digits.png")
## A Sherrin is about 0.29 m end to end and 0.18 m across.
const BALL_R := 0.09
const BALL_LONG := 1.6
const DROP_T := 0.35          # s: a ball out of a man's hands takes this to reach where it lies
const DROP_SNAP := 0.25       # m: a smaller gap than this is drawn straight away
const ROLL_TURN := 8.0         # rad/s: a rolling ball's long axis turns across its way at most this fast
const ROLL_SETTLE := 0.2       # s: from his hands or a landing it eases into its roll over this
const ROLL_JUMP := 3.0         # m: a bigger move in one frame is the ball put somewhere, not rolled

var director: MatchDirector
var players: Array = []        # [{node, anim, ring}] in director.tokens order
var ball: MeshInstance3D
var camera: Camera3D
var film: MeshInstance3D  # the broadcast film look (_film)
var anim: Oval3DAnim          # the animation session's controller (row 198)
var umpires: Array = []        # [{node, anim, ring, role, k}]: the vignettes' umpire set
var crowd: Oval3DCrowd
## The ground's big screens and fence signs (Oval3DScreens): live score, GOAL card, replay.
var screens: Oval3DScreens
## The ground the match is at (VignetteGround.ground_of), set before build(): its model when it
## has one (GroundModels), else the stand and crowd.
var ground := ""
var _turf_mat: ShaderMaterial  # the turf's paint (oval3d_ground.gdshader)
var _crowd_t := 0.0           # s of match the crowd has run (its idle and cheer clock)
var _goal_on := false          # the director was showing a goal last frame
var _look := Vector3.ZERO
var _in_hands := false         # the ball was drawn in a man's hands last frame
var _drop_from := Vector3.ZERO # where it left his hands
var _drop_t := -1.0            # s into its fall to the turf; -1 when not falling
var _roll_yaw := 0.0           # the rolling ball's long axis, as a turn about UP
var _roll := 0.0               # how far it has turned over about that axis
var _on_turf := false          # it was rolling (or lying) last frame
var _settle_t := 0.0           # s since it came out of his hands or the air


func build(p_director: MatchDirector, home: String, away: String) -> void:
	director = p_director
	_environment()
	_ground()
	_posts()
	var slug := GroundModels.slug_for(ground) if ground != "" else ""
	if slug != "":
		_ground_model(slug, "", home, away)
	else:
		_stands(home, away)
	screens = Oval3DScreens.new()
	add_child(screens)
	screens.build(self, get_node_or_null("Ground"), Vector2(HALF_LEN + FENCE, HALF_WID + FENCE), home, away)
	var scene: PackedScene = load(player_glb)
	# Each club in its home guernsey, as the vignettes dress them (StoppageVignette._dress).
	var kits := [_kit(GameDB.club_guernsey(home)), _kit(GameDB.club_guernsey(away))]
	for t in director.tokens:
		var side := int(t.get("side", 0))
		var p := _player(scene, kits[side], GameDB.club_colours(home if side == 0 else away), home if side == 0 else away)
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
	_film()
	sync(0.0)


## The broadcast film look over the whole picture (director's pick, rule 2.112): a quad
## glued to the camera that redraws what the camera drew (oval3d_film.gdshader).
func _film() -> void:
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://scripts/ui/match/oval3d_film.gdshader")
	# Drawn last but the club rings (RENDER_PRIORITY_MAX), which keep their exact colour (rule 2.81).
	mat.render_priority = Material.RENDER_PRIORITY_MAX - 1
	var qm := QuadMesh.new()
	qm.size = Vector2(2, 2)
	film = MeshInstance3D.new()
	film.mesh = qm
	film.material_override = mat
	# The shader places it over the whole screen, wherever the camera looks.
	film.extra_cull_margin = 16384.0
	film.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	film.position = Vector3(0, 0, -1)
	camera.add_child(film)
	turf.film = mat


## Copy the director's state onto the scene. The animations advance here, by dt, so the
## carrier's hands are where this frame puts them when the ball goes between them.
## A player touches the ball (or the man) this frame: kick, handball, ruck_tap, mark,
## gather, handball_receive, tackle, smother, spoil, bounce (i -1: the field umpire),
## goal_celebrate. `at` is where the ball goes, metres on the ground; `other` the man
## tackled or smothered. Called at the moment of contact (3d view 2, 2026-11-15).
func anim_event(i: int, kind: StringName, at: Vector2, other := -1) -> void:
	anim.event(i, kind, at, other)


func sync(dt: float) -> void:
	# The animation clock first: a tackle about to land starts its two-man clip here.
	anim.frame(dt)
	_sync_crowd(dt)
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
	# The umpires first: the players are drawn clear of where they are this frame (_spaced).
	_move_umpires(dt)
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
	var bp: Vector2 = director.ball["pos"]
	var h := float(director.ball.get("h", 0.0))
	if _ump_ball:
		# An umpire has it: never a player standing within a metre of it.
		holder = -1
	if _umpire_ball(dt):
		_in_hands = true
		_on_turf = false
		_drop_t = -1.0
	elif holder >= 0 and holder < players.size():
		_hold_ball(players[holder])
		_in_hands = true
		_on_turf = false
		_drop_t = -1.0
	else:
		var to := Vector3(bp.x, BALL_R if resting else maxf(BALL_R, h), bp.y)
		if mode == "flight":
			_drop_t = -1.0
		elif _in_hands and dt > 0.0 and ball.position.distance_to(to) > DROP_SNAP:
			# Out of his hands onto the turf (a spill from a tackle, a fumble, a man walking off a
			# dead ball): it falls from where his hands had it, never jumps there in one frame.
			_drop_from = ball.position
			_drop_t = 0.0
		_in_hands = false
		if _drop_t >= 0.0 and dt > 0.0:
			_drop_t += dt
			var u := clampf(_drop_t / DROP_T, 0.0, 1.0)
			to = Vector3(lerpf(_drop_from.x, to.x, u), lerpf(_drop_from.y, to.y, u * u), lerpf(_drop_from.z, to.z, u))
			if u >= 1.0:
				_drop_t = -1.0
		var moved := Vector2(to.x - ball.position.x, to.z - ball.position.z)
		ball.position = to
		if mode == "flight":
			ball.rotation = Vector3.ZERO
			_roll_yaw = 0.0
			_roll = 0.0
			_on_turf = false
		else:
			_roll_ball(moved, dt)
	_umpire_let_go(dt)
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
	# An umpire is a body too (his hips where his clip has them: the bounce runs him two metres
	# in): no player is drawn through him; the player gives way, the umpire keeps his mark.
	for u in umpires:
		var skel: Skeleton3D = u["skel"]
		var hips := to_local(skel.global_transform * skel.get_bone_global_pose(_pelvis(u)).origin)
		var c := Vector2(hips.x, hips.z)
		for i in range(at.size()):
			var gap: Vector2 = at[i] - c
			var dist := gap.length()
			if dist < UMP_BODY_GAP:
				at[i] = c + (gap / dist if dist > 0.001 else Vector2.RIGHT.rotated(float(i))) * UMP_BODY_GAP
	return at


## His pelvis bone (cached on the umpire's entry).
func _pelvis(u: Dictionary) -> int:
	if not u.has("pelvis"):
		u["pelvis"] = maxi((u["skel"] as Skeleton3D).find_bone("pelvis"), 0)
	return int(u["pelvis"])


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
## A ball off the hands and out of the air rolls: its long axis turns across the way it goes and
## it turns over on its round side, distance / BALL_R, so it never slides along the turf (and its
## point never digs in). From his hands or a landing it eases into that roll over ROLL_SETTLE.
func _roll_ball(moved: Vector2, dt: float) -> void:
	var settle := 1.0
	if not _on_turf:
		_on_turf = true
		_settle_t = 0.0
	if _settle_t < ROLL_SETTLE and dt > 0.0:
		_settle_t += dt
		settle = clampf(_settle_t / ROLL_SETTLE, 0.0, 1.0)
	var d := moved.length()
	if d > 0.002 and d < ROLL_JUMP:
		var want := atan2(moved.x, moved.y) + PI * 0.5
		# The ball is the same both ways along its axis: turn the shorter way.
		var dy := wrapf(want - _roll_yaw, -PI * 0.5, PI * 0.5)
		_roll_yaw += clampf(dy, -ROLL_TURN * dt, ROLL_TURN * dt)
		var axis := Vector3(sin(_roll_yaw), 0.0, cos(_roll_yaw))
		var spin := Vector3.UP.cross(Vector3(moved.x, 0.0, moved.y) / d)
		_roll = fmod(_roll + signf(spin.dot(axis)) * absf(spin.dot(axis)) * d / BALL_R, TAU)
	var target := Quaternion(Basis(Vector3.UP, _roll_yaw) * Basis(Vector3.BACK, _roll))
	ball.quaternion = target if settle >= 1.0 else ball.quaternion.slerp(target, settle)


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


## The crowd's clock, and a goal the moment the director shows one: the scoring side's
## supporters rise.
func _sync_crowd(dt: float) -> void:
	_crowd_t += dt
	if crowd == null:
		return
	crowd.set_now(_crowd_t)
	var goal := not director.flash.is_empty() and bool(director.flash.get("goal", false))
	if goal and not _goal_on and director.emitted > 0:
		var ev: Dictionary = director.events[director.emitted - 1]
		crowd.cheer(int(ev.get("side", 0)), _crowd_t)
	_goal_on = goal


## The sides change ends: +1 when the home side kicks to the far end of the camera's ground
## (periods 1 and 3), -1 the other way. The ground and everyone on it turn half a turn; the
## camera stays put, so the home side then attacks the other way up the screen.
func set_ends(sign: float) -> void:
	rotation.y = 0.0 if sign > 0.0 else PI
	umpires_after_cut()


## The picture has cut away from the live play (a goal's replay, the ends changing at a
## break): on the next live frame the umpires are on their spots, the field umpire on his mark
## for the coming stoppage, instead of a run the picture never showed.
func umpires_after_cut() -> void:
	_ump_cut = true


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
## The turf and light for the day's weather and time of day: turf.apply(weather, slot).
var turf: Oval3DTurf
var _env: Environment
var _sun: DirectionalLight3D


func _environment() -> void:
	var env := Environment.new()
	_env = env
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
	_sun = sun


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
	_turf_mat = sm
	turf = Oval3DTurf.new(self, sm, _env, _sun, pm.size * 0.5)
	add_child(turf)
	turf.apply("", VignetteKickoff.DAY)


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


## The stand all the way round and its crowd (Oval3DCrowd: 3D people near the camera, cards
## beyond, each in his club's colours), then the fence at its foot.
func _stands(home: String, away: String) -> void:
	crowd = Oval3DCrowd.new()
	crowd.name = "Crowd"
	add_child(crowd)
	crowd.build(HALF_LEN + FENCE, HALF_WID + FENCE, STAND_DEPTH, STAND_RISE,
			GameDB.club_colours(home), GameDB.club_colours(away))
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


## A real ground's model in place of the stand, its crowd and the fence (GroundModels: the
## model and its seats, laid so its fence meets the match's). With home and away given, the
## crowd sits on the model's seats (Oval3DCrowd.build_on_seats; the director chose "Seat the
## crowd in the MCG", 2026-11-20); without them, or at a ground with no seat files, the seats
## stay empty. base is the folder holding the model and its seat files; "" is the game's own
## copy. The ground inspector (tools/inspect) passes a folder on disk to show a copy that is
## not in the game yet.
func _ground_model(slug: String, base := "", home := "", away := "") -> void:
	var root := GroundModels.instantiate(slug, base)
	add_child(root)
	turf.set_ground(slug)
	turf.light_stands(root)
	_turf_mat.set_shader_parameter("fence_clip", GroundModels.MATCH_FENCE)
	_apron_skirt()
	if home == "":
		return
	var seats := GroundModels.seat_transforms(slug, base)
	if seats.is_empty():
		return
	crowd = Oval3DCrowd.new()
	crowd.name = "Crowd"
	root.add_child(crowd)
	crowd.build_on_seats(seats, GroundModels.seat_points(slug, base),
			GameDB.club_colours(home), GameDB.club_colours(away))


## How far past the match's fence the apron skirt runs, and how far under the turf it lies (under
## the model's own ground, GroundModels.UNDER_TURF, so wherever the model has ground, that shows).
const SKIRT_OUT := 8.0
const SKIRT_DROP := 0.3


## Where a model's own fence runs outside the match's (a metre or a few on part of the lap) it has
## no ground drawn between the turf's edge and its wall, and the sky under the world showed through
## as a white strip at the foot of the fence. A ring of the turf's apron, from just inside the
## match's fence to SKIRT_OUT past it, lies under the model's ground and fills that gap with grass.
func _apron_skirt() -> void:
	var f := GroundModels.MATCH_FENCE
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_normal(Vector3.UP)
	var n := 180
	for i in n:
		var a0 := TAU * i / n
		var a1 := TAU * (i + 1) / n
		var p := [Vector3(cos(a0) * f.x * 0.97, 0.0, sin(a0) * f.y * 0.97),
				Vector3(cos(a1) * f.x * 0.97, 0.0, sin(a1) * f.y * 0.97),
				Vector3(cos(a1) * (f.x + SKIRT_OUT), 0.0, sin(a1) * (f.y + SKIRT_OUT)),
				Vector3(cos(a0) * (f.x + SKIRT_OUT), 0.0, sin(a0) * (f.y + SKIRT_OUT))]
		for k in [0, 1, 2, 0, 2, 3]:
			st.add_vertex(p[k])
	var mi := MeshInstance3D.new()
	mi.name = "ApronSkirt"
	mi.mesh = st.commit()
	mi.position.y = -SKIRT_DROP
	var sm := _turf_mat.duplicate() as ShaderMaterial
	sm.set_shader_parameter("fence_clip", Vector2.ZERO)
	mi.material_override = sm
	add_child(mi)
	turf.follow(sm)


## A .glb as a node (GroundModels.load_glb): the imported copy for a file in the game, read
## straight off disk otherwise. null if it cannot be read.
static func load_glb(path: String) -> Node3D:
	return GroundModels.load_glb(path)


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
	for part in ["body", "head"]:
		for map in [["col", "Basecolor"], ["nrm", "Normal"], ["srmf", "SRMF"]]:
			m.set_shader_parameter("skin_%s_%s" % [part, map[0]],
					load("res://assets/oval3d/skin/%s_%s.png" % [part.capitalize(), map[1]]))
	m.set_shader_parameter("kit_atlas", GameDB.kit_atlas())
	m.set_shader_parameter("kit_grid", GameDB.kit_grid())
	# The club's current home guernsey, drawn from its photo (data/kits_today.csv), with its
	# collar and armhole bindings on the guernsey's own edges.
	var today: Dictionary = kit.get("today", {})
	if not today.is_empty() and GameDB.kits_today_atlas() != null:
		m.set_shader_parameter("kit_design", [float(100 + int(today["cell"]))])
		m.set_shader_parameter("kit_atlas", GameDB.kits_today_atlas())
		m.set_shader_parameter("kit_grid", GameDB.kits_today_grid())
		m.set_shader_parameter("kit_collar", today["collar"])
		m.set_shader_parameter("kit_arms", today["armholes"])
		m.set_shader_parameter("kit_trim", Vector2(float(today["collar_cm"]), float(today["armholes_cm"])) / 100.0)
		# The number in the club's own colour (and edge, Richmond's black), from match photos.
		m.set_shader_parameter("kit_number", today.get("number", Color(0, 0, 0, 0)))
		m.set_shader_parameter("kit_number_edge", today.get("number_edge", Color(0, 0, 0, 0)))
		# The club's own shorts with it (the guernsey's colour where they match).
		if (today.get("shorts", Color(0, 0, 0, 0)) as Color).a > 0.0:
			m.set_shader_parameter("shorts", today["shorts"])
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
	# His own Tripo head, where the director made one (rule 2.99): the MetaHuman head comes off.
	_head(p, pid)
	# His real height and weight, and a face of his own (Oval3DBuild; row 202, 2d).
	Oval3DBuild.apply(p, player_glb, who if who is Dictionary else {}, pid)


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
	# The builds' and faces' morph targets come across, their scalp drawn in by the same lift.
	out.blend_shape_mode = am.blend_shape_mode
	for b in range(am.get_blend_shape_count()):
		out.add_blend_shape(am.get_blend_shape_name(b))
	for s in range(surfs.size()):
		var a: Array = surfs[s]
		var ns: PackedVector3Array = a[Mesh.ARRAY_NORMAL]
		var k: Array = keys[s]
		for i in range(ns.size()):
			var n: Vector3 = near.get(k[i], Vector3.ZERO)
			if n.length_squared() > 0.0:
				ns[i] = n.normalized()
		a[Mesh.ARRAY_NORMAL] = ns
		var shapes := am.surface_get_blend_shape_arrays(s)
		for sh in shapes:
			var bv: PackedVector3Array = (sh as Array)[Mesh.ARRAY_VERTEX]
			for i in range(bv.size()):
				if lift.has(k[i]):
					bv[i] -= lift[k[i]] * SCALP_LIFT
			(sh as Array)[Mesh.ARRAY_VERTEX] = bv
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a, shapes, {}, _custom_format(am, s))
		out.surface_set_material(s, am.surface_get_material(s))
		out.surface_set_name(s, am.surface_get_name(s))
	_skulls[m] = out
	return out


## The guernsey's and shorts' surfaces in the GLB (ard_body.REGIONS).
const GUERNSEY_SURFACE := "ARD_guernsey"
const SHORTS_SURFACE := "ARD_shorts"
const SKIN_SURFACE := "ARD_skin"
## How far onto the skin, round the neck and armholes, the guernsey may be painted (metres).
const SKIN_REACH := 0.03
## How near the guernsey's nearest corner that skin must be (metres).
const SKIN_GAP := 0.02
## And how far off the guernsey's surface, along its normal (metres).
const SKIN_OFF := 0.004
## CUSTOM1 and CUSTOM2 as four floats each (oval3d_player.gdshader: kit_edge, kit_fore, kit_g).
## CUSTOM0 stays the mesh's own: the MetaHuman skin coordinates.
const EDGE_FORMAT := (Mesh.ARRAY_CUSTOM_RGBA_FLOAT << Mesh.ARRAY_FORMAT_CUSTOM1_SHIFT) 		| (Mesh.ARRAY_CUSTOM_RGBA_FLOAT << Mesh.ARRAY_FORMAT_CUSTOM2_SHIFT)
const EDGE_MASK := (Mesh.ARRAY_FORMAT_CUSTOM_MASK << Mesh.ARRAY_FORMAT_CUSTOM1_SHIFT) 		| (Mesh.ARRAY_FORMAT_CUSTOM_MASK << Mesh.ARRAY_FORMAT_CUSTOM2_SHIFT)
const FAR := 1.0
## CUSTOM1.w on the skin round the neck and armholes (1 the guernsey, 0.5 the shorts).
const SKIN := 0.3
static var _edged := {}


## The guernsey's depth-middle (halfway between its front and back) every centimetre up the body,
## from its corners within 2 cm of that height: the line between the front and back pictures
## (the guernsey's build splits its picture coordinates on the same line). [0] is the lowest height.
static func _depth_middle(gv: PackedVector3Array) -> PackedFloat32Array:
	var lo := INF
	var hi := -INF
	for q in gv:
		lo = minf(lo, q.y)
		hi = maxf(hi, q.y)
	var n := int(ceil((hi - lo) / 0.01)) + 1
	var zmin := PackedFloat32Array()
	var zmax := PackedFloat32Array()
	zmin.resize(n)
	zmax.resize(n)
	zmin.fill(INF)
	zmax.fill(-INF)
	for q in gv:
		var r := int(round((q.y - lo) / 0.01))
		for k in range(maxi(0, r - 2), mini(n, r + 3)):
			zmin[k] = minf(zmin[k], q.z)
			zmax[k] = maxf(zmax[k], q.z)
	var out := PackedFloat32Array([lo])
	for k in range(n):
		out.append((zmin[k] + zmax[k]) * 0.5 if zmax[k] >= zmin[k] else 0.0)
	return out


static func _middle_at(mid: PackedFloat32Array, y: float) -> float:
	var f := clampf((y - mid[0]) / 0.01, 0.0, float(mid.size() - 2))
	var k := mini(int(f), mid.size() - 3)
	return lerpf(mid[k + 1], mid[k + 2], f - float(k))


## The mesh with distances in CUSTOM1 on the guernsey, the shorts and the skin round the neck
## and armholes, so the shader draws the guernsey's edges as clean curves and the bindings a true
## width inside them. The guernsey was cut from the body along whole triangles, so its open edges
## are staircases (notches up to 0.8 cm) and the skin fills the notches. The armholes are re-cut in
## the model itself along one smooth line each (tools/oval3d/recut_armholes.py), so the skin round
## them stays skin. The neck edge is drawn along its loop smoothed (Taubin, which keeps its size),
## set just outside the farthest notch, and the skin inside that line wears the guernsey. The hem is drawn as one level
## line round the body, as a guernsey's hem is. The lowest loop is the hem, the
## one nearest the middle the neck, the other two the armholes.
## x: metres inside the neck's drawn edge (negative outside it); y: the same for the nearer
## armhole; z: metres above the hem line, which runs level all round at the height of the mesh
## hem's highest point (the mesh's hem dips in a V in front and rises in an M behind); w: 1 on the
## guernsey, 0.5 on the shorts, SKIN on the skin (outside SKIN_REACH of the neck and armholes,
## x and y are -SKIN_REACH: a small number, so the edge's smoothing stays a pixel wide). CUSTOM2: x metres in front of the body's middle, so a triangle over a seam knows
## which side it is on; yzw on that skin, the nearest guernsey corner's pattern coordinates. Once
## per mesh; every player shares the copy.
static func _kit_edges(m: Mesh) -> Mesh:
	if _edged.has(m):
		return _edged[m]
	var am := m as ArrayMesh
	var gs := -1
	var ss := -1
	var ks := -1
	if am != null:
		for s in range(am.get_surface_count()):
			var mat := am.surface_get_material(s)
			var nm := mat.resource_name if mat != null else ""
			if nm == GUERNSEY_SURFACE:
				gs = s
			elif nm == SHORTS_SURFACE:
				ss = s
			elif nm == SKIN_SURFACE:
				ks = s
	if gs < 0:
		_edged[m] = m
		return m
	var ga := am.surface_get_arrays(gs)
	var gv: PackedVector3Array = ga[Mesh.ARRAY_VERTEX]
	var gi: PackedInt32Array = ga[Mesh.ARRAY_INDEX]
	# Weld the corners (the seams split them); an edge with one face is an open edge.
	var weld := {}
	var pts := PackedVector3Array()
	var wid := PackedInt32Array()
	wid.resize(gv.size())
	for i in range(gv.size()):
		var k := Vector3i((gv[i] * 1e5).round())
		if not weld.has(k):
			weld[k] = pts.size()
			pts.append(gv[i])
		wid[i] = weld[k]
	var faces := {}
	for f in range(0, gi.size(), 3):
		for c in range(3):
			var a := wid[gi[f + c]]
			var b := wid[gi[f + (c + 1) % 3]]
			var e := Vector2i(mini(a, b), maxi(a, b))
			faces[e] = int(faces.get(e, 0)) + 1
	var nbr := {}
	for e: Vector2i in faces:
		if faces[e] == 1:
			if not nbr.has(e.x):
				nbr[e.x] = []
			if not nbr.has(e.y):
				nbr[e.y] = []
			nbr[e.x].append(e.y)
			nbr[e.y].append(e.x)
	# Each open edge in order round its loop.
	var loops := []
	var seen := {}
	for v0 in nbr:
		if seen.has(v0):
			continue
		var ids := PackedInt32Array([v0])
		seen[v0] = true
		var cur: int = v0
		while true:
			var next := -1
			for u in nbr[cur]:
				if not seen.has(u):
					next = u
					break
			if next < 0:
				break
			seen[next] = true
			ids.append(next)
			cur = next
		if ids.size() >= 8:
			loops.append(_edge_loop(ids, pts))
	if loops.size() < 4:
		_edged[m] = m
		return m
	loops.sort_custom(func(a, b): return a["mid"].y < b["mid"].y)
	var hem: Dictionary = loops[0]
	var rest := loops.slice(1)
	rest.sort_custom(func(a, b): return absf(a["mid"].x) < absf(b["mid"].x))
	var neck: Dictionary = rest[0]
	var arms := rest.slice(1)
	var level := -INF
	var hem_top := -INF
	for q in hem["raw"]:
		hem_top = maxf(hem_top, q.y)
		level = maxf(level, q.y)
	var low := INF
	for l in rest:
		for q in l["raw"]:
			low = minf(low, q.y)
	# The cloth under the drawn hem is worn as shorts: its moulded folds are smoothed away.
	var gbs := am.surface_get_blend_shape_arrays(gs)
	_smooth_hem(ga, gbs, gi, wid, pts.size(), faces, level)
	# The guernsey's pattern coordinates (as the shader reads them) near its neck and armholes,
	# lent to the skin there so the skin can wear the guernsey up to the drawn edge.
	var guv: PackedVector2Array = ga[Mesh.ARRAY_TEX_UV]
	var guv2: PackedVector2Array = ga[Mesh.ARRAY_TEX_UV2]
	var gn: PackedVector3Array = ga[Mesh.ARRAY_NORMAL]
	var lend := []
	for i in range(gv.size()):
		if gv[i].y > low - 0.06 and _inside(gv[i], neck).y < SKIN_REACH + 0.02:
			lend.append(i)
	# The guernsey's own cut edge round the neck and armholes (not the hem): the shader fades the cloth
	# to the skin over the last pixel before it, measured on the mesh itself (CUSTOM2.y: 0 on it, 1 off it).
	var cut := {}
	for v in nbr:
		if pts[v].y > low - 0.01:
			cut[v] = true
	var mid := _depth_middle(gv)
	var measure := func(vs: PackedVector3Array, kind: float) -> Array:
		var out := PackedFloat32Array()
		out.resize(vs.size() * 4)
		var more := PackedFloat32Array()
		more.resize(vs.size() * 4)
		for i in range(vs.size()):
			var p := vs[i]
			var e := Vector4(FAR, FAR, FAR, kind)
			more[i * 4] = p.z - _middle_at(mid, p.y)
			if kind == 1.0:
				more[i * 4 + 1] = 0.0 if cut.has(wid[i]) else 1.0
			if kind != 0.5 and p.y > low - 0.06:
				var n := _inside(p, neck)
				var r := _nearest_arm(p, arms)
				if kind == 1.0:
					# The bindings are a few centimetres at most: only the top of the guernsey is measured.
					e.x = n.x + float(neck["out"])
					e.y = r.x
				elif n.y < SKIN_REACH:
					# Round the armholes the model's own edge is the line (re-cut smooth in the
					# model): skin there stays skin, and only the neck's line counts.
					e.x = n.x + float(neck["out"])
					e.y = FAR
					var bi := -1
					var bd := INF
					for j in lend:
						var d := p.distance_squared_to(gv[j])
						if d < bd:
							bd = d
							bi = j
					if bi >= 0:
						more[i * 4 + 1] = guv[bi].x
						more[i * 4 + 2] = 1.0 - guv[bi].y
						more[i * 4 + 3] = 1.0 - guv2[bi].y
					# Skin in a notch lies on or just under the guernsey's surface; skin across a gap from
					# it, or standing out from it (the inner arm, which hangs beside the armpit), never
					# wears it.
					if bd > SKIN_GAP * SKIN_GAP or (bi >= 0 and (p - gv[bi]).dot(gn[bi]) > SKIN_OFF):
						e = Vector4(-SKIN_REACH, -SKIN_REACH, FAR, SKIN)
				else:
					e = Vector4(-SKIN_REACH, -SKIN_REACH, FAR, SKIN)
			elif kind == SKIN:
				e = Vector4(-SKIN_REACH, -SKIN_REACH, FAR, SKIN)
			if kind != SKIN and p.y < hem_top + 0.06:
				e.z = p.y - level
			out[i * 4] = e.x
			out[i * 4 + 1] = e.y
			out[i * 4 + 2] = e.z
			out[i * 4 + 3] = e.w
		return [out, more]
	var out := ArrayMesh.new()
	out.blend_shape_mode = am.blend_shape_mode
	for b in range(am.get_blend_shape_count()):
		out.add_blend_shape(am.get_blend_shape_name(b))
	for s in range(am.get_surface_count()):
		var a := ga if s == gs else am.surface_get_arrays(s)
		var bsa := gbs if s == gs else am.surface_get_blend_shape_arrays(s)
		var flags := _custom_format(am, s)
		if s == gs:
			a[Mesh.ARRAY_VERTEX] = gv
		if s == gs or s == ss or s == ks:
			var vs: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
			var both: Array = measure.call(vs, 1.0 if s == gs else (0.5 if s == ss else SKIN))
			a[Mesh.ARRAY_CUSTOM1] = both[0]
			a[Mesh.ARRAY_CUSTOM2] = both[1]
			flags = (flags & ~EDGE_MASK) | EDGE_FORMAT
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a, bsa, {}, flags)
		out.surface_set_material(s, am.surface_get_material(s))
		out.surface_set_name(s, am.surface_get_name(s))
	_edged[m] = out
	return out


## The guernsey's cloth below the drawn hem line (level), which the shader paints as shorts: the
## mesh's hem dips up to 6 cm under that line in front and 3.6 cm behind, and the folds moulded into
## that strip showed as lumps under the hem (director 2026-11-17, "lumpy seams between shorts and
## shirt"; he chose "Smooth the 6 cm strip"). Each corner of the strip is eased towards its
## neighbours (Taubin, which keeps the strip's size, so it does not sink into the body), in the rest
## pose and in every build morph alike; the cloth's open edge, where the shorts begin, stays put so
## no gap opens. The strip's normals are then taken from its new faces.
static func _smooth_hem(ga: Array, bsa: Array, gi: PackedInt32Array, wid: PackedInt32Array,
		count: int, faces: Dictionary, level: float) -> void:
	var gv: PackedVector3Array = ga[Mesh.ARRAY_VERTEX]
	var nbr := []
	nbr.resize(count)
	for i in range(count):
		nbr[i] = PackedInt32Array()
	for e: Vector2i in faces:
		nbr[e.x].append(e.y)
		nbr[e.y].append(e.x)
	var edge := {}
	for e: Vector2i in faces:
		if faces[e] == 1:
			edge[e.x] = true
			edge[e.y] = true
	var one := PackedInt32Array()  # one vertex index per welded corner
	one.resize(count)
	for i in range(gv.size()):
		one[wid[i]] = i
	var move := PackedInt32Array()
	for w in range(count):
		if gv[one[w]].y < level and not edge.has(w):
			move.append(w)
	if move.is_empty():
		return
	var sets := [ga]
	sets.append_array(bsa)
	for arrs: Array in sets:
		var vs: PackedVector3Array = arrs[Mesh.ARRAY_VERTEX]
		var p := PackedVector3Array()
		p.resize(count)
		for w in range(count):
			p[w] = vs[one[w]]
		for it in range(20):
			for f in [0.5, -0.53]:
				var t := p.duplicate()
				for w in move:
					var avg := Vector3.ZERO
					for u in nbr[w]:
						avg += p[u]
					t[w] = p[w] + f * (avg / float(nbr[w].size()) - p[w])
				p = t
		for i in range(vs.size()):
			vs[i] = p[wid[i]]
		arrs[Mesh.ARRAY_VERTEX] = vs
		# Normals of the moved corners from the faces round them.
		var ns: PackedVector3Array = arrs[Mesh.ARRAY_NORMAL]
		if ns == null or ns.is_empty():
			continue
		var acc := PackedVector3Array()
		acc.resize(count)
		for f in range(0, gi.size(), 3):
			var a := wid[gi[f]]
			var b := wid[gi[f + 1]]
			var c := wid[gi[f + 2]]
			var fn := (p[c] - p[a]).cross(p[b] - p[a])
			acc[a] += fn
			acc[b] += fn
			acc[c] += fn
		var moved := {}
		for w in move:
			moved[w] = true
		for i in range(vs.size()):
			if moved.has(wid[i]) and acc[wid[i]].length_squared() > 0.0:
				var n := acc[wid[i]].normalized()
				ns[i] = n if n.dot(ns[i]) >= 0.0 else -n
		arrs[Mesh.ARRAY_NORMAL] = ns


## One open edge of the guernsey (ids: welded corners in order round it): its raw points, the
## loop smoothed, each smoothed point's direction into the cloth, "deep", how far the deepest
## notch reaches inside the smoothed loop, and "out", how far the farthest one reaches outside.
static func _edge_loop(ids: PackedInt32Array, pts: PackedVector3Array) -> Dictionary:
	var n := ids.size()
	var raw := PackedVector3Array()
	var mid := Vector3.ZERO
	for v in ids:
		raw.append(pts[v])
		mid += pts[v]
	var sm := raw.duplicate()
	for it in range(10):
		for f in [0.5, -0.53]:
			var t := sm.duplicate()
			for i in range(n):
				t[i] = sm[i] + f * (0.5 * (sm[(i - 1 + n) % n] + sm[(i + 1) % n]) - sm[i])
			sm = t
	# Into the cloth: from the smoothed point towards the middle of the cloth within 4 cm, square
	# to the edge.
	var into := PackedVector3Array()
	into.resize(n)
	for i in range(n):
		var along := (sm[(i + 1) % n] - sm[(i - 1 + n) % n]).normalized()
		var sum := Vector3.ZERO
		var k := 0
		for q in pts:
			if q.distance_squared_to(sm[i]) < 0.0016:
				sum += q
				k += 1
		var v := sum / maxi(k, 1) - sm[i]
		into[i] = (v - along * v.dot(along)).normalized()
	var l := {"ids": ids, "raw": raw, "sm": sm, "bow": sm, "into": into, "mid": mid / n, "deep": 0.0, "out": 0.0}
	for q in raw:
		var d := _inside(q, l).x
		l["deep"] = maxf(float(l["deep"]), d)
		l["out"] = maxf(float(l["out"]), -d)
	return l


## Point p against an edge loop (_edge_loop): x metres inside its drawn edge (negative outside),
## y the distance to its nearest smoothed point, z that point's height in front of the middle.
## x is measured from that point's place on the bow (the smoothed point itself).
static func _inside(p: Vector3, l: Dictionary) -> Vector3:
	var sm: PackedVector3Array = l["sm"]
	var bi := 0
	var bd := INF
	for i in range(sm.size()):
		var d := p.distance_squared_to(sm[i])
		if d < bd:
			bd = d
			bi = i
	var into: PackedVector3Array = l["into"]
	var bow: PackedVector3Array = l["bow"]
	return Vector3((p - bow[bi]).dot(into[bi]), sqrt(bd), sm[bi].z)


## _inside against the nearer armhole, x measured from its drawn edge (see _edge_loop's "out").
static func _nearest_arm(p: Vector3, arms: Array) -> Vector3:
	var best := Vector3(FAR, INF, 0.0)
	for l in arms:
		var a := _inside(p, l)
		if a.y < best.y:
			best = a + Vector3(float(l["out"]), 0.0, 0.0)
	return best


## The real players' Tripo heads (rule 2.99): <player id>.glb, cut and fitted onto the body's neck
## socket by tools/oval3d/heads/fit_head.py, in the body's rest space. Director 2026-11-17: "have a
## body with a neck socket and put sockets on all our heads".
const HEADS_DIR := "res://assets/oval3d/heads/"
## The socket: one of the body's own edge loops round the neck, just above the guernsey collar
## (tools/oval3d/heads/socket.py). The body keeps everything below it; each head's cut edge sits on it.
const SOCKET_JSON := "res://assets/oval3d/heads/socket.json"
## Per head: {"skin": "#rrggbb"}, his skin under the back of his neck (fit_head.py prints it): the
## body's skin, and the colour his neck's bottom 2 cm blends to.
const HEADS_JSON := "res://assets/oval3d/heads/heads.json"
const HEAD_SHADER := preload("res://scripts/ui/match/oval3d_head.gdshader")
static var _headless := {}
static var _heads_info = null
static var _socket := {}
static var _socket_heads := {}


## Put his own head on figure p if there is one; otherwise leave the MetaHuman head.
func _head(p: Dictionary, pid: String) -> void:
	if p.get("head_node") is Node:
		(p["head_node"] as Node).free()
	p.erase("head_node")
	var path := HEADS_DIR + pid + ".glb"
	var has_head := pid != "" and ResourceLoader.exists(path) and not socket().is_empty()
	var body: MeshInstance3D = null
	for mi in (p["node"] as Node3D).find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if not m.has_meta("kit"):
			continue
		if not m.has_meta("full_mesh"):
			m.set_meta("full_mesh", m.mesh)
		if body == null or m.mesh.get_surface_count() > body.mesh.get_surface_count():
			body = m
		var want: Mesh = _without_head(m.get_meta("full_mesh")) if has_head else m.get_meta("full_mesh")
		if m.mesh != want:
			var over := []
			for s in range(m.get_surface_override_material_count()):
				over.append(m.get_surface_override_material(s))
			var shapes := []
			for k in range(m.get_blend_shape_count()):
				shapes.append(m.get_blend_shape_value(k))
			m.mesh = want
			for s in range(over.size()):
				m.set_surface_override_material(s, over[s])
			for k in range(shapes.size()):
				m.set_blend_shape_value(k, shapes[k])
	if not has_head or body == null:
		return
	if p.get("hair_node") is Node:
		(p["hair_node"] as Node).free()
	p.erase("hair_node")
	if _heads_info == null:
		_heads_info = JSON.parse_string(FileAccess.get_file_as_string(HEADS_JSON)) if FileAccess.file_exists(HEADS_JSON) else {}
		if not _heads_info is Dictionary:
			_heads_info = {}
	var skin := str((_heads_info as Dictionary).get(pid, {}).get("skin", ""))
	for mi in (p["node"] as Node3D).find_children("*", "MeshInstance3D", true, false):
		if (mi as MeshInstance3D).has_meta("kit"):
			(mi as GeometryInstance3D).set_instance_shader_parameter("scalp", SCALP["bald"])
			if skin != "":
				(mi as GeometryInstance3D).set_instance_shader_parameter("skin", Color(skin))
	# His head is skinned to the body's own skeleton: his neck bends with the body's neck bones and its
	# bottom band carries the body's build morphs (Oval3DBuild sets them by name), so it stays on the
	# socket whatever his height, weight or the turn of his head.
	var head := MeshInstance3D.new()
	head.name = "Head"
	head.mesh = socket_head(path, body.get_meta("full_mesh"))
	head.transform = body.transform
	head.skin = body.skin
	body.get_parent().add_child(head)
	head.skeleton = head.get_path_to(body.get_node(body.skeleton))
	if skin != "":
		head.set_instance_shader_parameter("skin", Color(skin))
	p["head_node"] = head


## The socket ring (socket.json): "ring" its points in order round the neck, "centre" the middle of
## the neck, "ang"/"y" each point's angle round the centre (0 his front, toward his left) and height.
static func socket() -> Dictionary:
	if not _socket.is_empty() or not FileAccess.file_exists(SOCKET_JSON):
		return _socket
	var d = JSON.parse_string(FileAccess.get_file_as_string(SOCKET_JSON))
	if not d is Dictionary:
		return _socket
	var c := Vector3(d["centre"][0], d["centre"][1], d["centre"][2])
	var pts := []
	for q in d["ring"]:
		var v := Vector3(q[0], q[1], q[2])
		pts.append([_socket_angle(v, c), v])
	pts.sort_custom(func(x, y): return x[0] < y[0])
	_socket = {"centre": c, "ang": pts.map(func(x): return x[0]), "y": pts.map(func(x): return x[1].y),
			"ring": pts.map(func(x): return x[1])}
	return _socket


static func _socket_angle(v: Vector3, c: Vector3) -> float:
	return fposmod(atan2(v.x - c.x, v.z - c.z), TAU)


## Where angle t falls on the ring: [i, j, w], between its points i and j, w of the way to j.
static func _socket_at(t: float) -> Array:
	var ang: Array = _socket["ang"]
	var n := ang.size()
	for i in range(n):
		var a0: float = ang[i]
		var a1: float = ang[(i + 1) % n] + (TAU if i == n - 1 else 0.0)
		var tt := t + TAU if t < a0 else t
		if tt <= a1:
			return [i, (i + 1) % n, (tt - a0) / maxf(1e-6, a1 - a0)]
	return [0, 0, 0.0]


## The ring's height at v's angle round the neck.
static func _socket_y(v: Vector3) -> float:
	var at := _socket_at(_socket_angle(v, _socket["centre"]))
	return lerpf(_socket["y"][at[0]], _socket["y"][at[1]], at[2])


## His head (HEADS_DIR glb) as a mesh skinned to the body's skeleton, once per head and body: every
## point takes the bone weights of the body's nearest skin point (the MetaHuman's own head and neck,
## so his neck bends as theirs did), and his neck's bottom band (the vertex colour's red, fit_head.py:
## 1 on the socket, 0 from 2 cm up) carries the body's build morphs as the socket's points move.
static func socket_head(path: String, full: Mesh) -> Mesh:
	var key := path + str(full.get_instance_id())
	if _socket_heads.has(key):
		return _socket_heads[key]
	var am := full as ArrayMesh
	var root: Node = (load(path) as PackedScene).instantiate()
	var src: MeshInstance3D = root.find_children("*", "MeshInstance3D", true, false)[0]
	var xf := Transform3D.IDENTITY
	var n: Node = src
	while n != root and n is Node3D:
		xf = (n as Node3D).transform * xf
		n = n.get_parent()
	var head_arr := src.mesh.surface_get_arrays(0)
	var head_mat := src.mesh.surface_get_material(0)
	root.free()
	# The body's skin points, bucketed in 2 cm cells for the nearest-point search.
	var skin_s := 0
	for s in range(am.get_surface_count()):
		var mat := am.surface_get_material(s)
		if mat != null and mat.resource_name == "ARD_skin":
			skin_s = s
	var ba := am.surface_get_arrays(skin_s)
	var bv: PackedVector3Array = ba[Mesh.ARRAY_VERTEX]
	var bn: PackedVector3Array = ba[Mesh.ARRAY_NORMAL]
	var bb: PackedInt32Array = ba[Mesh.ARRAY_BONES]
	var bw: PackedFloat32Array = ba[Mesh.ARRAY_WEIGHTS]
	var per := bb.size() / maxi(1, bv.size())
	var cells := {}
	for i in range(bv.size()):
		var k := Vector3i((bv[i] / 0.02).floor())
		if not cells.has(k):
			cells[k] = PackedInt32Array()
		cells[k].append(i)
	var nearest := func(v: Vector3) -> int:
		var c := Vector3i((v / 0.02).floor())
		var best := -1
		var bd := INF
		for reach in range(0, 8):
			for dx in range(-reach, reach + 1):
				for dy in range(-reach, reach + 1):
					for dz in range(-reach, reach + 1):
						if maxi(absi(dx), maxi(absi(dy), absi(dz))) != reach:
							continue
						var cell = cells.get(c + Vector3i(dx, dy, dz))
						if cell == null:
							continue
						for i in cell:
							var d := bv[i].distance_squared_to(v)
							if d < bd:
								bd = d
								best = i
			if best >= 0 and sqrt(bd) < 0.02 * reach:
				break
		return best
	# Each ring point's body vertex, for the morphs' moves at the socket.
	var ring: Array = socket()["ring"]
	var ring_i := []
	for q in ring:
		ring_i.append(nearest.call(q))
	var hv: PackedVector3Array = head_arr[Mesh.ARRAY_VERTEX]
	var hn: PackedVector3Array = head_arr[Mesh.ARRAY_NORMAL]
	var hc := PackedColorArray()
	if head_arr[Mesh.ARRAY_COLOR] != null:
		hc = head_arr[Mesh.ARRAY_COLOR]
	var bones := PackedInt32Array()
	var weights := PackedFloat32Array()
	bones.resize(hv.size() * per)
	weights.resize(hv.size() * per)
	var share := PackedFloat32Array()
	share.resize(hv.size())
	var at := []
	for i in range(hv.size()):
		hv[i] = xf * hv[i]
		hn[i] = (xf.basis * hn[i]).normalized()
		var j: int = nearest.call(hv[i])
		for k in range(per):
			bones[i * per + k] = bb[j * per + k]
			weights[i * per + k] = bw[j * per + k]
		share[i] = hc[i].r if hc.size() == hv.size() else 0.0
		at.append(_socket_at(_socket_angle(hv[i], socket()["centre"])) if share[i] > 0.0 else [])
		# On the socket his neck faces the way the body's skin does there, easing back to his own going
		# up the band, so the light runs across the join without a line.
		if share[i] > 0.0:
			var aa: Array = at[i]
			var rn: Vector3 = bn[ring_i[aa[0]]].lerp(bn[ring_i[aa[1]]], aa[2]).normalized()
			hn[i] = hn[i].lerp(rn, share[i]).normalized()
		# On the socket itself he bends exactly as the body's edge does between its two ring points: their
		# bone weights blended by where he sits between them, so no gap opens along the join.
		if share[i] >= 0.999:
			var ab: Array = at[i]
			var mix := {}
			for e in [[ring_i[ab[0]], 1.0 - ab[2]], [ring_i[ab[1]], ab[2]]]:
				for k in range(per):
					var bw_k: float = bw[e[0] * per + k] * e[1]
					if bw_k > 0.0:
						var bone: int = bb[e[0] * per + k]
						mix[bone] = mix.get(bone, 0.0) + bw_k
			var order: Array = mix.keys()
			order.sort_custom(func(x, y): return mix[x] > mix[y])
			var total := 0.0
			for k in range(mini(per, order.size())):
				total += mix[order[k]]
			for k in range(per):
				bones[i * per + k] = order[k] if k < order.size() else 0
				weights[i * per + k] = mix[order[k]] / total if k < order.size() else 0.0
	head_arr[Mesh.ARRAY_VERTEX] = hv
	head_arr[Mesh.ARRAY_NORMAL] = hn
	head_arr[Mesh.ARRAY_BONES] = bones
	head_arr[Mesh.ARRAY_WEIGHTS] = weights
	head_arr[Mesh.ARRAY_TANGENT] = null
	# Each build morph: the band moves as the socket's points do, by its share.
	var shapes := []
	var out := ArrayMesh.new()
	out.blend_shape_mode = am.blend_shape_mode
	var body_shapes := am.surface_get_blend_shape_arrays(skin_s)
	for b in range(am.get_blend_shape_count()):
		out.add_blend_shape(am.get_blend_shape_name(b))
		var sv: PackedVector3Array = body_shapes[b][Mesh.ARRAY_VERTEX]
		var mv := PackedVector3Array(hv)
		for i in range(hv.size()):
			if share[i] <= 0.0:
				continue
			var a: Array = at[i]
			var d0: Vector3 = sv[ring_i[a[0]]] - bv[ring_i[a[0]]]
			var d1: Vector3 = sv[ring_i[a[1]]] - bv[ring_i[a[1]]]
			mv[i] += d0.lerp(d1, a[2]) * share[i]
		var sh := []
		sh.resize(Mesh.ARRAY_MAX)
		sh[Mesh.ARRAY_VERTEX] = mv
		sh[Mesh.ARRAY_NORMAL] = hn
		shapes.append(sh)
	var flags := am.surface_get_format(skin_s) & Mesh.ARRAY_FLAG_USE_8_BONE_WEIGHTS
	out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, head_arr, shapes, {}, flags)
	var mat := ShaderMaterial.new()
	mat.shader = HEAD_SHADER
	if head_mat is BaseMaterial3D:
		mat.set_shader_parameter("tex", (head_mat as BaseMaterial3D).albedo_texture)
	# The body skin's own sheen (the MetaHuman body map's mean roughness, 0.73), not Tripo's 0.9: with
	# its own, his neck read darker than the body's at the socket.
	mat.set_shader_parameter("rough", 0.73)
	out.surface_set_material(0, mat)
	_socket_heads[key] = out
	return out


## The body with the MetaHuman head taken off at the socket: every triangle above the ring (its corners
## on or above it, one at least above), the eyes and the scalp. The vertices and morphs stay, so his
## build still applies.
static func _without_head(m: Mesh) -> Mesh:
	if _headless.has(m):
		return _headless[m]
	var am := m as ArrayMesh
	if am == null:
		return m
	var out := ArrayMesh.new()
	out.blend_shape_mode = am.blend_shape_mode
	for k in range(am.get_blend_shape_count()):
		out.add_blend_shape(am.get_blend_shape_name(k))
	for s in range(am.get_surface_count()):
		var a := am.surface_get_arrays(s)
		var mat := am.surface_get_material(s)
		var nm := mat.resource_name if mat != null else ""
		var vs: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
		var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
		var keep := PackedInt32Array()
		if nm != HAIR_SURFACE and nm != EYE_MATERIAL:
			# 1 above the ring, 0 on it (within 1 mm), -1 below.
			var side := PackedInt32Array()
			side.resize(vs.size())
			for i in range(vs.size()):
				var dy := vs[i].y - _socket_y(vs[i])
				side[i] = 1 if dy > 0.001 else (0 if dy >= -0.001 else -1)
			for f in range(0, idx.size(), 3):
				var s0 := side[idx[f]]
				var s1 := side[idx[f + 1]]
				var s2 := side[idx[f + 2]]
				if mini(s0, mini(s1, s2)) >= 0 and maxi(s0, maxi(s1, s2)) > 0:
					continue
				keep.append_array([idx[f], idx[f + 1], idx[f + 2]])
		if keep.is_empty():
			keep = PackedInt32Array([0, 0, 0])
		a[Mesh.ARRAY_INDEX] = keep
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a, am.surface_get_blend_shape_arrays(s), {},
				_custom_format(am, s))
		out.surface_set_material(s, mat)
		out.surface_set_name(s, am.surface_get_name(s))
	_headless[m] = out
	return out


## The custom channels' types on surface s (the MetaHuman's own skin coordinates ride in
## CUSTOM0, oval3d_player.gdshader), which a rebuilt surface must be told again.
static func _custom_format(am: ArrayMesh, s: int) -> int:
	var f := am.surface_get_format(s)
	var out := 0
	for c in range(4):
		var shift: int = Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT + c * Mesh.ARRAY_FORMAT_CUSTOM_BITS
		out |= f & (Mesh.ARRAY_FORMAT_CUSTOM_MASK << shift)
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


static var _loops := {}


## LOOPS_GLB's jog, carry and idle, looping, their tracks pointed at the skeleton at skel_path
## (from the AnimationPlayer's root) by bone name. Loaded once; every player shares them.
static func _loop_anims(skel_path: NodePath) -> Dictionary:
	var key := str(skel_path)
	if _loops.has(key):
		return _loops[key]
	var out := {}
	var ps: PackedScene = load(loops_glb)
	if ps:
		var n := ps.instantiate()
		var src: AnimationPlayer = n.find_children("*", "AnimationPlayer", true, false)[0]
		for name in ["jog", "carry", "idle"]:
			if not src.has_animation(name):
				continue
			var a: Animation = src.get_animation(name).duplicate(true)
			for t in range(a.get_track_count()):
				var path := a.track_get_path(t)
				var bone := path.get_concatenated_subnames()
				if bone == "":
					bone = str(path.get_name(path.get_name_count() - 1))
				a.track_set_path(t, NodePath(key + ":" + bone))
			a.loop_mode = Animation.LOOP_LINEAR
			out[name] = a
		n.free()
	_loops[key] = out
	return out


## Each club's guernsey cut to its own photo's outline (tools/kits/guernsey3d: recut5.py, then
## cut_res.gd): the skin and guernsey surfaces of the body, rebuilt for that club's men. A cut file
## names the shared body's points by number and keeps only the points the cut added.
const CUTS_DIR := "res://assets/oval3d/cuts"
static var _club_bodies := {}


## Body mesh m with club's own guernsey cut, where one exists for this body (the same morph
## targets in the same order, the same point counts); otherwise m. Once per mesh and club; the
## club's men share it.
static func club_body(m: Mesh, club: String) -> Mesh:
	var path := "%s/%s.res" % [CUTS_DIR, club]
	var am := m as ArrayMesh
	if club == "" or am == null or not ResourceLoader.exists(path):
		return m
	var key := [m, club]
	if _club_bodies.has(key):
		return _club_bodies[key]
	_club_bodies[key] = m
	var cut := load(path) as ArrayMesh
	if cut == null or cut.get_blend_shape_count() != am.get_blend_shape_count():
		return m
	for b in range(am.get_blend_shape_count()):
		if cut.get_blend_shape_name(b) != am.get_blend_shape_name(b):
			return m
	var added := {}
	for c in range(cut.get_surface_count()):
		added[cut.surface_get_name(c)] = c
	var swaps := 0
	for s in range(am.get_surface_count()):
		var nm := _surface_name(am, s)
		if cut.has_meta(nm + "_index"):
			if int(cut.get_meta(nm + "_base")) != am.surface_get_array_len(s):
				return m
			swaps += 1
	if swaps == 0:
		return m
	var out := ArrayMesh.new()
	out.blend_shape_mode = am.blend_shape_mode
	for b in range(am.get_blend_shape_count()):
		out.add_blend_shape(am.get_blend_shape_name(b))
	for s in range(am.get_surface_count()):
		var nm := _surface_name(am, s)
		var a := am.surface_get_arrays(s)
		var shapes := am.surface_get_blend_shape_arrays(s)
		var flags := _custom_format(am, s)
		if cut.has_meta(nm + "_index"):
			var c: int = added.get(nm, -1)
			if c >= 0:
				_append_points(a, cut.surface_get_arrays(c))
				var more := cut.surface_get_blend_shape_arrays(c)
				for b in range(shapes.size()):
					_append_points(shapes[b], more[b])
			a[Mesh.ARRAY_INDEX] = cut.get_meta(nm + "_index")
			# The guernsey's flat pattern (unwrap.py, cut_res.gd): each point's place in the club's atlas cell.
			if cut.has_meta(nm + "_unwrap"):
				a[Mesh.ARRAY_CUSTOM3] = cut.get_meta(nm + "_unwrap")
				flags |= Mesh.ARRAY_CUSTOM_RG_FLOAT << Mesh.ARRAY_FORMAT_CUSTOM3_SHIFT
			_drop_unused(a, shapes)
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a, shapes, {}, flags)
		out.surface_set_material(s, am.surface_get_material(s))
		out.surface_set_name(s, am.surface_get_name(s))
	_club_bodies[key] = out
	return out


static func _surface_name(am: ArrayMesh, s: int) -> String:
	var mat := am.surface_get_material(s)
	return mat.resource_name if mat != null else ""


## Keeps only the points the triangles use (the cut leaves the shared body's points it cut away
## unused; the kit edges must not measure them), renumbering the index; shapes alike.
static func _drop_unused(a: Array, shapes: Array) -> void:
	var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
	var n := (a[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
	var map := PackedInt32Array()
	map.resize(n)
	map.fill(-1)
	var keep := PackedInt32Array()
	for i in idx:
		if map[i] < 0:
			map[i] = 0
	for i in range(n):
		if map[i] == 0:
			map[i] = keep.size()
			keep.append(i)
	if keep.size() == n:
		return
	for j in range(idx.size()):
		idx[j] = map[idx[j]]
	a[Mesh.ARRAY_INDEX] = idx
	for arrs in [a] + shapes:
		for t in range(Mesh.ARRAY_MAX):
			if t == Mesh.ARRAY_INDEX or arrs[t] == null:
				continue
			var src = arrs[t]
			var per: int = src.size() / n
			var dst = src.slice(0, 0)
			for r in keep:
				for c in range(per):
					dst.append(src[r * per + c])
			arrs[t] = dst


## Adds the points in more (no index) to the end of a, channel by channel.
static func _append_points(a: Array, more: Array) -> void:
	for t in range(Mesh.ARRAY_MAX):
		if t != Mesh.ARRAY_INDEX and a[t] != null and more[t] != null:
			a[t].append_array(more[t])


## club: whose guernsey cut he wears (club_body); "" the body as it is.
func _player(scene: PackedScene, kit: ShaderMaterial, cols: Array, club := "") -> Dictionary:
	var node: Node3D = scene.instantiate()
	add_child(node)
	# Every surface wears the kit except the boots and the eyes, which keep their own material.
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		m.mesh = _kit_edges(_skull(club_body(m.mesh, club)))
		for s in range(m.mesh.get_surface_count()):
			var own := m.mesh.surface_get_material(s)
			if own == null or not own.resource_name in [BOOT_MATERIAL, EYE_MATERIAL]:
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
	var lib := ap.get_animation_library("")
	var loops := _loop_anims(ap.get_node(ap.root_node).get_path_to(skel))
	for n in ["jog", "carry", "idle"]:
		if loops.has(n):
			if lib.has_animation(n):
				lib.remove_animation(n)
			lib.add_animation(n, loops[n])
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
	# A marker, not lit: drawn after the film and its tone, in the exact club colour (rule 2.81).
	rm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	rm.render_priority = Material.RENDER_PRIORITY_MAX
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
## At a stoppage one of them takes the ball (_stoppage_umpire): the field umpire nearest the
## centre for a centre bounce, the nearest field umpire for a ball-up, the boundary umpire on
## that wing for a throw-in. He goes to his mark (_stoppage_mark), has the ball in his hands
## (_umpire_ball) and puts it in play with the bounce clip the director passed (rule 2.75):
## the whole clip for a centre bounce, timed so the ball hits the turf on the bounce; only its
## lift of the ball, at speed, for a ball-up or a throw-in (no throw clip exists yet).
const UMP_SPEED := 7.0
## The umpire taking a stoppage runs to his mark at a sprint.
const UMP_SPRINT := 8.5
const UMP_RUN_FROM := 1.4
const UMP_CLIP := "umpire_bounce_01"
## umpire_bounce_01, measured (tools/oval3d/probe_umpire_clip.gd): the ball leaves his hands at
## T_REL and is on the turf at T_HIT, BOUNCE_REACH metres in front of where he started.
const UMP_T_REL := 1.87
const UMP_T_HIT := 1.96
const UMP_BOUNCE_REACH := 2.4
## Up to here (the ball lifted to his chest) he may stand and wait for a late set-up.
const UMP_T_HOLD := 0.4
## The latest a bounce clip starts: the ball overhead, about to come down (after a cut).
const UMP_T_LATEST := 1.6
## A set-up's estimated time left, as the bounce clip trusts it (_bounce_in).
const UMP_SETUP_TRUST := 0.7
## How much quicker than a turn in play he squares up within 3 m of his mark.
const UMP_SQUARE := 3.0
## A ball-up or throw-in: the lift of the ball from his chest, played at UMP_LIFT_RATE.
const UMP_T_LIFT := 0.45
const UMP_LIFT_RATE := 2.0
## On his mark within this many metres; the ball comes to his hands within UMP_TAKE of it.
const UMP_SET := 0.3
const UMP_TAKE := 2.5
## The ball goes from where it was to his hands (picked up) over UMP_PICK seconds, and from his
## hands onto the director's flight (let go) over UMP_LET_GO.
const UMP_PICK := 0.3
const UMP_LET_GO := 0.2
## From the end of a clip to his stand.
const UMP_BLEND_OUT := 0.4

var _ump_job := -1            # the umpire taking the stoppage (index in umpires)
var _ump_placed := false      # the umpires have been put on their first spots
var _ump_cut := false         # the picture has just cut away (umpires_after_cut)
var _ump_snapped := false     # ...and this frame the umpires were put on their spots
var _ump_time := -1.0         # the director's time last frame
var _ump_step := 1.0 / 30.0   # the director seconds of the last frame that moved
var _ump_ball := false        # the ball is in his hands this frame
var _ump_pick := -1.0         # seconds since he took it (the pick-up blend)
var _ump_from := Vector3.ZERO # where the ball was when he took it
var _ump_off := Vector3.ZERO  # let go: his hands less the director's ball, easing out
var _ump_off_t := -1.0
var _ump_hit_from := Vector3.ZERO  # a bounce: where the ball left his hands


## The umpire who takes stoppage `st` (director.stoppage_now), -1 for none. Kept for the whole
## stoppage once chosen; a clip being played keeps its man until it ends.
func _stoppage_umpire(st: Dictionary) -> int:
	if st.is_empty():
		return -1
	if _ump_job >= 0:
		return _ump_job
	var at: Vector2 = st["at"]
	var want := "boundary" if str(st["kind"]) == "throwin" else "field"
	var best := -1
	var best_d := INF
	for u in umpires:
		if str(u["role"]) != want or (u as Dictionary).has("clip"):
			continue
		var n: Node3D = u["node"]
		var d := Vector2(n.position.x, n.position.z).distance_to(at)
		if d < best_d:
			best_d = d
			best = int(u["k"])
	return best


## [mark, facing] for the umpire taking stoppage `st`: a centre bounce from BOUNCE_REACH back
## across the ground (the rucks come in from up and down the ground, never through his run); a
## ball-up just off the ball; a throw-in just over the line, his back to the play, as the boundary
## umpires throw it in.
func _stoppage_mark(st: Dictionary) -> Array:
	var at: Vector2 = st["at"]
	match str(st["kind"]):
		"bounce":
			return [at - Vector2(0.0, UMP_BOUNCE_REACH), Vector2(0.0, 1.0)]
		"throwup":
			return [at - Vector2(0.0, 0.6), Vector2(0.0, 1.0)]
		_:
			var out := Vector2(at.x / (HALF_LEN * HALF_LEN), at.y / (HALF_WID * HALF_WID))
			out = out.normalized() if out.length() > 0.0 else Vector2(0.0, 1.0)
			return [at + out * 0.6, out]


func _move_umpires(frame_dt: float) -> void:
	if umpires.is_empty():
		return
	# The umpires move in the director's time, as the players do: double speed through real
	# footy's pauses (rule 2.93), still while the play is held for a replay (rule 2.96).
	var dt := clampf(director.time - _ump_time, 0.0, 0.5) if _ump_time >= 0.0 else frame_dt
	_ump_time = director.time
	if dt > 0.0:
		_ump_step = dt
	var spots := _umpire_spots()
	var bp: Vector2 = director.ball["pos"]
	var st: Dictionary = director.stoppage_now()
	var flying := str(director.ball.get("mode", "")) == "flight"
	if st.is_empty() and (_ump_job < 0 or not (umpires[_ump_job] as Dictionary).has("clip")):
		_ump_job = -1
	if not st.is_empty():
		_ump_job = _stoppage_umpire(st)
	var held := false
	var first := (not _ump_placed or _ump_cut) and not st.is_empty()
	_ump_placed = _ump_placed or first
	_ump_cut = false
	_ump_snapped = first
	for u in umpires:
		var node: Node3D = u["node"]
		var ap: AnimationPlayer = u["anim"]
		var k := int(u["k"])
		if u.has("clip"):
			held = _umpire_clip(u, st, dt) or held
			continue
		if u.has("out") and _umpire_blend_out(u, dt):
			continue
		var at := Vector2(node.position.x, node.position.z)
		var want: Vector2 = spots[k][1]
		var face := Vector2.ZERO
		var job := k == _ump_job and not st.is_empty()
		if job:
			var m := _stoppage_mark(st)
			want = m[0]
			face = m[1]
		if first:
			# The first picture (the opening bounce), or the first after a cut: everyone already
			# on his spot.
			at = want
			if face != Vector2.ZERO:
				node.rotation.y = atan2(face.x, face.y)
		var step := want - at
		var vel := Vector2.ZERO
		if dt > 0.0 and step.length() > 0.05:
			var move := step.limit_length((UMP_SPRINT if job else UMP_SPEED) * dt)
			at += move
			vel = move / dt
		node.position = Vector3(at.x, 0.0, at.y)
		var speed := vel.length()
		var clip := "idle"
		var rate := 1.0
		# Turning at a pivot's pace, as the players do (Oval3DAnim.TURN).
		var turn := Oval3DAnim.TURN * dt if dt > 0.0 else PI
		var on_mark := job and at.distance_to(want) < UMP_SET
		if job and at.distance_to(want) < 3.0:
			# Squaring up on his mark: quicker than a turn in play, so he is set in time.
			turn *= UMP_SQUARE
		if speed > UMP_RUN_FROM and not on_mark:
			node.rotation.y = rotate_toward(node.rotation.y, atan2(vel.x, vel.y), turn)
			clip = "jog"
			rate = clampf(speed / LOOP_SPEED, 0.45, 2.3)
		else:
			var to := face if face != Vector2.ZERO else bp - at
			if to.length() > 0.5 or face != Vector2.ZERO:
				node.rotation.y = rotate_toward(node.rotation.y, atan2(to.x, to.y), turn)
		var ball_near := bp.distance_to(st["at"]) < UMP_TAKE if job else false
		if on_mark and ball_near and not flying:
			# On his mark with the ball: it is in his hands, held at his chest (the clip's
			# first frame) until he puts it in play.
			held = true
			if ap.current_animation != UMP_CLIP:
				ap.play(UMP_CLIP, 0.25)
			ap.seek(0.0, false)
			ap.advance(maxf(dt, 1e-4))
			var going := _bounce_in(st)
			var squared := face == Vector2.ZERO or absf(angle_difference(node.rotation.y, atan2(face.x, face.y))) < 0.3
			if str(st["kind"]) == "bounce" and is_finite(going) and squared:
				# The bounce is coming: the clip starts, and keeps time with it (_umpire_clip).
				# With less time than the whole wind-up (a set-up takes about a second once the
				# ball is back), he starts into it, the ball already lifted.
				var t0 := clampf(UMP_T_HIT - going, 0.0, UMP_T_LATEST)
				u["clip"] = {"kind": "bounce", "t": t0, "rate": 1.0,
						"end": ap.current_animation_length, "at": st["at"]}
				ap.seek(t0, true)
			continue
		if ap.current_animation != clip:
			ap.play(clip, 0.2)
			ap.seek(fmod(float(k) * 1.37, ap.current_animation_length), false)
		ap.advance(maxf(dt * rate, 1e-4))
	# The ball left the job umpire's hands this frame (a ball-up or throw-in going up): his
	# arms lift it, at speed.
	if not held and _ump_ball and _ump_job >= 0 and flying:
		var u: Dictionary = umpires[_ump_job]
		if not u.has("clip"):
			u["clip"] = {"kind": "lift", "t": 0.0, "rate": UMP_LIFT_RATE, "end": UMP_T_LIFT}
	_umpire_ball_state(held)


## One frame of an umpire's one-off clip (a bounce, or the lift of a ball-up or throw-in). True
## while the ball is still his (in his hands, or on its way from them to the turf at a bounce).
func _umpire_clip(u: Dictionary, st: Dictionary, dt: float) -> bool:
	var c: Dictionary = u["clip"]
	var ap: AnimationPlayer = u["anim"]
	var before := float(c["t"])
	var bouncing := str(c["kind"]) == "bounce"
	var rate := float(c["rate"])
	if bouncing and before < UMP_T_HIT:
		# Keeping time with the director's bounce (its set-up time is an estimate that firms as
		# the players reach their spots): the ball is on the turf when he bounces it. While it is
		# still far off he holds the ball at his chest, before the run in.
		var going := _bounce_in(st)
		var need := UMP_T_HIT - before
		rate = clampf(need / maxf(going, 0.02), 0.0 if before < UMP_T_HOLD else 0.3, 5.0)
	elif bouncing:
		# After the ball hits the turf, the follow-through runs at the take's own speed.
		rate = 1.0
	c["t"] = before + dt * rate
	if float(c["t"]) >= float(c["end"]):
		_end_umpire_clip(u)
		return false
	# Advanced, never sought: a seek would leave the blend in from his stand where it was.
	ap.advance(float(c["t"]) - before)
	if not bouncing:
		return false
	if float(c["t"]) < UMP_T_REL:
		return true
	if before < UMP_T_REL:
		_ump_hit_from = _umpire_hands(u)
	# Out of his hands and onto the turf where the director bounces it, and there until the
	# director's bounce takes it up (a frame or two when his clip runs ahead of it).
	return str(director.ball.get("mode", "")) != "flight"


## Director seconds to the bounce of stoppage `st` for the umpire's clip to keep time with, less
## one frame: exact in the wait before it; while the players set, the estimate cut by
## UMP_SETUP_TRUST (a set-up mostly ends sooner than its estimate, and the clip slows more
## gracefully than it hurries).
func _bounce_in(st: Dictionary) -> float:
	if str(st.get("kind", "")) != "bounce":
		return 0.0
	var going := float(st["in"])
	going = going if bool(st.get("sure", false)) else going * UMP_SETUP_TRUST
	# Aimed a frame early: the last picture before the bounce has the ball on the turf.
	return maxf(going - _ump_step, 0.0)


## The clip is over: back to his stand, blended over UMP_BLEND_OUT, his body left where the clip
## took it (the bounce runs him in two metres): as the pose blends from the clip's to his stand,
## he is carried forward by as much, so his hips never slide back (_umpire_blend_out).
func _end_umpire_clip(u: Dictionary) -> void:
	var ap: AnimationPlayer = u["anim"]
	var skel: Skeleton3D = u["skel"]
	var node: Node3D = u["node"]
	var hips := to_local(skel.global_transform * skel.get_bone_global_pose(_pelvis(u)).origin)
	ap.play("idle", UMP_BLEND_OUT)
	ap.seek(fmod(float(u["k"]) * 1.37, ap.current_animation_length), false)
	u["out"] = {"base": node.position, "by": Vector3(hips.x - node.position.x, 0.0, hips.z - node.position.z), "t": 0.0}
	u.erase("clip")


## One frame of the blend out of a clip (_end_umpire_clip). False once it is over.
func _umpire_blend_out(u: Dictionary, dt: float) -> bool:
	var o: Dictionary = u["out"]
	o["t"] = float(o["t"]) + dt
	var w := clampf(float(o["t"]) / UMP_BLEND_OUT, 0.0, 1.0)
	(u["node"] as Node3D).position = (o["base"] as Vector3) + (o["by"] as Vector3) * w
	(u["anim"] as AnimationPlayer).advance(maxf(dt, 1e-4))
	if w >= 1.0:
		u.erase("out")
		return false
	return true


## Between an umpire's palms (as _hold_ball finds a player's), in the scene's frame.
func _umpire_hands(u: Dictionary) -> Vector3:
	var palms := _umpire_palms(u)
	return (palms[0] + palms[1]) * 0.5


func _umpire_palms(u: Dictionary) -> Array:
	var skel: Skeleton3D = u["skel"]
	var gt := skel.global_transform
	var out := []
	for k in range(2):
		var pose := skel.get_bone_global_pose(u["hands"][k])
		out.append(gt * (pose.origin + pose.basis.y.normalized() * float(u["hand_len"][k]) * 0.6))
	return out


## Whether the job umpire has the ball this frame, and the blends in and out of his hands.
func _umpire_ball_state(held: bool) -> void:
	if held and not _ump_ball:
		# Just after a cut he has it already; in play he takes it over UMP_PICK.
		_ump_pick = -1.0 if _ump_snapped else 0.0
		_ump_from = ball.global_position if ball != null else Vector3.ZERO
	if not held and _ump_ball and ball != null:
		_ump_off_t = 0.0
		_ump_off = ball.global_position
	_ump_ball = held


## Just after an umpire lets the ball go, the gap between his hands and the director's ball
## (already placed this frame) eases out over UMP_LET_GO: it leaves his hands, never jumps.
func _umpire_let_go(dt: float) -> void:
	if _ump_off_t < 0.0 or dt <= 0.0 or _ump_ball:
		return
	if _ump_off_t == 0.0:
		_ump_off = _ump_off - ball.global_position
	_ump_off_t += dt
	var u := clampf(_ump_off_t / UMP_LET_GO, 0.0, 1.0)
	ball.global_position += _ump_off * (1.0 - u) * (1.0 - u)
	if u >= 1.0:
		_ump_off_t = -1.0


## Puts the ball where the umpire has it (his hands, or falling from them to the turf at a
## bounce) and returns true; false when no umpire has it.
func _umpire_ball(dt: float) -> bool:
	if not _ump_ball or _ump_job < 0:
		return false
	var u: Dictionary = umpires[_ump_job]
	var c: Dictionary = u.get("clip", {})
	var want := _umpire_hands(u)
	if str(c.get("kind", "")) == "bounce" and float(c["t"]) >= UMP_T_REL:
		var at: Vector2 = c["at"]
		var turf := global_transform * Vector3(at.x, BALL_R, at.y)
		var f := clampf((float(c["t"]) - UMP_T_REL) / (UMP_T_HIT - UMP_T_REL), 0.0, 1.0)
		var st: Dictionary = director.stoppage_now()
		if str(st.get("kind", "")) == "bounce" and float(st["in"]) <= _ump_step * 1.05:
			# The director bounces it next frame: it is on the turf now.
			f = 1.0
		want = _ump_hit_from.lerp(turf, f)
		_ump_pick = -1.0
	if _ump_pick >= 0.0 and dt > 0.0:
		_ump_pick += dt
		var f := clampf(_ump_pick / UMP_PICK, 0.0, 1.0)
		want = _ump_from.lerp(want, f * f * (3.0 - 2.0 * f))
		if f >= 1.0:
			_ump_pick = -1.0
	ball.global_position = want
	if str(c.get("kind", "")) != "bounce" or float(c["t"]) < UMP_T_REL:
		# Its long axis across his hands, as a player holds it.
		var palms := _umpire_palms(u)
		var across: Vector3 = palms[1] - palms[0]
		if across.length() > 0.01 and absf(across.normalized().dot(Vector3.UP)) < 0.99:
			ball.look_at(ball.global_position + across, Vector3.UP)
	return true


func _mat(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = 0.85
	return m
