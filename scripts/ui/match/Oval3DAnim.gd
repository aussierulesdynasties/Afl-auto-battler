class_name Oval3DAnim
extends RefCounted
## The 3D oval's animation controller (row 198, owned by the animation session; Oval3D.gd only
## calls frame(), step() and event()). Picks each player's clip, facing and rate from his token
## and the ball, and advances his AnimationPlayer by dt: jog / idle / carry, and the two-man
## tackle clips (row 197).

## The run loop's own pace (m/s at rate 1) is measured off the loop itself, from how fast its
## planted foot travels back under the hips (loop_speed): each body's loop has its own stride
## (the MetaHuman's covers 5.40 m/s, the old body's 5.73), and a guessed constant skated them.
const JOG_SPEED := Oval3D.LOOP_SPEED   # used only when a loop has no foot on the ground to read
## Everything below is in drawn metres a second: how fast his node really moves across the
## turf this frame (the director's tokens run on their own clock, MatchDirector.TEMPO times
## slower than the picture, so a token's vel is not the pace the legs must match).
const RUN_FROM := 2.0          # m/s drawn: slower than this he stands (and shuffles his feet)
const RATE_MIN := 0.38         # the slowest the run loop plays, a jog a little under RUN_FROM
## The fastest. The picture runs MatchDirector.TEMPO times the movement clock (rule 2.49), so a
## man at a real 9 m/s is drawn at about 15: the loop plays fast enough to keep its feet under
## him, as footage played fast does, up to this; past it the planted feet hold the difference.
const RATE_MAX := 3.4
const PACE_FOLLOW := 0.08      # s: the drawn pace is smoothed over about this long
const JUMP := 20.0             # m/s: a drawn move faster than this is a re-placement, not running
const STOP_HOLD := 0.2         # s: he must be that slow this long to stand; a shorter check is part of the run
## A man closing on the ball carrier who slows as he gets there is setting himself for the
## tackle, not stopping: he keeps running this much longer (the take starts well inside it).
## Director 2026-11-22: "the tackler is standing by idly waiting for the tackle".
const CLOSE_IN := 6.0          # m from the carrier
const CLOSE_HOLD := 0.6        # s
const TURN := 9.0              # rad/s (about 520 degrees): the fastest he turns, a footballer's pivot
## Running, he changes direction off a planted foot: the body swings round quickly while a foot
## is held on the turf (_plant keeps that foot where and how it landed) and hardly at all in the
## air between strides, so a cut reads as plant-and-go, not a spin on the spot.
const TURN_PLANTED := 24.0     # rad/s with a foot held down
const TURN_AIR := 12.0          # rad/s with both feet off the turf
## The slow gaits (Oval3D.GAITS_GLB, motion capture). Below the run a man off the ball walks,
## not a slow-motion jog (the run loop played at a third of its pace, about a quarter of every
## match measured 2026-11-27, tools/visual/measure_oval3d_gaits.gd). Moving away from the ball or
## across it at a walking or jogging pace, he keeps facing it: a backpedal or a side-step, the
## body turned so the clip's own direction of travel is exactly his, the head on the ball.
## Faster than a gait's top he turns and runs. Paces are drawn m/s (the picture's), as RUN_FROM.
const GAITS := ClipLimits.GAITS
const WALK_FROM := 0.6         # m/s drawn: slower than this he stands (and shuffles his feet)
const WALK_TO := 2.0           # the walk's top (RUN_FROM: the run takes over)
const BACKSTEP_TO := 1.4       # walking backwards up to this, then the backpedal
const BACK_TO := 2.6           # the backpedal's top; faster, he turns and runs
const SHUFFLE_TO := 1.2        # side-stepping up to this, then the side-run
const SIDE_TO := 3.2           # the side-run's top
const BACK_FROM := deg_to_rad(125.0)   # moving this far off the ball's way: backwards
const SIDE_FROM := deg_to_rad(60.0)    # this far: side-on
const GAIT_STAY := 0.1         # a gait is kept until its edge is passed by this share (no flicker)
const GAIT_TURN := deg_to_rad(20.0)    # and an angle edge by this
const GAIT_HOLD := 0.6         # s: the least he stays in a moving loop before changing to another
## The way each gait carries him, against the way he faces, as a turn of his yaw (+ to his left).
const GAIT_WAY := {"walk": 0.0, "backstep": PI, "backpedal": PI, "shuffle_l": PI / 2.0,
		"shuffle_r": -PI / 2.0, "side_run_l": PI / 2.0, "side_run_r": -PI / 2.0}
## Eyes on the ball (plan §2.6): the neck takes part of the turn and the head the rest, inside a
## real person's range (about 80 degrees each way, 35 up or down), so nobody turns like an owl.
## The carrier looks where he runs, not at the ball in his hands.
const LOOK := [["neck_01", 35.0, 20.0, 0.5], ["head", 45.0, 25.0, 1.0]]  # bone, yaw, pitch, influence
const LOOK_FOLLOW := 8.0       # 1/s: how fast the eyes catch a moving ball
## A man lying in a take is all of him on the turf, not only his hips: these bones, where
## they are near the ground, are handed to the director so runners keep off him
## (MatchDirector.lying_spots, MatchMotion.keep_off).
const BODY_BONES := ["pelvis", "head", "hand_l", "hand_r", "calf_l", "calf_r", "foot_l", "foot_r"]
const SIDESTEP := 6.0           # m/s: the fastest he is drawn stepping round a man lying down
const LIE_HIGH := 0.7          # m: a bone lower than this is lying on the turf
const BALL_R := 0.09          # m: the ball on the turf (Oval3D.BALL_R)

## Tackles (row 197). Each pair is one motion-capture take of two men, tackler and tacklee,
## sharing an origin, a clock and a length (tackle_pairs.json: contact_s is where the arms
## meet). Both men join the take at the point of its run-in where its tackler is as far from
## its tacklee as ours is (at least LEAD before the contact), the tacklee anchored where he
## stands, the take turned about him so its tackler comes from where ours is.
const PAIRS := "res://assets/oval3d/tackle_pairs.json"
const LEAD := 0.3              # clip s: the run-in starts at least this long before the contact
## m: how much further out than a take's own run-in its clip may start.
const RUN_IN_SLACK := 3.0
const CHASE_LEAD := 0.12       # s: the most of a take a chase-down plays before its contact
## The takes were captured standing: their tacklee waits for the hit and their tackler walks in.
## Joined by a man running flat out, the take stopped him dead (a 15 m/s carrier stood still for
## the 0.4 s before the arms met). A chase-down joins the take at the hit instead, and both men
## carry the carrier's run into the fall: the whole take slides along his line, its speed dying
## away over SLIDE_T (bodies driven to the turf, as a run-down tackle looks on the broadcast).
const SLIDE_T := 0.8           # s: the run-down's momentum spent
const SLIDE_MAX := 16.0        # m/s: the most of the carrier's drawn pace carried into it
const LEAD_MIN := 0.12         # the least run-in, when the tackle comes without warning
const LEAD_RATE := 1.5         # fastest the run-in plays to fit a short warning
const SLOW := 0.6              # slowest it plays while the contact is still to come
const CATCH_UP := 2.0          # fastest it plays when the contact has come first
const HURRY := 2.0             # how fast the get-up plays once the play has moved on
## Clip s from the arms meeting to the take's up_s: a tackled man is back on his feet 1.5 s
## after the tackle (director, 2026-11-17: "1.5 would probably be the sweet spot"), so the
## clip's own 2.7-3.1 s from contact to standing plays faster to fit (MatchDirector.TAKE_UP
## lets him move from then).
const UP_IN := 1.5
const UP_LATE := 0.25           # s: the get-up never squeezed into less than this
## The pair is slid, as one, toward where the director has the two men: the clip's own
## travel (a fall carried on, a get-up stepping off) left the picture metres off the play
## (3D bug bash, 2026-11-23: 5-10 m). It follows over about FOLLOW_S, never faster than SLIDE.
## It turns, too, about the middle of the two, so the line from tackler to tackled runs the
## way the director has it (TURN_S, never faster than SWING).
const FOLLOW_S := 0.05
const SLIDE := 12.0            # m/s, on their feet (the run-in, the standing tail)
const TURN_S := 0.12
const SWING := 2.0             # rad/s, on their feet
## Down on the turf, between the contact and up_s, a slide reads as skating: it creeps.
const SLIDE_DOWN := 3.0        # m/s
const SWING_DOWN := 1.2        # rad/s
const UP_EARLY := 0.6           # clip s: this short of up_s he is standing enough to go
const GO_IN := 0.3             # s
const FAR := 5.0               # m: his token this far from him = the play has moved on
const CLOSE_EARLY := 0.8       # s: a slowing tackler's take may start this much before its usual lead
const MOVE_OFF := 0.3          # m/s: his token moving this fast = the play wants him (a take ends at up_s)
const KNOCK_UP := 0.2           # s of a scoop's clip past the touch before a ball off his hands ends it
const KNOCK_OFF := 1.0          # m: how far off him that ball has to be by then
const BLEND := 0.2             # s: the pose he was in eases into the clip (and the clip out)
const GAP_CLOSE := 4.0         # m/s: after a tackle he runs back to his spot, at least this fast
const GAP_MAX := 9.0           # m/s: and at most this fast
const APART := 0.8             # m: on that run his hips stay this far from the man he tackled (or who tackled him)
const REACH := 1.6             # m: MatchDirector's chase ends this close (its "chase" phase)
const STEP := 1.0 / 30.0       # s: the takes' frame
const FOOT_DOWN := 0.03        # m: a foot this close to its lowest in a loop is on the ground
## Planted feet (real footage never skates): a foot that comes down on the turf stays where it
## came down until the clip lifts it, the leg bending to keep it there (a two-bone reach of the
## thigh and calf, the sole kept as it landed). It lets go if the body has gone too far from it.
## A man standing or shuffling keeps both feet down and steps one across when his body has
## drifted off it, so a stand that turns to the ball or creeps a metre does it in steps.
const LET_GO := 0.06           # s: a lifted foot hands back to the clip over this long
const PULL_RUN := 0.45         # m: running, a planted foot is dragged rather than held further than this from where the clip has it
const PULL_STAND := 0.2        # m: standing, a foot this far off its place steps across
const STEP_TIME := 0.22        # s: one shuffle step
const STEP_LIFT := 0.06        # m: how high the foot comes off the turf in that step
const LEGS := [["thigh_l", "calf_l", "foot_l", "ball_l"], ["thigh_r", "calf_r", "foot_r", "ball_r"]]

