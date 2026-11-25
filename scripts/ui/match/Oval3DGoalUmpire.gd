class_name Oval3DGoalUmpire
extends RefCounted
## The goal umpire's flags in a 3D match (row 202), as 2025 broadcasts show them. Both flags are
## stowed furled in the padding of one goal post. After he signals a goal he walks to that post,
## draws both (the near hand, the other taking one), walks back toward the middle and waves them
## facing the ground; then back at the post he winds the cloths round their sticks, wedges them
## back, stands a while and walks back to his place on the line. After a behind he draws one, waves
## it by the post and puts it back.
##
## Oval3D hands him over once his signal ends (start) and runs him each frame while u has
## "routine" (step); a score at his end while he is still at it puts the flags straight back
## (stop) so he can signal it. Real time, as his signals are: they are his, not the play's.

## How quickly he turns on the spot (radians a second: a pivot of the feet).
const TURN_RATE := 4.0
## The stowed sticks stand off the post's centre (the padding is 0.36 m round).
const POST_PAD := 0.375
## How far he walks from the post toward the middle to wave a goal.
const WAVE_OFF := 2.5
## After the furl he stands by the post before going back to his place.
const STAND_AFTER := 4.5
## How fast the cloth's stream answers the stick's speed, and the speed (m/s at the stick's tip)
## that streams it out flat.
const AIR_EASE := 6.0
const AIR_FULL := 4.0
## Below this (a walk's swing of the arm) the cloth still hangs.
const AIR_STILL := 1.2
## Its tip this high off the turf (m) and the cloth stands out, held aloft (2025 broadcasts).
const AIR_ALOFT := Vector2(1.9, 2.4)
## A flag taken from one hand by the other slides into its new fist over this long (the hands
## close on the sticks a fist's width apart).
const SETTLE := 0.25
## A frame longer than this (a hitch) is taken as this long: his routine never jumps ahead.
const DT_MAX := 0.1
## Back in a behind's wave to put the flag away (Oval3DCrew.BEHIND_FLAG, past its last swing, the
## flag coming down to the padding), blended in from where he is over BLEND_IN.
const BEHIND_PUT_BACK := 3.6
const BLEND_IN := 0.45


## His flags, stowed in the padding of one post at his end (each man his own post, as the
## broadcasts show either used), and where he stands to reach them, worked out from his own draw
## clip so his fist meets the sticks. Call once he is on the ground.
static func setup(oval: Node3D, u: Dictionary, end: float, rng_seed: int) -> void:
	var skel: Skeleton3D = u["skel"]
	var ap: AnimationPlayer = u["anim"]
	var node: Node3D = u["node"]
	var fl := Oval3DCrew.flags(skel, Oval3DCrew.glb_for(oval.player_glb))
	if fl.is_empty() or not ap.has_animation(Oval3DCrew.GOAL_WAVE):
		return
	# Which hand is nearer his post: the same at either end (the post on that side of him as he
	# faces the ground).
	var near := "r" if rng_seed % 2 == 0 else "l"
	var draw := Oval3DCrew.FLAGS_DRAW + near
	if not ap.has_animation(draw):
		return
	# His near fist on the stowed sticks, in his own frame, from the clip on this body.
	var held := (fl[near]["grip"] as Oval3DGrip).held_at(skel)
	ap.play(draw, 0.0)
	ap.seek(Oval3DCrew.DRAW_GRAB, true)
	var hand := _rel_node(node, skel) * skel.get_bone_global_pose(skel.find_bone("hand_" + near))
	ap.play("idle", 0.0)
	ap.seek(0.0, true)
	u["flags"] = fl
	u["flag"] = {"near": near, "end": 0.0,
			"a_rel": hand * held, "b_rel": hand * held * Transform3D(Basis.IDENTITY, Oval3DCrew.PAIR_GAP),
			"held": {"r": (fl["r"]["grip"] as Oval3DGrip).held_at(skel), "l": (fl["l"]["grip"] as Oval3DGrip).held_at(skel)},
			"furl": {"r": 0.0, "l": 0.0}, "air": {"r": 0.0, "l": 0.0}, "tip": {}, "settle": {}}
	set_end(oval, u, end)


