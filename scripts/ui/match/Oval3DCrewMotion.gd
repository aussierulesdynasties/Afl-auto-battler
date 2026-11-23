class_name Oval3DCrewMotion
extends RefCounted
## The clubs' trainers and runners on the 3D oval (row 202), where and when the AFL's rules let
## them be (AFL Regulations 2026):
##   - 12.2(g)(iv): up to four trainers a club wait where the 50-metre arcs meet the boundary,
##     against the fence. Here each club has one at each of the four.
##   - 12.13: a trainer may go onto the ground with drinks only in a break in play (a player
##     lining up a shot at goal is one) and must be off before play restarts; the runner only
##     once the goal umpire has signalled a goal, and must be leaving as play restarts.
## So: while a set shot is lined up, each club's trainer nearest the play runs a drink to the
## nearest of his men who is clear of the kicker, and runs back to the fence once the ball is
## kicked; in the break after a goal every trainer with a man of his in reach runs one out; after a goal each club's runner runs from the interchange to the man of his nearest the
## centre, and back as the ball is bounced. Looks only: the sim never sees them.

const FENCE := 3.5            # m outside the boundary line the trainers stand
const PAIR := 1.2             # m apart, the two clubs' trainers at one spot
const RUN := 6.0              # m/s, a trainer's or runner's run
const STOP := 1.1             # m from his man he stops at
const CLEAR := 12.0           # m a drink's man is at least from the kicker
const FAR := 70.0             # m from the camera beyond which a standing crewman's idle holds still
const REACH := 35.0           # m from his place the farthest man a trainer takes a drink to
const BENCH_X := 9.0          # m either side of centre, the clubs' interchange benches
const BENCH_OUT := 4.0        # m outside the boundary
const RUN_FROM := 1.4         # m/s: below it he stands

var oval: Oval3D
var crew: Array = []          # {node, anim, skel, role, side, home: Vector2, job: int, k}
var _time := -1.0
var _runner_on := false       # a goal has been signalled and the centre bounce is not yet near


func _init(p_oval: Oval3D) -> void:
	oval = p_oval


## Where 50-metre arc `end` (+1 or -1) meets the boundary on wing `wing` (+1 or -1), FENCE
## metres outside it, in the director's metres (x along the ground, y across).
static func arc_spot(end: float, wing: float, out := FENCE) -> Vector2:
	var goal := Vector2(MatchMotion.GOAL_X * end, 0.0)
	var best := Vector2.ZERO
	var best_d := INF
	for i in range(721):
		var t := PI * 0.5 * float(i) / 720.0
		var p := Vector2(MatchMotion.HALF_LEN * cos(t) * end, MatchMotion.HALF_WID * sin(t) * wing)
		if MatchMotion.shaped():
			# A traced ground: the real boundary line, not the ellipse.
			p = MatchMotion.edge_point(atan2(sin(t) * wing, cos(t) * end))
		var d := absf(p.distance_to(goal) - 50.0)
		if d < best_d:
			best_d = d
			best = p
	return _outside(best, out)


## p on the boundary, moved `out` metres outward along the ellipse's normal there.
static func _outside(p: Vector2, out: float) -> Vector2:
	if MatchMotion.shaped():
		return p + MatchMotion.fence_normal(p) * out
	var n := Vector2(p.x / (MatchMotion.HALF_LEN * MatchMotion.HALF_LEN), p.y / (MatchMotion.HALF_WID * MatchMotion.HALF_WID))
	return p + n.normalized() * out if n.length() > 0.0 else p


## The bench of club `side` (0 home, 1 away): BENCH_OUT outside the boundary on the -y wing.
static func bench(side: int) -> Vector2:
	var x := BENCH_X * (-1.0 if side == 0 else 1.0)
	var y := -MatchMotion.edge_y(x, -1.0)
	return _outside(Vector2(x, y), BENCH_OUT)


## Trainers' shorts: black (2025 broadcasts, three clubs).
const TRAINER_SHORTS := Color(0.04, 0.04, 0.045)
## The yellow squeeze bottles trainers hand out (2025 broadcasts).
const BOTTLE := Color(1.0, 0.86, 0.12)