## Kicks, handballs and marks (row 198): the motion-capture clips of each, played so that the
## frame where boot or fist meets the ball, or the ball meets his hands, lands on the director's
## touch (clip_moments.json, read off each clip by tools/oval3d/clip_markers.py). The clip starts
## that long ahead of the touch, while he still holds the ball (MatchDirector.dispose_due) or
## while it is still in the air to him (catch_due), and its rate steers the contact frame onto
## the touch as the director's estimate firms up.
const MOMENTS := "res://assets/oval3d/clip_moments.json"
const MOVE_RATE_MIN := 0.6     # slowest a kick, handball or mark plays while its touch is coming
const MOVE_RATE_MAX := 1.6     # fastest
const GRAVITY := 9.8           # m/s^2: the dropped ball falls to the boot
const ON_BOOT := 0.09          # m: the ball's centre above the toe bone at contact
const ON_PALM := 0.08          # m: a handball sits this far above the palm that holds it
## A kicker lets the ball go from one hand, the kick side's, not from between both: in the run-in
## his other arm swings up and away (palm gap ~1 m in every kick clip, measured 2026-11-22) while
## the kick-side hand guides the ball down to about hip height (0.87-0.92 m) and drops it. As the
## palms part from HELD_GAP to FREE_GAP the ball goes over to the kick-side palm.
const HELD_GAP := 0.32         # m: palms closer than this hold it between them
const FREE_GAP := 0.55         # m: palms this far apart: it is on the kick-side palm alone
## Its long axis, measured off the broadcast footage 2026-11-22: in the guiding hand in the run-in
## it leans ~42 deg off the flat, pointing the way he runs (kick_on_run_03); as it drops it is
## near upright, 0-10 deg off the vertical (drop_punt_02 side-on), point down to the boot.
const GUIDE_TILT := deg_to_rad(42.0)
const DROP_TILT := deg_to_rad(82.0)
const CATCH_EASE := 0.12       # s of clip before a mark's contact that the ball runs into his hands
## The director's touch can come before the clip's contact (its estimate of the hold was long, or
## it gave no warning at all). The ball then stays on his palm or falls to his boot a moment
## longer while the clip hurries to the contact (launch_pending), never leaving from his hands:
## at most this much clip time is left to play (any more is cut, eased from the pose he was in).
const CATCH_UP_MAX := 0.3
const HOLD_SHORT := 0.02      # clip s short of the contact a move waits at for a late touch
const CAUGHT_MAX := 2.0       # s a mark taken ahead of the director's possession is kept, at most

var director: MatchDirector
var players: Array
## One record per tackle drawn: who, victim, pair, start_t, event_t, hit_t (the clock when the
## clip's arms meet), lead (clip s of run-in), turn_deg (the tacklee's turn to face it),
## warp_m / warp_deg (the tackler's correction over the run-in), at (the director's tackle
## spot), contact (where the clip's arms meet), root (the tacklee's hips then). For the
## capture tool and the tests.
var tackles: Array = []
var _targets: Array = []       # per player: the Node3D his look-at modifiers aim at
var _looks: Array = []         # per player: his LookAtModifier3D nodes
var _pairs := {}               # take name -> its tackle_pairs.json entry
var _clock := 0.0              # s of animation time
var _rig := Transform3D()      # a figure's node -> its skeleton
var _pelvis := -1
var _body := PackedInt32Array()  # BODY_BONES' indices
var _hips := {}                # animation name -> [pelvis position track, rotation track]
var _in: Array = []            # per player: the pair he is in, {} for none
var _blend: Array = []         # per player: the pose he is easing out of, {} for none
var _back: Array = []          # per player: where a finished pair left him (INF: nowhere)
var _face: Array = []          # per player: the way his hips faced when that pair finished
var _gap: Array = []           # per player: his drawn spot minus his token's, closing
var _mate: Array = []          # per player: the other man of the take he is running back from, -1 for none
var _rate: Array = []          # per player: the rate his running clip played at last
var _still: Array = []         # per player: s he has been slower than RUN_FROM
var _takes := {}               # take name -> {dist: hips apart, foot: planted foot} per STEP
var _tracks := {}              # animation name -> {bone: rotation track}, "hips": position track
var _once: Array = []          # per player: the scoop he is in, {anim, t, t0, touch, end, yaw, at, off}, {} for none
var _was: Array = []           # per player: where his node stood last frame (INF: nowhere yet)
var _pace: Array = []          # per player: his drawn velocity on the turf, smoothed (m/s)
var _loop_speed := {}          # loop name -> m/s its planted foot covers at rate 1
var _lift := {}                # loop name -> the share of its cycle at which the left foot lifts
var _gait_t: Array = []        # per player: s in his current clip
var _floor := [INF, INF]       # each ball bone's lowest in the run loop, in the figure's space
var _legs: Array = []          # bone indices [thigh, calf, foot, ball] per leg, [] if the rig has none
## per player, per foot: {at: world point the ball bone is held at, yaw: node yaw when it came
## down, w: 1 held .. 0 the clip's, step: s into a shuffle step (-1 none), from: where it began}
var _feet: Array = []
var _launching := -1           # the man whose clip still owes the ball its contact (launch_pending)
var _moments := {}             # clip -> clip_moments.json entry, plus what _read_moments measures


func _init(p_director: MatchDirector, p_players: Array) -> void:
	director = p_director
	players = p_players
	for p in players:
		_add_look(p)
		_in.append({})
		_blend.append({})
		_back.append(Vector2.INF)
		_face.append(0.0)
		_still.append(0.0)
		_gap.append(Vector2.ZERO)
		_mate.append(-1)
		_rate.append(1.0)
		_once.append({})
		_was.append(Vector2.INF)
		_pace.append(Vector2.ZERO)
		_gait_t.append(0.0)
		_feet.append([{}, {}])
	var res = load(PAIRS)
	if res is JSON:
		_pairs = (res as JSON).data
	if players.size() > 0:
		var p: Dictionary = players[0]
		var skel: Skeleton3D = p["skel"]
		_pelvis = skel.find_bone("pelvis")
		for b in BODY_BONES:
			var bi := skel.find_bone(b)
			if bi >= 0:
				_body.append(bi)
		var n: Node = skel
		while n != null and n != p["node"]:
			_rig = (n as Node3D).transform * _rig
			n = n.get_parent()
		_read_takes(p)
		_read_moments(p)
		for name in ["jog", "carry"] + GAITS:
			_loop_speed[name] = _measure_loop(p, name)
		var skel0: Skeleton3D = p["skel"]
		for leg in LEGS:
			var ids := []
			for b in leg:
				ids.append(skel0.find_bone(b))
			if ids.has(-1):
				_legs = []
				break
			_legs.append(ids)


## Each take's run-in, frame by frame: how far apart the two men's hips are and which of the
## tackler's feet is on the ground (read once, on the first figure, before the match draws).
func _read_takes(p: Dictionary) -> void:
	var ap: AnimationPlayer = p["anim"]
	for name in _pairs:
		var cs := float(_pairs[name]["contact_s"])
		var dist := []
		var foot := []
		var k := 0
		while k * STEP <= cs + 0.001:
			var hk := _clip_hips(ap, name + "_tackler", k * STEP).origin
			var he := _clip_hips(ap, name + "_tacklee", k * STEP).origin
			dist.append(Vector2(hk.x - he.x, hk.z - he.z).length())
			ap.play(name + "_tackler")
			ap.seek(k * STEP, true)
			foot.append(_planted(p))
			k += 1
		_takes[name] = {"dist": dist, "foot": foot}
	ap.play("idle")


## m/s the run loop covers at rate 1 on a man of the average build: how fast its planted foot
## travels back under the hips (the loops have their travel taken out). JOG_SPEED when the clip
## cannot be read. A man's own stride is this times his legs (p["leg"], Oval3DBuild): a tall
## man covers more ground a stride, a short one less.
func loop_speed(name: String, p := {}) -> float:
	return float(_loop_speed.get(name, JOG_SPEED)) * float(p.get("leg", 1.0))


func _measure_loop(p: Dictionary, name: String) -> float:
	var ap: AnimationPlayer = p["anim"]
	if not ap.has_animation(name):
		return JOG_SPEED
	var skel: Skeleton3D = p["skel"]
	var feet := [skel.find_bone("ball_l"), skel.find_bone("ball_r")]
	if feet.has(-1):
		return JOG_SPEED
	ap.play(name)
	var length := ap.current_animation_length
	var n := 150
	var at := []
	var lo := [INF, INF]
	for k in range(n + 1):
		ap.seek(length * k / n, true)
		var row := []
		for f in range(2):
			var q := _rig * skel.get_bone_global_pose(feet[f]).origin
			row.append(q)
			lo[f] = minf(lo[f], q.y)
		at.append(row)
	var sum := 0.0
	var count := 0
	for k in range(n):
		var a0: Vector3 = at[k][0]
		var b0: Vector3 = at[k + 1][0]
		if a0.y < lo[0] + FOOT_DOWN and b0.y >= lo[0] + FOOT_DOWN and not _lift.has(name):
			_lift[name] = float(k + 1) / n
		for f in range(2):
			var a: Vector3 = at[k][f]
			var b: Vector3 = at[k + 1][f]
			if a.y < lo[f] + FOOT_DOWN and b.y < lo[f] + FOOT_DOWN:
				sum += Vector2(b.x - a.x, b.z - a.z).length() / (length / n)
				count += 1
	ap.play("idle")
	# Read off this man's build: brought back to the average one (loop_speed, _plant).
	var leg := float(p.get("leg", 1.0))
	if name == "jog":
		_floor = [lo[0] / leg, lo[1] / leg]
	return sum / count / leg if count > 0 else JOG_SPEED


## A moving loop: the run, the run with the ball, or a slow gait.
static func is_loop(name: String) -> bool:
	return name in ["jog", "carry"] or name in GAITS


## The slow gait for a man off the ball moving at `speed` (drawn m/s) along `vel`, or "" to run
## facing his way (too fast for any gait, or the ball right on him). Moving roughly towards the
## ball, or at a walk with the ball near the way he goes, he walks; well off it, he backpedals or
## side-steps, facing so the gait's way is his (GAIT_WAY). `cur`, the gait he is in, is kept
## until an edge is passed by GAIT_STAY or GAIT_TURN.
func _gait(cur: String, pos: Vector2, vel: Vector2, speed: float) -> String:
	var keep := func(name: String, edge: float) -> float:
		return edge * (1.0 + GAIT_STAY if cur == name else 1.0 - GAIT_STAY)
	var to: Vector2 = (director.ball["pos"] as Vector2) - pos
	var off := 0.0
	if to.length() > 2.0:
		off = absf(angle_difference(atan2(to.x, to.y), atan2(vel.x, vel.y)))
	var backing := cur in ["backstep", "backpedal"]
	var siding := cur.begins_with("shuffle") or cur.begins_with("side_run")
	if off > BACK_FROM - (GAIT_TURN if backing else 0.0) and speed < keep.call("backpedal", BACK_TO):
		return "backstep" if speed < keep.call("backstep", BACKSTEP_TO) else "backpedal"
	if off > SIDE_FROM - (GAIT_TURN if siding or backing else 0.0) and speed < SIDE_TO * (1.0 + GAIT_STAY if siding else 1.0 - GAIT_STAY):
		# Side-on to the ball's way: face whichever side keeps the ball the more in front, and
		# step the way he goes. His right, facing yaw y, is (-cos y, sin y).
		var y1 := atan2(vel.x, vel.y) + PI / 2.0
		var y2 := atan2(vel.x, vel.y) - PI / 2.0
		var ball_y := atan2(to.x, to.y)
		var y := y1 if absf(angle_difference(y1, ball_y)) < absf(angle_difference(y2, ball_y)) else y2
		var right := Vector2(-cos(y), sin(y)).dot(vel) > 0.0
		var quick := speed >= SHUFFLE_TO * (1.0 - GAIT_STAY if cur.begins_with("side_run") else 1.0 + GAIT_STAY)
		return ("side_run_" if quick else "shuffle_") + ("r" if right else "l")
	if speed < keep.call("walk", WALK_TO):
		return "walk"
	return ""