## His flags at the post of the end he is at (the goal umpires change ends with the teams): where
## he stands to reach them, where he waves, and the flags put there.
static func set_end(oval: Node3D, u: Dictionary, end: float) -> void:
	if not u.has("flag") or end == 0.0:
		return
	var f: Dictionary = u["flag"]
	var fl: Dictionary = u["flags"]
	var node: Node3D = u["node"]
	var near := str(f["near"])
	f["end"] = end
	# At the post he faces the ground, the post on his near hand's side.
	var face := Vector3(-end, 0.0, 0.0)
	var right := face.cross(Vector3.UP)
	var post_z := absf(Oval3D.GOAL_GAP * 0.5) * signf(right.z) * (1.0 if near == "r" else -1.0)
	var yaw := atan2(face.x, face.z)
	var stand_basis := Basis(Vector3.UP, yaw).scaled(node.scale)
	# Where he stands: his fist's sticks against the padding, on the side facing the goal.
	var stick_at := Vector3(end * MatchMotion.GOAL_X, 0.0, post_z - signf(post_z) * POST_PAD)
	var off := stand_basis * (f["a_rel"] as Transform3D).origin
	var post_spot := Vector2(stick_at.x - off.x, stick_at.z - off.z)
	var stand := Transform3D(stand_basis, Vector3(post_spot.x, 0.0, post_spot.y))
	# Stowed: each flag's node in the ground's frame, where his fist will close on it.
	var stowed := {near: stand * (f["a_rel"] as Transform3D), _other(near): stand * (f["b_rel"] as Transform3D)}
	f["post"] = post_spot
	f["wave"] = post_spot + Vector2(0.0, -signf(post_z)) * WAVE_OFF
	f["yaw"] = yaw
	f["stowed"] = stowed
	u.erase("home")
	for s in ["r", "l"]:
		var n: Node3D = fl[s]["node"]
		if n.get_parent() == null or n.get_parent() == oval:
			if n.get_parent() == null:
				oval.add_child(n)
			n.transform = stowed[s]


static func _other(s: String) -> String:
	return "l" if s == "r" else "r"


## n's transform relative to its ancestor `to`.
static func _rel_node(to: Node, n: Node3D) -> Transform3D:
	var t := Transform3D.IDENTITY
	var at: Node = n
	while at != null and at != to:
		if at is Node3D:
			t = (at as Node3D).transform * t
		at = at.get_parent()
	return t


## His routine after a score's signal: `home` his place on the line. When the score came while
## he still had flags out from the last one, he finishes with those (holding()).
static func start(u: Dictionary, goal: bool, home: Vector2) -> void:
	if not u.has("flag"):
		return
	var f: Dictionary = u["flag"]
	var near := str(f["near"])
	var steps := []
	var held := holding(u)
	steps.append({"do": "walk", "to": f["post"], "clip": Oval3DCrew.WALK_FLAGS if held == 2 else Oval3DCrew.WALK})
	steps.append({"do": "turn", "yaw": f["yaw"]})
	if held == 2:
		steps.append({"do": "clip", "clip": Oval3DCrew.FLAGS_FURL + near})
	elif held == 1:
		steps.append({"do": "clip", "clip": Oval3DCrew.BEHIND_FLAG + near, "from": BEHIND_PUT_BACK})
	elif goal:
		steps.append({"do": "clip", "clip": Oval3DCrew.FLAGS_DRAW + near})
		steps.append({"do": "walk", "to": f["wave"], "clip": Oval3DCrew.WALK_FLAGS})
		steps.append({"do": "turn", "yaw": f["yaw"]})
		steps.append({"do": "clip", "clip": Oval3DCrew.GOAL_WAVE})
		steps.append({"do": "walk", "to": f["post"], "clip": Oval3DCrew.WALK_FLAGS})
		steps.append({"do": "turn", "yaw": f["yaw"]})
		steps.append({"do": "clip", "clip": Oval3DCrew.FLAGS_FURL + near})
	else:
		steps.append({"do": "clip", "clip": Oval3DCrew.BEHIND_FLAG + near})
	steps.append({"do": "stand", "for": STAND_AFTER})
	steps.append({"do": "walk", "to": home, "clip": Oval3DCrew.WALK})
	steps.append({"do": "turn", "yaw": f["yaw"]})
	var node: Node3D = u["node"]
	# Where he is and which way he faces are the routine's own: a goal's replay puts every man
	# back where he was for its length (Oval3DBroadcast), and he carries on from here after it.
	u["routine"] = {"steps": steps, "i": 0, "t": 0.0, "begun": false,
			"pos": Vector2(node.position.x, node.position.z), "rot": node.rotation.y}


