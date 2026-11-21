class_name MatchMotion
extends RefCounted
## Player and ball movement for the live match view. Presentation only: nothing
## here reads or writes MatchSim state.
##
## Units are metres and presentation seconds. Presentation time runs a little
## faster than real time (see MatchDirector.TEMPO), so speeds are a real
## player's scaled by that: a 30 km/h sprint (~8.5 m/s) is about 13 m/s here.
##
## Players are steered, not lerped: velocity changes are capped by acceleration
## and braking limits, so starts, stops and turns take time and paths curve.
## A token only reads a new goal after its own reaction delay, which keeps a
## team from moving as one rigid block.

## The standard oval's half-axes: MatchSim's own ground, whose goal line is at +-85 m
## (Ratings "goal_line"), a little inside the boundary.
const STD_HALF_LEN := 86.3
const STD_HALF_WID := 67.4
const STD_GOAL_X := 85.0
## How far the goal line sits inside the boundary at the middle of the goals.
const GOAL_IN := STD_HALF_LEN - STD_GOAL_X
## The ground this match is played on: its half-axes and goal line (use_field). Every
## ground plays at its own size (row 202 2b): the MCG long and wide, North Hobart small.
## The defaults are written out, not taken from the constants above: a static var set
## from an expression stays 0 when a tool runs with --script (VignetteGround.GOAL_Y).
static var HALF_LEN := 86.3
static var HALF_WID := 67.4
static var GOAL_X := 85.0


## Play on a ground whose boundary has these half-axes (metres); Vector2.ZERO is the
## standard oval.
static func use_field(half: Vector2) -> void:
	if half.x <= 0.0 or half.y <= 0.0:
		half = Vector2(STD_HALF_LEN, STD_HALF_WID)
	HALF_LEN = half.x
	HALF_WID = half.y
	# The standard oval's own goal line exactly, so every spot on it is as it always was (gx).
	GOAL_X = STD_GOAL_X if half.x == STD_HALF_LEN else half.x - GOAL_IN


## The standard oval's x (MatchSim's field position, a set-up spot) on this ground.
## Inside each 50 m arc the distance from goal is kept, so a 40 m set shot is 40 m out
## on every ground; the centre square keeps its own 25 m either side where the ground
## has room; between the two the ground takes up the difference. Identity on the
## standard oval. Monotonic, odd, and +-STD_GOAL_X lands on +-GOAL_X.
static func gx(x: float) -> float:
	if GOAL_X == STD_GOAL_X:
		return x
	var a := absf(x)
	var arc := GOAL_X - 50.0                      # this ground's 50 m line, from the centre
	var sq := minf(25.0, arc * 25.0 / 35.0)       # the centre square's edge where it fits
	var out: float
	if a >= 35.0:
		out = GOAL_X - (STD_GOAL_X - a)
	elif a >= 25.0:
		out = sq + (a - 25.0) / 10.0 * (arc - sq)
	else:
		out = a / 25.0 * sq
	return out if x >= 0.0 else -out


## This ground's x back on the standard oval: the inverse of gx.
static func sx(x: float) -> float:
	if GOAL_X == STD_GOAL_X:
		return x
	var a := absf(x)
	var arc := GOAL_X - 50.0
	var sq := minf(25.0, arc * 25.0 / 35.0)
	var out: float
	if a >= arc:
		out = STD_GOAL_X - (GOAL_X - a)
	elif a >= sq:
		out = 25.0 + (a - sq) / maxf(arc - sq, 0.001) * 10.0
	else:
		out = a / maxf(sq, 0.001) * 25.0
	return out if x >= 0.0 else -out


## How much wider (or narrower) this ground is than the standard oval: a spot set by
## the width of the ground (a wing, a flank, a pocket) moves out or in by this.
static func wy() -> float:
	return HALF_WID / STD_HALF_WID


## A spot on the standard oval (a slot, a set-up) on this ground: x by gx, y by wy.
static func on_ground(v: Vector2) -> Vector2:
	return Vector2(gx(v.x), v.y * wy())