## 0 when his left foot is the lower, 1 when his right is.
func _planted(p: Dictionary) -> int:
	var skel: Skeleton3D = p["skel"]
	var l := (_rig * skel.get_bone_global_pose(skel.find_bone("ball_l"))).origin.y
	var r := (_rig * skel.get_bone_global_pose(skel.find_bone("ball_r"))).origin.y
	return 0 if l < r else 1


## Clip seconds of a take's run-in from where its tackler is `d` metres from its tacklee to the
## contact (the whole run-in when ours is farther out than the take starts).
func _lead(name: String, d: float) -> float:
	var cs := float(_pairs[name]["contact_s"])
	var dist: Array = _takes[name]["dist"]
	for k in range(dist.size()):
		if float(dist[k]) <= d:
			return clampf(cs - k * STEP, LEAD_MIN, cs)
	return LEAD_MIN


## Where his hips are drawn, on the ground.
func _drawn(i: int) -> Vector2:
	var h := _hips_world(players[i])
	return Vector2(h.origin.x, h.origin.z)


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
		# With symmetry the limit is each way (Godot), so the angles go in as they are: twice them
		# craned a ruckman's head 70 degrees back at the bounce.
		m.primary_limit_angle = deg_to_rad(l[1])
		m.secondary_limit_angle = deg_to_rad(l[2])
		m.influence = l[3]
		skel.add_child(m)
		m.target_node = m.get_path_to(target)
		mods.append(m)
	_targets.append(target)
	_looks.append(mods)


## Once a frame, before the contacts and the players: the clock, a tackle about to land (its
## clip starts now), and every running pair's clip time.
func frame(dt: float) -> void:
	_clock += dt
	director.lying_spots.clear()
	var ahead := director.tackle_ahead()
	if not ahead.is_empty() and not _pairs.is_empty():
		var who := int(ahead["who"])
		var v := int(ahead["victim"])
		var pr: Dictionary = _in[who]
		if pr.is_empty() or int(pr["who"]) != who or int(pr["victim"]) != v:
			var due := _due(who, v, float(ahead["left"]))
			# Start as soon as the run-in of some take, from the distance he is out, fits.
			var need := LEAD
			var d := _drawn(who).distance_to(_drawn(v))
			var run_in := 0.0
			for name in _pairs:
				need = maxf(need, _lead(name, d))
				run_in = maxf(run_in, float((_takes[name]["dist"] as Array)[0]))
			var run_down: bool = director.chasing_down()
			if run_down:
				# The takes' carriers stand or walk into them: in a run-down the carrier runs on in
				# his own stride until the last CHASE_LEAD before the director's take
				# (run_down_due: he is at the tackle's spot with the tackler at his back).
				need = CHASE_LEAD
				due = director.run_down_due()
			# A tackler the director has slowed as he arrives would stand (under RUN_FROM) and
			# wait for the take: the take starts then instead, its run-in carrying him in
			# (director 2026-11-22: "the tackler is standing by idly waiting for the tackle").
			var slowing := (_pace[who] as Vector2).length() < RUN_FROM and due <= need + CLOSE_EARLY \
					and not run_down
			# ...and no further out than a take's own run-in (and a stride or two): from a long
			# way off he runs in on his legs first, not on the clip (seed 31: a 30 m run-in on a
			# take a few metres long, the clip dragging him). A run-down joins at the hit.
			if (due <= need or slowing) and (run_down or d <= run_in + RUN_IN_SLACK):
				_start(who, v, false)
	var seen := {}
	for pr in _in:
		if pr.is_empty() or seen.has(pr["id"]):
			continue
		seen[pr["id"]] = true
		_advance(pr, dt)


## An interchange (Oval3D._send_off): the man coming on is drawn at `from` (the gate) and
## runs to his slot's spot, as a man back from a tackle does (GAP_CLOSE to GAP_MAX).
func run_on(i: int, from: Vector2) -> void:
	if i < 0 or i >= _gap.size():
		return
	if not (_in[i] as Dictionary).is_empty():
		_leave(i)
	_back[i] = Vector2.INF
	_gap[i] = from - (director.tokens[i]["pos"] as Vector2)


## Animation seconds until the chase from `who` to `v` reaches MatchDirector's REACH.
func _due(who: int, v: int, left: float) -> float:
	var a: Dictionary = director.tokens[who]
	var b: Dictionary = director.tokens[v]
	var gap: Vector2 = (b["pos"] as Vector2) - (a["pos"] as Vector2)
	var d := gap.length()
	if d < 0.001:
		return 0.0
	var closing := ((a["vel"] as Vector2) - (b["vel"] as Vector2)).dot(gap / d) * MatchDirector.TEMPO
	return minf(maxf(0.0, d - REACH) / maxf(closing, 1.0), left / MatchDirector.TEMPO)


func _advance(pr: Dictionary, dt: float) -> void:
	if pr["fresh"]:
		pr["fresh"] = false
		return
	_follow(pr, dt)
	var cs := float(pr["cs"])
	var c := float(pr["c"])
	var rate := 1.0
	if c < cs:
		if pr["arrived"]:
			rate = CATCH_UP
		else:
			var ahead := director.tackle_ahead()
			var due := 0.05
			if not ahead.is_empty() and int(ahead["who"]) == int(pr["who"]):
				due = _due(int(pr["who"]), int(pr["victim"]), float(ahead["left"]))
				if director.chasing_down():
					due = minf(due, director.run_down_due())
			rate = clampf((cs - c) / maxf(due, 0.05), SLOW, LEAD_RATE)
	else:
		# Down and back up in UP_IN; then the take's standing tail at its own pace.
		if c < float(pr["up"]):
			rate = maxf(1.0, (float(pr["up"]) - cs) / UP_IN)
			# ...and up by the time the director lets him go (MatchDirector.TAKE_UP after its
			# tackle): a contact landing late left him on the deck while his man ran on, 10-17 m
			# behind him (3D bug bash, 2026-11-23).
			var tk: Dictionary = director.tokens[int(pr["who"])]
			if tk.has("tackle_t"):
				var left := (MatchDirector.TAKE_UP - (director.time - float(tk["tackle_t"]))) / MatchDirector.TEMPO
				rate = maxf(rate, (float(pr["up"]) - c) / maxf(left, UP_LATE))
		# The get-up hurries when the play has gone on without them.
		for i in [int(pr["who"]), int(pr["victim"])]:
			if _in[i] != pr:
				continue
			if _drawn(i).distance_to(director.tokens[i]["pos"]) > FAR:
				rate = maxf(rate, HURRY)
			# The director has him running again while the clip still has him getting up: he
			# is up and away within GO_IN.
			if c >= cs and c < float(pr["up"]) \
					and (director.tokens[i]["vel"] as Vector2).length() * MatchDirector.TEMPO > RUN_FROM:
				rate = maxf(rate, (float(pr["up"]) - c) / GO_IN)
	var nc := c + dt * rate
	if c < cs and nc >= cs:
		_hit(pr)
	pr["c"] = nc


## Keep the pair and the director together. A man the director has down in this take (from
## the contact until MatchDirector.TAKE_UP after it) lies where the take puts him: his token is
## moved there, as the director's "his body is where the take put him" means. The fall carries
## the two of them 2-4 m, which the director does not know (3D bug bash, 2026-11-23: the picture
## 5-10 m off the play, or, when the picture chased the tokens, the pile skating at 3-7 m/s).
## While both are on their feet (the run-in, the standing tail) the pair is turned and slid,
## as one, toward the director's places: the line between them to the director's, then the
## mean of how far each is drawn from his token (each is then off by half the difference
## between the clip's spacing and the director's). The run masks that slide.
func _follow(pr: Dictionary, dt: float) -> void:
	if dt <= 0.0:
		return
	var who := int(pr["who"])
	var v := int(pr["victim"])
	var adj: Transform3D = pr["adj"]
	var down := float(pr["c"]) >= float(pr["cs"]) and float(pr["c"]) < float(pr["up"])
	var swing := SWING_DOWN if down else SWING
	var slide := SLIDE_DOWN if down else SLIDE
	var free: Array = []
	for i in [who, v]:
		if _in[i] != pr:
			continue
		if float(pr["c"]) >= float(pr["cs"]) and not director._on_feet(i):
			director.tokens[i]["pos"] = _drawn(i)
			_lying(i)
		else:
			free.append(i)
	if free.size() == 2:
		var dk := _drawn(who)
		var dv := _drawn(v)
		var drawn := dv - dk
		var want: Vector2 = (director.tokens[v]["pos"] as Vector2) - (director.tokens[who]["pos"] as Vector2)
		if drawn.length() > 0.4 and want.length() > 0.4:
			# A turn about UP by phi takes a line at angle a on the turf to a - phi.
			var phi := wrapf(drawn.angle() - want.angle(), -PI, PI)
			phi = clampf(phi * (1.0 - exp(-dt / TURN_S)), -swing * dt, swing * dt)
			var mid := (dk + dv) * 0.5
			var m3 := Vector3(mid.x, 0.0, mid.y)
			adj = Transform3D(Basis(Vector3.UP, phi), m3 - Basis(Vector3.UP, phi) * m3) * adj
	# Only when neither is down: one lying where the take put him holds the pair still.
	if free.size() == _count_in(pr) and not free.is_empty():
		var err := Vector2.ZERO
		for i in free:
			err += (director.tokens[i]["pos"] as Vector2) - _drawn(i)
		var mv := (err / free.size() * (1.0 - exp(-dt / FOLLOW_S))).limit_length(slide * dt)
		adj.origin += Vector3(mv.x, 0.0, mv.y)
	pr["adj"] = adj


## He is drawn round a man lying in a take, never through him: his token keeps off the body
## (MatchMotion.keep_off), but where he is drawn off his token (back from a tackle, the
## draw-apart) he could still run over it. He sidesteps at SIDESTEP at most.
func _step_round(i: int, pos: Vector2, dt: float) -> void:
	if director.lying_spots.is_empty():
		return
	var here: Vector2 = pos + (_gap[i] as Vector2)
	var want := here
	for sp in director.lying_spots:
		var d := want - sp
		if d.length() < MatchMotion.LIE_CLEAR:
			var out := d.normalized() if d.length() > 0.001 else Vector2.RIGHT.rotated(float(i))
			want = sp + out * MatchMotion.LIE_CLEAR
	if want != here:
		_gap[i] = (_gap[i] as Vector2) + (want - here).limit_length(SIDESTEP * maxf(dt, 1.0 / 60.0))


## Hand the director the parts of man i that lie on the turf.
func _lying(i: int) -> void:
	var p: Dictionary = players[i]
	var skel: Skeleton3D = p["skel"]
	var to := (p["node"] as Node3D).transform * _rig
	for bi in _body:
		var at := to * skel.get_bone_global_pose(bi).origin
		if at.y < LIE_HIGH:
			director.lying_spots.append(Vector2(at.x, at.z))


func _count_in(pr: Dictionary) -> int:
	return int(_in[int(pr["who"])] == pr) + int(_in[int(pr["victim"])] == pr)


