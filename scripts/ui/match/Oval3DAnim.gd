class_name Oval3DAnim
extends RefCounted
## The 3D oval's animation controller (row 198, owned by the animation session; Oval3D.gd only
## calls step()). Picks each player's clip, facing and rate from his token and the ball, and
## advances his AnimationPlayer by dt. This default holds the prototype's jog / idle / carry logic.

const JOG_SPEED := 6.0
const RUN_FROM := 1.4          # m/s: slower than this he stands
## Eyes on the ball (plan §2.6): the neck takes part of the turn and the head the rest, inside a
## real person's range (about 80 degrees each way, 35 up or down), so nobody turns like an owl.
## The carrier looks where he runs, not at the ball in his hands.
const LOOK := [["neck_01", 35.0, 20.0, 0.5], ["head", 45.0, 25.0, 1.0]]  # bone, yaw, pitch, influence
const LOOK_FOLLOW := 8.0       # 1/s: how fast the eyes catch a moving ball
const BALL_R := 0.09          # m: the ball on the turf (Oval3D.BALL_R)

var director: MatchDirector
var players: Array
var _targets: Array = []       # per player: the Node3D his look-at modifiers aim at
var _looks: Array = []         # per player: his LookAtModifier3D nodes


func _init(p_director: MatchDirector, p_players: Array) -> void:
	director = p_director
	players = p_players
	for p in players:
		_add_look(p)


func _add_look(p: Dictionary) -> void:
	var skel: Skeleton3D = p["skel"]
	var target := Node3D.new()
	(p["node"] as Node3D).add_child(target)
	target.top_level = true
	var mods := []
	for l in LOOK:
		var m := LookAtModifier3D.new()
		m.bone_name = l[0]
		m.forward_axis = SkeletonModifier3D.BONE_AXIS_PLUS_Z
		m.primary_rotation_axis = Vector3.AXIS_Y
		m.use_angle_limitation = true
		m.symmetry_limitation = true
		m.primary_limit_angle = deg_to_rad(l[1] * 2.0)
		m.secondary_limit_angle = deg_to_rad(l[2] * 2.0)
		m.influence = l[3]
		skel.add_child(m)
		m.target_node = m.get_path_to(target)
		mods.append(m)
	_targets.append(target)
	_looks.append(mods)


## Pose player i for this frame. holder = the index with the ball in his hands, or -1.
func step(i: int, p: Dictionary, holder: int, pos: Vector2, vel: Vector2, dt: float) -> void:
	var node: Node3D = p["node"]
	var speed := vel.length()
	var ap: AnimationPlayer = p["anim"]
	var want := "carry" if i == holder else "idle"
	var rate := 0.0 if i == holder else 1.0
	if speed > RUN_FROM:
		node.rotation.y = atan2(vel.x, vel.y)
		want = "carry" if i == holder else "jog"
		rate = clampf(speed / JOG_SPEED, 0.45, 2.3)
	elif i != holder:
		# Standing: face the ball (the carrier keeps his heading).
		var to: Vector2 = (director.ball["pos"] as Vector2) - pos
		if to.length() > 0.5:
			node.rotation.y = atan2(to.x, to.y)
	if ap.current_animation != want:
		var at := fmod(float(i) * 0.137, 0.66)
		if ap.current_animation != "idle" and ap.current_animation != "":
			at = ap.current_animation_position
		ap.play(want)
		ap.seek(fmod(at, ap.current_animation_length), false)
	if want == "carry" and rate == 0.0:
		# Standing with the ball: the carry's first key, both legs under him (poses.carry
		# at p = 0), not frozen mid-stride.
		ap.seek(0.0, false)
	# A zero step leaves a freshly played pose unapplied (a standing holder kept the idle
	# arms), so a still pose still advances by a sliver.
	ap.advance(maxf(dt * rate, 1e-4))
	_look_at_ball(i, i == holder, dt)


func _look_at_ball(i: int, carrying: bool, dt: float) -> void:
	var bp: Vector2 = director.ball["pos"]
	var h := float(director.ball.get("h", 0.0))
	var want := Vector3(bp.x, maxf(h, BALL_R), bp.y)
	var target: Node3D = _targets[i]
	if dt <= 0.0 or target.global_position == Vector3.ZERO:
		target.global_position = want
	else:
		target.global_position = target.global_position.lerp(want, clampf(dt * LOOK_FOLLOW, 0.0, 1.0))
	for m in _looks[i]:
		(m as LookAtModifier3D).active = not carrying