const JOG_SHARE := 0.52      # structural running is a jog, not a sprint
const ACCEL := 14.0          # m/s^2 speeding up
const BRAKE := 20.0          # m/s^2 slowing down or turning hard
const ARRIVE_STOP := 0.35    # inside this, a token settles
const MIN_SEP := 1.5         # bodies do not overlap more than this
## Motion limits that hold for every shape and every call (the motion critic,
## 2026-10-18: one-frame snaps of 4 to 10 m and a crash at twice a sprint).
## SPRINT caps how far any token moves in a step, whatever asks it to move: a
## new goal, a set-up's quicker reset, Throw numbers at it's legs, or bodies
## easing apart. It is the fastest carry rating's top speed (14.6) rounded up.
## WALK is the pace bodies in a pile ease apart at: never an instant push.
const SPRINT := 15.0
const WALK := 2.5
## Bodies steer round each other instead of passing through (2026-11-16: a
## running man went straight through another, 1,361 times in three matches).
## Two proven crowd methods, as in Weiss et al. 2017 ("Position-Based
## Multi-Agent Dynamics for Real-Time Crowd Simulation"):
## - far off, anticipation: each body feels the time-to-collision force of
##   Karamouzas, Skinner and Guy 2014 ("Universal Power Law Governing
##   Pedestrian Interactions"), E = k / tau^2 * exp(-tau / tau0), so it turns
##   or checks before a collision rather than at it (avoid);
## - at contact, a limit: two bodies may not close inside BODY of each other
##   (hold_apart). It only takes back the part of a step that closed the gap,
##   so it never pushes anyone and never adds motion.
## Contact that is meant (a tackle, a smother, a pack, a ruck contest, a
## marking contest) is left to happen: the director names those bodies, which
## do not avoid each other and may close to TOUCH.
const BODY := 0.75           # hip to hip at contact: about one body wide
const TOUCH := 0.45          # ...and when the play means them to touch: chest to chest, never one body inside another
const AVOID_K := 1.5         # the power law's scale (Karamouzas et al.: 1.5)
const AVOID_TAU0 := 1.0      # s: collisions further off than this hardly count
const AVOID_SEE := 9.0       # m: bodies further off are not considered
const AVOID_MAX := BRAKE     # m/s^2: avoiding turns no harder than braking


## A new token at `pos`. `top` is its sprint speed; `reaction` its read delay.
static func make_token(pos: Vector2, top: float, reaction: float) -> Dictionary:
	return {
		"pos": pos, "vel": Vector2.ZERO, "goal": pos, "pending": pos,
		"react_left": 0.0, "reaction": reaction, "top": top,
		"urgency": 0.0, "pending_urgency": 0.0, "down": 0.0, "air": 0.0,
		# Dead-ball repositioning pace (set-ups only): scales speed and
		# acceleration so a reset that takes half a minute in a real game
		# fits a few seconds. 1.0 in play.
		"reset": 1.0,
	}


## Ask a token to head for `goal`. The token keeps its current goal until its
## reaction delay has passed; `immediate` skips the delay (a set play the
## player already knows, such as walking back for a centre bounce).
static func set_goal(t: Dictionary, goal: Vector2, urgency: float, immediate := false) -> void:
	goal = clamp_to_oval(goal, 2.0)
	if immediate:
		t["goal"] = goal
		t["pending"] = goal
		t["urgency"] = urgency
		t["pending_urgency"] = urgency
		t["react_left"] = 0.0
		return
	t["pending"] = goal
	t["pending_urgency"] = urgency
	if float(t["react_left"]) > 0.0:
		return  # still reading the play; the latest goal applies when it ends
	if (t["goal"] as Vector2).distance_to(goal) > 1.5:
		# A real change of plan waits for the read; small corrections (tracking
		# a moving player) apply at once.
		t["react_left"] = float(t["reaction"])
	else:
		t["goal"] = goal
		t["urgency"] = urgency