## The arms meet in the clip: where, and when, against the director's tackle.
func _hit(pr: Dictionary) -> void:
	var rec: Dictionary = pr["rec"]
	rec["hit_t"] = _clock
	var e: Dictionary = _pairs[pr["name"]]
	var cp: Transform3D = (pr["adj"] as Transform3D) * (pr["P"] as Transform3D)
	var at := cp * Vector3(float(e["contact"]["x"]), 0.0, float(e["contact"]["z"]))
	rec["contact"] = Vector2(at.x, at.z)
	var v := int(pr["victim"])
	var hips := _hips_world(players[v])
	rec["root"] = Vector2(hips.origin.x, hips.origin.z)


## Start a pair: the take whose tackler comes from nearest where ours is, turned about the
## tacklee. `arrived` when the director's contact has already come (the run-in's pace is set
## each frame in _advance from the time left).
## True while his kick or handball clip is still short of its contact (the ball not yet gone).
func _mid_move(i: int) -> bool:
	var o: Dictionary = _once[i]
	return not o.is_empty() and str(o.get("how", "")) in ["kick", "handball"] and float(o["t"]) < float(o["touch"])


func _start(who: int, v: int, arrived: bool, at := Vector2.INF) -> void:
	for i in [who, v]:
		if not (_in[i] as Dictionary).is_empty():
			_leave(i)
		if not _mid_move(i):
			_once[i] = {}
	var pk: Dictionary = players[who]
	var pv: Dictionary = players[v]
	var far := false
	for i in [who, v]:
		var tok: Vector2 = director.tokens[i]["pos"]
		if _drawn(i).distance_to(tok) > FAR:
			# Still on his way back from an earlier tackle, long after the play moved on: he
			# joins this one from where the director has him.
			(players[i]["node"] as Node3D).position = Vector3(tok.x, 0.0, tok.y)
			_gap[i] = Vector2.ZERO
			_back[i] = Vector2.INF
			far = true
	var hk := _hips_world(pk)
	var hv := _hips_world(pv)
	var K := Vector2(hk.origin.x, hk.origin.z)
	var V := Vector2(hv.origin.x, hv.origin.z)
	var yk := _yaw_of(hk.basis)
	var yv := _yaw_of(hv.basis)
	var ap: AnimationPlayer = pk["anim"]
	var running := is_loop(ap.current_animation)
	var foot := _planted(pk)
	var best := {}
	for name in _pairs:
		var e: Dictionary = _pairs[name]
		var cs := float(e["contact_s"])
		# Join the take where its tackler is as far out as ours.
		var lead := _lead(name, (K - V).length())
		if arrived:
			lead = minf(lead, LEAD_MIN)
		elif director.chasing_down():
			lead = minf(lead, CHASE_LEAD)
		var c0 := cs - lead
		var ce := _clip_hips(ap, name + "_tacklee", c0)
		var ck := _clip_hips(ap, name + "_tackler", c0)
		var e2 := Vector2(ce.origin.x, ce.origin.z)
		var k2 := Vector2(ck.origin.x, ck.origin.z)
		var theta := yv - _yaw_of(ce.basis)
		if (K - V).length() > 0.3:
			theta = _yaw_vec(K - V) - _yaw_vec(k2 - e2)
		var turn := wrapf(yv - (theta + _yaw_of(ce.basis)), -PI, PI)
		var score := absf(turn) + 0.1 * absf((K - V).length() - (k2 - e2).length())
		# The take whose tackler has the same foot down as ours runs on in step.
		var feet: Array = _takes[name]["foot"]
		if running and int(feet[clampi(roundi(c0 / STEP), 0, feet.size() - 1)]) != foot:
			score += 0.35
		if best.is_empty() or score < float(best["score"]):
			best = {"name": name, "theta": theta, "turn": turn, "ce": ce, "ck": ck, "c0": c0,
					"cs": cs, "score": score}
	if best.is_empty():
		return
	var name: String = best["name"]
	var P := Transform3D(Basis(Vector3.UP, float(best["theta"])), Vector3.ZERO)
	var ce: Transform3D = best["ce"]
	var ck: Transform3D = best["ck"]
	P.origin = Vector3(V.x, 0.0, V.y) - P.basis * Vector3(ce.origin.x, 0.0, ce.origin.z)
	var pk3 := P * Vector3(ck.origin.x, 0.0, ck.origin.z)
	var wk := Vector3(K.x, 0.0, K.y) - pk3
	var dyk := wrapf(yk - (float(best["theta"]) + _yaw_of(ck.basis)), -PI, PI)
	var rec := {"who": who, "victim": v, "pair": name, "start_t": _clock, "event_t": -1.0,
			"hit_t": -1.0, "lead": float(best["cs"]) - float(best["c0"]),
			"turn_deg": rad_to_deg(float(best["turn"])), "warp_m": wk.length(),
			"warp_deg": rad_to_deg(dyk), "at": at, "contact": Vector2.INF, "root": Vector2.INF,
			"from": K, "stand": V, "far": far}
	if arrived:
		rec["event_t"] = _clock
	tackles.append(rec)
	var pr := {"id": tackles.size(), "name": name, "who": who, "victim": v, "P": P,
			"adj": Transform3D.IDENTITY,
			"c0": float(best["c0"]), "c": float(best["c0"]), "cs": float(best["cs"]),
			"len": float(_pairs[name]["length_s"]), "arrived": arrived, "rec": rec,
			"up": float(_pairs[name].get("up_s", _pairs[name]["length_s"])),
			# A chase-down's momentum (SLIDE_T): the carrier's drawn velocity as the take starts.
			"slide": (_pace[v] as Vector2).limit_length(SLIDE_MAX) if director.chasing_down() else Vector2.ZERO,
			"t0": _clock,
			# Started by frame() this frame: its clock has already been stepped past.
			"fresh": not arrived,
			"roles": {
				who: {"anim": name + "_tackler", "pivot": pk3, "w": wk, "dy": dyk},
				v: {"anim": name + "_tacklee", "pivot": Vector3(V.x, 0.0, V.y), "w": Vector3.ZERO,
						"dy": float(best["turn"])}}}
	for i in [who, v]:
		_in[i] = pr
		if _mid_move(i):
			# Tackled as he kicks or handballs: the tackler comes on at once (never standing
			# waiting), and this man's swing plays on until boot or fist meets the ball, then he
			# joins the take where it has got to (step()).
			continue
		_once[i] = {}
		_snap(i, players[i])
		_back[i] = Vector2.INF
		_gap[i] = Vector2.ZERO
		for m in _looks[i]:
			(m as LookAtModifier3D).active = false


## Pose player i for this frame. holder = the index with the ball in his hands, or -1.
func step(i: int, p: Dictionary, holder: int, pos: Vector2, vel: Vector2, dt: float) -> void:
	if not (_in[i] as Dictionary).is_empty() and not _mid_move(i):
		if not (_once[i] as Dictionary).is_empty():
			# His kick has met the ball: into the take that started round him.
			_once[i] = {}
			_snap(i, p)
		_was[i] = Vector2.INF
		_feet[i] = [{}, {}]
		_step_pair(i, p, dt, vel)
		return
	var node: Node3D = p["node"]
	var o: Dictionary = _once[i]
	if not o.is_empty():
		o["keep"] = o.has("caught") and holder != i and _clock - float(o["caught"]) < CAUGHT_MAX
	if not o.is_empty() and not o.get("keep", false) \
			and (float(o["t"]) >= float(o["end"]) or _off_hands(i, o, holder, pos)):
		# The clip's end (MatchDirector.SCOOPS): the jog eases in over BLEND.
		_end_once(i)
		o = {}
	if o.is_empty() and (_in[i] as Dictionary).is_empty() and _gap[i] == Vector2.ZERO:
		o = _move_due(i, holder)
	elif not o.is_empty() and str(o.get("how", "")) != "" and not o.get("arrived", false):
		_steer(i, o)
	if _back[i] != Vector2.INF:
		# Off the take's ground (the frame after it ends): he stands where his hips were.
		node.transform = Transform3D(Basis(Vector3.UP, float(_face[i])), node.position)
		(p["ring"] as Node3D).position = Vector3(0.0, 0.03, 0.0)
		_gap[i] = (_back[i] as Vector2) - pos
		_back[i] = Vector2.INF
	var gap: Vector2 = _gap[i]
	if gap != Vector2.ZERO:
		# Back from a tackle: he runs to his spot.
		var back := clampf(2.0 * gap.length(), GAP_CLOSE, GAP_MAX)
		_gap[i] = gap - gap.limit_length(back * dt)
		_round(i, pos, gap, back * dt)
	_step_round(i, pos, dt)
	if gap != Vector2.ZERO or _gap[i] != Vector2.ZERO:
		node.position = Vector3(pos.x + (_gap[i] as Vector2).x, 0.0, pos.y + (_gap[i] as Vector2).y)
	if not o.is_empty():
		# The clip carries him from where the scoop began (its own run): his token runs the
		# same line at the same pace, and any gap left closes as from a take once it ends.
		var t0 := float(o["t0"])
		var span := float(o["touch"]) - t0
		var k := 1.0 if span <= 0.001 else clampf((float(o["t"]) - t0) / span, 0.0, 1.0)
		if o.has("face"):
			_track_move(o, pos, vel, dt)
		var spot: Vector2 = (o["at"] as Vector2) + (o["off"] as Vector2) * (1.0 - k)
		_gap[i] = spot - pos
		node.position = Vector3(spot.x, 0.0, spot.y)
		_was[i] = Vector2.INF
		_feet[i] = [{}, {}]
		_step_once(i, p, o, dt)
		return
	# How fast he is drawn moving: his node's move this frame, smoothed (the run must match
	# the turf going under him, whatever moved him: his token, the spacing, a run back).
	var here := Vector2(node.position.x, node.position.z)
	if dt > 0.0 and _was[i] != Vector2.INF:
		var dv: Vector2 = (here - (_was[i] as Vector2)) / dt
		if dv.length() < JUMP:
			_pace[i] = (_pace[i] as Vector2).lerp(dv, 1.0 - exp(-dt / PACE_FOLLOW))
	elif dt > 0.0:
		_pace[i] = vel * MatchDirector.TEMPO
	_was[i] = here
	vel = _pace[i]
	var speed := vel.length()
	var ap: AnimationPlayer = p["anim"]
	var want := "carry" if i == holder else "idle"
	var rate := 0.0 if i == holder else 1.0
	# The carrier only runs (carry); a man off the ball walks from WALK_FROM when the gaits loaded.
	var go := RUN_FROM if i == holder or not ap.has_animation("walk") else WALK_FROM
	_still[i] = 0.0 if speed > go else float(_still[i]) + dt
	# A check in his stride (slow for under STOP_HOLD) is still running: he doesn't stand up
	# for three frames and set off again.
	var hold := STOP_HOLD
	if holder >= 0 and holder != i and holder < players.size() and here.distance_to(Vector2((players[holder]["node"] as Node3D).position.x, (players[holder]["node"] as Node3D).position.z)) < CLOSE_IN:
		hold = CLOSE_HOLD
	var running: bool = speed > go or (float(_still[i]) < hold
			and is_loop(ap.current_animation) and dt > 0.0)
	# He turns at a footballer's pivot, never through half a turn in one frame. dt 0 (the
	# first draw) sets him facing.
	var turn := TURN * dt if dt > 0.0 else PI
	if running:
		want = "carry" if i == holder else "jog"
		var face := atan2(vel.x, vel.y)
		if i != holder and go < RUN_FROM:
			var g := _gait(ap.current_animation, pos, vel, maxf(speed, go))
			var cur := str(ap.current_animation)
			if g != "" and cur in GAITS and g != cur and float(_gait_t[i]) < GAIT_HOLD:
				g = cur   # settled into a gait a moment before changing to another
			if g != "":
				want = g
				face = wrapf(face - float(GAIT_WAY[g]), -PI, PI)
		if speed > go:
			var swing := turn
			if dt > 0.0 and not _legs.is_empty():
				swing = (TURN_PLANTED if _held(i) else TURN_AIR) * dt
			node.rotation.y = rotate_toward(node.rotation.y, face, swing)
		var least := RUN_FROM if want in ["jog", "carry"] else go
		rate = clampf(maxf(speed, least) / loop_speed(want, p), RATE_MIN, RATE_MAX)
	elif i != holder:
		# Standing: face the ball (the carrier keeps his heading).
		var to: Vector2 = (director.ball["pos"] as Vector2) - pos
		if to.length() > 0.5:
			node.rotation.y = rotate_toward(node.rotation.y, atan2(to.x, to.y), turn)
	_gait_t[i] = float(_gait_t[i]) + dt if ap.current_animation == want else 0.0
	if ap.current_animation != want:
		# Spread over the 10 s stand loop so a standing line doesn't sway in step.
		var at := fmod(float(i) * 1.37, 10.0)
		var was := str(ap.current_animation)
		if was in ["jog", "carry"] and want in ["jog", "carry"]:
			at = ap.current_animation_position
		elif is_loop(was) and is_loop(want) and _lift.has(was) and _lift.has(want):
			# From one gait to another in step: the new loop joins at the same point of the
			# stride (the left foot as far from lifting), so no foot jumps.
			var u := ap.current_animation_position / maxf(ap.current_animation_length, 0.001) - float(_lift[was])
			at = fposmod(u + float(_lift[want]), 1.0) * ap.get_animation(want).length
		if was == "idle" or is_loop(was):
			# Running to standing and back eases over BLEND: the capture's stride is too real to
			# cut from mid-air to a stand in one frame.
			_snap(i, p)
		ap.play(want)
		ap.seek(fmod(at, ap.current_animation_length), false)
	if want == "carry" and rate == 0.0:
		# Standing with the ball: the carry's first frame, a left foot-strike, not a
		# flight phase.
		ap.seek(0.0, false)
	# A zero step leaves a freshly played pose unapplied (a standing holder kept the idle
	# arms), so a still pose still advances by a sliver.
	ap.advance(maxf(dt * rate, 1e-4))
	_rate[i] = rate
	_ease(i, p, dt)
	_plant(i, p, dt, not running)
	_look_at_ball(i, i == holder, dt)