## A new score at his end before he has finished: he leaves off to signal it, any flags he has
## out staying in his hands (start finishes with them).
static func stop(u: Dictionary) -> void:
	u.erase("routine")


## How many flags he has in his hands.
static func holding(u: Dictionary) -> int:
	if not u.has("flags"):
		return 0
	var fl: Dictionary = u["flags"]
	var n := 0
	for s in ["r", "l"]:
		var p := (fl[s]["node"] as Node3D).get_parent()
		if p == fl["r"]["on"] or p == fl["l"]["on"]:
			n += 1
	return n

## One frame of his routine. False once it is over (he is back on the line).
static func step(oval: Node3D, u: Dictionary, dt: float) -> bool:
	dt = clampf(dt, 0.0, DT_MAX)
	var r: Dictionary = u["routine"]
	var steps: Array = r["steps"]
	var ap: AnimationPlayer = u["anim"]
	var node: Node3D = u["node"]
	node.position = Vector3((r["pos"] as Vector2).x, 0.0, (r["pos"] as Vector2).y)
	node.rotation.y = float(r["rot"])
	var going := _step(oval, u, r, steps, ap, dt)
	r["pos"] = Vector2(node.position.x, node.position.z)
	r["rot"] = node.rotation.y
	return going


static func _step(oval: Node3D, u: Dictionary, r: Dictionary, steps: Array, ap: AnimationPlayer, dt: float) -> bool:
	while int(r["i"]) < steps.size():
		var s: Dictionary = steps[int(r["i"])]
		var first := not bool(r["begun"])
		r["begun"] = true
		var done := false
		match str(s["do"]):
			"walk":
				done = _walk(u, s, dt, first)
			"turn":
				done = _turn(u, float(s["yaw"]), dt, first)
			"clip":
				done = _clip(oval, u, str(s["clip"]), dt, first, float(s.get("from", 0.0)))
			"stand":
				if first:
					ap.play("idle", 0.3)
					r["t"] = 0.0
				r["t"] = float(r["t"]) + dt
				ap.advance(maxf(dt, 1e-4))
				done = float(r["t"]) >= float(s["for"])
		if not done:
			cloth(u, dt)
			return true
		r["i"] = int(r["i"]) + 1
		r["begun"] = false
		r["t"] = 0.0
		dt = 0.0
	u.erase("routine")
	cloth(u, dt)
	return false


static func _walk(u: Dictionary, s: Dictionary, dt: float, first: bool) -> bool:
	var node: Node3D = u["node"]
	var ap: AnimationPlayer = u["anim"]
	var at := Vector2(node.position.x, node.position.z)
	var to: Vector2 = s["to"]
	var gap := to - at
	if gap.length() < 0.03:
		node.position = Vector3(to.x, 0.0, to.y)
		return true
	var clip := str(s["clip"])
	if first or ap.current_animation != clip:
		ap.play(clip, 0.3)
	# Facing where he walks, turned on the spot first if he must turn far.
	var want := atan2(gap.x, gap.y)
	var off := absf(angle_difference(node.rotation.y, want))
	node.rotation.y = rotate_toward(node.rotation.y, want, TURN_RATE * dt)
	if off > 0.6:
		ap.advance(maxf(dt, 1e-4))
		return false
	var move := gap.limit_length(Oval3DCrew.WALK_SPEED * dt)
	at += move
	node.position = Vector3(at.x, 0.0, at.y)
	ap.advance(maxf(dt, 1e-4))
	return false


static func _turn(u: Dictionary, yaw: float, dt: float, first: bool) -> bool:
	var node: Node3D = u["node"]
	var ap: AnimationPlayer = u["anim"]
	var done := absf(angle_difference(node.rotation.y, yaw)) < 0.02
	if done:
		node.rotation.y = yaw
	else:
		node.rotation.y = rotate_toward(node.rotation.y, yaw, TURN_RATE * dt)
	# Stopped: back to his stand as he turns; with his flags, the wave's first pose (both
	# carried down by his sides) held.
	if _holding(u):
		if first or ap.current_animation != Oval3DCrew.GOAL_WAVE:
			ap.play(Oval3DCrew.GOAL_WAVE, 0.3)
		ap.seek(0.0, false)
	elif first or ap.current_animation != "idle":
		ap.play("idle", 0.3)
	ap.advance(maxf(dt, 1e-4))
	return done