## One integration step of `dt` seconds.
static func step(t: Dictionary, dt: float) -> void:
	if float(t["react_left"]) > 0.0:
		t["react_left"] = float(t["react_left"]) - dt
		if float(t["react_left"]) <= 0.0:
			t["goal"] = t["pending"]
			t["urgency"] = t["pending_urgency"]
	if float(t["air"]) > 0.0:
		t["air"] = maxf(0.0, float(t["air"]) - dt)
	var pos: Vector2 = t["pos"]
	var vel: Vector2 = t["vel"]
	var desired := Vector2.ZERO
	if float(t["down"]) > 0.0:
		t["down"] = maxf(0.0, float(t["down"]) - dt)
	else:
		var to: Vector2 = (t["goal"] as Vector2) - pos
		var d := to.length()
		var top: float = float(t["top"]) * float(t.get("reset", 1.0)) \
				* lerpf(JOG_SHARE, 1.0, clampf(float(t["urgency"]), 0.0, 1.0))
		if t.has("cap"):
			top = minf(top, float(t["cap"]))   # held to a set pace (a scoop's own run)
		if d > ARRIVE_STOP:
			# Arrive: the fastest speed from which the token can still stop
			# at the goal, so it eases in instead of overshooting.
			var speed := minf(top, sqrt(2.0 * BRAKE * float(t.get("reset", 1.0)) * 0.55
					* maxf(0.0, d - ARRIVE_STOP * 0.5)))
			desired = to / d * speed
	var dv := desired - vel
	var limit := (ACCEL if desired.length_squared() > vel.length_squared()
			and dv.dot(vel) >= 0.0 else BRAKE) * float(t.get("reset", 1.0)) * dt
	vel += dv.limit_length(limit)
	# Steering round the bodies ahead (avoid), within the braking limit.
	vel += (t.get("avoid", Vector2.ZERO) as Vector2) * dt
	vel = vel.limit_length(SPRINT)
	vel = _fence_brake(pos, vel, float(t.get("reset", 1.0)))
	pos += vel * dt
	var clamped := clamp_to_oval(pos, 1.0)
	if clamped != pos:
		# On the fence he slides along it: only the speed into it goes
		# (row 201 gap 13: halving the whole speed each step was a dead stop).
		var n := fence_normal(clamped)
		vel -= n * maxf(0.0, vel.dot(n))
		pos = clamped
	t["pos"] = pos
	t["vel"] = vel


## Ease overlapping bodies apart over `dt` seconds (positions only, half each
## way): each body moves at most WALK * dt, so a pile parts at a walk and
## never jumps.
static func separate(tokens: Array, dt: float) -> void:
	var n := tokens.size()
	var pos := PackedVector2Array()
	pos.resize(n)
	for i in range(n):
		pos[i] = tokens[i]["pos"]
	var push := PackedVector2Array()
	push.resize(n)
	var any := false
	for i in range(n):
		var pa := pos[i]
		for j in range(i + 1, n):
			var d := pos[j] - pa
			if absf(d.x) >= MIN_SEP or absf(d.y) >= MIN_SEP:
				continue
			var l := d.length()
			if l >= MIN_SEP:
				continue
			# Two on the very same spot part along a line of their own.
			var u := d / l if l > 0.001 else Vector2.RIGHT.rotated(float(i * 7 + j))
			var half := u * (MIN_SEP - l) * 0.5
			push[i] -= half
			push[j] += half
			any = true
	if not any:
		return
	var most := WALK * dt
	for i in range(n):
		if push[i] != Vector2.ZERO:
			tokens[i]["pos"] = pos[i] + push[i].limit_length(most)


## True when tokens `i` and `j` are meant to touch: both are in `meant` (ids).
static func _meant(meant: Dictionary, i: int, j: int) -> bool:
	return meant.has(i) and meant.has(j)


## How much a token gives way to another (Weiss et al. 2017 weight each body's
## share of a constraint by its inverse mass): 1 for a man free to check or turn,
## 0 for a man the play holds to a set pace ("cap", a scoop's run), who keeps
## his line while the man in his way gives way for both of them.
static func _give(t: Dictionary) -> float:
	return 0.0 if t.has("cap") else 1.0