## A scoop at the ball: the clip at its time, facing where the ball lay when it began.
func _step_once(i: int, p: Dictionary, o: Dictionary, dt: float) -> void:
	if str(o.get("how", "")) == "mark" and not o.get("arrived", false) and director.catch_due(i).is_empty():
		# The ball has come down (its flight is over) but the director still has him running the
		# last of the way onto it: the mark is his now, his hands at it this frame (eased, as a
		# late touch). He plays it out and keeps the ball until the director hands it to him,
		# never standing frozen with his hands up nor the ball waiting in the air for him.
		_arrive(i, o)
		o["rate"] = 1.0
		o["caught"] = _clock
		o["keep"] = true
	var t := float(o["t"]) + dt * float(o.get("rate", 1.0))
	if o.has("caught") and o.get("keep", false):
		t = minf(t, float(o["end"]))
	if str(o.get("how", "")) != "" and not o.get("arrived", false) and t > float(o["touch"]) - HOLD_SHORT:
		# The director's hold ran longer than its estimate: he waits a frame short of the contact
		# (boot or hands not through the ball before the ball leaves or arrives).
		o["held"] = float(o.get("held", 0.0)) + dt
		t = maxf(float(o["t"]), float(o["touch"]) - HOLD_SHORT)
	o["t"] = t
	var ap: AnimationPlayer = p["anim"]
	(p["node"] as Node3D).rotation.y = float(o.get("face", o["yaw"]))
	if ap.current_animation != str(o["anim"]):
		ap.play(str(o["anim"]))
	ap.seek(minf(float(o["t"]), ap.current_animation_length), true)
	_rate[i] = 1.0
	_ease(i, p, dt)
	# The clip carries his hips off its origin (a kick's run-through, a scoop): his ring stays
	# under him, as in a take.
	var hips := _rig * (p["skel"] as Skeleton3D).get_bone_global_pose(_pelvis)
	(p["ring"] as Node3D).position = Vector3(hips.origin.x, 0.03, hips.origin.z)
	_look_at_ball(i, false, dt)


## Out of the scoop: like the end of a take, he is where its hips left him and eases into
## running or standing, never a slide back.
## Once his hands have been to it, a ball that has come off them and rolled on ends his scoop:
## he is not left reaching down to the turf for it (seed 31: 0.6 s after a knock, director
## 2026-11-16: "the ball never moves without a man's hands on it", nor do his hands without it).
func _off_hands(i: int, o: Dictionary, holder: int, pos: Vector2) -> bool:
	if holder == i or float(o["t"]) < float(o["touch"]) + KNOCK_UP:
		return false
	var b: Dictionary = director.ball
	return str(b["mode"]) in ["loose", "dead"] and (b["pos"] as Vector2).distance_to(pos) > KNOCK_OFF


func _end_once(i: int) -> void:
	var p: Dictionary = players[i]
	var spot: Vector2 = (_once[i] as Dictionary)["at"]
	(p["node"] as Node3D).position = Vector3(spot.x, 0.0, spot.y)  # where his last pose was drawn
	var hips := _hips_world(p)
	_snap(i, p)
	_face[i] = float((_once[i] as Dictionary).get("face", (_once[i] as Dictionary)["yaw"]))
	_back[i] = Vector2(hips.origin.x, hips.origin.z)
	_once[i] = {}


## A man in a pair: the take at the pair's clip time, placed by the pair (and, over the run-in,
## the correction from where he really was), his club ring under his hips.
func _step_pair(i: int, p: Dictionary, dt: float, vel := Vector2.ZERO) -> void:
	var pr: Dictionary = _in[i]
	var role: Dictionary = pr["roles"][i]
	var ap: AnimationPlayer = p["anim"]
	var c := minf(float(pr["c"]), float(pr["len"]))
	if ap.current_animation != role["anim"]:
		ap.play(role["anim"])
	ap.seek(c, true)
	var f := 0.0
	if float(pr["cs"]) > float(pr["c0"]):
		f = 1.0 - smoothstep(float(pr["c0"]), float(pr["cs"]), c)
	var pivot: Vector3 = role["pivot"]
	var warp := Transform3D(Basis(Vector3.UP, float(role["dy"]) * f), pivot + (role["w"] as Vector3) * f) \
			* Transform3D(Basis.IDENTITY, -pivot)
	var node: Node3D = p["node"]
	node.transform = (pr["adj"] as Transform3D) * warp * (pr["P"] as Transform3D)
	var sv: Vector2 = pr.get("slide", Vector2.ZERO)
	if sv != Vector2.ZERO:
		var u := clampf((_clock - float(pr["t0"])) / SLIDE_T, 0.0, 1.0)
		var s := sv * (SLIDE_T / 3.0) * (1.0 - pow(1.0 - u, 3.0))
		node.transform.origin += Vector3(s.x, 0.0, s.y)
	_ease(i, p, dt)
	var hips := _rig * (p["skel"] as Skeleton3D).get_bone_global_pose(_pelvis)
	(p["ring"] as Node3D).position = Vector3(hips.origin.x, 0.03, hips.origin.z)
	# Up off the ground (the pair's up_s), he goes as soon as the play wants him: the rest of
	# the clip is the two of them standing (MatchDirector.TAKE_UP lets him move from then).
	# Nearly up, with the director already sending him (MatchDirector.TAKE_UP passed), he goes
	# now rather than finishing the clip while his man runs off (3D bug bash: 4 m behind in
	# ball-up packs).
	var up := float(pr["up"])
	if not director._on_feet(i):
		up = INF
	elif float(pr["c"]) >= float(pr["cs"]):
		up -= UP_EARLY
	if float(pr["c"]) >= float(pr["len"]) or (float(pr["c"]) >= minf(up, float(pr["up"])) and vel.length() > MOVE_OFF):
		_leave(i)


## Out of the pair: he stands where the take left him, facing as his hips do, and eases into
## running or standing from there. The node moves there on his next step, once the clip that
## follows has his hips back over his feet: moved now, this frame's pose (the take's hips,
## metres off the take's origin) was drawn that far off, beside the camera for one frame.
func _leave(i: int) -> void:
	var p: Dictionary = players[i]
	var hips := _hips_world(p)
	_snap(i, p)
	_face[i] = _yaw_of(hips.basis)
	_back[i] = Vector2(hips.origin.x, hips.origin.z)
	var pr: Dictionary = _in[i]
	_mate[i] = -1
	if not pr.is_empty():
		_mate[i] = int(pr["victim"]) if int(pr["who"]) == i else int(pr["who"])
	_in[i] = {}


## On the run back from a take he goes round the other man of it, never through him: the
## straight line to his spot can cross the man still getting up beside him (3d view 2,
## 2026-11-15: their hips came 0.18 m apart). `step_len` is how far he runs this frame.
func _round(i: int, pos: Vector2, pull: Vector2, step_len: float) -> void:
	var m := int(_mate[i])
	if m < 0:
		return
	if (_gap[i] as Vector2) == Vector2.ZERO:
		_mate[i] = -1
		return
	var them: Vector2
	if _back[m] != Vector2.INF:
		them = _back[m]
	elif not (_in[m] as Dictionary).is_empty():
		_mate[i] = -1  # he is in a new take: that one keeps the two apart
		return
	else:
		them = (director.tokens[m]["pos"] as Vector2) + (_gap[m] as Vector2)
	if pos.distance_to(them) < APART:
		_mate[i] = -1  # his own spot is beside him: the director keeps those apart
		return
	var me: Vector2 = pos + (_gap[i] as Vector2)
	var off := me - them
	if off.length() >= APART:
		return
	var out := off.normalized() if off.length() > 0.01 else Vector2.RIGHT.rotated(float(i))
	# Round the side he is already heading, so a run straight at him still gets past.
	var side := Vector2(-out.y, out.x)
	if side.dot(-pull) < 0.0:
		side = -side
	_gap[i] = them + out * APART + side * step_len * 0.5 - pos


## Hold the pose he is in now, to ease out of over BLEND (_ease).
func _snap(i: int, p: Dictionary) -> void:
	var skel: Skeleton3D = p["skel"]
	var rots := []
	for b in range(skel.get_bone_count()):
		rots.append(skel.get_bone_pose_rotation(b))
	_blend[i] = {"rots": rots, "hips": skel.get_bone_pose_position(_pelvis),
			"yaw": (p["node"] as Node3D).rotation.y, "t": 0.0, "src": ""}
	var ap: AnimationPlayer = p["anim"]
	if (_in[i] as Dictionary).is_empty() and (ap.current_animation == "idle" or is_loop(ap.current_animation)):
		# Out of running or standing: that clip keeps playing under the ease, so his legs keep
		# stepping as they were instead of a frozen stride dragging along the turf.
		_blend[i]["src"] = ap.current_animation
		_blend[i]["st"] = ap.current_animation_position