## The crew of both clubs: four trainers and a runner each, in the club's own socks (the runner his shorts too)
## (body: each club's kit material) under the crew's tops. clubs: [home, away].
func build(scene: PackedScene, body: Array, clubs: Array) -> void:
	var shorts := []
	var tops := []
	for c in clubs:
		var g: Dictionary = GameDB.club_guernsey(c)
		shorts.append(g.get("shorts", Color(0.1, 0.1, 0.12)))
		tops.append(g.get("base", Color(0.07, 0.07, 0.08)))
	var tee_kits := []
	var vest_kits := []
	var runner_kits := []
	var trainer_body := []
	for side in range(2):
		var sh: Color = shorts[side]
		var top: Color = tops[side]
		# 2025 broadcasts: the purple vest over the club's own top, with black shorts.
		tee_kits.append(oval._kit({"design": "plain", "base": top, "pattern": top, "pattern2": top,
				"shorts": TRAINER_SHORTS}))
		vest_kits.append(oval._kit({"design": "plain", "base": Oval3DCrew.TRAINER_VEST,
				"pattern": Oval3DCrew.TRAINER_VEST, "pattern2": Oval3DCrew.TRAINER_VEST,
				"shorts": TRAINER_SHORTS}))
		var tb := (body[side] as ShaderMaterial).duplicate() as ShaderMaterial
		tb.set_shader_parameter("shorts", TRAINER_SHORTS)
		trainer_body.append(tb)
		runner_kits.append(oval._kit({"design": "plain", "base": Oval3DCrew.RUNNER_TOP,
				"pattern": Oval3DCrew.RUNNER_TOP, "pattern2": Oval3DCrew.RUNNER_TOP, "shorts": sh}))
	var k := 0
	for side in range(2):
		for end in [-1.0, 1.0]:
			for wing in [-1.0, 1.0]:
				var spot := arc_spot(end, wing)
				# The two clubs side by side along the fence.
				var along := Vector2(-spot.y, spot.x).normalized() * PAIR * (0.5 if side == 0 else -0.5)
				_add(scene, "trainer", side, spot + along, trainer_body[side], tee_kits[side], vest_kits[side], k)
				k += 1
		_add(scene, "runner", side, bench(side), body[side], runner_kits[side], null, k)
		k += 1


func _add(scene: PackedScene, role: String, side: int, home: Vector2, body: ShaderMaterial, kit: Material,
		vest: Material, k: int) -> void:
	var c := oval._player(scene, body, [Color.WHITE])
	Oval3DCrew.dress(c, role, Oval3D.player_glb, kit, vest)
	oval.look(c, oval._crew_look(20 + k))
	(c["ring"] as Node3D).visible = false
	if role == "trainer":
		_bottle(c)
	c["role"] = role
	c["side"] = side
	c["home"] = home
	c["job"] = -1
	c["k"] = k
	var n: Node3D = c["node"]
	n.position = Vector3(home.x, 0.0, home.y)
	# Facing the ground.
	n.rotation.y = atan2(-home.x, -home.y)
	crew.append(c)


## A drink bottle in his right hand (Oval3DCrew's crew_bottle), as trainers carry them.
func _bottle(c: Dictionary) -> void:
	var all := Oval3DCrew.pieces(Oval3DCrew.glb_for(Oval3D.player_glb))
	if not all.has("crew_bottle"):
		return
	var skel: Skeleton3D = c["skel"]
	var on := BoneAttachment3D.new()
	on.bone_name = "hand_r"
	skel.add_child(on)
	var mi := MeshInstance3D.new()
	mi.name = "crew_bottle"
	mi.mesh = (all["crew_bottle"] as Dictionary)["mesh"]
	var grip := Oval3DGrip.new()
	grip.name = "grip"
	skel.add_child(grip)
	mi.transform = grip.held_at(skel)
	var m := StandardMaterial3D.new()
	m.albedo_color = BOTTLE
	m.roughness = 0.35
	mi.material_override = m
	on.add_child(mi)
	c["bottle"] = mi