## Set each token's "avoid" (an acceleration, read by step) from the
## time-to-collision power law (Karamouzas, Skinner and Guy 2014; their
## reference force, with m = 2): the sooner two bodies on their present
## courses would come within BODY, the harder each turns or checks, the
## force pointing along the miss that is quickest to widen. A body on the deck
## does not steer, but the others still go round it. Pairs in `meant` (ids)
## do not avoid each other.
static func avoid(tokens: Array, meant: Dictionary = {}) -> void:
	var n := tokens.size()
	var pos := PackedVector2Array()
	var vel := PackedVector2Array()
	pos.resize(n)
	vel.resize(n)
	var force := PackedVector2Array()
	force.resize(n)
	var give := PackedFloat32Array()
	give.resize(n)
	for i in range(n):
		pos[i] = tokens[i]["pos"]
		vel[i] = tokens[i]["vel"]
		give[i] = _give(tokens[i])
	var rr := BODY * BODY
	for i in range(n):
		var pa := pos[i]
		for j in range(i + 1, n):
			var w := pos[j] - pa
			if absf(w.x) >= AVOID_SEE or absf(w.y) >= AVOID_SEE:
				continue
			if _meant(meant, i, j) or give[i] + give[j] <= 0.0:
				continue
			var v := vel[i] - vel[j]
			var a := v.dot(v)
			if a < 0.0001:
				continue
			var b := w.dot(v)
			var c := w.dot(w) - rr
			if c <= 0.0 or b <= 0.0:
				continue   # already touching (hold_apart's job), or moving apart
			var disc := b * b - a * c
			if disc <= 0.0:
				continue   # on these courses they miss
			disc = sqrt(disc)
			var tau := (b - disc) / a
			if tau <= 0.0 or tau > AVOID_TAU0 * 4.0:
				continue
			# -dE/dx for i (and the opposite for j), as in the reference code.
			var f := -AVOID_K * exp(-tau / AVOID_TAU0) * (v - (v * b - w * a) / disc) \
					/ (a * tau * tau) * (2.0 / tau + 1.0 / AVOID_TAU0)
			# Shared as the reference code shares it (each gets f), unless one keeps his line.
			var share := 2.0 / (give[i] + give[j])
			force[i] += f * give[i] * share
			force[j] -= f * give[j] * share
	for i in range(n):
		var t: Dictionary = tokens[i]
		t["avoid"] = Vector2.ZERO if float(t["down"]) > 0.0 else force[i].limit_length(AVOID_MAX)


## The contact limit: after a step, two bodies that closed inside BODY of each
## other give back the part of their moves that closed it (each in proportion
## to how much of the closing was his), so neither passes through the other.
## Only the closing part goes: a runner slides round the man in his way. Moves
## only shrink, so the SPRINT and WALK limits still hold. Bodies already
## inside BODY that are not closing are left to separate. `from` holds each
## token's position before the step; pairs in `meant` (ids) may close to TOUCH.
static func hold_apart(tokens: Array, from: Array, meant: Dictionary = {}) -> void:
	var n := tokens.size()
	var pos := PackedVector2Array()
	pos.resize(n)
	var give := PackedFloat32Array()
	give.resize(n)
	for i in range(n):
		pos[i] = tokens[i]["pos"]
		give[i] = _give(tokens[i])
	for pass_i in range(3):
		var any := false
		for i in range(n):
			var p1 := pos[i]
			for j in range(i + 1, n):
				var p2 := pos[j]
				var d := p2 - p1
				if absf(d.x) >= BODY or absf(d.y) >= BODY:
					continue
				var l := d.length()
				var lim := TOUCH if _meant(meant, i, j) else BODY
				if l >= lim:
					continue
				var was: Vector2 = (from[j] as Vector2) - (from[i] as Vector2)
				var lw := was.length()
				if l >= lw - 0.0001:
					continue   # not closing
				var u := d / l if l > 0.001 else (was / lw if lw > 0.001 else Vector2.RIGHT)
				var in_i := maxf(0.0, (p1 - (from[i] as Vector2)).dot(u))
				var in_j := maxf(0.0, -(p2 - (from[j] as Vector2)).dot(u))
				var tot := in_i + in_j
				if tot < 0.00001:
					continue
				var back := minf(minf(lim, lw) - l, tot)
				# Each gives back his own closing, weighted by how much he gives way; a man
				# who keeps his line gives back only what the other cannot.
				var gi := in_i * give[i]
				var gj := in_j * give[j]
				var take_j := minf(back * gj / maxf(gi + gj, 0.00001), in_j)
				var take_i := minf(back - take_j, in_i)
				take_j = minf(back - take_i, in_j)
				in_i = take_i
				in_j = take_j
				p1 -= u * take_i
				pos[i] = p1
				pos[j] = p2 + u * take_j
				tokens[i]["pos"] = p1
				tokens[j]["pos"] = pos[j]
				# Their closing speed goes too (only the closing part).
				var vi: Vector2 = tokens[i]["vel"]
				var vj: Vector2 = tokens[j]["vel"]
				if in_i > 0.0:
					tokens[i]["vel"] = vi - u * maxf(0.0, vi.dot(u))
				if in_j > 0.0:
					tokens[j]["vel"] = vj - u * minf(0.0, vj.dot(u))
				any = true
		if not any:
			return