## Ease from the held pose into the one the clip just set. The hips keep the clip's place on
## the ground (the node carries that) and their facing in the world, so nobody spins or slides.
func _ease(i: int, p: Dictionary, dt: float) -> void:
	var b: Dictionary = _blend[i]
	if b.is_empty():
		return
	b["t"] = float(b["t"]) + dt
	var w := smoothstep(0.0, BLEND, float(b["t"]))
	if w >= 1.0:
		_blend[i] = {}
		return
	var skel: Skeleton3D = p["skel"]
	var rots: Array = b["rots"]
	var hips_from: Vector3 = b["hips"]
	var src := str(b["src"])
	if src != "":
		var a := (p["anim"] as AnimationPlayer).get_animation(src)
		var tr := _bone_tracks(src, a, skel)
		b["st"] = fmod(float(b["st"]) + dt * float(_rate[i]), maxf(a.length, 0.001))
		rots = rots.duplicate()
		for bone in tr:
			if bone is int:
				rots[bone] = a.rotation_track_interpolate(int(tr[bone]), float(b["st"]))
		if int(tr["hips"]) >= 0:
			hips_from = a.position_track_interpolate(int(tr["hips"]), float(b["st"]))
	for k in range(rots.size()):
		if k != _pelvis:
			skel.set_bone_pose_rotation(k, (rots[k] as Quaternion).slerp(skel.get_bone_pose_rotation(k), w))
	var up := skel.get_bone_parent(_pelvis)
	var to_model := _rig.basis * (skel.get_bone_global_pose(up).basis if up >= 0 else Basis.IDENTITY)
	var turn := Basis(Vector3.UP, float(b["yaw"]) - (p["node"] as Node3D).rotation.y)
	var held := Quaternion((to_model.inverse() * turn * to_model).orthonormalized()) * (rots[_pelvis] as Quaternion)
	skel.set_bone_pose_rotation(_pelvis, held.slerp(skel.get_bone_pose_rotation(_pelvis), w))
	var height := (to_model.inverse() * Vector3.UP).normalized()
	var cur := skel.get_bone_pose_position(_pelvis)
	var h := lerpf(hips_from.dot(height), cur.dot(height), w)
	skel.set_bone_pose_position(_pelvis, cur + height * (h - cur.dot(height)))


## Keep his planted feet where they came down (see LET_GO). `standing`: he is in the stand
## loop, both feet down, stepping across when his body has drifted off one. dt 0 (a fresh draw)
## takes the clip's feet as they are.
func _plant(i: int, p: Dictionary, dt: float, standing: bool) -> void:
	if _legs.is_empty() or _floor[0] == INF:
		return
	var skel: Skeleton3D = p["skel"]
	var node: Node3D = p["node"]
	var g := skel.global_transform
	var feet: Array = _feet[i]
	if dt <= 0.0:
		_feet[i] = [{}, {}]
		return
	# The one foot allowed to step this frame, standing: the one furthest off its place.
	var stepper := -1
	if standing:
		var worst := PULL_STAND
		for f in range(2):
			var lk: Dictionary = feet[f]
			if lk.is_empty():
				continue
			if float(lk["step"]) >= 0.0:
				stepper = -2  # one is already stepping
				break
			var q := g * skel.get_bone_global_pose(_legs[f][3]).origin
			var off := Vector2(q.x - (lk["at"] as Vector3).x, q.z - (lk["at"] as Vector3).z).length()
			if off > worst:
				worst = off
				stepper = f
	for f in range(2):
		var leg: Array = _legs[f]
		var q := g * skel.get_bone_global_pose(leg[3]).origin
		var down := q.y - node.global_position.y < float(_floor[f]) * float(p.get("leg", 1.0)) + FOOT_DOWN
		var lk: Dictionary = feet[f]
		if lk.is_empty():
			if down:
				feet[f] = {"at": q, "yaw": node.rotation.y, "w": 1.0, "step": -1.0, "from": q}
			continue
		var at: Vector3 = lk["at"]
		var pull := Vector2(q.x - at.x, q.z - at.z).length()
		if standing and down and float(lk["w"]) >= 1.0:
			if f == stepper:
				lk["step"] = 0.0
				lk["from"] = at
			if float(lk["step"]) >= 0.0:
				# A shuffle step: the foot lifts, crosses to where the stand has it, and goes down.
				lk["step"] = float(lk["step"]) + dt
				var k := smoothstep(0.0, STEP_TIME, float(lk["step"]))
				var from: Vector3 = lk["from"]
				at = from.lerp(q, k)
				at.y = q.y + STEP_LIFT * sin(PI * k)
				lk["yaw"] = lerp_angle(float(lk["yaw"]), node.rotation.y, k)
				if k >= 1.0:
					lk["step"] = -1.0
					at = q
					lk["yaw"] = node.rotation.y
				lk["at"] = at
			else:
				at.y = q.y
		elif down and float(lk["w"]) >= 1.0:
			# Held where it came down until the clip lifts it; the clip keeps the heel-toe roll.
			# A body that has run on past the leg's reach drags it, no further than PULL_RUN.
			if pull > PULL_RUN:
				var back := Vector2(at.x - q.x, at.z - q.z).normalized() * PULL_RUN
				at = Vector3(q.x + back.x, q.y, q.z + back.y)
				lk["at"] = at
			at.y = q.y
		elif down and float(lk["w"]) <= 0.0:
			# A fresh foot-strike: it holds from here.
			lk["at"] = q
			lk["yaw"] = node.rotation.y
			lk["w"] = 1.0
			lk["step"] = -1.0
			at = q
		else:
			# Lifted by the clip (or pulled too far): it hands back to the clip.
			lk["w"] = maxf(0.0, float(lk["w"]) - dt / LET_GO)
			lk["step"] = -1.0
			at.y = q.y
		var w := float(lk["w"])
		if w <= 0.0:
			continue
		var want := q.lerp(at, w)
		_reach(skel, g, leg, want - q, wrapf(float(lk["yaw"]) - node.rotation.y, -PI, PI) * w)


## Whether a foot of his is held on the turf now (last frame's plant).
func _held(i: int) -> bool:
	for lk in _feet[i]:
		if not (lk as Dictionary).is_empty() and float(lk["w"]) >= 1.0 and float(lk["step"]) < 0.0:
			return true
	return false


## Bend one leg so its ball bone moves by `off` (world metres), the foot turned `yaw` about the
## up axis from where the clip has it: the thigh and calf of a two-bone reach, knee kept on the
## side the clip bent it.
func _reach(skel: Skeleton3D, g: Transform3D, leg: Array, off: Vector3, yaw: float) -> void:
	if off.length_squared() < 1e-8 and absf(yaw) < 1e-4:
		return
	var inv := g.affine_inverse()
	var o := inv.basis * off
	var up := (inv.basis * Vector3.UP).normalized()
	var th := skel.get_bone_global_pose(leg[0])
	var ca := skel.get_bone_global_pose(leg[1])
	var ft := skel.get_bone_global_pose(leg[2])
	var ball := skel.get_bone_global_pose(leg[3])
	var turn := Basis(up, yaw)
	# Where the ankle must go: the ball's move, plus the foot's turn about the ball.
	var target := ball.origin + o - turn * (ball.origin - ft.origin)
	var a := th.origin
	var b := ca.origin
	var c := ft.origin
	var l1 := a.distance_to(b)
	var l2 := b.distance_to(c)
	var to := target - a
	var d := clampf(to.length(), absf(l1 - l2) + 0.001, l1 + l2 - 0.001)
	if to.length() < 0.001:
		return
	var dir := to.normalized()
	var bend := (b - a) - dir * (b - a).dot(dir)
	if bend.length() < 0.001:
		bend = (b - a).cross(c - b).cross(dir)
		if bend.length() < 0.001:
			return
	bend = bend.normalized()
	var cos_a := clampf((l1 * l1 + d * d - l2 * l2) / (2.0 * l1 * d), -1.0, 1.0)
	var knee := a + dir * (l1 * cos_a) + bend * (l1 * sqrt(1.0 - cos_a * cos_a))
	var r1 := _arc(b - a, knee - a)
	var c1 := a + r1 * (c - a)
	var r2 := _arc(c1 - knee, (a + dir * d) - knee)
	var th_b := r1 * th.basis
	var ca_b := r2 * r1 * ca.basis
	var ft_b := turn * ft.basis
	var pelvis := skel.get_bone_global_pose(skel.get_bone_parent(leg[0])).basis
	skel.set_bone_pose_rotation(leg[0], Quaternion((pelvis.inverse() * th_b).orthonormalized()))
	skel.set_bone_pose_rotation(leg[1], Quaternion((th_b.inverse() * ca_b).orthonormalized()))
	skel.set_bone_pose_rotation(leg[2], Quaternion((ca_b.inverse() * ft_b).orthonormalized()))


## The shortest turn taking direction u onto v.
func _arc(u: Vector3, v: Vector3) -> Basis:
	var un := u.normalized()
	var vn := v.normalized()
	var ax := un.cross(vn)
	var s := ax.length()
	if s < 1e-6:
		return Basis.IDENTITY
	return Basis(ax / s, atan2(s, un.dot(vn)))


## An animation's rotation track per bone index, and its hips' position track ("hips").
func _bone_tracks(name: String, a: Animation, skel: Skeleton3D) -> Dictionary:
	if not _tracks.has(name):
		var tr := {"hips": -1}
		for k in range(a.get_track_count()):
			var bone := skel.find_bone(str(a.track_get_path(k)).get_slice(":", 1))
			if bone < 0:
				continue
			if a.track_get_type(k) == Animation.TYPE_ROTATION_3D:
				tr[bone] = k
			elif a.track_get_type(k) == Animation.TYPE_POSITION_3D and bone == _pelvis:
				tr["hips"] = k
		_tracks[name] = tr
	return _tracks[name]


## A player's hips in Oval3D's space, as drawn now.
func _hips_world(p: Dictionary) -> Transform3D:
	return (p["node"] as Node3D).transform * _rig * (p["skel"] as Skeleton3D).get_bone_global_pose(_pelvis)


## A take's hips at clip time c, in the figure's own space (read off the clip, not played).
func _clip_hips(ap: AnimationPlayer, anim: String, c: float) -> Transform3D:
	if not _hips.has(anim):
		var a := ap.get_animation(anim)
		var tr := [-1, -1]
		for k in range(a.get_track_count()):
			if str(a.track_get_path(k)).ends_with(":pelvis"):
				if a.track_get_type(k) == Animation.TYPE_POSITION_3D:
					tr[0] = k
				elif a.track_get_type(k) == Animation.TYPE_ROTATION_3D:
					tr[1] = k
		_hips[anim] = [a, tr]
	var a: Animation = _hips[anim][0]
	var tr: Array = _hips[anim][1]
	var skel: Skeleton3D = players[0]["skel"]
	var rest := skel.get_bone_rest(_pelvis)
	var pos := a.position_track_interpolate(tr[0], c) if tr[0] >= 0 else rest.origin
	var rot := a.rotation_track_interpolate(tr[1], c) if tr[1] >= 0 else rest.basis.get_rotation_quaternion()
	var up := skel.get_bone_parent(_pelvis)
	var parent := skel.get_bone_global_rest(up) if up >= 0 else Transform3D()
	return _rig * parent * Transform3D(Basis(rot), pos)