## One frame: who is wanted where (a drink in a break before a shot, the runner after a goal),
## then each runs there or back to his place, jogging, and stands facing the play.
func step(frame_dt: float) -> void:
	if crew.is_empty():
		return
	var d: MatchDirector = oval.director
	# In the director's time, as the players and umpires move (still while a replay holds play).
	var dt := clampf(d.time - _time, 0.0, 0.5) if _time >= 0.0 else frame_dt
	_time = d.time
	var shot: Dictionary = d.shot_now()
	var st: Dictionary = d.stoppage_now()
	var bp: Vector2 = d.ball["pos"]
	var drinks := not shot.is_empty() and bool(shot.get("set", false)) and str(shot.get("phase", "")) in ["line_up", "hold", "possess"]
	# The runner: on once the goal is signalled, off as the centre bounce comes.
	if not shot.is_empty() and bool(shot.get("goal", false)) and str(shot.get("phase", "")) in ["emit", "celebrate"]:
		_runner_on = true
	elif _runner_on and (st.is_empty() or str(st.get("kind", "")) != "bounce" or float(st.get("in", INF)) < 4.0) \
			and shot.is_empty():
		_runner_on = false
	var runner_on := _runner_on
	# Drinks: before a set shot the trainer of each club nearest the play; in the break after a
	# goal every trainer with a man of his within reach. Each keeps his man for the whole break.
	for side in range(2):
		var tr := _nearest_trainer(side, bp) if drinks else -1
		var taken := {}
		for c in crew:
			if int(c["side"]) != side:
				continue
			var want := -1
			if str(c["role"]) == "trainer" and (int(c["k"]) == tr or runner_on):
				want = int(c["job"])
				if want < 0:
					want = _drink_man(side, bp, Vector2(c["home"]), taken)
				taken[want] = true
			elif str(c["role"]) == "runner" and runner_on:
				want = int(c["job"]) if int(c["job"]) >= 0 else _nearest_man(side, Vector2.ZERO, bp, 0.0, {}, INF)
			c["job"] = want
	for c in crew:
		_move(c, dt, bp)


## The trainer of club side nearest the ball.
func _nearest_trainer(side: int, bp: Vector2) -> int:
	var best := -1
	var bd := INF
	for c in crew:
		if int(c["side"]) == side and str(c["role"]) == "trainer":
			var dd := (c["home"] as Vector2).distance_to(bp)
			if dd < bd:
				bd = dd
				best = int(c["k"])
	return best


## The man of club side his trainer runs a drink to: the nearest to the trainer who is CLEAR of
## the kicker (the ball), so the drink never crosses the shot.
func _drink_man(side: int, bp: Vector2, from: Vector2, taken: Dictionary) -> int:
	return _nearest_man(side, from, bp, CLEAR, taken, REACH)


## The man of club side nearest `to`, at least `clear` from away_from, not in taken, within reach.
func _nearest_man(side: int, to: Vector2, away_from: Vector2, clear: float, taken: Dictionary, reach: float) -> int:
	var best := -1
	var bd := INF
	var toks: Array = oval.director.tokens
	for i in range(toks.size()):
		var t: Dictionary = toks[i]
		if int(t.get("side", 0)) != side:
			continue
		var p: Vector2 = t["pos"]
		if p.distance_to(away_from) < clear:
			continue
		var dd := p.distance_to(to)
		if dd < bd and dd <= reach and not taken.has(i):
			bd = dd
			best = i
	return best


func _move(c: Dictionary, dt: float, bp: Vector2) -> void:
	var n: Node3D = c["node"]
	var ap: AnimationPlayer = c["anim"]
	var at := Vector2(n.position.x, n.position.z)
	var want: Vector2 = c["home"]
	var face := -at
	var job := int(c["job"])
	if job >= 0:
		var man: Vector2 = oval.director.tokens[job]["pos"]
		var gap := at - man
		want = man + (gap.normalized() if gap.length() > 0.01 else Vector2(1, 0)) * STOP
		face = man - at
	elif at.distance_to(want) < 0.3:
		face = bp - at
	var step := want - at
	var vel := Vector2.ZERO
	if dt > 0.0 and step.length() > 0.05:
		var move := step.limit_length(RUN * dt)
		at += move
		vel = move / dt
	n.position = Vector3(at.x, 0.0, at.y)
	var turn := Oval3DAnim.TURN * dt if dt > 0.0 else PI
	var clip := "idle"
	var rate := 1.0
	if vel.length() > RUN_FROM:
		n.rotation.y = rotate_toward(n.rotation.y, atan2(vel.x, vel.y), turn)
		clip = "jog"
		rate = clampf(vel.length() / oval.anim.loop_speed("jog", c), Oval3DAnim.RATE_MIN, Oval3DAnim.RATE_MAX)
	elif face.length() > 0.5:
		n.rotation.y = rotate_toward(n.rotation.y, atan2(face.x, face.y), turn)
	if ap.current_animation != clip:
		ap.play(clip, 0.2)
		ap.seek(fmod(float(c["k"]) * 1.37, ap.current_animation_length), false)
	# Standing at the fence far from the camera, his idle is not worth a phone's time to pose:
	# it holds until the camera comes near or he moves.
	var cam := oval.get_viewport().get_camera_3d() if oval.is_inside_tree() else null
	# (Posed once first, so his hands hold what they carry.)
	if clip == "idle" and job < 0 and cam != null and c.get("posed", false) \
			and cam.global_position.distance_to(n.global_position) > FAR:
		return
	c["posed"] = true
	ap.advance(maxf(dt * rate, 1e-4))