## Hold a token's move this step to SPRINT * dt from where it started (`from`),
## whatever moved it: steering, easing apart, the oval's edge.
static func limit_step(t: Dictionary, from: Vector2, dt: float) -> void:
	var moved: Vector2 = (t["pos"] as Vector2) - from
	var most := SPRINT * dt
	if moved.length_squared() > most * most:
		t["pos"] = from + moved.limit_length(most)


## Seconds a token needs to reach `p` from rest-ish, for flight timing.
static func eta(t: Dictionary, p: Vector2) -> float:
	var d := maxf(0.0, (t["pos"] as Vector2).distance_to(p) - 1.0)
	var top := float(t["top"])
	# Time lost getting up to speed from the current velocity.
	var ramp := maxf(0.0, top - (t["vel"] as Vector2).length()) / ACCEL * 0.5
	return float(t["react_left"]) + ramp + d / top


static func inside_oval(p: Vector2, margin := 0.0) -> bool:
	var ax := HALF_LEN - margin
	var ay := HALF_WID - margin
	return (p.x * p.x) / (ax * ax) + (p.y * p.y) / (ay * ay) <= 1.0


## The outward normal of the fence's ellipse nearest `p`.
static func fence_normal(p: Vector2) -> Vector2:
	var n := Vector2(p.x / (HALF_LEN * HALF_LEN), p.y / (HALF_WID * HALF_WID))
	return n.normalized() if n.length_squared() > 0.0 else Vector2.RIGHT


## A man running at the fence slows within his braking limit so he pulls up
## at it (row 201 gap 13), keeping his speed along it. `vel` is limited to the
## speed from which he can still stop before the 1 m margin.
const FENCE_LOOK := 12.0
static func _fence_brake(pos: Vector2, vel: Vector2, reset: float) -> Vector2:
	var n := fence_normal(pos)
	var out := vel.dot(n)
	if out <= 0.0:
		return vel
	# Distance to the fence (less the margin) along the normal, near enough for an ellipse this round.
	var k := sqrt((pos.x * pos.x) / ((HALF_LEN - 1.0) * (HALF_LEN - 1.0))
			+ (pos.y * pos.y) / ((HALF_WID - 1.0) * (HALF_WID - 1.0)))
	var gap := (1.0 - k) * pos.length() / maxf(k, 0.001)
	if gap > FENCE_LOOK:
		return vel
	var top := sqrt(2.0 * BRAKE * reset * maxf(0.0, gap))
	return vel - n * maxf(0.0, out - top) if out > top else vel


## Pull `p` back inside the oval shrunk by `margin` metres.
static func clamp_to_oval(p: Vector2, margin := 0.0) -> Vector2:
	var ax := HALF_LEN - margin
	var ay := HALF_WID - margin
	var k := (p.x * p.x) / (ax * ax) + (p.y * p.y) / (ay * ay)
	if k <= 1.0:
		return p
	return p / sqrt(k)