## The way a pair of hips faces, as a node yaw (0 faces +Z): from the hip-to-hip axis, which
## stays level whether he runs, bends or lies on his front.
func _yaw_of(b: Basis) -> float:
	var x := b.x
	return atan2(-x.z, x.x)


func _yaw_vec(v: Vector2) -> float:
	return atan2(v.x, v.y)


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


## A touch of the ball (or the man) at its moment of contact (Oval3D.anim_event). A tackle
## starts its pair if the run-in has not (the contact came without warning) and marks the
## contact's time; any other touch by a man in a pair takes him out of it.
func event(i: int, kind: StringName, at: Vector2, other := -1) -> void:
	if i < 0 or i >= _in.size():
		return
	if kind == &"ground_ball" and (_in[i] as Dictionary).is_empty():
		# He goes down for the loose ball (MatchDirector "scoop"), with the clip the director
		# chose for him: on the run at pace, or nearer and slower, gathered from a stand.
		var node: Node3D = players[i]["node"]
		var clip := int(director.tokens[i].get("scoop_k", MatchDirector.SCOOP_AT_PACE))
		var sc: Dictionary = MatchDirector.SCOOPS[clip]
		if not (players[i]["anim"] as AnimationPlayer).has_animation(str(sc["clip"])):
			return
		var here := Vector2(node.position.x, node.position.z)
		var to := at - here
		_snap(i, players[i])
		# The clip starts where the director's touch lands (both from his token's distance).
		var t0 := MatchDirector.scoop_from((director.tokens[i]["pos"] as Vector2).distance_to(at), clip)
		var side := float(sc["side"])
		var yaw := MatchDirector.scoop_yaw(to, clip) if to.length() > 0.05 else node.rotation.y
		var fw := Vector2(sin(yaw), cos(yaw))
		var hand := Vector2(-cos(yaw), sin(yaw))   # his right, facing fw
		# Placed so that his hands meet the ball at the touch; his hips start where they are,
		# and the difference eases out by the touch.
		var spot := at - fw * MatchDirector.scoop_lead(clip) - hand * side
		var run := maxf(float(sc["travel"]) - (float(sc["touch"]) - t0) * float(sc["run"]), 0.0)
		_once[i] = {"anim": str(sc["clip"]), "t": t0, "t0": t0, "touch": float(sc["touch"]),
				"end": float(sc["end"]), "yaw": yaw, "at": spot, "off": here - fw * run - spot}
		return
	var o: Dictionary = _once[i]
	if kind in [&"kick", &"handball", &"mark"]:
		if not o.is_empty() and str(o.get("how", "")) == str(kind):
			# The touch his clip was steering for: from here it plays at its own pace, and a
			# late clip jumps to its contact (eased from the pose he was in), never the ball
			# leaving or landing before boot, fist or hands are there.
			_arrive(i, o)
			return
		if (_in[i] as Dictionary).is_empty() and kind != &"mark":
			# No warning (the director gave no hold before it): the clip from CATCH_UP_MAX
			# before its contact, eased in from his stride, the ball held until boot or fist
			# meets it.
			if not o.is_empty():
				_end_once(i)
			var clip := _move_clip(i, str(kind))
			if clip != "":
				_start_move(i, clip, CATCH_UP_MAX, at, false)
				_arrive(i, _once[i])
			return
	if not o.is_empty():
		_end_once(i)
	if kind == &"tackle" and other >= 0 and other < _in.size() and not _pairs.is_empty():
		var pr: Dictionary = _in[i]
		if pr.is_empty() or int(pr["who"]) != i or int(pr["victim"]) != other:
			_start(i, other, true, at)
			return
		pr["arrived"] = true
		(pr["rec"] as Dictionary)["event_t"] = _clock
		(pr["rec"] as Dictionary)["at"] = at
		return
	var pr2: Dictionary = _in[i]
	if not pr2.is_empty() and int(pr2["victim"]) == i and kind in [&"mark", &"handball_receive", &"gather"] \
			and float(pr2["c"]) < float(pr2["cs"]):
		# He takes the ball as the tackle closes on him (caught holding it): the touch arrives
		# just after the clip started, and he stays in it to be tackled.
		return
	if not pr2.is_empty():
		_leave(i)


## The clip each move plays: a kick off his own foot (the player's "foot", right unless his
## record says left; a left-footer has a left-foot take), on the run or from a walk; a handball;
## a mark at the height the ball comes to him.
func _move_clip(i: int, how: String, high := true) -> String:
	var pick := ""
	match how:
		"kick":
			if str(players[i].get("foot", "R")) == "L":
				pick = "kick_on_run_02_run"
			elif (_pace[i] as Vector2).length() > RUN_FROM:
				pick = "kick_on_run_03"
			else:
				pick = "drop_punt_02"
		"handball":
			pick = "handball_on_run_01"
		"mark":
			pick = "overhead_mark_01" if high else "chest_mark_02"
	return pick if _moments.has(pick) else ""


## Each move clip's contact, measured once on the first figure as the game draws him: where the
## boot (its top, where the ball meets it) or the palms are at the contact frame, the way the
## swing or reach goes then (the clip's own aim, turned onto the target when played), and how high
## his palms hold the ball when the clip starts (where a dropped ball falls from).
func _read_moments(p: Dictionary) -> void:
	var res = load(MOMENTS)
	if not res is JSON:
		return
	var ap: AnimationPlayer = p["anim"]
	var data: Dictionary = (res as JSON).data
	for name in data:
		if not ap.has_animation(name):
			continue
		var m: Dictionary = (data[name] as Dictionary).duplicate()
		var c := float(m["contact"])
		ap.play(name)
		ap.seek(c, true)
		var at := _limb(p, str(m["limb"]))
		var hips := _clip_hips(ap, name, c).origin
		ap.seek(maxf(c - STEP, 0.0), true)
		var swing := at - _limb(p, str(m["limb"]))
		if str(m["kind"]) == "mark":
			swing = at - hips    # he faces the ball he marks
		ap.seek(float(m["start"]), true)
		m["at"] = at
		m["hips_c"] = Vector2(hips.x, hips.z)
		m["aim"] = atan2(swing.x, swing.z)
		_moments[name] = m
	ap.play("idle")


## A ball-handling bone's point in the figure's space: a boot's top or a palm (60% along the
## hand bone, the point Oval3D._hold_ball uses).
func _limb(p: Dictionary, limb: String) -> Vector3:
	var skel: Skeleton3D = p["skel"]
	if limb.begins_with("hand"):
		var palms := _palms(p)
		return (palms[0] + palms[1]) * 0.5
	var pose := skel.get_bone_global_pose(skel.find_bone(limb))
	return _rig * pose.origin + Vector3.UP * ON_BOOT


## Both palms in the figure's space, [left, right].
func _palms(p: Dictionary) -> Array:
	var skel: Skeleton3D = p["skel"]
	var out := []
	for k in range(2):
		var b := int((p["hands"] as Array)[k])
		var pose := skel.get_bone_global_pose(b)
		out.append(_rig * (pose.origin + pose.basis.y.normalized() * float(p["hand_len"][k]) * 0.6))
	return out


## A kick or handball coming from his hands, or a mark coming to them, close enough that its
## clip's lead from start to contact covers it: the clip starts.
func _move_due(i: int, holder: int) -> Dictionary:
	if _moments.is_empty():
		return {}
	var due := director.dispose_due(i) if i == holder else director.catch_due(i)
	if due.is_empty():
		return {}
	var how := str(due["how"])
	var clip := _move_clip(i, how, float(due.get("h", 2.4)) > 1.8)
	if clip == "":
		return {}
	var m: Dictionary = _moments[clip]
	if float(due["left"]) > float(m["contact"]) - float(m["start"]):
		return {}
	_start_move(i, clip, float(due["left"]), due.get("aim", Vector2.INF), false, due.get("from", Vector2.INF))
	return _once[i]


## Start a move clip `left` seconds before its contact. A kick or handball keeps his hips on the
## line he is running (where he will be at the contact), turned so the swing goes at `aim`; a
## mark puts his hands where the ball comes down (`aim`), facing back up its flight (`from`).
## His hips start where they are and ease onto the clip's own line by the contact (as a scoop).
func _start_move(i: int, clip: String, left: float, aim: Vector2, late: bool, from := Vector2.INF) -> void:
	var p: Dictionary = players[i]
	var m: Dictionary = _moments[clip]
	var node: Node3D = p["node"]
	var c := float(m["contact"])
	var t0 := c if late else clampf(c - left, float(m["start"]), c)
	var here := Vector2(node.position.x, node.position.z)
	var how := "mark" if str(m["kind"]) == "mark" else str(m["kind"])
	var yaw := node.rotation.y
	var face := yaw
	var spot := here
	if how == "mark":
		var land: Vector2 = aim if aim != Vector2.INF else here
		var back: Vector2 = (from - land) if from != Vector2.INF else Vector2.ZERO
		if back.length() > 0.5:
			yaw = atan2(back.x, back.y) - float(m["aim"])
		var at: Vector3 = m["at"]
		spot = land - Vector2(at.x, at.z).rotated(-yaw)
	else:
		# Where his token will be at the contact on the run it is making (_track_move keeps it
		# so), his hips turned the way he faces now.
		var meet := here + (director.tokens[i]["vel"] as Vector2) * MatchDirector.TEMPO * left
		var to: Vector2 = (aim - meet) if aim != Vector2.INF else Vector2.ZERO
		if to.length() > 1.0:
			yaw = atan2(to.x, to.y) - float(m["aim"])
		spot = meet - (m["hips_c"] as Vector2).rotated(-face)
	var ap: AnimationPlayer = p["anim"]
	var h0 := _clip_hips(ap, clip, t0).origin
	var hips_now := _hips_world(p).origin
	var off := Vector2(hips_now.x, hips_now.z) - (spot + Vector2(h0.x, h0.z).rotated(-face))
	_snap(i, p)
	_once[i] = {"anim": clip, "t": t0, "t0": t0, "touch": c, "end": float(m["end"]), "yaw": yaw,
			"at": spot, "off": off if t0 < c else Vector2.ZERO, "how": how, "rate": 1.0,
			"arrived": false, "kind": str(m["kind"])}
	if how != "mark":
		_once[i]["face"] = face
		_once[i]["aim"] = aim


## A kick or handball goes where his token goes. His hips meet the ball where his token is at
## the contact, on the run it is making now, re-aimed every frame: set once from his run as the
## clip began, a man turning to run in for his free kick ran the other way and was drawn 6 m
## from his token at the kick, the ball then flying sideways off his boot to the token's line
## (seed 20, Weddle). On a steady run the spot stays put and the clip's own run carries his
## hips there. He turns to the kick at a planted pivot (TURN_PLANTED), never in one frame;
## after the contact the spot runs on behind his token as his follow-through does.
func _track_move(o: Dictionary, pos: Vector2, vel: Vector2, dt: float) -> void:
	var m: Dictionary = _moments[str(o["anim"])]
	var left := (float(o["touch"]) - float(o["t"])) / maxf(float(o.get("rate", 1.0)), 0.05)
	var meet := pos + vel * MatchDirector.TEMPO * left
	var aim: Vector2 = o.get("aim", Vector2.INF)
	if aim != Vector2.INF and left > 0.0 and (aim - meet).length() > 1.0:
		o["yaw"] = atan2((aim - meet).x, (aim - meet).y) - float(m["aim"])
	var turn := TURN_PLANTED * dt if dt > 0.0 else PI
	o["face"] = rotate_toward(float(o["face"]), float(o["yaw"]), turn)
	o["at"] = meet - (m["hips_c"] as Vector2).rotated(-float(o["face"]))