static func _holding(u: Dictionary) -> bool:
	var fl: Dictionary = u["flags"]
	return (fl["r"]["grip"] as Oval3DGrip).active or (fl["l"]["grip"] as Oval3DGrip).active


static func _clip(oval: Node3D, u: Dictionary, clip: String, dt: float, first: bool, from := 0.0) -> bool:
	var ap: AnimationPlayer = u["anim"]
	var r: Dictionary = u["routine"]
	var f: Dictionary = u["flag"]
	var near := str(f["near"])
	var far := _other(near)
	if first:
		ap.play(clip, BLEND_IN if from > 0.0 else 0.2)
		ap.seek(from, true)
		r["t"] = from
	var before := float(r["t"])
	var t := before + dt
	r["t"] = t
	var crossed := func(at: float) -> bool: return before < at and t >= at
	var furl: Dictionary = f["furl"]
	if clip.begins_with(Oval3DCrew.FLAGS_DRAW):
		if crossed.call(Oval3DCrew.DRAW_GRAB):
			_hold(u, near, near, false)
			_hold(u, far, near, true)
		if crossed.call(Oval3DCrew.DRAW_TAKE):
			_hold(u, far, far, false)
		var o := _ramp(t, Oval3DCrew.DRAW_OPEN)
		if t >= Oval3DCrew.DRAW_OPEN.x:
			furl[near] = maxf(float(furl[near]), o)
			furl[far] = maxf(float(furl[far]), o)
	elif clip.begins_with(Oval3DCrew.FLAGS_FURL):
		if crossed.call(Oval3DCrew.FURL_GIVE):
			_hold(u, far, near, true)
		var w: Array = Oval3DCrew.FURL_WIND
		if t >= (w[0] as Vector2).x:
			furl[near] = minf(float(furl[near]), 1.0 - _ramp(t, w[0]))
		if t >= (w[1] as Vector2).x:
			furl[far] = minf(float(furl[far]), 1.0 - _ramp(t, w[1]))
		if crossed.call(Oval3DCrew.FURL_STOW):
			_stow(oval, u, near)
			_stow(oval, u, far)
	elif clip.begins_with(Oval3DCrew.BEHIND_FLAG):
		if crossed.call(Oval3DCrew.BEHIND_GRAB):
			_hold(u, near, near, false)
		if t >= Oval3DCrew.BEHIND_OPEN.x:
			furl[near] = maxf(float(furl[near]), _ramp(t, Oval3DCrew.BEHIND_OPEN))
		if crossed.call(Oval3DCrew.BEHIND_STOW):
			_stow(oval, u, near)
	if t >= ap.current_animation_length:
		return true
	ap.advance(maxf(t - before, 1e-4))
	return false


static func _ramp(t: float, span: Vector2) -> float:
	return smoothstep(span.x, span.y, t)


## Flag `which` into hand `hand`'s fist (beside the one already there when `pair`).
static func _hold(u: Dictionary, which: String, hand: String, pair: bool) -> void:
	var fl: Dictionary = u["flags"]
	var f: Dictionary = u["flag"]
	var n: Node3D = fl[which]["node"]
	var on: Node3D = fl[hand]["on"]
	var held: Transform3D = (f["held"] as Dictionary)[hand]
	if pair:
		held = held * Transform3D(Basis.IDENTITY, Oval3DCrew.PAIR_GAP)
	var was := n.global_transform if n.is_inside_tree() else Transform3D.IDENTITY
	var from_hand := n.get_parent() is BoneAttachment3D and n.get_parent() != on
	if n.get_parent() != on:
		if n.get_parent() != null:
			n.get_parent().remove_child(n)
		on.add_child(n)
	# (Out of a replay's hold on it, if one was showing it put away.)
	n.top_level = false
	n.transform = held
	if from_hand and on.is_inside_tree():
		# From the other hand: it slides into this fist from where it was.
		(f["settle"] as Dictionary)[which] = {"from": on.global_transform.affine_inverse() * was, "to": held, "t": 0.0}
	(fl[hand]["grip"] as Oval3DGrip).active = true
	if hand != which:
		(fl[which]["grip"] as Oval3DGrip).active = _in_hand(u, which)