## Before the touch, the clip's rate steers its contact onto the director's latest estimate.
func _steer(i: int, o: Dictionary) -> void:
	var due := director.dispose_due(i) if str(o["how"]) != "mark" else director.catch_due(i)
	if due.is_empty():
		return
	if o.has("drop"):
		# The ball is falling to his boot: the clip keeps the pace the fall was timed at.
		return
	var to_go := float(o["touch"]) - float(o["t"])
	o["rate"] = clampf(to_go / maxf(float(due["left"]), 0.02), MOVE_RATE_MIN, MOVE_RATE_MAX)


## Where the ball is drawn while his kick or handball has it (Oval3D draws it there), INF while
## it is simply between his palms. A handball sits on the palm that holds it until the fist goes
## through it. A kick's ball leaves both hands as late as it can still fall to the boot by the
## contact, and falls (gravity, from his palms to the top of his boot) to meet it.
func ball_at(i: int) -> Vector3:
	if i < 0 or i >= _once.size():
		return Vector3.INF
	var o: Dictionary = _once[i]
	if o.is_empty() or not str(o.get("kind", "")) in ["kick", "handball"]:
		return Vector3.INF
	var p: Dictionary = players[i]
	var m: Dictionary = _moments[str(o["anim"])]
	var node: Node3D = p["node"]
	var t := float(o["t"])
	var c := float(o["touch"])
	var xf := node.transform
	if t >= c:
		return xf * _limb(p, str(m["limb"]))
	if str(o["kind"]) == "handball":
		var palms := _palms(p)
		var hold: Vector3 = palms[1] if str(m["limb"]) == "hand_l" else palms[0]
		return xf * hold + Vector3.UP * ON_PALM
	var to := xf * (m["at"] as Vector3)
	if not o.has("drop"):
		# He lets go when the real seconds left to the contact are the time the ball takes to
		# fall from the hand that has it (where it is now) to the top of his boot: g, in real
		# time, whatever pace the clip is played at (measured 2026-11-22: a 0.5 s float, g 7.1,
		# when it was let go from between both palms).
		var hands := _guide(p, str(m["limb"]), xf)
		o["guide"] = float(hands["w"])
		var fall := sqrt(2.0 * maxf((hands["at"] as Vector3).y - to.y, 0.05) / GRAVITY)
		var left := (c - t) / maxf(float(o.get("rate", 1.0)), 0.05)
		if left > fall:
			return Vector3.INF if float(hands["w"]) <= 0.0 else hands["at"]
		o["drop"] = hands["at"]
		o["drop_base"] = xf.origin
		o["drop_clock"] = _clock
		o["drop_span"] = maxf(left, 0.01)
		o["drop_fall"] = o["drop_span"]   # the fall as first timed (measure_oval3d_moves)
		o["drop_g"] = GRAVITY
		o["drop_v0"] = ((to.y - (hands["at"] as Vector3).y) + 0.5 * GRAVITY * left * left) / maxf(left, 0.01)
	_carry_drop(o, xf)
	var from: Vector3 = o["drop"]
	var span := float(o["drop_span"])
	if _clock - float(o["drop_clock"]) >= span:
		# Fallen to the boot while the clip waits a frame or two short of its contact for the
		# director's touch (HOLD_SHORT): on the boot, which is all but there.
		return xf * _limb(p, str(m["limb"]))
	var tau := clampf(_clock - float(o["drop_clock"]), 0.0, span)
	var u := tau / span
	var g := float(o["drop_g"])
	o["drop_to"] = to
	return Vector3(lerpf(from.x, to.x, u), from.y + float(o["drop_v0"]) * tau - 0.5 * g * tau * tau, lerpf(from.z, to.z, u))


## A dropped ball goes on with the man who let it go: its fall starts where his hand was on him,
## and his figure is carried on to the contact (his run's spot is re-aimed every frame,
## _track_move). Left where the hand was on the ground, it fell up to 1.5 m behind his hips as he
## ran on to it (seed 42, held ball after the ends change).
func _carry_drop(o: Dictionary, xf: Transform3D) -> void:
	var base: Vector3 = o.get("drop_base", xf.origin)
	var moved := Vector3(xf.origin.x - base.x, 0.0, xf.origin.z - base.z)
	o["drop"] = (o["drop"] as Vector3) + moved
	if o.has("drop_to"):
		o["drop_to"] = (o["drop_to"] as Vector3) + moved
	o["drop_base"] = xf.origin


## A falling kick's ball now: [where it is, how fast it is falling (m/s, up +)].
func _drop_now(o: Dictionary) -> Array:
	var from: Vector3 = o["drop"]
	var span := float(o["drop_span"])
	var tau := clampf(_clock - float(o["drop_clock"]), 0.0, span)
	var g := float(o["drop_g"])
	var v0 := float(o["drop_v0"])
	var to: Vector3 = o.get("drop_to", from)
	var u := tau / span
	var at := Vector3(lerpf(from.x, to.x, u), from.y + v0 * tau - 0.5 * g * tau * tau, lerpf(from.z, to.z, u))
	return [at, v0 - g * tau]


## Where a kicker's hands have the ball before he drops it: between his palms while they are
## together, on the kick-side palm once they part (HELD_GAP..FREE_GAP). {at: world point, w: 0..1
## of the way to that palm}.
func _guide(p: Dictionary, limb: String, xf: Transform3D) -> Dictionary:
	var palms := _palms(p)
	var l: Vector3 = palms[0]
	var r: Vector3 = palms[1]
	var w := smoothstep(HELD_GAP, FREE_GAP, l.distance_to(r))
	var kick_hand: Vector3 = r if limb == "ball_r" else l
	return {"at": xf * ((l + r) * 0.5).lerp(kick_hand, w), "w": w}


## The way the ball's long axis points while his kick has it (world), ZERO when it simply lies
## across his palms. Across the palms while they hold it together, leaning GUIDE_TILT off the
## flat along his run once the kick-side hand has it alone, near upright as it drops.
func ball_axis(i: int) -> Vector3:
	if i < 0 or i >= _once.size():
		return Vector3.ZERO
	var o: Dictionary = _once[i]
	if o.is_empty() or str(o.get("kind", "")) != "kick" or float(o["t"]) >= float(o["touch"]):
		return Vector3.ZERO
	var p: Dictionary = players[i]
	var xf := (p["node"] as Node3D).transform
	var fwd := xf.basis.z
	fwd.y = 0.0
	fwd = fwd.normalized() if fwd.length() > 0.01 else Vector3.FORWARD
	if o.has("drop"):
		return fwd * cos(DROP_TILT) + Vector3.UP * sin(DROP_TILT)
	var w := float(o.get("guide", 0.0))
	if w <= 0.0:
		return Vector3.ZERO
	var palms := _palms(p)
	var across: Vector3 = xf.basis * ((palms[1] as Vector3) - (palms[0] as Vector3))
	var lean := fwd * cos(GUIDE_TILT) + Vector3.UP * sin(GUIDE_TILT)
	if across.length() < 0.01:
		return lean
	across = across.normalized()
	if across.dot(lean) < 0.0:
		across = -across
	return across.slerp(lean, w).normalized()


## The man who has marked the ball before the director gives it to him (see _step_once): the
## ball is drawn in his hands. -1 when there is none.
func caught() -> int:
	for i in range(_once.size()):
		var o: Dictionary = _once[i]
		if not o.is_empty() and o.has("caught") and o.get("keep", true):
			return i
	return -1


## A mark's last CATCH_EASE before its contact: the ball comes the rest of the way into his
## hands. {} when nobody's mark is that close. {to: between his palms, w: 0..1 of the way}.
func catch_at() -> Dictionary:
	for i in range(_once.size()):
		var o: Dictionary = _once[i]
		if o.is_empty() or str(o.get("kind", "")) != "mark" or o.get("arrived", false):
			continue
		var to_go := float(o["touch"]) - float(o["t"])
		if to_go > CATCH_EASE:
			continue
		var p: Dictionary = players[i]
		var palms := _palms(p)
		return {"to": (p["node"] as Node3D).transform * ((palms[0] + palms[1]) * 0.5),
				"w": 1.0 - clampf(to_go / CATCH_EASE, 0.0, 1.0)}
	return {}


## The director's touch for his move: a clip still short of its contact plays out at its fastest
## (a mark's at once: the ball is in his hands), whatever is left past CATCH_UP_MAX is cut.
func _arrive(i: int, o: Dictionary) -> void:
	o["arrived"] = true
	var to_go := float(o["touch"]) - float(o["t"])
	if o.has("drop") and to_go > 0.0:
		# The ball is already falling to his boot: the clip hurries to the contact and the fall
		# is re-timed to meet it from where the ball is now, never slower than gravity.
		_carry_drop(o, (players[i]["node"] as Node3D).transform)
		var now := _drop_now(o)
		var span := to_go / MOVE_RATE_MAX
		var to: Vector3 = (players[i]["node"] as Node3D).transform * ((_moments[str(o["anim"])] as Dictionary)["at"] as Vector3)
		var g := 2.0 * ((now[0] as Vector3).y + float(now[1]) * span - to.y) / (span * span)
		var v0 := float(now[1])
		if g < GRAVITY:
			g = GRAVITY
			v0 = (to.y - (now[0] as Vector3).y + 0.5 * g * span * span) / span
		o["drop"] = now[0]
		o["drop_clock"] = _clock
		o["drop_span"] = span
		o["drop_v0"] = v0
		o["drop_g"] = g
		o["rate"] = MOVE_RATE_MAX
		_launching = i
		return
	if to_go <= 0.0:
		o["rate"] = 1.0
		return
	if str(o["how"]) == "mark" or to_go > CATCH_UP_MAX:
		_snap(i, players[i])
		o["t"] = float(o["touch"]) - (0.0 if str(o["how"]) == "mark" else CATCH_UP_MAX)
	o["rate"] = MOVE_RATE_MAX
	if str(o["how"]) != "mark":
		_launching = i


## The man launch_pending draws the ball for, -1 when none.
func launching() -> int:
	return _launching


## The man whose kick or handball the director has already let go but whose clip has not reached
## its contact yet: where the ball is drawn until it does (on his palm, or falling to his boot).
## INF when there is none.
func launch_pending() -> Vector3:
	if _launching < 0:
		return Vector3.INF
	var o: Dictionary = _once[_launching]
	if o.is_empty() or not str(o.get("kind", "")) in ["kick", "handball"] or o.get("launched", false):
		_launching = -1
		return Vector3.INF
	if float(o["t"]) >= float(o["touch"]):
		# The contact frame itself: on the boot or fist, then the flight takes it.
		o["launched"] = true
	var at := ball_at(_launching)
	if at == Vector3.INF:
		# Still between his palms (a cut clip short of its drop).
		var palms := _palms(players[_launching])
		at = (players[_launching]["node"] as Node3D).transform * ((palms[0] + palms[1]) * 0.5)
	return at