## Whether hand s holds a flag.
static func _in_hand(u: Dictionary, s: String) -> bool:
	var fl: Dictionary = u["flags"]
	var on: Node3D = fl[s]["on"]
	for k in ["r", "l"]:
		if (fl[k]["node"] as Node3D).get_parent() == on:
			return true
	return false


## Flag `which` back in the padding where it is kept.
static func _stow(oval: Node3D, u: Dictionary, which: String) -> void:
	var fl: Dictionary = u["flags"]
	var f: Dictionary = u["flag"]
	var n: Node3D = fl[which]["node"]
	(f["settle"] as Dictionary).erase(which)
	if n.get_parent() != oval:
		if n.get_parent() != null:
			n.get_parent().remove_child(n)
		oval.add_child(n)
	n.top_level = false
	n.transform = (f["stowed"] as Dictionary)[which]
	for s in ["r", "l"]:
		(fl[s]["grip"] as Oval3DGrip).active = _in_hand(u, s)


## Each cloth as it is: furled or open, and streaming as fast as its stick moves (or held high
## aloft), hanging when it is still.
static func cloth(u: Dictionary, dt: float) -> void:
	if not u.has("flag"):
		return
	var fl: Dictionary = u["flags"]
	var f: Dictionary = u["flag"]
	var settle: Dictionary = f["settle"]
	for s in settle.keys():
		var e: Dictionary = settle[s]
		e["t"] = float(e["t"]) + dt
		var w := smoothstep(0.0, SETTLE, float(e["t"]))
		(fl[s]["node"] as Node3D).transform = (e["from"] as Transform3D).interpolate_with(e["to"], w)
		if w >= 1.0:
			settle.erase(s)
	for s in ["r", "l"]:
		var n: Node3D = fl[s]["node"]
		var m: ShaderMaterial = fl[s]["cloth"]
		m.set_shader_parameter("furl", float(f["furl"][s]))
		if not n.is_inside_tree():
			continue
		var tip := n.global_transform * Vector3(0.0, 0.5, 0.0)
		var tips: Dictionary = f["tip"]
		# Held up over his head it stands out in the breeze; low and still it hangs.
		var want := smoothstep(AIR_ALOFT.x, AIR_ALOFT.y, tip.y - (u["node"] as Node3D).global_position.y) * 0.7
		if dt > 0.0 and tips.has(s):
			var speed := tip.distance_to(tips[s]) / dt
			want = maxf(want, smoothstep(AIR_STILL, AIR_FULL, speed))
		tips[s] = tip
		var air: Dictionary = f["air"]
		if dt > 0.0:
			air[s] = lerpf(float(air[s]), want, clampf(dt * AIR_EASE, 0.0, 1.0))
		m.set_shader_parameter("air", float(air[s]))



## A goal's replay is on (Oval3DBroadcast): every man is put back where he was, before any flag
## came out, so a flag in his hands is drawn back in the padding, furled, for its length (live
## again: in_replay false, back in his hands as the routine has them).
static func in_replay(oval: Node3D, u: Dictionary, on: bool) -> void:
	if not u.has("flag"):
		return
	var fl: Dictionary = u["flags"]
	var f: Dictionary = u["flag"]
	for s in ["r", "l"]:
		var n: Node3D = fl[s]["node"]
		if n.get_parent() == oval:
			continue
		var m: ShaderMaterial = fl[s]["cloth"]
		if on:
			n.top_level = true
			n.global_transform = oval.global_transform * ((f["stowed"] as Dictionary)[s] as Transform3D)
			m.set_shader_parameter("furl", 0.0)
			m.set_shader_parameter("air", 0.0)
		elif n.top_level:
			n.top_level = false
			var settle: Dictionary = f["settle"]
			var hand := "r" if n.get_parent() == fl["r"]["on"] else "l"
			var held: Transform3D = (f["held"] as Dictionary)[hand]
			if hand != s:
				held = held * Transform3D(Basis.IDENTITY, Oval3DCrew.PAIR_GAP)
			n.transform = settle[s]["to"] if settle.has(s) else held
			m.set_shader_parameter("furl", float(f["furl"][s]))
