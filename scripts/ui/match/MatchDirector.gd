class_name MatchDirector
extends RefCounted
## Visual interpretation of a MatchSim event log.
##
## MatchSim decides everything that happens. Its log says who had the ball,
## where along the ground (fp, metres, side 0 attacking +x) and what they did.
## The director decides only how that looks: where across the ground the
## ball goes, how long it is in the air, who leads to it and who chases, how
## the teams hold their shape, and how stoppages and restarts are staged. It
## never reads or changes MatchSim, never writes to an event, and draws from
## its own random stream, so replaying a match cannot change it.
##
## Each event becomes a beat: a short list of phases (a kick in flight, a
## receiver collecting, the event itself, the carrier running on). The event
## is released to the match screen at the phase where it visibly happens: a
## mark when the ball is caught, a goal when it crosses the line.
##
## Shapes follow what real footage shows (see docs/MATCH_VIEW.md): most of the
## ground holds a structure and barely moves while six to ten players work
## around the ball; every player pairs with an opponent and one defender
## sits loose; centre bounces set up 6-6-6; kick-ins face a zone.

const DISPOSALS := ["handball", "kick", "mark"]
## Off-the-ball entries: an interchange, a coach's call, a player going off hurt.
const META := ["sub", "moment", "injury"]
const SUBSTEP := 1.0 / 60.0
const STRUCTURE_EVERY := 0.45
## Presentation time runs this much faster than the movement model's own
## clock: a broadcast pace, so a match fits a few minutes at the default 4x.
const TEMPO := 1.65

## Positions in the attacking frame of a side: x toward the goal it attacks.
## Paired names (FB/FF, BPL/FPL, ...) sit on the same ground, so every player
## has a direct opponent.
const SLOTS := {
	"RUCK": [["R", Vector2(-2, 3)]],
	"MID": [["C", Vector2(3, -5)], ["RR", Vector2(-6, 9)], ["RV", Vector2(-9, -9)],
			["WL", Vector2(0, -40)], ["WR", Vector2(0, 40)]],
	# In the selection's spot order (TeamBuilder.SPOTS): the goal-square post,
	# the flanks, the pockets, the centre half post - so the key posts the
	# selection gives its key players are the ones he stands in.
	"DEF": [["FB", Vector2(-68, 0)], ["HBL", Vector2(-40, -30)], ["HBR", Vector2(-40, 30)],
			["BPL", Vector2(-62, -20)], ["BPR", Vector2(-62, 20)], ["CHB", Vector2(-44, 0)]],
	"FWD": [["FF", Vector2(66, 0)], ["HFL", Vector2(38, -30)], ["HFR", Vector2(38, 30)],
			["FPL", Vector2(60, -20)], ["FPR", Vector2(60, 20)], ["CHF", Vector2(42, 0)]],
}
const EXTRA_SLOTS := [Vector2(-20, -16), Vector2(20, 16), Vector2(-20, 16),
		Vector2(20, -16), Vector2(-28, 0), Vector2(28, 0), Vector2(0, -24), Vector2(0, 24)]
const OPPOSITE := {"FB": "FF", "BPL": "FPL", "BPR": "FPR", "CHB": "CHF", "HBL": "HFL",
		"HBR": "HFR", "FF": "FB", "FPL": "BPL", "FPR": "BPR", "CHF": "CHB", "HFL": "HBL",
		"HFR": "HBR", "C": "C", "RR": "RR", "RV": "RV", "WL": "WL", "WR": "WR", "R": "R"}

## Centre-bounce set-up (attacking frame): at most four per side in the
## centre square, wingers on the wings, six in each 50 m arc. Defenders stand
## goal-side of their forward.
const CENTRE := {
	"R": Vector2(-1.2, 0), "C": Vector2(-5, -5), "RR": Vector2(-5, 5), "RV": Vector2(-9, 0),
	"WL": Vector2(-1, -36), "WR": Vector2(-1, 36),
	"FB": Vector2(-72, 0), "BPL": Vector2(-68, -15), "BPR": Vector2(-68, 15),
	"CHB": Vector2(-47, 0), "HBL": Vector2(-51, -22), "HBR": Vector2(-51, 22),
	"FF": Vector2(70, 0), "FPL": Vector2(66, -15), "FPR": Vector2(66, 15),
	"CHF": Vector2(45, 0), "HFL": Vector2(49, -22), "HFR": Vector2(49, 22),
}
const SQUARE := ["R", "C", "RR", "RV"]

## The zone a side sets against a kick-in (attacking frame of the zoning side,
## so these lines sit in the kicking side's back half).
const ZONE := {
	"FWD": [Vector2(50, -30), Vector2(50, -10), Vector2(50, 10), Vector2(50, 30),
			Vector2(64, -12), Vector2(64, 12)],
	"MID": [Vector2(24, -38), Vector2(24, -22), Vector2(24, -7), Vector2(24, 7),
			Vector2(24, 22), Vector2(24, 38)],
	"DEF": [Vector2(-2, -30), Vector2(-2, -10), Vector2(-2, 10), Vector2(-2, 30),
			Vector2(-22, -8), Vector2(-22, 8)],
}

var events: Array = []
var tokens: Array = []          # every token; ids index this array
var ball := {}
## Who is off the ground now, per side: [{num, pid, name}], from the result's
## opening bench (MatchSim.result "bench") and every interchange since. A player
## coming on leaves his place on the bench to the man he replaces. Empty for a
## result that does not say who was on the bench.
var bench: Array = [[], []]
var cursor := 0                 # next event to stage
var emitted := 0                # events released so far
var time := 0.0
var mode := "centre"            # camera hint: centre, stoppage, open, shot, kickin, break
var actor := -1                 # token id the feed is talking about
var flash := {}                 # {pos, left, goal}
## Every time the ball reaches an event's location: {idx, kind, pos, want_x}.
## Kept for the tests and the capture tool; bounded.
var arrivals: Array = []
## The moments a player touches the ball (or the man), for the 3D figures' clips (row 198):
## {who, kind, at, other}, recorded at contact (foot or hand on the ball), only while
## want_contacts is on; the 3D oval drains it every frame. `who` -1 on a bounce is the
## field umpire; `at` is where the ball goes (or the spot of the bounce, the tackle).
var contacts: Array = []
var want_contacts := false
var _last_how := &""

var _rng := RandomNumberGenerator.new()
var _ids := [{}, {}]            # side -> {num: token id}
var _beat := {}
var _phases: Array = []
var _pi := 0
var _pt := 0.0
var _locs := {}                 # event index -> planned ball location
var _busy := {}                 # token ids a phase is steering this beat
## Named receivers already leading to a future possession: token id -> event
## index. A lead holds until that event starts, so it never flickers back to
## structure mid-run.
var _lead := {}
var _struct_ball := Vector2.ZERO
var _poss := 0
var _struct_timer := 0.0
var _out: Array = []
## The match's own calls over time (MatchSim.timeline) and how far into them
## playback has got: per side, the entry in force.
var _timeline: Array = []
var _tl_i := 0
var _tac := [{}, {}]
## pid -> {def: a defender by trade, h: height in cm}, from the result's
## roster (its list_role) or the player's record (_who).
var _trade := {}
## Attack Corridor: each player's lane across the ground (token id -> y), fixed by
## his line's slot order (_attack_lanes), so the side narrows as a whole team.
var _lane := {}
## Win Contest: per side, the two half-line players shadowing the ball in open
## play, left one first (_pick_shadows).
var _shadow := [[], []]
## Win Contest: where the pack's ring is being set this beat (INF for none):
## the play's other runs keep clear of it (_clear_of_pack).
var _ring_at := Vector2.INF
## Win Contest: ball-ups pinned to where the ball was when the umpire called them
## (event k -> the shift from the logged spot), _pin_ballup.
var _ballup_pin := {}
## Bodies meant to touch in the beat now running (token id -> true): each
## phase's own players (a tackle's pair, a smother, a gather), a pack, the rucks
## at a bounce, a marking contest. MatchMotion lets these meet; everyone else
## steers round everyone (MatchMotion.avoid, hold_apart). _meant_now.
var _meant := {}
var _meant_beat := -1


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
func setup(result: Dictionary, p_events: Array) -> void:
	events = p_events
	cursor = 0
	emitted = 0
	time = 0.0
	actor = -1
	flash = {}
	arrivals = []
	_locs = {}
	_ballup_pin = {}
	_busy = {}
	_lead = {}
	_beat = {}
	_phases = []
	_out = []
	_timeline = result.get("timeline", [])
	_tl_i = 0
	_tac = [{}, {}]
	# Presentation stream: seeded from the fixture, never from MatchSim.
	_rng.seed = hash("%s|%s|%s|view" % [result.get("home", ""), result.get("away", ""),
			result.get("label", "")])
	_trade = {}
	for side_roster in result.get("roster", []):
		for p in (side_roster as Array):
			_trade[str(p.get("id", ""))] = _trade_of(str(p.get("id", "")), str(p.get("list_role", "")))
	_build_tokens(_starting_roster(result.get("roster", []), events))
	_lane = {}
	_attack_lanes(0)
	_attack_lanes(1)
	_shadow = [[], []]
	bench = [[], []]
	var opening: Array = result.get("bench", [])
	for side in range(mini(2, opening.size())):
		for p in (opening[side] as Array):
			(bench[side] as Array).append({"num": int(p.get("num", 0)), "pid": str(p.get("id", "")),
					"name": str(p.get("name", ""))})
	ball = {"pos": Vector2.ZERO, "h": 0.0, "mode": "dead", "holder": -1,
			"from": Vector2.ZERO, "to": Vector2.ZERO, "h0": 0.0, "h1": 0.0,
			"apex": 0.0, "dur": 1.0, "t": 0.0, "vel": Vector2.ZERO, "kind": ""}
	for id in range(tokens.size()):
		var t: Dictionary = tokens[id]
		var p := _centre_spot(t, -1)
		t["pos"] = p
		MatchMotion.set_goal(t, p, 0.0, true)
	mode = "centre"
	_struct_ball = Vector2.ZERO


## The 18 who started, per side. A finished match's roster lists who was on
## the ground at full time (then the bench who played); walking the log's
## interchanges backwards recovers the opening line-up, so the players at the
## first bounce - and every sub after it - are the real ones. A live match
## starts with no events, and its roster already is the opening 18.
static func _starting_roster(roster: Array, log: Array) -> Array:
	if roster.size() < 2:
		return roster
	var out := []
	for side in range(2):
		var all: Array = roster[side]
		# A sub takes the slot (and so the role) of the player he replaces:
		# walk back the players, keep the slots' roles.
		var on := []
		var roles := []
		for p in all.slice(0, 18):
			on.append(int(p.get("num", 0)))
			roles.append(str(p.get("role", "MID")))
		for i in range(log.size() - 1, -1, -1):
			var ev: Dictionary = log[i]
			if str(ev.get("kind", "")) != "sub" or int(ev.get("side", -1)) != side:
				continue
			var at := on.find(int(ev.get("num", -1)))
			if at >= 0:
				on[at] = int(ev.get("off_num", -1))
		var by_num := {}
		for p in all:
			by_num[int(p.get("num", 0))] = p
		var side_out := []
		for k in range(on.size()):
			if by_num.has(on[k]):
				var p: Dictionary = (by_num[on[k]] as Dictionary).duplicate()
				p["role"] = roles[k]
				side_out.append(p)
		out.append(side_out if side_out.size() == on.size() else all)
	return out


func _build_tokens(roster: Array) -> void:
	tokens = []
	_ids = [{}, {}]
	if roster.size() < 2:
		return
	for side in range(2):
		var groups := {"RUCK": [], "MID": [], "DEF": [], "FWD": []}
		for p in (roster[side] as Array).slice(0, 18):
			var r := str(p.get("role", "MID"))
			groups[r if groups.has(r) else "MID"].append(p)
		# The midfielders the match plays on the wings (Roles.mark_wings, carried
		# in the roster as "line") take the WL/WR slots; the rest fill the
		# centre square. Old results without the field keep list order.
		var inside := []
		var wings := []
		for p in groups["MID"]:
			(wings if str(p.get("line", "")) == "WING" else inside).append(p)
		# Three for the centre square, then the wings, then any extra.
		groups["MID"] = inside.slice(0, 3) + wings + inside.slice(3)
		var extra := 0
		for role in ["RUCK", "MID", "DEF", "FWD"]:
			var slots: Array = SLOTS[role]
			var list: Array = groups[role]
			for i in range(list.size()):
				var p: Dictionary = list[i]
				var slot := ""
				var base: Vector2
				if i < slots.size():
					slot = str(slots[i][0])
					base = slots[i][1]
				else:
					slot = "X%d" % extra
					base = EXTRA_SLOTS[extra % EXTRA_SLOTS.size()]
					extra += 1
				tokens.append(_make_token(p, side, role, slot, base))
	for id in range(tokens.size()):
		var t: Dictionary = tokens[id]
		t["id"] = id
		(_ids[int(t["side"])] as Dictionary)[int(t["num"])] = id
	# Direct opponents by paired slot, until the match's own calls say
	# otherwise (_assign).
	for t in tokens:
		t["match"] = -1
		t["loose"] = false
		t["tagging"] = false
		t["chasing"] = -1
		var want := str(OPPOSITE.get(str(t["slot"]), ""))
		if want != "":
			for o in tokens:
				if int(o["side"]) != int(t["side"]) and str(o["slot"]) == want:
					t["match"] = int(o["id"])
					break
		t["slot_match"] = t["match"]
	# Only a defender by trade minds a forward (_fit_defence).
	_assign()


func _make_token(p: Dictionary, side: int, role: String, slot: String, base: Vector2) -> Dictionary:
	var carry := 50.0
	var pl = GameDB.player_by_id(str(p.get("id", "")))
	if pl != null and pl.has("attr"):
		carry = float((pl["attr"] as Dictionary).get("carry", 50.0))
	# Speed from the carry rating (run-and-carry players are the quick ones);
	# presentation only, it never feeds back into the match.
	var top := 11.6 + 2.6 * clampf((carry - 50.0) / 50.0, -1.0, 1.0) + _rng.randf_range(-0.4, 0.4)
	if role == "RUCK":
		top *= 0.88
	var t := MatchMotion.make_token(Vector2.ZERO, top, _rng.randf_range(0.10, 0.30))
	t["side"] = side
	t["num"] = int(p.get("num", 0))
	t["name"] = GameDB.player_display_name_by_id(str(p.get("id", "")), str(p.get("name", "Player")))
	# Who he is, for the ring and the name over him (PitchView).
	t["pid"] = str(p.get("id", ""))
	t["surname"] = _surname(str(t["pid"]), str(t["name"]))
	t["role"] = role
	t["slot"] = slot
	t["base"] = base
	# A player's own habits: where he likes to stand relative to his slot, and
	# a slow wander so a held structure still breathes.
	t["jitter"] = Vector2(_rng.randf_range(-5, 5), _rng.randf_range(-4, 4))
	t["phase"] = _rng.randf_range(0.0, TAU)
	return t


# ---------------------------------------------------------------------------
# Frame update
# ---------------------------------------------------------------------------
## Advance presentation time by `dt` seconds (already scaled by playback
## speed). Returns the events released during the step, in log order.
func advance(dt: float) -> Array:
	_out = []
	dt *= TEMPO
	var n := maxi(1, ceili(dt / SUBSTEP))
	var h := dt / float(n)
	for i in range(n):
		_tick(h)
		# Stop at the final siren so the caller can close playback.
		if not _out.is_empty() and str((_out[-1] as Dictionary).get("kind", "")) == "final":
			break
	return _out


func idle() -> bool:
	return _beat.is_empty() and cursor >= events.size()


## The bodies meant to touch this beat (_meant). A new beat starts a new set,
## keeping only the last beat's bodies still in touch with each other (a pack
## breaking up as the ball comes out), so they part on their own runs.
func _meant_now() -> Dictionary:
	var k := int(_beat.get("k", -1))
	if k != _meant_beat and not _beat.is_empty():
		_meant_beat = k
		var still := {}
		var ids := _meant.keys()
		for a in range(ids.size()):
			for b in range(a + 1, ids.size()):
				var pa: Vector2 = tokens[int(ids[a])]["pos"]
				if pa.distance_to(tokens[int(ids[b])]["pos"]) < MatchMotion.BODY:
					still[int(ids[a])] = true
					still[int(ids[b])] = true
		_meant = still
	return _meant


## Note phase `p`'s own players as meant to touch (_meant): whoever it names,
## its pack, and the rucks at a bounce or throw-up.
func _mark_meant(p: Dictionary) -> void:
	var m := _meant_now()
	for key in ["who", "victim", "other", "by", "toward", "recv", "scoop", "along"]:
		if typeof(p.get(key)) == TYPE_INT and int(p[key]) >= 0:
			m[int(p[key])] = true
	for id in p.get("members", []):
		m[int(id)] = true
	for id in (p.get("spots", {}) as Dictionary):
		m[int(id)] = true
	if str(p.get("t", "")) in ["bounce", "throwup"]:
		for t in tokens:
			if str(t["role"]) == "RUCK" and (t["pos"] as Vector2).distance_to(p["at"]) < 40.0:
				m[int(t["id"])] = true


## A tackle being run down right now (the chase before the contact), for the 3D figures to
## start the tackle clip a moment early: {who, victim, left} with `left` the director seconds
## before the chase gives up and the tackle lands anyway; {} otherwise. Read-only.
func tackle_ahead() -> Dictionary:
	if str(_beat.get("kind", "")) != "tackle" or _pi >= _phases.size():
		return {}
	var p: Dictionary = _phases[_pi]
	if str(p.get("t", "")) != "chase" or not p.get("_entered", false):
		return {}
	return {"who": int(p["who"]), "victim": int(p["victim"]), "left": maxf(0.0, float(p["max"]) - _pt)}


func _tick(h: float) -> void:
	time += h
	var guard := 0
	while guard < 64:
		guard += 1
		if _beat.is_empty():
			if cursor >= events.size():
				break
			_start_beat(cursor)
			cursor += 1
		if not _run_phases(h if guard == 1 else 0.0):
			break
	_pin_called_ballup()
	_struct_timer -= h
	if _struct_timer <= 0.0:
		_struct_timer = STRUCTURE_EVERY
		_refresh_structure()
	# Motion limits (MatchMotion.SPRINT, WALK): whatever moved a token this
	# step, it moved no faster than a sprint.
	var from := []
	MatchMotion.avoid(tokens, _meant_now())
	for t in tokens:
		from.append(t["pos"])
		if not _on_feet(int(t["id"])):
			# Still in his tackle's take (down, then back up): his body is where the take put
			# him, so whatever the play asks of him waits until he is up.
			t["down"] = maxf(0.0, float(t["down"]) - h)
			t["vel"] = Vector2.ZERO
			continue
		MatchMotion.step(t, h)
	MatchMotion.separate(tokens, h)
	MatchMotion.hold_apart(tokens, from, _meant_now())
	for i in range(tokens.size()):
		MatchMotion.limit_step(tokens[i], from[i], h)
	_update_ball(h)
	_keep_off_ball()
	if not flash.is_empty():
		flash["left"] = float(flash["left"]) - h
		if float(flash["left"]) <= 0.0:
			flash = {}


## Run the current beat. Returns true when the beat finished (so the next one
## may start in the same tick), false while a phase is still running.
func _run_phases(h: float) -> bool:
	var guard := 0
	while _pi < _phases.size() and guard < 32:
		guard += 1
		var p: Dictionary = _phases[_pi]
		if not p.get("_entered", false):
			p["_entered"] = true
			_pt = 0.0
			_enter(p)
			_mark_meant(p)
		else:
			_pt += h
			h = 0.0
		if not _done(p):
			return false
		_pi += 1
	_beat = {}
	return true


# ---------------------------------------------------------------------------
# Beats
# ---------------------------------------------------------------------------
func _start_beat(k: int) -> void:
	_apply_timeline(k)
	var ev: Dictionary = events[k]
	var kind := str(ev.get("kind", ""))
	_beat = {"k": k, "kind": kind}
	_phases = []
	_pi = 0
	_busy = {}
	for t in tokens:
		t.erase("cap")
		t.erase("line")
	var side := int(ev.get("side", -1))
	if side >= 0 and not META.has(kind):
		_poss = side
	if kind == "ballup":
		_pin_ballup(k)
	match kind:
		"sub", "final", "injury":
			_phases = [{"t": "emit"}]
		"moment":
			_phases = [{"t": "emit"}, {"t": "wait", "dur": 0.5, "ease": true}]
		"quarter":
			mode = "break"
			_phases = [{"t": "emit"}, {"t": "wait", "dur": 1.6, "ease": true}]
		"free":
			_phases = _free_phases(k)
		"last_disposal", "out_on_full":
			_phases = _boundary_free_phases(k)
		"fifty":
			_phases = _fifty_phases(k)
		"throwin":
			_phases = _throwin_phases(k)
		"tackle":
			_phases = _tackle_phases(k)
		"smother":
			_phases = _smother_phases(k)
		"spoil":
			_phases = _spoil_phases(k)
		"pressure":
			_phases = _pressure_phases(k)
		"inside50":
			_phases = _inside50_phases(k)
		"goal", "behind":
			_phases = _shot_phases(k)
		"rebound":
			_phases = _rebound_phases(k)
		"pass":
			_phases = _pass_phases(k)
		"receive":
			_phases = _set_receive_phases(k)
		"pack":
			_phases = _pack_phases(k)
		"clanger":
			_phases = _clanger_phases(k)
		"ballup":
			_phases = _ballup_phases(k)
		_:
			if DISPOSALS.has(kind):
				_phases = _possession_phases(k)
			else:
				_phases = [{"t": "emit"}]
	_ring_at = Vector2.INF
	if (kind == "ballup" or kind == "throwin") and (_plan_of(0) == "contest" or _plan_of(1) == "contest"):
		var rat := _loc(k)
		_ring_at = rat if kind == "ballup" else Vector2(rat.x, rat.y * 0.78)
	_anticipate(k)
	var bp := _struct_ball
	if _phases.size() > 0 and str((_phases[0] as Dictionary).get("t", "")) == "flight":
		bp = (_phases[0] as Dictionary)["to"]
	_pick_shadows(bp)
	_refresh_structure()
	# Who works around the ball is settled once a beat, so the role does not
	# flick between neighbours (and send them back and forth) mid-play.
	_ball_zone(bp)


static func _possession(kind: String) -> bool:
	return DISPOSALS.has(kind) or kind == "clanger"


func _prev_real(k: int) -> int:
	var i := k - 1
	while i >= 0 and META.has(str((events[i] as Dictionary).get("kind", ""))):
		i -= 1
	return i


func _next_real(k: int) -> int:
	var i := k + 1
	while i < events.size() and META.has(str((events[i] as Dictionary).get("kind", ""))):
		i += 1
	return i if i < events.size() else -1


## How a possession event starts: from open play, a centre bounce, a kick-in,
## a ball-up, a free kick or a loose ball. Read straight from the event before
## it, matching MatchSim's restarts: a goal or a quarter break -> centre
## bounce, a behind -> kick-in from the goal square, a logged "ballup" ->
## ball-up where play stopped.
func _restart(k: int) -> String:
	var ev: Dictionary = events[k]
	var pk := _prev_real(k)
	var pkind := "" if pk < 0 else str((events[pk] as Dictionary).get("kind", ""))
	match pkind:
		"", "goal", "quarter":
			return "centre"
		"behind":
			return "kickin"
		"ballup":
			return "ballup"
		"throwin":
			return "throwin"
		"free", "last_disposal", "out_on_full", "fifty":
			return "free"
		"clanger", "tackle", "smother", "spoil":
			# No stoppage logged: the ball is won where it fell.
			return "loose"
	return "open"


func _possession_phases(k: int) -> Array:
	var ev: Dictionary = events[k]
	var a := _actor_id(ev)
	var kind := str(ev.get("kind", ""))
	var loc := _loc(k)
	var tail := _receive(k, a)
	match _restart(k):
		"centre":
			return _centre_phases(k, a, loc) + tail
		"kickin":
			return _kickin_phases(k, a, loc) + tail
		"ballup":
			# The ruck's tap to the player who wins it, out of the ball-up beat.
			return [{"t": "flight", "to": loc, "dur": 0.3, "apex": 0.8, "h0": 3.0, "recv": a, "how": "ruck_tap"}] + tail
		"throwin":
			# The boundary umpire has the ball on the line; throw it back into
			# the pack and let the logged winner collect it.
			return [{"t": "flight", "to": loc, "dur": 0.55, "apex": 6.0, "h0": 1.0, "recv": a}] + tail
		"free":
			# The free's taker kicks it to the man who wins it: he has the ball
			# in his hands first (seed 31 FRE v STK: the ball rolled loose
			# through the free and flew off with nobody within 4 m of it).
			# Played on to himself, he runs it to the spot instead.
			var taker := _free_taker_of(k)
			var take := _take_free(taker)
			if taker >= 0 and taker == a:
				return take + [{"t": "hold", "who": a, "carry": loc, "run": true,
						"max": (ball["pos"] as Vector2).distance_to(loc) / float(tokens[a]["top"]) * 1.6 + 0.5}] + tail
			# The ball comes to the mark as a kick would: 0.4 s when it is close,
			# and a kick's own time when it is not (a fixed 0.4 s sent it 52 m
			# from the boundary line in one frame at 8x).
			var back := _flight_shape("kick", (ball["pos"] as Vector2).distance_to(loc))
			return take + [{"t": "wait", "dur": 0.3, "ease": true},
					{"t": "flight", "to": loc, "dur": maxf(0.4, back.x),
						"apex": 1.5 if back.x <= 0.4 else back.y, "recv": a}] + tail
		"loose":
			return tail
	var pk := _prev_real(k)
	var prev: Dictionary = events[pk] if pk >= 0 else {}
	var hb := str(prev.get("kind", "")) == "handball"
	var d := (ball["pos"] as Vector2).distance_to(loc)
	if d < FLIGHT_MIN:
		# The ball is already where this possession is won (two events past
		# the goal line both clamp to it): the receiver comes and takes it. A
		# flight of no length only lifted the ball and held it there, hanging
		# 2.45 m up while the marker ran in (picture_truth, traits' 2027 match).
		return tail
	if hb and d > 18.0:
		hb = false
	var shape := _flight_shape("handball" if hb else "kick", d)
	var flight := {"t": "flight", "to": loc, "dur": shape.x, "apex": shape.y, "recv": a,
			"adapt": true, "h1": 2.4 if kind == "mark" else 1.0}
	if hb:
		flight["hang"] = HANDBALL_HANG_MAX
		flight["how"] = "handball"
	if not prev.is_empty() and int(prev.get("side", -1)) != int(ev.get("side", -1)):
		# Possession changed hands without an event (the chain broke down):
		# show the ball won in a contest.
		flight["contest"] = true
	return [flight] + tail


## The receiver takes the ball at its logged spot. The event is released when
## he gets there, or once the ball has sat there a moment (a bobble he is still
## running onto), so a late arrival never holds up the log.
func _receive(k: int, a: int) -> Array:
	# About to be tackled or smothered: he runs onto it where it lies, and is
	# caught there. A rolled ball would be steered to a far receiver, and the
	# next event released metres from its logged spot (a smother 15.8 m off).
	var nk := _next_real(k)
	var roll := not (nk >= 0 and str((events[nk] as Dictionary).get("kind", "")) in ["tackle", "pressure", "smother"])
	return [{"t": "collect", "who": a, "max": 0.25}, {"t": "emit", "log": true},
			{"t": "collect", "who": a, "roll": roll}, {"t": "possess", "who": a}, _hold(k, a)]


func _hold(k: int, who: int) -> Dictionary:
	var kind := str((events[k] as Dictionary).get("kind", ""))
	var dur := 0.07 + _rng.randf_range(0.0, 0.06)
	if kind == "mark":
		dur = 0.32
	elif kind == "kick":
		dur = 0.12 + _rng.randf_range(0.0, 0.08)
	var nk := _next_real(k)
	var carry := Vector2.INF
	if nk >= 0 and who >= 0:
		var nev: Dictionary = events[nk]
		var nkind := str(nev.get("kind", ""))
		if nkind == "tackle" or nkind == "pressure":
			return {"t": "hold", "who": who, "dur": 0.05}
		if (DISPOSALS.has(nkind) or nkind == "inside50" or nkind == "clanger") \
				and _restart(nk) == "open" and int(nev.get("side", -1)) == int((events[k] as Dictionary).get("side", -2)):
			# The carrier runs on toward the next contest before disposing,
			# which is where most metres come from in real ball movement.
			var here := _loc(k)
			var there := _loc(nk)
			var gap := here.distance_to(there)
			if kind == "handball" and gap > HANDBALL_REACH and gap - HANDBALL_DISH <= HANDBALL_RUN_MAX:
				# Run it down and dish off short: a handball, never a
				# 30 m flick drawn as a kick.
				var dish := there + (here - there).normalized() * HANDBALL_DISH
				return {"t": "hold", "who": who, "dur": dur, "carry": dish, "run": true,
						"max": (gap - HANDBALL_DISH) / float(tokens[who]["top"]) * 1.6 + 0.5}
			carry = here + (there - here).limit_length(minf(10.0, gap * 0.3))
	return {"t": "hold", "who": who, "dur": dur, "carry": carry}


func _centre_phases(k: int, a: int, loc: Vector2) -> Array:
	var pk := _prev_real(k)
	var after_goal := pk >= 0 and str((events[pk] as Dictionary).get("kind", "")) == "goal"
	var layout := {}
	for t in tokens:
		layout[int(t["id"])] = _centre_spot(t, a)
	return [
		{"t": "setup", "layout": layout, "ball_to": Vector2.ZERO, "mode": "centre", "keep": a,
			"min": 1.1 if after_goal else 0.8, "max": 4.0},
		{"t": "wait", "dur": 0.3},
		{"t": "bounce", "at": Vector2.ZERO, "recv": a, "loc": loc},
		{"t": "flight", "to": loc, "dur": 0.3, "apex": 0.6, "h0": 3.5, "recv": a, "how": "ruck_tap"},
	]


## A kick-in after a behind, as MatchSim plays it: the defending side restarts
## from its goal square (the logged fp) with no contest, while the side that
## scored sets a zone. `kicker` takes the ball there; the kick itself is the
## logged disposal that follows.
func _kickin_phases(k: int, kicker: int, g: Vector2) -> Array:
	var pk := _prev_real(k)
	var kside := 1 - int((events[pk] as Dictionary).get("side", 0))
	var dir := _dir(kside)
	if kicker < 0 or int(tokens[kicker]["side"]) != kside:
		# No logged kicker yet (an error logged first): the full back has it.
		kicker = -1
		var best := INF
		for t in tokens:
			if int(t["side"]) == kside and str(t["role"]) == "DEF":
				var d := (t["pos"] as Vector2).distance_to(g)
				if d < best:
					best = d
					kicker = int(t["id"])
	var layout := {}
	var zone_side := 1 - kside
	var used := {"FWD": 0, "MID": 0, "DEF": 0}
	for t in tokens:
		var id := int(t["id"])
		if id == kicker:
			layout[id] = g + Vector2(dir * 1.0, 0)
		elif int(t["side"]) == zone_side:
			var grp := "MID" if str(t["role"]) == "RUCK" else str(t["role"])
			var pts: Array = ZONE.get(grp, ZONE["MID"])
			var i := int(used.get(grp, 0))
			used[grp] = i + 1
			var p: Vector2 = pts[i] if i < pts.size() else Vector2(12, -20 + 10 * (i - pts.size()))
			layout[id] = Vector2(p.x * _dir(zone_side), p.y) + (t["jitter"] as Vector2) * 0.4
		else:
			layout[id] = _structure_spot(t, g, kside)
	return [
		{"t": "setup", "layout": layout, "ball_to": g, "mode": "kickin", "min": 0.9, "max": 4.0, "keep": kicker},
		{"t": "collect", "who": kicker},
		{"t": "possess", "who": kicker, "quiet": true},
		{"t": "wait", "dur": 0.3},
	]


## A logged ball-up: the ball gets to where play stopped (the kick or scramble
## that ended the chain), a pack forms, the umpire throws it up. The tap to
## whoever wins it opens the next beat.
func _ballup_phases(k: int) -> Array:
	var at := _loc(k)
	var out := []
	var d := (ball["pos"] as Vector2).distance_to(at)
	if d > 3.0:
		var shape := _flight_shape("kick", d)
		out.append({"t": "flight", "to": at, "dur": shape.x, "apex": shape.y, "recv": -1,
				"mode": "stoppage"})
	elif _ballup_pin.has(k) and (_ballup_pin[k] as Vector2).length() > 3.0:
		# Pinned to the ball (Win Contest): no flight to the logged spot, but the
		# ball-up keeps the time that flight took, so the pack forms and every
		# later beat runs when it did before the pin.
		out.append({"t": "wait", "dur": _flight_shape("kick", (_ballup_pin[k] as Vector2).length()).x,
				"drop": at})
	var nk := _next_real(k)
	var winner := _actor_id(events[nk]) if nk >= 0 else -1
	var members := _nearest(at, 0, _pack_n(0), [winner]) + _nearest(at, 1, _pack_n(1), [winner])
	for t in tokens:
		if str(t["role"]) == "RUCK" and not members.has(int(t["id"])):
			members.append(int(t["id"]))
	if winner >= 0 and not members.has(winner):
		members.append(winner)
	var extra := _pack_n(0) + _pack_n(1) - 6
	out += [{"t": "pack", "at": at, "members": members, "min": 0.35, "max": 0.9 + PACK_EXTRA_WAIT * extra,
				"need": 4 + extra, "mode": "stoppage", "winner": winner, "drop": at},
			{"t": "throwup", "at": at},
			{"t": "emit", "log": true}]
	return out


## The disposal has crossed the line. The ball reaches the boundary and the
## nearby players form a pack; the next possession beat is the actual throw-in.
func _throwin_phases(k: int) -> Array:
	var at := _loc(k)
	var out := []
	var d := (ball["pos"] as Vector2).distance_to(at)
	if d > 2.0:
		var shape := _flight_shape("kick", d)
		out.append({"t": "flight", "to": at, "dur": shape.x, "apex": shape.y,
				"recv": -1, "mode": "stoppage"})
	var infield := Vector2(at.x, at.y * 0.78)
	var nk := _next_real(k)
	var winner := _actor_id(events[nk]) if nk >= 0 else -1
	var members := _nearest(infield, 0, _pack_n(0), [winner]) + _nearest(infield, 1, _pack_n(1), [winner])
	for t in tokens:
		if str(t["role"]) == "RUCK" and not members.has(int(t["id"])):
			members.append(int(t["id"]))
	if winner >= 0 and not members.has(winner):
		members.append(winner)
	var extra := _pack_n(0) + _pack_n(1) - 6
	out += [{"t": "pack", "at": infield, "members": members, "min": 0.25, "max": 0.75 + PACK_EXTRA_WAIT * extra,
				"need": 4 + extra,
				"mode": "stoppage", "winner": winner},
			{"t": "emit", "log": true}]
	return out


## A last-disposal or out-on-full free: show the ball crossing the line. The
## following possession beat uses the normal free-kick restart.
func _boundary_free_phases(k: int) -> Array:
	var at := _loc(k)
	var out := []
	var d := (ball["pos"] as Vector2).distance_to(at)
	if d > 2.0:
		var shape := _flight_shape("kick", d)
		out.append({"t": "flight", "to": at, "dur": shape.x, "apex": shape.y,
				"recv": -1, "mode": "stoppage"})
	out += [{"t": "emit", "log": true}] + _take_free(_actor_id(events[k])) + [{"t": "wait", "dur": 0.35, "ease": true}]
	return out


## Walk the mark 50m toward goal. The recipient does not take possession
## until the following free-kick restart beat.
func _fifty_phases(k: int) -> Array:
	var at := _loc(k)
	var d := (ball["pos"] as Vector2).distance_to(at)
	var who := _actor_id(events[k])
	var out := []
	if d > 1.0 and who >= 0:
		# He has the ball from the free (or takes it where it lies first): he
		# carries it up to the new mark, as a player does. A ball flown 50 m
		# ahead of him lay alone for six seconds while he ran to it
		# (picture_truth, a 49 m penalty), and a ball flown with nobody kicking
		# it breaks the oval's first rule.
		out += _take_free(who)
		out.append({"t": "hold", "who": who, "carry": at, "run": true, "mode": "stoppage",
				"max": d / float(tokens[who]["top"]) * 1.6 + 0.5})
	elif d > 1.0:
		# Never quicker than a kick covers the ground: 0.35 + d / 110 sent a
		# 50 m penalty's ball at 62.2 m a second (picture_truth, ball speed).
		out.append({"t": "flight", "to": at,
				"dur": maxf(clampf(0.35 + d / 110.0, 0.35, 0.9), _flight_shape("kick", d).x),
				"apex": 1.2, "recv": who, "mode": "stoppage"})
	out += [{"t": "emit", "log": true}, {"t": "wait", "dur": 0.25, "ease": true}]
	return out


func _tackle_phases(k: int) -> Array:
	var ev: Dictionary = events[k]
	var tk := _actor_id(ev)
	var victim := int(ball["holder"])
	if victim >= 0 and int(tokens[victim]["side"]) == int(ev.get("side", -1)):
		victim = -1
	if victim < 0:
		var pk := _prev_real(k)
		if pk >= 0:
			victim = _actor_id(events[pk])
	if tk < 0 or victim < 0:
		return [{"t": "emit", "log": true}]
	return [{"t": "chase", "who": tk, "victim": victim, "max": 1.6},
			{"t": "emit", "log": true},
			{"t": "down", "who": tk, "victim": victim, "dur": 0.55}]


## Pressure that forces a turnover: the presser closes on the carrier and
## the ball spills to him, no stoppage.
## A blocked kick: the defender reaches the boot, the ball spills and both
## sides react to the loose ball. No automatic possession is invented here.
func _smother_phases(k: int) -> Array:
	var ev: Dictionary = events[k]
	var who := _actor_id(ev)
	var victim := int(ball["holder"])
	if who < 0 or victim < 0:
		return [{"t": "emit", "log": true}, {"t": "fumble", "dur": 0.25}]
	return [{"t": "chase", "who": who, "victim": victim, "max": 0.8},
			{"t": "emit", "log": true},
			{"t": "fumble", "dur": 0.25, "how": "smother", "who": who, "other": victim}]


## A spoil happens at the drop of the ball and leaves it alive on the deck.
func _spoil_phases(k: int) -> Array:
	var ev: Dictionary = events[k]
	var who := _actor_id(ev)
	var loc := _loc(k)
	var out := []
	var d := (ball["pos"] as Vector2).distance_to(loc)
	if d > 1.0:
		var shape := _flight_shape("kick", d)
		out.append({"t": "flight", "to": loc, "dur": shape.x, "apex": shape.y,
				"recv": -1, "mode": "open"})
	if who >= 0:
		out.append({"t": "collect", "who": who, "max": 0.18})
	out += [{"t": "emit", "log": true}, {"t": "fumble", "dur": 0.28, "how": "spoil", "who": who}]
	return out


func _pressure_phases(k: int) -> Array:
	var ph := _tackle_phases(k)
	if ph.size() < 3:
		return ph
	var who := int((ph[0] as Dictionary)["who"])
	# A presser the chase left short: the spilled ball comes his way off the
	# men nearest it, as a free's taker's does (seed 1 RIC v SYD k511, k545:
	# 20-29 m off, the ball waited 1.8-2.5 s).
	return [ph[0], ph[1], {"t": "collect", "who": who, "roll": true}, {"t": "possess", "who": who}]


func _inside50_phases(k: int) -> Array:
	var ev: Dictionary = events[k]
	var a := _actor_id(ev)
	var out := []
	if a >= 0 and int(ball["holder"]) != a:
		out += [{"t": "collect", "who": a}, {"t": "possess", "who": a, "quiet": true}]
	var loc := _loc(k)
	var nk := _next_real(k)
	var recv := _actor_id(events[nk]) if nk >= 0 else -1
	var src: Vector2 = ball["pos"]
	if nk >= 0 and str(events[nk].get("kind", "")) == "mark" and (events[nk] as Dictionary).has("band"):
		# He marks where he kicks from (T2.24): the entry lands on the set
		# shot's spot, on the side of the ground it was coming down. Not when
		# that spot is well behind the kicker (an entry logged on the goal line
		# with a 45 m band): an entry never flies back towards his own goal.
		var spot := _set_spot(int(events[nk].get("side", 0)), str(events[nk]["band"]), loc.y)
		if (spot.x - src.x) * _dir(int(ev.get("side", 0))) > -SET_SPOT_BACK:
			loc = spot
			_locs[nk] = loc
	var d := src.distance_to(loc)
	var shape := _flight_shape("kick", d)
	out += [{"t": "emit"},
			{"t": "flight", "to": loc, "dur": shape.x, "apex": shape.y + 3.0, "recv": recv,
				"adapt": true, "contest": true, "log_k": k, "mode": "shot"},
			{"t": "wait", "dur": 0.1}]
	return out


func _shot_phases(k: int) -> Array:
	var ev: Dictionary = events[k]
	var s := _actor_id(ev)
	var side := int(ev.get("side", 0))
	var goal := str(ev.get("kind", "")) == "goal"
	var gy := _rng.randf_range(-2.4, 2.4) if goal \
			else signf(_rng.randf() - 0.5) * _rng.randf_range(4.0, 8.5)
	var target := Vector2(MatchMotion.GOAL_X * _dir(side), gy)
	var out := []
	# A bomb that sailed over the pack is still in the air: no new kick.
	var pk := _prev_real(k)
	var over := pk >= 0 and str((events[pk] as Dictionary).get("kind", "")) == "pack" \
			and str((events[pk] as Dictionary).get("outcome", "")) == "through"
	# A set shot (from a mark) is staged: he steps back and the ground holds.
	# In open play he kicks on the move and everyone else keeps playing.
	var set_shot := bool(ev.get("set_shot", true))
	if over:
		pass
	elif s >= 0 and set_shot:
		out += [{"t": "collect", "who": s}, {"t": "possess", "who": s, "quiet": true},
				{"t": "hold", "who": s, "dur": 0.45, "carry": Vector2.INF, "back": true}]
	elif s >= 0:
		var on := (target - (ball["pos"] as Vector2)).normalized() * 4.0
		# He runs onto it before he shoots: capped at 0.35 s, the ball was put
		# in his hands from up to 4.6 m and kicked from where it lay (seed 31
		# FRE v STK, five open-play shots).
		out += [{"t": "collect", "who": s, "roll": true}, {"t": "possess", "who": s, "quiet": true},
				{"t": "hold", "who": s, "dur": 0.0, "carry": (ball["pos"] as Vector2) + on}]
	var d := (ball["pos"] as Vector2).distance_to(target)
	if not set_shot:
		out.append({"t": "crumb", "at": target, "side": side})
	out += [{"t": "flight", "to": target, "dur": 0.3 + d / 48.0, "apex": 3.0 + d * 0.14,
				"recv": -1, "mode": "shot"},
			{"t": "emit", "log": true, "flash": "goal" if goal else "behind"},
			{"t": "celebrate", "who": s, "dur": 1.2 if goal else 0.45}]
	return out


## ARD-M4-013: the coach's set-shot call, staged from what the log names.
## Each call starts the same way, at the mark (he steps back, the ground
## holds), then looks different: he shoots, plays on to a teammate leading
## up, or bombs it high into a goal-square pack.
func _set_up(who: int) -> Array:
	if who < 0:
		return []
	return [{"t": "collect", "who": who}, {"t": "possess", "who": who, "quiet": true},
			{"t": "hold", "who": who, "dur": 0.45, "carry": Vector2.INF, "back": true}]


## Plays on: a short kick to the teammate leading up, or to the defender who
## cuts it off (a rebound follows when it is intercepted).
func _pass_phases(k: int) -> Array:
	var s := _actor_id(events[k])
	var out := _set_up(s) + [{"t": "emit", "log": true}]
	var nk := _next_real(k)
	if nk < 0:
		return out
	var nev: Dictionary = events[nk]
	var r := _actor_id(nev)
	if r < 0:
		return out
	var to: Vector2 = _loc(nk) if str(nev.get("kind", "")) == "receive" else (tokens[r]["pos"] as Vector2)
	var d := (ball["pos"] as Vector2).distance_to(to)
	var shape := _flight_shape("kick", d)
	out.append({"t": "flight", "to": to, "dur": shape.x, "apex": shape.y, "recv": r,
			"adapt": true, "h1": 2.4, "mode": "open"})
	return out


## He marks the pass on the lead: his own set shot follows.
func _set_receive_phases(k: int) -> Array:
	var a := _actor_id(events[k])
	if a < 0:
		return [{"t": "emit", "log": true}]
	return [{"t": "collect", "who": a, "max": 0.3}, {"t": "possess", "who": a},
			{"t": "emit", "log": true}]


## Bombed into the goal square: the named players and the nearest of each
## side form the pack under a high ball; it ends as the log says. "through"
## leaves the ball with the kicker, whose own shot follows over the pack.
func _pack_phases(k: int) -> Array:
	var ev: Dictionary = events[k]
	var side := int(ev.get("side", 0))
	var outcome := str(ev.get("outcome", ""))
	var kicker := int(ball["holder"])
	if kicker < 0 and outcome == "through":
		kicker = _actor_id(ev)
	var at := Vector2(clampf(float(ev.get("fp", 0.0)), -MatchMotion.GOAL_X, MatchMotion.GOAL_X), 0.0)
	var named := {}
	for key in ["marker_id", "spoiler_id", "crumber_id", "defender_id"]:
		var t := _token_by_pid(str(ev.get(key, "")))
		if t >= 0:
			named[key] = t
	var members := []
	for key in named:
		if not members.has(named[key]) and key != "crumber_id":
			members.append(named[key])
	var skip := members + ([kicker] if kicker >= 0 else [])
	members += _nearest(at, side, 2, skip) + _nearest(at, 1 - side, 2, skip)
	var out := _set_up(kicker)
	out.append({"t": "pack", "at": at, "members": members, "min": 0.3, "max": 1.0, "mode": "shot"})
	# The crumber lurks at the front of the pack, not in it.
	if named.has("crumber_id"):
		var front := at - Vector2(6.0 * _dir(side), 0.0)
		out.append({"t": "hold", "who": named["crumber_id"], "dur": 0.0, "carry": front})
	var d := (ball["pos"] as Vector2).distance_to(at)
	var flight := {"t": "flight", "to": at, "dur": 0.4 + d / 42.0, "apex": clampf(8.0 + d * 0.25, 10.0, 18.0),
			"recv": -1, "h1": 2.6, "mode": "shot"}
	match outcome:
		"through":
			# Over every hand in the pack: the score beat carries it on.
			flight["h1"] = 5.5
			out.append(flight)
			return out + [{"t": "emit", "log": true}]
		"marked", "defence":
			var who := int(named.get("marker_id" if outcome == "marked" else "defender_id", -1))
			flight["recv"] = who
			out.append(flight)
			if who >= 0:
				out += [{"t": "possess", "who": who}]
			return out + [{"t": "emit", "log": true}]
		_:
			# Spoiled: a fist in the pack and the ball spills to the deck.
			out.append(flight)
			var sp := int(named.get("spoiler_id", -1))
			if sp >= 0:
				out.append({"t": "collect", "who": sp, "max": 0.18})
			return out + [{"t": "emit", "log": true}, {"t": "fumble", "dur": 0.28}]


func _token_by_pid(pid: String) -> int:
	if pid == "":
		return -1
	for t in tokens:
		if str(t["pid"]) == pid:
			return int(t["id"])
	return -1


## A free paid off a kick or handball (a block in the marking contest) is given
## where that ball came down, and the log has no landing of its own. So the
## disposal is drawn to the free's spot here; without it the ball stayed on the
## boot and reached the free's taker on a 0.4 s rocket, back past him (seed 43:
## 36 m, a defender's clearing kick).
func _free_phases(k: int) -> Array:
	var out := []
	var pk := _prev_real(k)
	var pkind := "" if pk < 0 else str((events[pk] as Dictionary).get("kind", ""))
	if pkind in ["kick", "handball"]:
		var loc := _loc(k)
		var d := (ball["pos"] as Vector2).distance_to(loc)
		if d > 1.0:
			var shape := _flight_shape("handball" if pkind == "handball" and d < 18.0 else "kick", d)
			out.append({"t": "flight", "to": loc, "dur": shape.x, "apex": shape.y, "recv": _actor_id(events[k])})
	# The umpire pays it, and the man it is paid to takes the ball: it never
	# rolls on through the free with nobody's hands on it.
	return out + [{"t": "emit"}] + _take_free(_actor_id(events[k])) + [{"t": "wait", "dur": 0.5, "ease": true}]


## The free's taker goes to the ball and has it in his hands (nothing when he
## already has it, or the log names nobody).
func _take_free(who: int) -> Array:
	if who < 0:
		return []
	if str(ball["mode"]) == "held" and int(ball["holder"]) == who:
		return []
	# (A ball still loose comes his way off the men round it, as any loose
	# ball does: walking 30 m to a ball nobody touches is play waiting.)
	return [{"t": "collect", "who": who, "roll": true}, {"t": "possess", "who": who, "quiet": true}]


## Who takes the free a possession beat restarts from: the man the free
## before it was paid to (-1 when there is none).
func _free_taker_of(k: int) -> int:
	var pk := _prev_real(k)
	if pk < 0 or not str((events[pk] as Dictionary).get("kind", "")) in ["free", "last_disposal", "out_on_full", "fifty"]:
		return -1
	return _actor_id(events[pk])


## Won back straight after a free kick: the free kick's set shot fell short
## and a back gathers it. The set shot is drawn from where the ball is to his
## logged spot; without it he took it where the free was given away (seed 42:
## 16 m off its spot).
func _rebound_phases(k: int) -> Array:
	var a := _actor_id(events[k])
	if _short_set_shot(k) and _locs.has(_prev_real(k)):
		# Set again here: a look-ahead may have cached the logged fp before the
		# mark was moved to its band's spot (seed 42 ev 947 flew 40 m back).
		_locs[k] = _short_spot(k)
	if _restart(k) == "free" or _short_set_shot(k):
		var loc := _loc(k)
		var d := (ball["pos"] as Vector2).distance_to(loc)
		if d > 1.0:
			var shape := _flight_shape("kick", d)
			return [{"t": "flight", "to": loc, "dur": shape.x, "apex": shape.y, "recv": a}] + _receive(k, a)
	return _receive(k, a)


## A rebound straight after a set-shot mark (one MatchSim tagged with its band):
## the shot did not score and the defence has it.
## Where a set shot that falls short comes down: MatchSim logs the rebound where
## the mark was taken, but he kicked from the band's spot (T2.24), so it drops on
## the line from there to goal, 40-90% of the way, at the point nearest the
## defender who wins it (3/4 of the way left him 40 m off on seed 42 ev 1149).
func _short_spot(k: int) -> Vector2:
	var pk := _prev_real(k)
	var spot: Vector2 = _locs[pk]
	var goal := Vector2(MatchMotion.GOAL_X * _dir(int((events[pk] as Dictionary).get("side", 0))), 0.0)
	var t := 0.75
	var a := _actor_id(events[k])
	var line := goal - spot
	if a >= 0 and line.length_squared() > 1.0:
		t = clampf(((tokens[a]["pos"] as Vector2) - spot).dot(line) / line.length_squared(), 0.4, 0.9)
	return spot.lerp(goal, t)


func _short_set_shot(k: int) -> bool:
	if str((events[k] as Dictionary).get("kind", "")) != "rebound":
		return false
	var pk := _prev_real(k)
	if pk < 0:
		return false
	var prev: Dictionary = events[pk]
	if str(prev.get("kind", "")) == "mark" and prev.has("band"):
		return true
	# A free's set shot that falls short (MatchSim tags it from_free and logs it
	# where the free was paid): the taker kicks it and it comes down short.
	# Drawn at the free's spot, the back took it out of the taker's hands with
	# no kick (seed 31 FRE v STK k149).
	return bool((events[k] as Dictionary).get("from_free", false)) \
			and str(prev.get("kind", "")) in ["free", "fifty", "last_disposal", "out_on_full"]


func _clanger_phases(k: int) -> Array:
	var ev: Dictionary = events[k]
	var e := _actor_id(ev)
	var loc := _loc(k)
	var out := []
	match _restart(k):
		"centre":
			out = _centre_phases(k, e, loc)
		"kickin":
			# An error logged before the kick-in: shown at the goal square.
			return _kickin_phases(k, -1, loc) + [{"t": "emit", "log": true}]
	var d := (ball["pos"] as Vector2).distance_to(loc)
	if out.is_empty() and str(ball["mode"]) in ["dead", "loose"] and e >= 0 and not _on_feet(e):
		# He is the man tackled, still on the deck: his clanger is the ball coming free of that
		# tackle, toward whoever plays it next, who runs onto it. He does not lie there while the
		# match waits for him to get up and fumble a ball he has already lost (seed 42: 3.1 s
		# with seven men running past it).
		var nk := _next_real(k)
		var nxt := _actor_id(events[nk]) if nk >= 0 else -1
		if nxt >= 0 and nxt != e and _on_feet(nxt):
			return [{"t": "spill", "toward": nxt, "dur": 0.4}, {"t": "emit", "log": true}]
	if out.is_empty() and d > 1.0 and str(ball["mode"]) in ["dead", "loose"] and e >= 0:
		# Nobody has it (the tackled man is on the deck with it): nobody kicks
		# it either. It spills out of the pack toward him and he runs onto it
		# where it lies (3d view 2, 2026-11-15: the ball flew 9 m up off a
		# falling pair with no kicker). He fumbles it once he is on it, not
		# from 3 m away: he runs at it at pace ("pace": aimed through the
		# ball, no easing to a stop), goes down for it on the run ("scoop")
		# and knocks it on along his line as his hands reach it ("along";
		# director 2026-11-16: the standing stoop read as "his hands are
		# covered in butter").
		return [{"t": "spill", "toward": e, "dur": 0.4}, {"t": "collect", "who": e, "pace": true},
				{"t": "wait", "dur": SCOOP_S, "scoop": e},
				{"t": "emit", "log": true}, {"t": "fumble", "dur": 0.35, "along": e}]
	if out.is_empty() and d > 1.0:
		var pk := _prev_real(k)
		var hb := pk >= 0 and str((events[pk] as Dictionary).get("kind", "")) == "handball"
		var shape := _flight_shape("handball" if hb and d < 18.0 else "kick", d)
		out.append({"t": "flight", "to": loc, "dur": shape.x, "apex": shape.y, "recv": e})
	out += [{"t": "collect", "who": e, "max": 0.3}, {"t": "emit", "log": true},
			{"t": "fumble", "dur": 0.35}]
	return out


## Flight time and apex for a disposal over `d` metres.
func _flight_shape(kind: String, d: float) -> Vector2:
	if kind == "handball":
		return Vector2(0.1 + d / 45.0, 0.6 + d * 0.04)
	return Vector2(0.2 + d / 64.0, clampf(2.0 + d * 0.2, 2.5, 16.0))


# ---------------------------------------------------------------------------
# Where the ball goes (presentation only: x is always the logged fp)
# ---------------------------------------------------------------------------
func _loc(k: int) -> Vector2:
	if _locs.has(k):
		return _locs[k]
	if _short_set_shot(k) and _locs.has(_prev_real(k)):
		_locs[k] = _short_spot(k)
		return _locs[k]
	var ev: Dictionary = events[k]
	var kind := str(ev.get("kind", ""))
	var x := clampf(float(ev.get("fp", 0.0)), -MatchMotion.GOAL_X, MatchMotion.GOAL_X)
	var pk := _prev_real(k)
	var src: Vector2 = _locs[pk] if pk >= 0 and _locs.has(pk) else (ball["pos"] as Vector2)
	var a := _actor_id(ev)
	if kind in ["inside50", "clanger"]:
		# Where the ball lands, not where the kicker stands: lean it toward
		# whoever the log says wins it next, so he is not left running 30 m
		# to a ball his team-mates are standing over.
		var nk := _next_real(k)
		if nk >= 0 and _actor_id(events[nk]) >= 0:
			a = _actor_id(events[nk])
	var ry: float = (tokens[a]["pos"] as Vector2).y if a >= 0 else src.y
	var p: Vector2
	if kind in ["throwin", "last_disposal", "out_on_full"]:
		p = _boundary_point(x, src.y)
	elif kind in ["goal", "behind", "rebound", "tackle", "pressure", "free", "fifty", "ballup"]:
		p = Vector2(x, src.y)
	elif _possession(kind) and _restart(k) == "centre":
		p = Vector2(0.0, signf(ry if ry != 0.0 else 1.0) * 3.5)
	elif _possession(kind) and _restart(k) == "kickin":
		p = Vector2(x, 0.0)   # the goal square: MatchSim logs the kick-in there
	elif _possession(kind) and _restart(k) == "throwin":
		# A boundary throw-in lands well inside the line, at the same
		# longitudinal field position as the crossing.
		p = Vector2(x, src.y * 0.78)
	elif kind == "clanger" and pk >= 0 and str((events[pk] as Dictionary).get("kind", "")) in ["tackle", "pressure"]:
		# Knocked loose out of the tackle (_clanger_phases spills it): it comes free a few metres
		# from the pack, toward whoever wins it next, never across the ground. Leaned as a kick is,
		# 34 of 74 spills on five seeds came free 10-82 m from their tackle, with nobody's hands
		# to carry it there (seed 31: 82 m, its man 67 m off).
		var tp := _loc(pk)
		p = Vector2(x, tp.y + clampf(ry - tp.y, -CLANGER_SPILL, CLANGER_SPILL))
	elif _possession(kind) and _restart(k) in ["ballup", "free", "loose"]:
		# (A pinned ball-up carries its shift on to the ball's next spot.)
		var px := x + (_ballup_pin[pk] as Vector2).x if pk >= 0 and _ballup_pin.has(pk) else x
		p = Vector2(px, src.y + _rng.randf_range(-6.0, 6.0))
	else:
		var hb := pk >= 0 and str((events[pk] as Dictionary).get("kind", "")) == "handball"
		var dy_raw := ry - src.y
		var dy: float
		if hb:
			dy = clampf(dy_raw * 0.6, -9.0, 9.0) + _rng.randf_range(-2.0, 2.0)
		else:
			dy = clampf(dy_raw * 0.7, -32.0, 32.0) + _rng.randf_range(-5.0, 5.0)
			if absf(x - src.x) < 12.0 and absf(dy) < 10.0:
				dy = (signf(dy_raw) if dy_raw != 0.0 else 1.0) * _rng.randf_range(10.0, 18.0)
			# (The roll is made as before whatever the plan, so the stream is unchanged.)
			if absf(src.y) > 22.0 and _rng.randf() < 0.1 and _plan_of(int(ev.get("side", 0))) != "attacking":
				dy = -src.y * 1.3 + _rng.randf_range(-5.0, 5.0)   # a switch of play (never down the corridor)
		var y := src.y + dy
		var side := int(ev.get("side", 0))
		if _plan_of(side) == "attacking" and a >= 0 and int(tokens[a]["side"]) == side and _lane.has(a):
			# Attack Corridor: the ball goes to the receiver's lane. He leads
			# from his slot, up his lane, never across to the ball, so the
			# receivers never converge on one column.
			y = float(_lane[a]) + _rng.randf_range(-1.0, 1.0)
		elif x * _dir(side) < -45.0:
			y *= 1.15   # clearing from defence: toward the boundary, away from the corridor
		p = Vector2(x, y)
		if hb and p.distance_to(src) < 3.0:
			p.y += 4.0 * (1.0 if _rng.randf() < 0.5 else -1.0)
	if kind in ["throwin", "last_disposal", "out_on_full"]:
		_locs[k] = p
		return p
	if absf(p.x) > 62.0:
		p.y = clampf(p.y, -26.0, 26.0)
	var ymax := (MatchMotion.HALF_WID - 4.0) * sqrt(maxf(0.0,
			1.0 - pow(p.x / (MatchMotion.HALF_LEN - 1.0), 2.0)))
	p.y = clampf(p.y, -ymax, ymax)
	_locs[k] = p
	return p


## Where a set shot from `band` is marked, on the oval: the band's metres from
## the middle of `side`'s attacking goal line, its angle off the line through
## the goals on the `lean` side (the ball's side of the ground).
func _set_spot(side: int, band: String, lean: float) -> Vector2:
	var metres := 35.0
	for b in MatchSim.SET_BANDS_ON:
		if str(b["key"]) == band:
			metres = float(b["metres"])
	var ang := deg_to_rad(float(DecisionVignette.SET_SPOTS.get(band, 0.0)))
	var across := (1.0 if lean >= 0.0 else -1.0) * sin(ang) * metres
	return Vector2(_dir(side) * (MatchMotion.GOAL_X - cos(ang) * metres), across)


## Win Contest: the ball-up is where the ball is when the umpire calls it (motion
## critic, 2026-10-18: the ring came in on the logged spot 15 m off and the ball
## then flew to it with nobody kicking it). Under that call the ball-up event `k`
## is pinned to the ball (where its flight lands, if it is in the air), so the
## ring, the pack and the ball agree from the call, and the ball's next spot keeps
## the same shift. Once per ball-up; other calls keep the logged spot. Draws
## nothing from the random stream.
func _pin_ballup(k: int) -> void:
	if _ballup_pin.has(k) or not (_plan_of(0) == "contest" or _plan_of(1) == "contest"):
		return
	var old := _peek_loc(k)
	var at: Vector2 = ball["to"] if str(ball["mode"]) == "flight" else ball["pos"]
	_locs[k] = at
	var shift := at - old
	_ballup_pin[k] = shift
	var nk := _next_real(k)
	if nk >= 0 and _locs.has(nk) and _restart(nk) == "ballup":
		var q := (_locs[nk] as Vector2) + shift
		q.x = clampf(q.x, -MatchMotion.GOAL_X, MatchMotion.GOAL_X)
		var ymax := (MatchMotion.HALF_WID - 4.0) * sqrt(maxf(0.0,
				1.0 - pow(q.x / (MatchMotion.HALF_LEN - 1.0), 2.0)))
		q.y = clampf(q.y, -ymax, ymax)
		_locs[nk] = q


## The umpire's call: the ball dead in a tackle or a pack with a ball-up next.
## Under Win Contest the ball-up is pinned to the ball there and then.
func _pin_called_ballup() -> void:
	if mode != "stoppage" or _beat.is_empty() or str(ball["mode"]) != "dead":
		return
	var kind := str(_beat.get("kind", ""))
	if kind == "ballup" or kind == "throwin":
		return
	var nk := _next_real(int(_beat["k"]))
	if nk >= 0 and str((events[nk] as Dictionary).get("kind", "")) == "ballup":
		_pin_ballup(nk)


# ---------------------------------------------------------------------------
# Anticipation: players read the events coming up
# ---------------------------------------------------------------------------
func _anticipate(k: int) -> void:
	var ev: Dictionary = events[k]
	var cur := _actor_id(ev)
	var j := _next_real(k)
	if j >= 0:
		var nev: Dictionary = events[j]
		var kind := str(nev.get("kind", ""))
		var a := _actor_id(nev)
		if a >= 0 and not _busy.has(a):
			if (kind == "tackle" or kind == "pressure") and cur >= 0:
				# The tackler is already closing from behind as the ball arrives.
				var at := _loc(k) if DISPOSALS.has(str(ev.get("kind", ""))) else (tokens[cur]["pos"] as Vector2)
				var from: Vector2 = tokens[a]["pos"]
				MatchMotion.set_goal(tokens[a], at + (from - at).limit_length(2.5), 1.0)
				_busy[a] = true
			elif kind == "inside50":
				var nk := _next_real(j)
				if nk >= 0:
					_contest(_loc(j), _actor_id(events[nk]), 0.95)
	if str(ev.get("kind", "")) == "inside50":
		var nk2 := _next_real(k)
		if nk2 >= 0:
			_contest(_loc(k), _actor_id(events[nk2]), 1.0)
	_lead_receivers(k, cur)


## A loose ball whose winner is still off it: the men nearest it, from either side, go at it.
## Each comes in at pace on his own line (one on top of it from a stand first gives himself a
## run at it), and the first there at the scoop's pace goes down for it on the run and knocks
## it on, angled toward the man MatchSim says comes out with it (the spilled ball's scoop).
## Nobody is slowed and nobody waits beside it for its own sake: the ball's path carries the
## result, never the men's pace (director 2026-11-16: "thats a predetermined clip"). The ball
## never moves without a man's hands on it (director 2026-11-16: a ball that "squirts away" on
## its own). Each knock is short and a scrap is capped, so the ball is never carried up the
## ground (and the next kick starts where the play is).
const KNOCK_EVERY := 0.45
const KNOCK_GATHER := 0.2
const KNOCK_METRES := 5.0
const KNOCK_CAP := 16.0
## No knock once the winner will be within KNOCK_CLEAR metres of it when the hands reach it
## (he takes it himself): the shortest knock (FUMBLE_METRES.x) plus the near gather's reach
## from a stand (scoop_lead(SCOOP_NEAR)). A knock stops KNOCK_SHORT metres short of him.
const KNOCK_CLEAR := 4.7
const KNOCK_SHORT := 3.0
## A knock never leaves the ball more than KNOCK_HOME metres (up or back the ground) from the
## logged spot of the play it belongs to: MatchSim says where it is won, and the scrap only
## shows how it gets there (a scrap that knocked it 5-8 m up the ground started the next kick
## off its spot).
const KNOCK_HOME := 2.0
## A clanger out of a tackle comes free at most this far across the ground from the pack.
const CLANGER_SPILL := 6.0
## The men nearest a loose ball (at most SCRAP_MEN, within SCRAP_REACH metres) go at it flat
## out, whether or not it is theirs to go down for (director 2026-11-16: nobody stands waiting
## beside it). Only once a scrap has knocked it its whole KNOCK_CAP do they hold SCRAP_HOLD
## metres off it for the winner.
const SCRAP_MEN := 3
const SCRAP_REACH := 15.0
const SCRAP_HOLD := SCOOP_LEAD + SCOOP_SPEED * SCOOP_SPEED / (2.0 * MatchMotion.ACCEL) + 0.15 + 0.6
## The two men of a tackle are drawn in its take (Oval3DAnim: down, then back up) until they
## are up: the latest of tackle_pairs.json's up_s - contact_s, 3.13 clip s, on this clock (the
## take then lets him go as soon as he moves). Until then neither joins the scrap for a loose
## ball (the take would not show him going down for it: Oval3DAnim plays a ground_ball touch
## only out of a take). Held to the clip's end (3.74 s), a man the play wanted next left the
## ball lying for 4 s and more (8 collects on the suite match, 16 over seeds 42 and 1-3).
const TAKE_UP := 3.14 * TEMPO


## How far a knock along `way` from `at` can carry it and still finish within KNOCK_HOME metres
## of the play's logged spot (up or back the ground; INF across it). Already further off, it
## may only come back toward the spot.
func _knock_room(at: Vector2, way: Vector2) -> float:
	if _beat.is_empty() or way.length() < 0.01:
		return INF
	var w := way.normalized()
	if absf(w.x) < 0.05:
		return INF
	var e := at.x - float(events[int(_beat.get("k", 0))].get("fp", at.x))
	var lim := maxf(KNOCK_HOME, absf(e))
	if w.x * e >= 0.0:
		return maxf(lim - absf(e), 0.0) / absf(w.x)
	return (absf(e) + lim) / absf(w.x)


## Whether he is back on his feet from his last tackle (either man of it).
func _on_feet(id: int) -> bool:
	return time - float(tokens[id].get("tackle_t", -TAKE_UP)) >= TAKE_UP


func _scrap(p: Dictionary, who: int) -> void:
	var at: Vector2 = ball["pos"]
	var to := _knock_way(who, at)
	var knocked := float(p.get("_knocked", 0.0))
	# The man who just knocked it on runs out his scoop before he joins the scrap again.
	var out := int(p.get("_out", -1))
	if out >= 0 and _pt >= float(p["_out_t"]):
		tokens[out].erase("cap")
		p.erase("_out")
		out = -1
	if out >= 0:
		_busy[out] = true
	var by := int(p.get("_by", -1))
	if by >= 0:
		# Down for it on the run; it rolls the last of the way into his hands.
		_busy[by] = true
		if _pt >= float(p["_touch_t"]):
			var bt: Dictionary = tokens[by]
			var line: Vector2 = bt.get("line", _line(bt))
			var step := clampf(minf(KNOCK_CAP - knocked, to.length() - KNOCK_SHORT), FUMBLE_METRES.x, KNOCK_METRES)
			var way := line.rotated(clampf(line.angle_to(to), -KNOCK_ON, KNOCK_ON))
			if p.get("_close", false):
				# On it first with the winner close: it comes off his hands into the winner's path.
				step = clampf(minf(KNOCK_CAP - knocked, to.length() - scoop_lead(SCOOP_NEAR)), FUMBLE_CLOSE, FUMBLE_METRES.x)
				way = to
				var wt: Dictionary = tokens[who]
				var wvel: Vector2 = wt["vel"]
				if to.length() < scoop_lead(SCOOP_NEAR) + FUMBLE_CLOSE and wvel.length() > 0.5:
					# He is on it already: knocked toward him it stopped at his feet, and he either
					# stopped dead for it or ran over it (seed 42, 1 m off at 2.9 m/s). It goes on
					# ahead of him along his run instead, a pickup's length on.
					var wk := SCOOP_AT_PACE if wvel.length() > scoop_speed(SCOOP_NEAR) + SCOOP_EASE else SCOOP_NEAR
					way = (wt["pos"] as Vector2) + wvel.normalized() * scoop_lead(wk) - at
					step = clampf(minf(KNOCK_CAP - knocked, way.length()), FUMBLE_CLOSE, FUMBLE_METRES.x)
			# Off his hands it always moves, but never far from where MatchSim says it is won.
			step = minf(step, maxf(_knock_room(at, way), FUMBLE_CLOSE))
			_knock_on(by, way, step)
			# He follows his own knock: on after it along its line at the scoop's pace, never pulling
			# up behind it (aimed from where he stood at where it stops, a short knock turned him
			# off its line: suite match, 39 degrees).
			MatchMotion.set_goal(bt, _ball_rest() + way.normalized() * RUN_THROUGH, 0.0, true)
			knocked += step
			p["_knocked"] = knocked
			p["_knock_t"] = _pt
			p["_out"] = by
			p["_out_t"] = _pt + scoop_after(_sk(by))
			p.erase("_touch_t")
			p.erase("_by")
			p.erase("_close")
			out = by
			by = -1
	var rest := _ball_rest()
	var step2 := minf(minf(KNOCK_METRES, _knock_room(rest, to)), minf(KNOCK_CAP - knocked, to.length() - KNOCK_SHORT))
	# A man goes down for it only if the winner will still be KNOCK_CLEAR off it when his hands
	# reach it (the winner coming in flat out brakes only to the scoop's pace meanwhile).
	var wv := maxf(-(tokens[who]["vel"] as Vector2).dot(to.normalized()), 0.0) if to.length() > 0.01 else 0.0
	var touch_s := (SCOOP_TOUCH - scoop_from(SCOOP_LEAD)) * TEMPO
	var w_on := wv * touch_s if wv <= SCOOP_SPEED \
			else (wv * wv - SCOOP_SPEED * SCOOP_SPEED) / (2.0 * MatchMotion.BRAKE) + SCOOP_SPEED * touch_s
	var cool := by < 0 and KNOCK_CAP - knocked >= FUMBLE_CLOSE \
			and _pt - float(p.get("_knock_t", -KNOCK_EVERY)) >= KNOCK_EVERY
	var can := cool and to.length() - w_on >= KNOCK_CLEAR and step2 >= FUMBLE_METRES.x
	var wd := (tokens[who]["pos"] as Vector2).distance_to(rest)
	var rolling: Vector2 = ball.get("vel", Vector2.ZERO) if str(ball["mode"]) == "loose" else Vector2.ZERO
	var near := []
	for t in tokens:
		var id := int(t["id"])
		if id != who and id != by and id != out and float(t.get("down", 0.0)) <= 0.0 and _on_feet(id):
			near.append([(t["pos"] as Vector2).distance_to(rest), id])
	near.sort()
	for i in range(mini(SCRAP_MEN, near.size())):
		if float(near[i][0]) > SCRAP_REACH:
			break
		var id := int(near[i][1])
		var t: Dictionary = tokens[id]
		_busy[id] = true
		# Where his hands would meet it (a ball rolling at him meets him sooner).
		var run: Vector2 = _scoop_aim(id, SCOOP_AT_PACE) - (t["pos"] as Vector2)
		var dir := run.normalized() if run.length() > 0.01 else _line(t)
		if KNOCK_CAP - knocked < FUMBLE_METRES.x:
			# Knocked its whole cap: it is the winner's, and they hold off it for him.
			t.erase("cap")
			MatchMotion.set_goal(t, rest - dir * SCRAP_HOLD, 1.0, true)
			continue
		var passes: Dictionary = p.get("_pass", {})
		p["_pass"] = passes
		if not cool or wd <= run.length() or (not can and p.get("_closed", false)):
			# Not his to go down for (a man is already down on it, the winner gets there as soon,
			# or its one close fumble is spent): he is in on it all the same, flat out, and runs
			# on past it beside it, never across it upright and never slowing beside it.
			t.erase("cap")
			MatchMotion.set_goal(t, _pass_line(passes, id, rest), 1.0, true)
			continue
		# He goes down once his hands will meet it a scoop's length ahead, rolling slowly enough
		# to take: on the run at the scoop's pace, or nearer and slower, gathered from a stand.
		# With the winner too close for a knock on (and not yet down for it himself: he goes
		# first whenever he can), it comes off his hands into the winner's path.
		var kind := _scoop_pick(id)
		if not can:
			# Once per scrap, and gathered from a stand: crouched over it, it comes off his hands
			# whichever way the winner is.
			var near_run := _scoop_aim(id, SCOOP_NEAR) - (t["pos"] as Vector2)
			kind = SCOOP_NEAR if not p.get("_closed", false) and near_run.length() <= scoop_lead(SCOOP_NEAR) \
					and _scoop_roll(id, SCOOP_NEAR) <= SCOOP_ROLL \
					and (t["vel"] as Vector2).length() <= scoop_speed(SCOOP_NEAR) + SCOOP_EASE else -1
		var pl: Array = passes.get(id, [])
		var on_line := pl.size() == 3 and (pl[1] as Vector2).distance_to(rest) <= 1.5 \
				and (t["pos"] as Vector2).distance_to(pl[0]) > 1.0
		if kind < 0 and (run.length() < scoop_lead(SCOOP_AT_PACE) or on_line):
			# Inside a scoop's length and still not going down for it (too near to at pace, too
			# quick to from a stand): held to the scoop's pace he walked straight over it (seed 31,
			# 2.9 m/s for half a second). He goes on past it beside it flat out, to the end of
			# that line (turned back a step past it, he dithered), and comes again.
			t.erase("cap")
			MatchMotion.set_goal(t, _pass_line(passes, id, rest), 1.0, true)
			continue
		# At it flat out, braking only to the scoop's pace (the spilled ball's collect).
		passes.erase(id)
		MatchMotion.set_goal(t, (t["pos"] as Vector2) + run + dir * RUN_THROUGH, 1.0, true)
		t["cap"] = sqrt(SCOOP_SPEED * SCOOP_SPEED + 2.0 * MatchMotion.BRAKE * 0.55 * maxf(run.length() - SCOOP_LEAD, 0.0))
		if kind >= 0:
			ball["vel"] = rolling
			ball["mode"] = "loose"
			ball["holder"] = -1
			t["scoop_k"] = kind
			p["_by"] = id
			p["_close"] = not can
			if not can:
				p["_closed"] = true
			var aim := _scoop_aim(id)
			p["_touch_t"] = _pt + _scoop_start(id)
			_contact(id, &"ground_ball", aim)
			by = id
			can = false
			cool = false


## While the winner goes down for a loose ball, the men nearest it (as in a scrap) keep coming
## at it flat out: nobody pulls up to watch him take it (director 2026-11-16). Each comes on his
## own line beside it and on past it (_pass_line). who -1: nobody has it won yet (a fumble), so
## every man near it goes, none held back.
func _scrap_in(p: Dictionary, who: int, brake := false) -> void:
	var rest := _ball_rest()
	var lines: Dictionary = p.get("_in", {})
	var near := []
	for t in tokens:
		var id := int(t["id"])
		if id != who and float(t.get("down", 0.0)) <= 0.0 and _on_feet(id):
			near.append([(t["pos"] as Vector2).distance_to(rest), id])
	near.sort()
	for i in range(mini(SCRAP_MEN, near.size())):
		if float(near[i][0]) > SCRAP_REACH:
			break
		if not lines.has(int(near[i][1])):
			lines[int(near[i][1])] = []
	p["_in"] = lines
	var wd := (tokens[who]["pos"] as Vector2).distance_to(rest) if who >= 0 else INF
	# The man MatchSim has gathering it next (off this man's hands) is the pressure on him: he
	# comes straight at it, not past it on a line, so it comes off the hands into his path
	# (seed 31: on his pass line he was 3.9 m off and running away as it came free, 0.7 s alone).
	var nc := _next_collector()
	if nc >= 0 and nc != who and _on_feet(nc) and float(tokens[nc].get("down", 0.0)) <= 0.0:
		lines[nc] = lines.get(nc, [])
	for id in lines.keys():
		_busy[id] = true
		var t: Dictionary = tokens[id]
		var r := (t["pos"] as Vector2).distance_to(rest)
		var go: bool = (brake and r < wd) or (int(id) == nc and nc != who)
		if go:
			# Spilling out of the tackle it is anybody's: a man there before the winner comes at it
			# flat out but brakes to the scoop's pace at it (as in the scrap), so he can go down
			# for it once it is loose, rather than running straight past it at full tilt.
			t["cap"] = sqrt(SCOOP_SPEED * SCOOP_SPEED + 2.0 * MatchMotion.BRAKE * 0.55 * maxf(r - SCOOP_LEAD, 0.0))
		else:
			t.erase("cap")
		MatchMotion.set_goal(t, _pass_line(lines, id, rest, go), 1.0, true)


## A man in on a loose ball that is not his to go down for comes through flat out on his own
## line, PASS_SIDE metres beside where it lies and RUN_THROUGH on past it: never across it
## upright, never slowing beside it (seed 31: three men ran straight over it at 8-10 m/s, one
## while another was down for it). through: a man who may go down for it comes straight at it.
## The line holds until he reaches its end or the ball is knocked off that spot (re-aimed at it
## every frame, a man who reached it ran circles round it); then he turns and comes again.
const PASS_SIDE := 1.2


func _pass_line(lines: Dictionary, id: int, rest: Vector2, through := false) -> Vector2:
	var t: Dictionary = tokens[id]
	var pos: Vector2 = t["pos"]
	var l: Array = lines.get(id, [])
	if l.size() == 3 and bool(l[2]) == through and (l[1] as Vector2).distance_to(rest) <= 1.5 \
			and pos.distance_to(l[0]) > 1.0:
		return l[0]
	var run := rest - pos
	var dir := run.normalized() if run.length() > 0.01 else _line(t)
	var aim := rest
	if not through:
		# Beside it, on the side he is already heading for.
		var side := dir.orthogonal()
		var v: Vector2 = t["vel"]
		if (v.length() > 0.5 and v.dot(side) < 0.0) or (v.length() <= 0.5 and id % 2 == 1):
			side = -side
		aim = rest + side * PASS_SIDE
		if pos.distance_to(aim) > 0.01:
			dir = (aim - pos).normalized()
	var goal := aim + dir * RUN_THROUGH
	lines[id] = [goal, rest, through]
	return goal


## In a scrap nobody's own run carries him across the loose ball upright (director 2026-11-16):
## a man on his feet who is not going down for it, heading onto it, steps round it KEEP_OFF
## from it, keeping the part of his run that goes past it. A pass line aims beside where it
## stops, but a fumble is still rolling and a man at 10 m/s curves to his line (suite match:
## 58 crossings, most in a fumble). A ball rolling past a man's boots is not him crossing it.
const KEEP_OFF := 0.8
## How long after the touch (clip seconds) his hands are still on it: the knock leaves them.
const KNOCK_HANDS := 0.3


func _keep_off_ball() -> void:
	if int(ball.get("holder", -1)) >= 0 or not str(ball["mode"]) in ["loose", "dead"] or _pi >= _phases.size():
		return
	var p: Dictionary = _phases[_pi]
	var st := str(p.get("t", ""))
	if not (st in ["spill", "fumble"] or (st == "collect" and (p.get("pace", false) or p.get("roll", false) or str(ball["mode"]) == "loose")) \
			or (st == "wait" and p.has("scoop"))):
		return
	var bp: Vector2 = ball["pos"]
	var his := [int(p.get("who", -1)), int(p.get("_by", -1)), int(p.get("scoop", -1)), int(p.get("toward", -1))]
	if p.has("_by"):
		# Another man's hands are going down on it: the winner comes on round him too, and it
		# comes off those hands into his path (suite match: he ran straight over it at 2.9 m/s).
		his[0] = -1
	for t in tokens:
		var id := int(t["id"])
		# (A man whose hands are on it, down to the touch and the knock off them, is let be; once
		# they are off it he goes round it like anyone: seed 31, a man ran over his own knock at
		# 6 m/s 1.2 s after he went down for it.)
		if id in his or not _on_feet(id) or time < float(t.get("hands_off", -99.0)):
			continue
		var w: Vector2 = (t["pos"] as Vector2) - bp
		var r := w.length()
		var v: Vector2 = t["vel"]
		if r >= KEEP_OFF or r < 0.001 or v.dot(w) >= 0.0:
			continue
		# Round it at his own pace (dropping only the part of his run into it stopped a man
		# at 5 m/s nearly dead beside it, and then he went down for it from a stand).
		var out := w / r
		var side := out.orthogonal()
		if v.dot(side) < 0.0:
			side = -side
		t["vel"] = side * v.length()
		t["pos"] = bp + out * KEEP_OFF


## Which way a scrap knocks the ball on to its winner: toward him, wherever he comes from
## (short knocks, capped per scrap, so it is never carried far up or back the ground).
## Who MatchSim has gathering the ball next (the next collect phase in this beat), or -1.
func _next_collector() -> int:
	for i in range(_pi + 1, _phases.size()):
		var q: Dictionary = _phases[i]
		if str(q.get("t", "")) == "collect":
			return int(q.get("who", -1))
	# The fumble ends its beat: the next event's man, when the ball stays loose to him.
	if _beat.is_empty() or not _loose_to().is_finite():
		return -1
	return _actor_id(events[_next_real(int(_beat["k"]))])


func _knock_way(who: int, at: Vector2) -> Vector2:
	return (tokens[who]["pos"] as Vector2) - at


## He goes down for the loose ball on the run (Oval3DAnim plays SCOOP_CLIP on his
## ground_ball touch, at _ball_rest): he runs on through where it stops at the scoop's own
## pace (held there until the beat ends, so his hips never fall behind him), and it rolls the
## last of the way into his hands. Nearer than a whole scoop, he runs only what is left to
## the touch. Returns the time to the touch on this clock.
func _scoop_start(who: int) -> float:
	var st: Dictionary = tokens[who]
	var to: Vector2 = _scoop_aim(who) - (st["pos"] as Vector2)
	var kind := _sk(who)
	var sc: Dictionary = SCOOPS[kind]
	var yaw := scoop_yaw(to, kind) if to.length() > 0.05 else _line(st).angle()
	var line := Vector2(sin(yaw), cos(yaw)) if to.length() > 0.05 else _line(st)
	var t0 := scoop_from(to.length(), kind)
	var pace := clampf(scoop_run(to.length(), kind) / (float(sc["touch"]) - t0), 0.0, float(sc["run"])) / TEMPO
	st["vel"] = line * pace
	st["cap"] = pace
	st["line"] = line
	MatchMotion.set_goal(st, (st["pos"] as Vector2) + line * RUN_THROUGH, 0.0, true)
	_busy[who] = true
	st["hands_off"] = time + (float(sc["touch"]) - t0 + KNOCK_HANDS) * TEMPO
	return (float(sc["touch"]) - t0) * TEMPO


## Which scoop he goes down for a loose ball with now, or -1 if neither yet: on the run at the
## scoop's pace within its length (SCOOP_AT_PACE), or nearer and slower, gathered from a stand
## (SCOOP_NEAR; director 2026-11-16: "retarget the grimes one", "we can use both"). Either way
## it rolls no faster than SCOOP_ROLL into his hands.
## roll_cap: how fast it may still be rolling at the touch (the man it is meant for takes one
## coming at him on the bounce, whatever its pace).
func _scoop_pick(who: int, roll_cap := SCOOP_ROLL) -> int:
	var t: Dictionary = tokens[who]
	for kind in [SCOOP_AT_PACE, SCOOP_NEAR]:
		var run: Vector2 = _scoop_aim(who, kind) - (t["pos"] as Vector2)
		if run.length() > scoop_lead(kind) or _scoop_roll(who, kind) > roll_cap:
			continue
		var sc: Dictionary = SCOOPS[kind]
		if kind == SCOOP_AT_PACE and scoop_run(run.length(), kind) \
				< 0.85 * float(sc["run"]) * (float(sc["touch"]) - scoop_from(run.length(), kind)):
			continue
		var dir := run.normalized() if run.length() > 0.01 else _line(t)
		# Only a man already near the pace this scoop gives him goes down for it (_scoop_start
		# sets his pace there: one sprinting past it stopped dead in a frame, and one at 3.4 m/s
		# with the ball at his feet stopped dead for a gather from a stand).
		var t0 := scoop_from(run.length(), kind)
		var pace := clampf(scoop_run(run.length(), kind) / (float(sc["touch"]) - t0), 0.0, float(sc["run"])) / TEMPO
		if absf((t["vel"] as Vector2).length() - pace) > SCOOP_EASE:
			continue
		if kind == SCOOP_NEAR or (t["vel"] as Vector2).dot(dir) >= SCOOP_SPEED * 0.85:
			return kind
	return -1


## The scoop he last went down with (SCOOPS).
func _sk(who: int) -> int:
	return int(tokens[who].get("scoop_k", SCOOP_AT_PACE))


## Where a loose ball is `s` seconds from now (it decays at exp(-3t)); a ball not rolling, where it is.
func _ball_at(s: float) -> Vector2:
	if str(ball["mode"]) != "loose":
		return ball["pos"]
	return (ball["pos"] as Vector2) + (ball.get("vel", Vector2.ZERO) as Vector2) * (1.0 - exp(-3.0 * s)) / 3.0


## Where his hands meet a loose ball if he goes down for it now: where it will have rolled to
## by the touch (a ball rolling at him meets him sooner, one rolling away later).
func _scoop_aim(who: int, kind := -1) -> Vector2:
	if kind < 0:
		kind = _sk(who)
	var at: Vector2 = tokens[who]["pos"]
	var touch := float(SCOOPS[kind]["touch"])
	var aim := _ball_rest()
	for i in 3:
		aim = _ball_at((touch - scoop_from(at.distance_to(aim), kind)) * TEMPO)
	return aim


## How fast a loose ball is still rolling when his hands meet it if he goes down for it now.
func _scoop_roll(who: int, kind := -1) -> float:
	if str(ball["mode"]) != "loose":
		return 0.0
	if kind < 0:
		kind = _sk(who)
	var d := (tokens[who]["pos"] as Vector2).distance_to(_scoop_aim(who, kind))
	return (ball.get("vel", Vector2.ZERO) as Vector2).length() \
			* exp(-3.0 * (float(SCOOPS[kind]["touch"]) - scoop_from(d, kind)) * TEMPO)


## Where a loose ball comes to rest (it decays at exp(-3t)); a ball not rolling, where it is.
func _ball_rest() -> Vector2:
	if str(ball["mode"]) != "loose":
		return ball["pos"]
	return (ball["pos"] as Vector2) + (ball.get("vel", Vector2.ZERO) as Vector2) / 3.0


## The ball comes off his hands on the run, `metres` along `way`; he runs on at the
## scoop's pace to the clip's end and pulls up short of where it stops.
func _knock_on(who: int, way: Vector2, metres: float) -> void:
	var t: Dictionary = tokens[who]
	var line: Vector2 = t.get("line", _line(t))
	ball["mode"] = "loose"
	ball["holder"] = -1
	# A loose ball decays at exp(-3t): a push of 3v travels about v metres.
	ball["vel"] = way.normalized() * metres * 3.0
	var kind := _sk(who)
	t["vel"] = line * scoop_speed(kind)
	t["cap"] = scoop_speed(kind)
	MatchMotion.set_goal(t, (t["pos"] as Vector2) + line * scoop_runout(kind), 0.0, true)


## The longest a player is left collecting before the ball is his.
const COLLECT_LIMIT := 6.0
## How far a ball nobody holds spills out of a tackle toward the man who gathers it.
const SPILL_METRES := 3.0
## A spilled ball lands at least this far from the man who gathers it, so he has the run-up
## to reach it at pace: from beside the tackle it squirts out the side, SPILL_PAST of the
## way back from him for every metre across.
const SPILL_RUNUP := 4.5
const SPILL_PAST := 0.44
## He goes down for a loose ball once his hands will meet it a scoop's length ahead
## (_scoop_aim) with it rolling no faster than SCOOP_ROLL metres a second: it rolls into his
## hands, and one coming at him is taken on the run rather than waited for at his feet.
const SCOOP_ROLL := 3.0
## A spilled ball's gatherer takes it on the run with the scoop Oval3DAnim plays (SCOOP_CLIP,
## 3d view 2's v2 take, the director's own two-hand gather carried to the chest; measured in
## the baked GLB): his right middle finger is lowest (0.03 m) SCOOP_TOUCH clip seconds in, SCOOP_REACH ahead of his hips
## and SCOOP_SIDE to their right, his hips SCOOP_TRAVEL on from where the clip began. They
## stand still until SCOOP_FROM (the bake's held first key) and then run a steady SCOOP_RUN
## metres a clip second to its end. It starts SCOOP_LEAD short of the ball; nearer, the clip
## starts later (scoop_from), never less than SCOOP_MIN before the touch.
const SCOOP_CLIP := "ground_ball_run_01"
const SCOOP_FROM := 0.05
const SCOOP_TOUCH := 0.40
const SCOOP_MIN := 0.25   # clip s: longer than Oval3DAnim.BLEND, so the scoop is fully his by the touch
const SCOOP_RUN := 4.8
const SCOOP_TRAVEL := 1.60
const SCOOP_REACH := 0.45
const SCOOP_SIDE := 0.34
const SCOOP_LEAD := SCOOP_TRAVEL + SCOOP_REACH
## The clip's end: the ball at his chest, his hips back at run height (Oval3DAnim eases the jog in).
const SCOOP_END := 0.70
## The scoop on this clock, which runs TEMPO times faster than the drawn one.
const SCOOP_S := SCOOP_TOUCH * TEMPO
const SCOOP_SPEED := SCOOP_RUN / TEMPO
## Nearer it and slower, he gathers it from a stand instead: ground_ball_run_grimes_01, from
## real footage of a ground ball gather (director 2026-11-16: "retarget the grimes one"). In the
## baked GLB his hips are still until 0.05 clip s and then run 1.84 m a clip second; both hands
## are lowest (0.03 m) 0.80 s in, the ball between them 1.64 m on from where the clip began and
## 0.03 m right of that line, 0.26 m ahead of his hips (1.38 m on). He is up with it by 1.45 s.
## Each scoop's numbers, as the SCOOP_* constants above give them for ground_ball_run_01.
const SCOOP_AT_PACE := 0
const SCOOP_NEAR := 1
## The most a man's speed may change (m/s, this clock) as he goes down for a loose ball: the
## scoop sets his pace to its own, and at MatchMotion.BRAKE this is about three frames' braking.
const SCOOP_EASE := 1.2
const SCOOPS := [
	{"clip": SCOOP_CLIP, "from": SCOOP_FROM, "touch": SCOOP_TOUCH, "min": SCOOP_MIN, "run": SCOOP_RUN,
			"travel": SCOOP_TRAVEL, "reach": SCOOP_REACH, "side": SCOOP_SIDE, "end": SCOOP_END},
	{"clip": "ground_ball_run_grimes_01", "from": 0.05, "touch": 0.80, "min": 0.25, "run": 1.84,
			"travel": 1.38, "reach": 0.26, "side": 0.03, "end": 1.45},
]


## The clip time a scoop starts at, d metres from the ball: late enough that his hips have
## only what is left of that d to run before his hand reaches it.
static func scoop_from(d: float, kind := SCOOP_AT_PACE) -> float:
	var sc: Dictionary = SCOOPS[kind]
	return clampf(float(sc["touch"]) - scoop_run(d, kind) / float(sc["run"]), float(sc["from"]),
			float(sc["touch"]) - float(sc["min"]))


## How far his hips run before his hand reaches a ball d metres off.
static func scoop_run(d: float, kind := SCOOP_AT_PACE) -> float:
	var side := float(SCOOPS[kind]["side"])
	return sqrt(maxf(d * d - side * side, 0.0)) - float(SCOOPS[kind]["reach"])


## The heading of a scoop at a ball `to` away: his right hand takes it SCOOP_SIDE out from
## his line, so he runs that much left of it.
static func scoop_yaw(to: Vector2, kind := SCOOP_AT_PACE) -> float:
	var side := float(SCOOPS[kind]["side"])
	return atan2(to.x, to.y) + atan2(side, sqrt(maxf(to.length_squared() - side * side, 0.01)))


## How far short of the ball a scoop begins (where his hands meet it, from where the clip began).
static func scoop_lead(kind: int) -> float:
	return float(SCOOPS[kind]["travel"]) + float(SCOOPS[kind]["reach"])


## A scoop's own pace on this clock.
static func scoop_speed(kind: int) -> float:
	return float(SCOOPS[kind]["run"]) / TEMPO


## After the touch his hips run on to the clip's end, then he pulls up (MatchMotion's arrive
## brakes him over the last 0.4 m); and that run-out on this clock.
static func scoop_runout(kind: int) -> float:
	return (float(SCOOPS[kind]["end"]) - float(SCOOPS[kind]["touch"])) * float(SCOOPS[kind]["run"]) + 0.4


static func scoop_after(kind: int) -> float:
	return (float(SCOOPS[kind]["end"]) - float(SCOOPS[kind]["touch"])) * TEMPO

## How far past a loose ball he aims his run at it, so he reaches it at pace instead of
## easing to a stop over it.
const RUN_THROUGH := 8.0
## A fumble on the run knocks the ball on along his line, at most this far off it (radians, 35 deg).
const KNOCK_ON := 0.61
## ...and this many metres (it rolls to rest well past where he pulls up, so he never runs
## over it: his hands take it SCOOP_REACH ahead of his hips, which stop scoop_runout(kind) on).
const FUMBLE_METRES := Vector2(3.0, 4.0)
## The shortest a ball comes off a man's hands into the path of a winner close by.
const FUMBLE_CLOSE := 0.5
## A ball knocked loose by a fumble, a spoil or a smother goes toward where the match has its
## next possession (the logged spot of the man who comes out with it: MatchSim says he wins
## it there), at most as far as that touch sends a ball (a spoil's punch carries furthest),
## within LOOSE_SPREAD of the line. With no possession next (a ball-up, a free), anywhere.
const LOOSE_REACH := {"spoil": 15.0, "smother": 6.0, "": 5.0}
const LOOSE_SPREAD := 0.45   # radians, 26 deg


## Where the ball knocked loose now is next won, or INF when no possession comes off it.
func _loose_to() -> Vector2:
	if _beat.is_empty():
		return Vector2.INF
	var nj := _next_real(int(_beat["k"]))
	if nj < 0 or _restart(nj) != "loose" or _actor_id(events[nj]) < 0:
		return Vector2.INF
	if str((events[nj] as Dictionary).get("kind", "")) in ["ballup", "throwin", "free", "last_disposal", "out_on_full", "fifty", "goal", "behind"]:
		return Vector2.INF
	return _loc(nj)
## How far behind the kicker an entry may land to stand a set-shot mark on its
## band's spot (T2.24); further back, it lands where the log has it.
const SET_SPOT_BACK := 20.0
## How much longer than its flat flight a kick may hang so its receiver gets
## under it: a 50 m kick up to about 2.9 s, a 20 m one 1.5 s, a real long
## kick's hang time. Defenders clearing their 50 (MatchSim D50_*) kick long to
## a team-mate up the ground; at 1.8 the ball beat him there and play waited
## (12 trace_collect matches: 214 collects of 1.5 s or more, 166 at 3.0, 162 on
## main before the clearing kicks).
const KICK_HANG_MAX := 3.0
## A possession won closer than this to the ball (metres) has no flight.
const FLIGHT_MIN := 1.0
## A handball stays flat: it never hangs more than this much longer.
const HANDBALL_HANG_MAX := 1.8
## A pickup's touch that came this long before its collect looked (seconds) is still his; one
## older was left from a beat that moved on.
const GATHER_LATE := 0.25
## A handball is a short pass. When the next possession is further off than
## HANDBALL_REACH, the carrier runs it down first and dishes off from
## HANDBALL_DISH out; more than HANDBALL_RUN_MAX of running and it is drawn
## as a kick, as before.
const HANDBALL_REACH := 15.0
const HANDBALL_DISH := 9.0
const HANDBALL_RUN_MAX := 35.0
## A carrier's running pace, for the lead timing (presentation m/s).
const CARRY_PACE := 10.0
const LEAD_EVENTS := 10         # how far down the log a lead can be planned
const LEAD_HORIZON := 7.0       # ...and how far ahead in presentation seconds
const LEAD_SLACK := 0.8         # start a run this much before it is strictly needed

## Send each named receiver toward his coming possession early enough to be
## there when the ball arrives. Walks the log ahead, estimating when each
## possession happens; a receiver starts his lead once the time left is about
## what he needs to get there, and holds it until his possession starts. Only
## receivers who need to go now move; everyone else keeps the team's shape.
func _lead_receivers(k: int, cur: int) -> void:
	for id in _lead.keys():
		if int(_lead[id]) <= k:
			_lead.erase(id)
	var ev: Dictionary = events[k]
	var prev_kind := str(ev.get("kind", ""))
	var prev_loc: Vector2 = ball["pos"]
	var t := 0.0
	if _possession(prev_kind) or ["inside50", "ballup", "rebound"].has(prev_kind):
		prev_loc = _loc(k)
		t = _flight_shape("kick", (ball["pos"] as Vector2).distance_to(prev_loc)).x + 0.2
	var j := k
	var first := -1
	var first_loc := Vector2.ZERO
	for n in range(LEAD_EVENTS):
		if t > LEAD_HORIZON:
			break
		j = _next_real(j)
		if j < 0:
			break
		var nev: Dictionary = events[j]
		var kind := str(nev.get("kind", ""))
		if ["goal", "behind", "quarter", "final"].has(kind):
			# A shot in open play off an entry: the man who kicks it runs onto
			# where the entry lands, as a receiver leads. Left to start at the
			# entry, he was 22-44 m off a ball lying dead (seed 42 RIC v SYD,
			# six shots).
			var sa := _actor_id(nev)
			if prev_kind == "inside50" and not bool(nev.get("set_shot", true)) 					and sa >= 0 and sa != cur and not _busy.has(sa) and int(_lead.get(sa, j)) >= j:
				var stok: Dictionary = tokens[sa]
				if _lead.has(sa) or n < 2 or MatchMotion.eta(stok, prev_loc) + LEAD_SLACK >= t:
					_lead[sa] = j
					MatchMotion.set_goal(stok, prev_loc, 1.0)
					_busy[sa] = true
			break  # restarts stage their own players
		if kind == "inside50":
			# The entry itself stages its contest, but whoever wins the ball
			# after it (a rebounding defender, a forward on the lead) can
			# start toward where it lands now.
			var at := _loc(j)
			t += _flight_shape("kick", prev_loc.distance_to(at)).x + 0.3
			prev_loc = at
			prev_kind = kind
			continue
		if kind == "tackle" or kind == "pressure":
			# The presser closes on the carrier from the possession before
			# his act, not when his own beat starts 30 m off (the 2026-10-08
			# record). He goes for where the carrier gets the ball.
			var pa := _actor_id(nev)
			if pa >= 0 and pa != cur and not _busy.has(pa) and int(_lead.get(pa, j)) == j:
				var ptok: Dictionary = tokens[pa]
				if _lead.has(pa) or n < 2 or MatchMotion.eta(ptok, prev_loc) + LEAD_SLACK >= t:
					_lead[pa] = j
					# A step off him on his own side, as _anticipate closes a tackler.
					var pfrom: Vector2 = ptok["pos"]
					MatchMotion.set_goal(ptok, prev_loc + (pfrom - prev_loc).limit_length(2.5), 1.0)
					_busy[pa] = true
			t += 1.2
			continue
		if kind in ["free", "last_disposal", "out_on_full", "fifty"]:
			# The man it is paid to is on his way to the spot already, as a
			# receiver leads: he takes the ball there and kicks it. Left to
			# start at the whistle, seed 31's taker ran 65 m to a ball lying
			# loose with a man stood over it.
			var floc := _loc(j)
			t += 0.8
			var fa := _actor_id(nev)
			# A lead to something later gives way: he takes his free first
			# (seed 1 RIC v SYD k21, led to his k27 kick, ran 25 m to his free).
			if fa >= 0 and fa != cur and not _busy.has(fa) and int(_lead.get(fa, j)) >= j:
				var ftok: Dictionary = tokens[fa]
				if _lead.has(fa) or n < 2 or MatchMotion.eta(ftok, floc) + LEAD_SLACK >= t:
					_lead[fa] = j
					MatchMotion.set_goal(ftok, floc, 1.0)
					_busy[fa] = true
			prev_loc = floc
			prev_kind = kind
			continue
		if kind == "throwin":
			var atb := _loc(j)
			t += _flight_shape("kick", prev_loc.distance_to(atb)).x + 1.0
			prev_loc = atb
			prev_kind = kind
			continue
		if kind == "ballup":
			var at := _loc(j)
			t += _flight_shape("kick", prev_loc.distance_to(at)).x + 1.4
			prev_loc = at
			prev_kind = kind
			continue
		# A clanger or a spoil is a touch of the ball where the log has it: the man who fumbles
		# or punches it leads there as a receiver does, so he is on it when it comes loose.
		if not _possession(kind) and not kind in ["rebound", "clanger", "spoil"]:
			t += 0.5
			continue
		var restart := _restart(j)
		if restart == "centre" or restart == "kickin":
			break
		var loc := _loc(j)
		var d := prev_loc.distance_to(loc)
		if prev_kind == "handball" and d > HANDBALL_REACH and d - HANDBALL_DISH <= HANDBALL_RUN_MAX:
			t += (d - HANDBALL_DISH) / CARRY_PACE + _flight_shape("handball", HANDBALL_DISH).x
		else:
			t += _flight_shape("handball" if prev_kind == "handball" and d < 18.0 else "kick", d).x
		var a := _actor_id(nev)
		# His earliest touch comes first: a lead to a later one gives way
		# (pauses over seeds 42 and 1-3: 121 with that lead kept, 102 without).
		if a >= 0 and a != cur and not _busy.has(a) and int(_lead.get(a, j)) >= j:
			var tok: Dictionary = tokens[a]
			# The next two receivers always lead (as before); further ones start
			# once the time left is about what they need to get there.
			# Slow it down: shorter, slower leads, each starting only when it must.
			var held := _burst_on(int(tok["side"]), "hold")
			if _lead.has(a) or (n < 2 and not held) or MatchMotion.eta(tok, loc) + LEAD_SLACK >= t:
				_lead[a] = j
				# A lead is a run, never a stroll: from a stride-out up to a
				# sprint when time is short.
				var top := float(tok["top"])
				var need := (tok["pos"] as Vector2).distance_to(loc) / maxf(0.3, t - float(tok["reaction"]))
				var u := clampf((need / top - MatchMotion.JOG_SHARE) / (1.0 - MatchMotion.JOG_SHARE) + 0.35, 0.6, 1.0)
				if held:
					u *= HOLD_LEAD
				MatchMotion.set_goal(tok, _clear_of_pack(loc), u)
				_busy[a] = true
				if n == 0:
					first = a
					first_loc = loc
		t += 0.25  # hold, collect
		prev_loc = loc
		prev_kind = kind
	# The next receiver's opponent follows him, unless that opponent is on a
	# lead of his own (often the case just before a turnover).
	if first >= 0:
		_trail(first, first_loc, 0.85)


## The receiver's direct opponent follows him a step behind, goal-side.
func _trail(a: int, goal: Vector2, urgency: float) -> void:
	var o := int(tokens[a]["match"])
	if o < 0 or _busy.has(o) or _lead.has(o):
		return
	var t: Dictionary = tokens[o]
	var own := Vector2(-MatchMotion.GOAL_X * _dir(int(t["side"])), 0.0)
	if (t["pos"] as Vector2).distance_to(goal) > 40.0:
		return
	MatchMotion.set_goal(t, _clear_of_pack(goal + (own - goal).normalized() * 2.2), urgency)
	_busy[o] = true


## A marking contest where a long kick lands: the winner, his opponent and
## the nearest player from each side fly for it.
func _contest(at: Vector2, winner: int, urgency: float) -> void:
	var members := []
	if winner >= 0:
		members.append(winner)
		var o := int(tokens[winner]["match"])
		if o >= 0:
			members.append(o)
	members += _nearest(at, 0, 1, members) + _nearest(at, 1, 1, members)
	for i in range(members.size()):
		var id: int = members[i]
		if _busy.has(id) and id != winner:
			continue
		var ang := TAU * float(i) / float(maxi(1, members.size())) + 0.4
		var off := Vector2.ZERO if id == winner else Vector2(cos(ang), sin(ang)) * 2.0
		MatchMotion.set_goal(tokens[id], at + off, urgency)
		_busy[id] = true
		_meant_now()[id] = true


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------
func _enter(p: Dictionary) -> void:
	if str(p["t"]) == "wait" and p.has("scoop"):
		# (Stamped whether or not a 3D oval is watching: _keep_off_ball reads it, and the play
		# must be the same either way.)
		tokens[int(p["scoop"])]["scoop_at"] = time
	if want_contacts:
		_touch(p)
	match str(p["t"]):
		"setup":
			mode = str(p.get("mode", "centre"))
			# A set-up never claims a player the log needs in the next few
			# events: he keeps his lead (roadmap §1.11 collection pauses, the
			# 2026-10-08 record: a receiver held on the goal line by a kick-in
			# layout, then a 60 m sprint to collect).
			var layout: Dictionary = {}
			for id in p["layout"]:
				if not _lead.has(id) or id == int(p.get("keep", -1)):
					layout[id] = p["layout"][id]
			p["layout"] = layout
			for id in layout:
				MatchMotion.set_goal(tokens[id], layout[id], 0.45, true)
				tokens[id]["reset"] = SETUP_PACE
				_busy[id] = true
			_ball_carry(p["ball_to"])
			_struct_ball = p["ball_to"]
		"wait":
			if p.has("drop"):
				_drop_held(p["drop"])
			if p.has("scoop"):
				p["dur"] = _scoop_start(int(p["scoop"]))
			if p.get("ease", false):
				for t in tokens:
					if not _busy.has(int(t["id"])):
						MatchMotion.set_goal(t, (t["pos"] as Vector2) + (t["vel"] as Vector2) * 0.25, 0.1)
						_busy[int(t["id"])] = true
		"bounce", "throwup":
			var at: Vector2 = p["at"]
			var up := 8.5 if p["t"] == "bounce" else 5.0
			_ball_flight(at, at, 0.4 if p["t"] == "bounce" else 1.8, 3.5, up,
					0.7 if p["t"] == "bounce" else 0.45)
			for t in tokens:
				# (A Win Contest ring has put its rucks, or the men standing in
				# for them, on the ball already: _pack_ring.)
				if str(t["role"]) == "RUCK" and not (_ring_at.is_finite() and p["t"] == "throwup"):
					var id := int(t["id"])
					MatchMotion.set_goal(t, at + Vector2(-0.8 * _dir(int(t["side"])), 0.0), 1.0, true)
					_busy[id] = true
			if p["t"] == "bounce":
				# A stacked ball-up: the wings crash in as the ball goes up.
				for t in tokens:
					var s := str(t["slot"])
					if (s == "WL" or s == "WR") and _centre_setup(int(t["side"])) == "stack":
						MatchMotion.set_goal(t, at + Vector2(-4.0 * _dir(int(t["side"])), 6.0 * signf((t["pos"] as Vector2).y)), 1.0, true)
						_busy[int(t["id"])] = true
					elif CONTEST_CRASH.has(s) and _centre_setup(int(t["side"])) == "stack":
						# Win Contest or Stack the stoppage: both half-lines crash in
						# too, once the ball is up, a beat after the wings.
						var out: Vector2 = (t["pos"] as Vector2) - at
						_crash_late(t, at + out.normalized() * CONTEST_RING)
						t["crashing"] = true
						_busy[int(t["id"])] = true
			if p.has("recv") and int(p["recv"]) >= 0 and p.has("loc"):
				MatchMotion.set_goal(tokens[int(p["recv"])], p["loc"], 1.0, true)
		"flight":
			if str(ball["mode"]) == "held":
				# Kicked from his hands: a ball he took this frame has not been
				# drawn there yet, and flew from where it lay 2.4 m off (seed 31).
				_update_ball(0.0)
			var to: Vector2 = p["to"]
			var from: Vector2 = ball["pos"]
			var dur := float(p.get("dur", 0.5))
			var recv := int(p.get("recv", -1))
			if recv >= 0:
				var r: Dictionary = tokens[recv]
				MatchMotion.set_goal(r, to, 1.0)
				_busy[recv] = true
				if p.get("adapt", false):
					# Hang the ball long enough for the receiver to get there,
					# within what a kick of that length can plausibly take
					# (KICK_HANG_MAX).
					dur = clampf(MatchMotion.eta(r, to) * 0.9, dur, dur * float(p.get("hang", KICK_HANG_MAX)))
				if p.get("contest", false):
					_contest(to, recv, 1.0)
			var h0 := float(p.get("h0", 1.0 if int(ball["holder"]) >= 0 else float(ball["h"])))
			_ball_flight(from, to, h0, float(p.get("h1", 1.0)), float(p.get("apex", 2.0)), dur)
			_struct_ball = to
			mode = str(p.get("mode", "open"))
			p["dur"] = dur
		"collect":
			var who := int(p.get("who", -1))
			if who >= 0:
				MatchMotion.set_goal(tokens[who], ball["pos"], 1.0, true)
				_busy[who] = true
		"possess":
			var who2 := int(p.get("who", -1))
			if who2 >= 0:
				ball["mode"] = "held"
				ball["holder"] = who2
				_busy[who2] = true
				_poss = int(tokens[who2]["side"])
				if not p.get("quiet", false):
					actor = who2
		"emit":
			_emit(p)
		"hold":
			var who3 := int(p.get("who", -1))
			if who3 >= 0:
				var t3: Dictionary = tokens[who3]
				var carry: Vector2 = p.get("carry", Vector2.INF)
				var goal: Vector2 = t3["pos"]
				if p.get("back", false):
					var att := Vector2(MatchMotion.GOAL_X * _dir(int(t3["side"])), 0.0)
					goal = goal + (goal - att).normalized() * 3.0
				elif carry.is_finite():
					goal = carry
				MatchMotion.set_goal(t3, goal, 0.8, true)
				_busy[who3] = true
			if p.has("mode"):
				mode = str(p["mode"])
		"chase":
			var vt: Dictionary = tokens[int(p["victim"])]
			MatchMotion.set_goal(vt, vt["pos"], 0.2, true)
			MatchMotion.set_goal(tokens[int(p["who"])], vt["pos"], 1.0, true)
			_busy[int(p["who"])] = true
			_busy[int(p["victim"])] = true
		"down":
			for id in [int(p["who"]), int(p["victim"])]:
				tokens[id]["down"] = float(p["dur"])
				tokens[id]["tackle_t"] = time
				tokens[id]["vel"] = (tokens[id]["vel"] as Vector2) * 0.3
			ball["mode"] = "dead"
			ball["holder"] = -1
			mode = "stoppage"
		"pack":
			mode = str(p.get("mode", "stoppage"))
			var at2: Vector2 = p["at"]
			if p.has("drop"):
				_drop_held(p["drop"])
			var members: Array = p["members"]
			if str(p.get("mode", "")) == "stoppage" and (_plan_of(0) == "contest" or _plan_of(1) == "contest"):
				# Win Contest: a ring, not a stack (_pack_ring).
				var spots := _pack_ring(at2, members, int(p.get("winner", -1)))
				p["spots"] = spots
				# The ring takes a moment longer to set than a stack: everyone in
				# place before the umpire throws it up (PACK_RING_WAIT at most).
				p["need"] = maxi(int(p.get("need", 4)), (members as Array).size())
				p["max"] = maxf(float(p.get("max", 1.0)), PACK_RING_WAIT)
				for id in spots:
					MatchMotion.set_goal(tokens[id], spots[id], 0.95)
					_busy[int(id)] = true
				# Everyone else near the ball clears out of the ring now, each on
				# his own bearing, a disc clear of the last to go that way.
				var gone := []
				for t in tokens:
					var off: Vector2 = (t["pos"] as Vector2) - at2
					if spots.has(int(t["id"])) or off.length() >= CONTEST_KEEP:
						continue
					var ang := off.angle() if off.length() > 0.01 else -PI * 0.5
					for tries in range(12):
						var clash := false
						for g in gone:
							if absf(wrapf(ang - float(g), -PI, PI)) < PACK_CLEAR_ARC:
								clash = true
						if not clash:
							break
						ang += PACK_CLEAR_ARC
					gone.append(ang)
					MatchMotion.set_goal(t, at2 + Vector2.from_angle(ang) * CONTEST_KEEP, 1.0, true)
					_busy[int(t["id"])] = true
			else:
				for i in range(members.size()):
					var ang := TAU * float(i) / float(maxi(1, members.size()))
					var r := 2.0 + 1.5 * float(i % 2)
					MatchMotion.set_goal(tokens[members[i]], at2 + Vector2(cos(ang), sin(ang)) * r, 0.95)
					_busy[int(members[i])] = true
			_struct_ball = at2
		"crumb":
			# The ball is in the air in open play: the nearest forwards lead to
			# the goal square for the crumb and the nearest defenders chase.
			var at4: Vector2 = p["at"]
			var drop := at4 - Vector2(10.0 * signf(at4.x), 0.0)
			var fwd_side := int(p["side"])
			for sd in [fwd_side, 1 - fwd_side]:
				for id in _nearest(drop, sd, 2, []):
					if not _busy.has(int(id)):
						MatchMotion.set_goal(tokens[id], drop, 0.9)
						_busy[int(id)] = true
		"celebrate":
			var who4 := int(p.get("who", -1))
			mode = "shot"
			if who4 >= 0 and float(p["dur"]) > 1.0:
				var at3: Vector2 = tokens[who4]["pos"]
				for id in _nearest(at3, int(tokens[who4]["side"]), 3, [who4]):
					if (tokens[id]["pos"] as Vector2).distance_to(at3) < 30.0:
						MatchMotion.set_goal(tokens[id], at3, 0.7)
						_busy[id] = true
			for t in tokens:
				if not _busy.has(int(t["id"])):
					MatchMotion.set_goal(t, (t["pos"] as Vector2) + (t["vel"] as Vector2) * 0.3, 0.1)
					_busy[int(t["id"])] = true
		"spill":
			# Out of the tackle, along the turf: at most SPILL_METRES, never past
			# half the gap to the man who gathers it. Beside the tackle there is no
			# run-up in that, so it squirts out the side, away from him, to land
			# SPILL_RUNUP from him: he runs onto it, it never rolls past his boots.
			var gp: Vector2 = tokens[int(p["toward"])]["pos"]
			var to2: Vector2 = gp - (ball["pos"] as Vector2)
			var dir2 := to2.normalized() if to2.length() > 0.01 else Vector2.RIGHT.rotated(_rng.randf_range(0.0, TAU))
			var land := (ball["pos"] as Vector2) + dir2 * minf(SPILL_METRES, to2.length() * 0.5)
			if land.distance_to(gp) < SPILL_RUNUP:
				var out := (dir2.orthogonal() * (1.0 if _rng.randf() < 0.5 else -1.0) - dir2 * SPILL_PAST).normalized()
				var b := -to2.dot(out)   # b·out, b = ball - gp
				var reach := -b + sqrt(maxf(b * b - to2.length_squared() + SPILL_RUNUP * SPILL_RUNUP, 0.0))
				land = MatchMotion.clamp_to_oval((ball["pos"] as Vector2) + out * reach, 3.0)
			ball["mode"] = "loose"
			ball["holder"] = -1
			# A loose ball decays at exp(-3t): a push of 3v travels about v metres.
			ball["vel"] = (land - (ball["pos"] as Vector2)) * 3.0
			MatchMotion.set_goal(tokens[int(p["toward"])], ball["pos"] + (ball["vel"] as Vector2) / 3.0, 1.0, true)
			_busy[int(p["toward"])] = true
		"fumble":
			ball["mode"] = "loose"
			ball["holder"] = -1
			if p.has("along"):
				# Off his hands on the run: knocked on, ahead of him along his line, turned toward
				# the man MatchSim has gathering it next, a pickup's length ahead of him on his run
				# (director 2026-11-16: the ball's path carries it to the winner; seed 31: knocked on
				# at random it went 4 m from him while he ran on away from it, and lay alone 0.8 s).
				# From a stand (the near gather) it can come off his hands any way.
				var al := int(p["along"])
				var ft: Dictionary = tokens[al]
				var line: Vector2 = ft.get("line", _line(ft))
				var way := line.rotated(_rng.randf_range(-KNOCK_ON, KNOCK_ON))
				var metres := _rng.randf_range(FUMBLE_METRES.x, FUMBLE_METRES.y)
				var nw := _next_collector()
				if nw >= 0 and nw != al:
					var wt: Dictionary = tokens[nw]
					var wvel: Vector2 = wt["vel"]
					var ahead := wvel.normalized() * scoop_lead(SCOOP_AT_PACE) if wvel.length() > 0.5 else Vector2.ZERO
					var to: Vector2 = (wt["pos"] as Vector2) + ahead - (ball["pos"] as Vector2)
					if to.length() > 0.01:
						way = to if _sk(al) == SCOOP_NEAR else line.rotated(clampf(line.angle_to(to), -KNOCK_ON, KNOCK_ON))
						metres = clampf(to.length(), FUMBLE_CLOSE, FUMBLE_METRES.y)
				_knock_on(al, way, minf(metres, maxf(_knock_room(ball["pos"], way), FUMBLE_CLOSE)))
			else:
				var to := _loose_to()
				if to.is_finite():
					# Toward where the match has it picked up next, as far as this touch sends it.
					var way: Vector2 = to - (ball["pos"] as Vector2)
					var reach: float = LOOSE_REACH.get(str(p.get("how", "")), LOOSE_REACH[""])
					var metres := minf(way.length(), reach) * _rng.randf_range(0.85, 1.0)
					ball["vel"] = way.normalized().rotated(_rng.randf_range(-LOOSE_SPREAD, LOOSE_SPREAD)) * metres * 3.0
				else:
					var ang2 := _rng.randf_range(0.0, TAU)
					ball["vel"] = Vector2(cos(ang2), sin(ang2)) * _rng.randf_range(6.0, 10.0)


## A phase that starts with a touch of the ball records it in `contacts` (see there).
func _touch(p: Dictionary) -> void:
	match str(p["t"]):
		"flight":
			var how := StringName(str(p.get("how", "kick")))
			var who := int(ball["holder"]) if str(ball["mode"]) == "held" else -1
			if how == &"ruck_tap":
				who = _nearest_ruck(ball["pos"])
			_last_how = how if who >= 0 else &""
			if who >= 0:
				_contact(who, how, p["to"])
		"possess":
			var who := int(p.get("who", -1))
			if who >= 0:
				var how := &"gather"
				if str(_beat.get("kind", "")) == "mark":
					how = &"mark"
				elif _last_how == &"handball":
					how = &"handball_receive"
				_contact(who, how, ball["pos"])
			_last_how = &""
		"wait":
			if p.has("scoop"):
				_contact(int(p["scoop"]), &"ground_ball", _scoop_aim(int(p["scoop"])))
		"down":
			var v := int(p["victim"])
			_contact(int(p["who"]), &"tackle", tokens[v]["pos"], v)
		"fumble":
			if p.has("how") and int(p.get("who", -1)) >= 0:
				_contact(int(p["who"]), StringName(str(p["how"])), ball["pos"], int(p.get("other", -1)))
		"bounce":
			_contact(-1, &"bounce", p["at"])
		"celebrate":
			if int(p.get("who", -1)) >= 0 and bool(flash.get("goal", false)):
				_contact(int(p["who"]), &"goal_celebrate", tokens[int(p["who"])]["pos"])


## The line a man is running on: his heading, or toward the ball when he is near still.
func _line(t: Dictionary) -> Vector2:
	var v: Vector2 = t["vel"]
	if v.length() > 0.5:
		return v.normalized()
	var to: Vector2 = (ball["pos"] as Vector2) - (t["pos"] as Vector2)
	return to.normalized() if to.length() > 0.01 else Vector2.RIGHT


func _contact(who: int, kind: StringName, at: Vector2, other := -1) -> void:
	if kind == &"ground_ball" and who >= 0:
		tokens[who]["scoop_at"] = time
	if not want_contacts:
		return
	contacts.append({"who": who, "kind": kind, "at": at, "other": other})
	if contacts.size() > 64:
		contacts.pop_front()


func _nearest_ruck(at: Vector2) -> int:
	var best := -1
	var bd := INF
	for t in tokens:
		if str(t["role"]) == "RUCK" and float(t["down"]) <= 0.0:
			var d := (t["pos"] as Vector2).distance_to(at)
			if d < bd:
				bd = d
				best = int(t["id"])
	return best

## Dead-ball repositioning during set-ups: players move this much faster than
## in play (a real reset takes 20-40 s), and play resumes once all but
## SETUP_STRAGGLERS are within SETUP_NEAR metres of their spots.
const SETUP_PACE := 1.5
const SETUP_NEAR := 5.0
const SETUP_STRAGGLERS := 3


func _end_reset_pace() -> void:
	for t in tokens:
		t["reset"] = 1.0


func _done(p: Dictionary) -> bool:
	match str(p["t"]):
		"setup":
			if _pt < float(p["min"]) or str(ball["mode"]) == "carry":
				return false
			var layout: Dictionary = p["layout"]
			var off := 0
			for id in layout:
				if (tokens[id]["pos"] as Vector2).distance_to(layout[id]) > SETUP_NEAR:
					off += 1
			# Set when all but a couple are in place; the cap stops one
			# straggler holding up the game.
			if off > SETUP_STRAGGLERS and _pt < float(p["max"]):
				return false
			_end_reset_pace()
			return true
		"pack":
			if _pt < float(p["min"]):
				return false
			var ring: Dictionary = p.get("spots", {})
			# A ring waits for the four on the ball (an umpire waits for his
			# rucks), up to PACK_RUCK_WAIT, and for the ground round it to clear.
			var rucks_set := true
			for id in ring:
				if (ring[id] as Vector2).distance_to(p["at"]) < 3.0 						and (tokens[id]["pos"] as Vector2).distance_to(ring[id]) >= PACK_INNER_SET:
					rucks_set = false
			if not ring.is_empty() and _pt < PACK_RUCK_WAIT:
				if not rucks_set:
					return false
				for t in tokens:
					if not ring.has(int(t["id"])) and (t["pos"] as Vector2).distance_to(p["at"]) < PACK_RING - 1.5:
						return false
			if _pt >= float(p["max"]):
				return true
			var n := 0
			for id in p["members"]:
				if ring.has(id):
					var on_ball: bool = (ring[id] as Vector2).distance_to(p["at"]) < 3.0
					if (tokens[id]["pos"] as Vector2).distance_to(ring[id]) < (PACK_INNER_SET if on_ball else PACK_SET):
						n += 1
				elif (tokens[id]["pos"] as Vector2).distance_to(p["at"]) < 5.0:
					n += 1
			# A bigger pack (Win Contest's extra numbers) takes a moment longer to form.
			var formed := n >= mini(int(p.get("need", 4)), (p["members"] as Array).size())
			if formed and not ring.is_empty():
				# A ring holds a moment once set, so it reads before the ball goes up.
				if not p.has("_set_t"):
					p["_set_t"] = _pt
				return _pt - float(p["_set_t"]) >= PACK_SETTLE
			return formed
		"collect":
			var who := int(p.get("who", -1))
			if who < 0:
				return true
			var t: Dictionary = tokens[who]
			if str(ball["mode"]) == "held" and int(ball["holder"]) != who:
				# Someone else still has it (a kick-in taker when the log
				# moves on without his kick): he puts it down where he is,
				# rather than carrying it up the ground for the receiver.
				ball["mode"] = "dead"
				ball["holder"] = -1
			var d := (t["pos"] as Vector2).distance_to(ball["pos"])
			var gt := float(t.get("gather_t", -1.0))
			if gt >= 0.0 and time < gt:
				# His hands are going down on it (the pickup): it is his at the touch, and the men
				# near it keep coming meanwhile. (A collect capped by "max" still ends on time: the
				# next one carries on with the same pickup, unless the next phase puts it in his hands.)
				_scrap_in(p, who)
				return _gather_cap(p)
			if gt >= 0.0:
				t.erase("gather_t")
				if time - gt <= GATHER_LATE:
					return true
			# (A man whose hands are already going down on it is always let finish: the ball comes
			# off them before the collect can end, COLLECT_LIMIT or not.)
			if p.has("_touch_t") and p.get("_close", false):
				# A man on it first with him close: he keeps coming at the scoop's pace, and it comes
				# off the man's hands into his path.
				# Braking (as MatchMotion's arrive does) only to reach it at the scoop's pace.
				MatchMotion.set_goal(t, ball["pos"], 1.0, true)
				t["cap"] = sqrt(SCOOP_SPEED * SCOOP_SPEED + 2.0 * MatchMotion.BRAKE * 0.55 * maxf(d - SCOOP_LEAD, 0.0))
				_scrap(p, who)
				return false
			if p.has("_touch_t"):
				# A team-mate's hands are going down on it in the scrap: he pulls up a few
				# metres short, and it comes off them toward him before he can have it.
				# Coming at pace for a spilled ball he holds off further: the knock comes at most
				# halfway to him, and he still has a run at it from there.
				var back: Vector2 = (t["pos"] as Vector2) - (ball["pos"] as Vector2)
				var hold := KNOCK_CLEAR + 1.0 if p.get("pace", false) else FUMBLE_METRES.x
				if p.get("pace", false) and back.length() <= hold:
					# Inside that, he keeps coming at the scoop's pace (never standing over it),
					# no nearer than KNOCK_CLEAR, so the knock stops a scoop's run ahead of him.
					MatchMotion.set_goal(t, (ball["pos"] as Vector2) + back.normalized() \
							* maxf(back.length() - 2.0, KNOCK_CLEAR), 1.0, true)
					t["cap"] = SCOOP_SPEED
				else:
					MatchMotion.set_goal(t, t["pos"] if back.length() <= hold \
							else (ball["pos"] as Vector2) + back.normalized() * hold, 1.0, true)
				_scrap(p, who)
				return false
			if p.get("pace", false):
				# At where his hands will meet it, flat out, aimed through it, braking (as
				# MatchMotion's arrive does) only to reach it at the scoop's own pace, never below.
				# He goes down for it once that spot is a scoop's length ahead.
				var aim := _scoop_aim(who, SCOOP_AT_PACE)
				var dr := (t["pos"] as Vector2).distance_to(aim)
				var to := aim - (t["pos"] as Vector2)
				MatchMotion.set_goal(t, aim + to.normalized() * RUN_THROUGH if dr > 0.01 else aim, 1.0, true)
				t["cap"] = sqrt(SCOOP_SPEED * SCOOP_SPEED + 2.0 * MatchMotion.BRAKE * 0.55 * maxf(dr - SCOOP_LEAD, 0.0))
				# (where his hands will meet it, rolling no faster than SCOOP_ROLL by then).
				var kind := _scoop_pick(who)
				if kind >= 0:
					t["scoop_k"] = kind
					return true
				if dr <= scoop_lead(SCOOP_AT_PACE):
					# Too near now to take it on the run (a close knock lands it a near gather's length
					# ahead): he brakes the last of the way to the near gather's pace, in a stride, and
					# takes it from there, rather than walking straight over it (suite match: the winner
					# crossed it at 2.9 m/s, 7 times).
					t["cap"] = minf(float(t["cap"]), scoop_speed(SCOOP_NEAR) + SCOOP_EASE - 0.05)
				if _pt > 0.1 and str(ball["mode"]) in ["dead", "loose"]:
					# While he is coming, the men already near it contest it (a spilled
					# ball is a loose ball like any other).
					_scrap(p, who)
			elif int(ball["holder"]) < 0 and (str(ball["mode"]) == "loose" \
					or (str(ball["mode"]) == "dead" and p.get("roll", false))):
				# A ball on the ground: he goes down and picks it up, as any man in a scrap does (at
				# pace, or the near gather from a stand), never a snap into his hands from a metre and
				# more off the turf (seed 31: a fumble bobbled 4.4 m/s at him with no hands on it, then
				# jumped 1.4 m into his). Coming flat out, braking only to the scoop's pace.
				var aim2 := _scoop_aim(who, SCOOP_AT_PACE)
				var dr2 := (t["pos"] as Vector2).distance_to(aim2)
				var to2 := aim2 - (t["pos"] as Vector2)
				MatchMotion.set_goal(t, aim2 + to2.normalized() * RUN_THROUGH if dr2 > 0.01 else aim2, 1.0, true)
				t["cap"] = sqrt(SCOOP_SPEED * SCOOP_SPEED + 2.0 * MatchMotion.BRAKE * 0.55 * maxf(dr2 - SCOOP_LEAD, 0.0))
				if dr2 <= scoop_lead(SCOOP_AT_PACE):
					t["cap"] = minf(float(t["cap"]), scoop_speed(SCOOP_NEAR) + SCOOP_EASE - 0.05)
				var kind2 := _scoop_pick(who, INF)
				if kind2 >= 0 and _pt - float(p.get("_knock_t", -KNOCK_EVERY)) >= KNOCK_GATHER:
					t["scoop_k"] = kind2
					t["gather_t"] = time + _scoop_start(who)
					_contact(who, &"ground_ball", _scoop_aim(who))
					_scrap_in(p, who)
					return _gather_cap(p)
			else:
				MatchMotion.set_goal(t, ball["pos"], 1.0, true)
				# A ball just knocked to him off a team-mate's hands rolls to him before he has it.
				if d <= 1.4 and _pt - float(p.get("_knock_t", -KNOCK_EVERY)) >= KNOCK_GATHER:
					return true
			if p.has("max") and _pt >= float(p["max"]):
				return true
			# Never a freeze: a ball against the fence or a crowd round it can
			# keep him just short of it. Close enough after a moment is his,
			# and no collect lasts longer than COLLECT_LIMIT. A ball just knocked his way
			# in a scrap rolls to him first.
			# (A ball on the ground he still goes down for: seed 31, this put it in his hands from 2 m.)
			if (_pt >= 1.5 and d <= 3.0 and not p.get("pace", false) and str(ball["mode"]) != "loose" \
					and _pt - float(p.get("_knock_t", -KNOCK_EVERY)) >= KNOCK_EVERY) or _pt >= COLLECT_LIMIT:
				return true
			# (No bobble his way any more: a ball on the ground moves only off a man's hands, and he
			# goes down for it where it lies. Director 2026-11-16.)
			if p.get("roll", false) and _pt > 0.1 and str(ball["mode"]) in ["dead", "loose"]:
				_scrap(p, who)
			return false
		"chase":
			var tk: Dictionary = tokens[int(p["who"])]
			var v: Dictionary = tokens[int(p["victim"])]
			MatchMotion.set_goal(tk, v["pos"], 1.0, true)
			return (tk["pos"] as Vector2).distance_to(v["pos"]) <= 1.6 or _pt >= float(p["max"])
		"emit", "possess":
			return true
		"hold":
			if p.get("run", false):
				var c: Dictionary = tokens[int(p["who"])]
				return (c["pos"] as Vector2).distance_to(p["carry"]) <= 1.5 or _pt >= float(p["max"])
			return _pt >= float(p.get("dur", 0.0))
		"flight":
			return _pt >= float(p["dur"])
		"bounce":
			return _pt >= 0.7
		"throwup":
			return _pt >= 0.45
		"wait":
			if p.has("scoop"):
				_scrap_in(p, int(p["scoop"]))
			return _pt >= float(p.get("dur", 0.0))
		"fumble":
			# Off a man's hands it is a loose ball like any other: the men nearest it go at it flat
			# out, the man who fumbled it too (seed 31: he walked on beside it, and a man who dropped
			# a mark stood still as it rolled off him).
			if str(ball["mode"]) in ["dead", "loose"] and int(ball["holder"]) < 0:
				_scrap_in(p, -1)
			return _pt >= float(p.get("dur", 0.0))
		"spill":
			# Out of the tackle it is a loose ball already: the men nearest it go at it now, rather
			# than walking to their press spot beside it until the collect starts.
			_scrap_in(p, int(p["toward"]), true)
			return _pt >= float(p.get("dur", 0.0))
		_:
			return _pt >= float(p.get("dur", 0.0))


## A collect capped by "max" ends on time while his pickup goes on (the next collect carries it
## on), except before the phase that puts it in his hands or takes it off them (possess, or a
## fumble): that waits for the touch (suite match: a fumble knocked it on from 5-7 m short of
## the hands going down for it, with nobody's hands on it).
func _gather_cap(p: Dictionary) -> bool:
	if not p.has("max") or _pt < float(p["max"]):
		return false
	var i := _pi + 1
	while i < _phases.size() and str((_phases[i] as Dictionary).get("t", "")) == "emit":
		i += 1
	return i >= _phases.size() or not str((_phases[i] as Dictionary).get("t", "")) in ["possess", "fumble"]


func _emit(p: Dictionary) -> void:
	var k := int(_beat["k"])
	var ev: Dictionary = events[k]
	var kind := str(ev.get("kind", ""))
	if kind == "sub":
		_sub(ev)
	var a := _actor_id(ev)
	if a >= 0 and not META.has(kind):
		actor = a
	if p.get("log", false):
		_log_arrival(k)
	var fl := str(p.get("flash", ""))
	if fl != "":
		flash = {"pos": ball["pos"], "left": 0.9, "goal": fl == "goal"}
	# Anything drawn before this in the same beat was the lead-up.
	emitted = k + 1
	_out.append(ev)


## Point on the oval boundary for longitudinal field position x. Keep a
## stable side of the ground when play is already near one boundary; otherwise
## choose one from the presentation RNG (replay deterministic, simulation-free).
func _boundary_point(x: float, source_y: float) -> Vector2:
	var nx := clampf(x / MatchMotion.HALF_LEN, -1.0, 1.0)
	var y := MatchMotion.HALF_WID * sqrt(maxf(0.0, 1.0 - nx * nx))
	var side := signf(source_y)
	if absf(source_y) < 2.0:
		side = -1.0 if _rng.randf() < 0.5 else 1.0
	return Vector2(x, side * y * 0.985)


func _log_arrival(k: int) -> void:
	var ev: Dictionary = events[k]
	var kind := str(ev.get("kind", ""))
	var want := float(ev.get("fp", 0.0))
	if kind == "goal" or kind == "behind":
		want = MatchMotion.GOAL_X * _dir(int(ev.get("side", 0)))
	elif (ev.has("band") or _short_set_shot(k)) and _locs.has(k):
		# A set-shot mark stands on its band's spot (T2.24), and a set shot
		# that falls short drops in front of goal from there, not at the logged fp.
		want = (_locs[k] as Vector2).x
	if arrivals.size() >= 4000:
		arrivals.pop_front()
	arrivals.append({"idx": k, "kind": kind, "pos": ball["pos"], "want_x": want})


func _sub(ev: Dictionary) -> void:
	var side := int(ev.get("side", -1))
	if side < 0 or side > 1:
		return
	var ids: Dictionary = _ids[side]
	var off := int(ev.get("off_num", -1))
	if not ids.has(off):
		return
	var id: int = ids[off]
	ids.erase(off)
	var t: Dictionary = tokens[id]
	# The man coming off takes the bench place of the man coming on.
	var sitting: Array = bench[side]
	for b in range(sitting.size()):
		if int(sitting[b]["num"]) == int(ev.get("num", -1)):
			sitting[b] = {"num": int(t["num"]), "pid": str(t.get("pid", "")), "name": str(t.get("name", ""))}
			break
	t["num"] = int(ev.get("num", t["num"]))
	t["name"] = str(ev.get("name", t["name"]))
	# The player on takes the ring and the name with the slot.
	var on_id := str(ev.get("player_id", ""))
	if on_id != "":
		t["pid"] = on_id
		t["surname"] = _surname(on_id, str(t["name"]))
	ids[int(t["num"])] = id
	_assign()


# ---------------------------------------------------------------------------
# Ball
# ---------------------------------------------------------------------------
func _ball_flight(from: Vector2, to: Vector2, h0: float, h1: float, apex: float, dur: float) -> void:
	ball["mode"] = "flight"
	ball["holder"] = -1
	ball["from"] = from
	ball["to"] = to
	ball["h0"] = h0
	ball["h1"] = h1
	ball["apex"] = apex
	ball["dur"] = maxf(0.05, dur)
	ball["t"] = 0.0


func _ball_carry(to: Vector2) -> void:
	if (ball["pos"] as Vector2).distance_to(to) < 0.5:
		ball["pos"] = to
		ball["mode"] = "dead"
		ball["holder"] = -1
		return
	ball["mode"] = "carry"
	ball["holder"] = -1
	ball["to"] = to


## A ball-up is a dead ball: a player still holding it (the free kick just
## paid) gives it back to the umpire's spot instead of walking off with it.
## The ball travels from his hand to the spot (_ball_carry, a short toss of up
## to about 3 m) rather than jumping there in one frame.
func _drop_held(at: Vector2) -> void:
	if str(ball["mode"]) != "held":
		return
	_ball_carry(at)


func _update_ball(h: float) -> void:
	match str(ball["mode"]):
		"held":
			var t: Dictionary = tokens[int(ball["holder"])]
			var v: Vector2 = t["vel"]
			var off := v.normalized() * 0.6 if v.length() > 0.5 else Vector2.ZERO
			ball["pos"] = (t["pos"] as Vector2) + off
			ball["h"] = 1.0
		"flight":
			ball["t"] = float(ball["t"]) + h
			var u := clampf(float(ball["t"]) / float(ball["dur"]), 0.0, 1.0)
			ball["pos"] = (ball["from"] as Vector2).lerp(ball["to"], u)
			ball["h"] = lerpf(float(ball["h0"]), float(ball["h1"]), u) \
					+ 4.0 * float(ball["apex"]) * u * (1.0 - u)
			if u >= 1.0:
				ball["mode"] = "dead"
		"carry":
			var to: Vector2 = ball["to"]
			var pos: Vector2 = ball["pos"]
			var step := 32.0 * h
			if pos.distance_to(to) <= step:
				ball["pos"] = to
				ball["mode"] = "dead"
			else:
				ball["pos"] = pos + (to - pos).normalized() * step
			ball["h"] = 1.2
		"loose":
			ball["pos"] = MatchMotion.clamp_to_oval((ball["pos"] as Vector2) + (ball["vel"] as Vector2) * h, 1.0)
			ball["vel"] = (ball["vel"] as Vector2) * exp(-3.0 * h)
			ball["h"] = maxf(0.0, float(ball["h"]) - 6.0 * h)
		_:
			ball["h"] = maxf(0.0, float(ball["h"]) - 7.0 * h)


# ---------------------------------------------------------------------------
# Who is on whom (ARD-M8-003 tactical timeline)
# ---------------------------------------------------------------------------
## A live match's timeline grows each quarter; MatchScene hands it over with
## the new events.
func set_timeline(timeline: Array) -> void:
	_timeline = timeline


## Bring in every recorded call that applies by event `k`.
func _apply_timeline(k: int) -> void:
	var changed := false
	while _tl_i < _timeline.size() and int((_timeline[_tl_i] as Dictionary).get("at", 0)) <= k:
		var e: Dictionary = _timeline[_tl_i]
		_tac[int(e.get("side", 0))] = e
		_tl_i += 1
		changed = true
	if changed:
		_assign()


## Who plays on whom, from the match's own calls where it recorded them: the
## named match-ups, the tagger on his man, the loose defender off his, and the
## forward sent to make him accountable. Slot pairs fill in the rest, and
## the back line is then fitted to the forwards it faces (_fit_defence).
func _assign() -> void:
	var by_pid := {}
	for t in tokens:
		by_pid[str(t["pid"])] = int(t["id"])
		t["match"] = int(t.get("slot_match", -1))
		t["loose"] = false
		t["tagging"] = false
		t["chasing"] = -1
	# Pairs the match recorded (its duels, the tag) and the loose men: the
	# back line's fitting leaves these alone. A match-up shows while its
	# defender stands in the back line and its forward up forward; one
	# rotated into another line plays there until he is back.
	var held := {}
	for side in range(2):
		var e: Dictionary = _tac[side]
		var duels: Dictionary = e.get("duels", {})
		for fid in duels:
			var f := int(by_pid.get(str(fid), -1))
			var d := int(by_pid.get(str(duels[fid]), -1))
			if f >= 0 and d >= 0 and str(tokens[d]["role"]) == "DEF" and str(tokens[f]["role"]) == "FWD":
				_pair(d, f)
				held[f] = true
				held[d] = true
	for side in range(2):
		var e: Dictionary = _tac[side]
		var tagger := int(by_pid.get(str(e.get("tagger", "")), -1))
		var target := int(by_pid.get(str(e.get("tag", "")), -1))
		if tagger >= 0 and target >= 0:
			_pair(tagger, target)
			tokens[tagger]["tagging"] = true
			held[tagger] = true
			held[target] = true
		var loose := int(by_pid.get(str(e.get("loose", "")), -1))
		if loose >= 0:
			_unpair(loose)
			tokens[loose]["loose"] = true
			held[loose] = true
	_fit_defence(held)
	# A forward sent to the other side's loose man: the forward left without
	# a direct opponent goes with him.
	for side in range(2):
		if not bool((_tac[side] as Dictionary).get("accountable", false)):
			continue
		var their_loose := int(by_pid.get(str((_tac[1 - side] as Dictionary).get("loose", "")), -1))
		if their_loose < 0:
			continue
		for t in tokens:
			if int(t["side"]) == side and str(t["role"]) == "FWD" and int(t["match"]) < 0:
				t["chasing"] = their_loose
				break


## The back line against the forwards it faces, after the recorded pairs:
## a player in a back slot minds a forward only when he is a defender by
## trade (a forward or a midfielder rotated into a back pocket plays the space
## and the ball). A defender keeps the forward his slot faces; a forward left
## without one is picked up by a free defender, the tallest free defender on
## the tallest such forward. A forward still left over has no direct
## opponent. `held`: token ids to leave.
func _fit_defence(held: Dictionary) -> void:
	for side in range(2):
		var fwds := []
		var defs := []
		var kept := {}
		for t in tokens:
			var id := int(t["id"])
			if held.has(id) or int(t["side"]) != side or str(t["role"]) != "DEF":
				continue
			var o := int(t["match"])
			var minds := o >= 0 and str(tokens[o]["role"]) == "FWD" and not held.has(o)
			if bool(_who(str(t["pid"]))["def"]):
				if minds:
					kept[o] = true
				else:
					defs.append(t)
			elif minds:
				_unpair(id)
		for t in tokens:
			var id := int(t["id"])
			if int(t["side"]) == side or str(t["role"]) != "FWD" or held.has(id) or kept.has(id):
				continue
			var o := int(t["match"])
			if o >= 0 and str(tokens[o]["role"]) == "DEF":
				_unpair(id)
			if int(t["match"]) < 0:
				fwds.append(t)
		var taller := func(a, b):
			var ha := float(_who(str(a["pid"]))["h"])
			var hb := float(_who(str(b["pid"]))["h"])
			if ha != hb:
				return ha > hb
			return int(a["id"]) < int(b["id"])
		fwds.sort_custom(taller)
		defs.sort_custom(taller)
		for i in range(mini(fwds.size(), defs.size())):
			_pair(int(defs[i]["id"]), int(fwds[i]["id"]))


## A player's trade and size for the back line's fitting: a defender when his
## own position (the result's list_role, else his record) or a second or
## learned one is in the back line.
func _who(pid: String) -> Dictionary:
	if not _trade.has(pid):
		_trade[pid] = _trade_of(pid, "")
	return _trade[pid]


static func _trade_of(pid: String, list_role: String) -> Dictionary:
	var pl = GameDB.player_by_id(pid)
	var rec: Dictionary = pl if pl is Dictionary else {}
	var own := list_role if list_role != "" else str(rec.get("role", ""))
	var def := own == "DEF"
	if not def and not rec.is_empty():
		def = Ratings.second_positions(rec).has("DEF")
	return {"def": def, "h": float(rec.get("height_cm", 0.0))}


## ARD-M8-003, persistent identity for important live roles (the director,
## 2026-10-06: "Build it"): the players whose job the match recorded keep
## their names on the oval while the job is on - the tagger and his man, each
## side's loose defender, and the forward sent to him. Only those few, never
## the 36. Token ids, in a stable order.
func role_labels() -> Array:
	var out := []
	for t in tokens:
		var id := int(t["id"])
		var tagged := false
		var o := int(t.get("match", -1))
		if o >= 0 and bool(tokens[o].get("tagging", false)):
			tagged = true
		if bool(t.get("tagging", false)) or tagged or bool(t.get("loose", false)) 				or int(t.get("chasing", -1)) >= 0:
			out.append(id)
	return out


func _unpair(a: int) -> void:
	var o := int(tokens[a]["match"])
	if o >= 0 and int(tokens[o]["match"]) == a:
		tokens[o]["match"] = -1
	tokens[a]["match"] = -1


func _pair(a: int, b: int) -> void:
	_unpair(a)
	_unpair(b)
	tokens[a]["match"] = b
	tokens[b]["match"] = a


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------
func _refresh_structure() -> void:
	if tokens.is_empty():
		return
	var ball_p := _struct_ball
	var crash := _stoppage_on()
	# The side in possession first, so the other side can mark up on them.
	for side in [_poss, 1 - _poss]:
		var spots := {}
		for t in tokens:
			if int(t["side"]) == side and not _busy.has(int(t["id"])):
				spots[int(t["id"])] = _structure_spot(t, ball_p, _poss)
		_structure_limits(side, spots, ball_p, crash)
		for id in spots:
			var t: Dictionary = tokens[id]
			var g: Vector2 = spots[id]
			var d := (t["pos"] as Vector2).distance_to(g)
			var u := minf(clampf(d / 45.0, 0.1, 0.6) * _call_pace(side),
					1.0 if _burst_on(side, "surge") else CALL_PACE_TOP)
			var crashing: bool = crash and CONTEST_CRASH.has(str(t["slot"])) and _crashes(side)
			if crashing:
				# Crashing a stoppage is a sprint: the wings from the moment it
				# is called, both half-lines a beat after them, so they do not
				# arrive as one block.
				var first := not bool(t.get("crashing", false))
				t["crashing"] = true
				var wing := str(t["slot"]).begins_with("W")
				if first and not wing:
					_crash_late(t, g)
				elif not wing and float(t["react_left"]) > 0.0:
					t["pending"] = MatchMotion.clamp_to_oval(g, 2.0)
				else:
					MatchMotion.set_goal(t, g, 1.0, true)
				continue
			t["crashing"] = false
			if side == _poss and _plan_of(side) == "attacking" and d > LANE_SPACE * 0.5:
				u = maxf(u, CORRIDOR_INTO)   # into the lanes smartly when the ball is won
			if _plan_of(side) == "contest" and not crash and (str(t["role"]) in ["MID", "RUCK"] or (_shadow[side] as Array).has(id)):
				u = maxf(u, CONTEST_HUNT)   # Win Contest: the ring hunts the ball
			if _ring_at.is_finite() and (t["pos"] as Vector2).distance_to(_ring_at) < CONTEST_KEEP:
				u = 1.0   # out of the way of the pack's ring, smartly
			# Throw numbers at it: the engine's legs go 1.3 times as fast
			# (MatchSim movement pace), so the run past the ball does too, up
			# to a sprint (MatchMotion.SPRINT).
			var surging: bool = side == _poss and _burst_on(side, "surge")
			if surging:
				t["reset"] = SURGE_LEGS
				if str(t["role"]) in ["MID", "RUCK"] or SURGE_RUNNERS.has(str(t["slot"])):
					u = 1.0   # ...and the men running past it go flat out
			elif float(t.get("reset", 1.0)) == SURGE_LEGS:
				t["reset"] = 1.0
			MatchMotion.set_goal(t, g, u)


## A goal kept clear of a Win Contest pack's ring while it is set: anyone the
## play sends near the ball stops CONTEST_KEEP off it.
func _clear_of_pack(g: Vector2) -> Vector2:
	if not _ring_at.is_finite():
		return g
	var out := g - _ring_at
	if out.length() >= CONTEST_KEEP:
		return g
	return _ring_at + (out.normalized() if out.length() > 0.01 else Vector2.UP) * CONTEST_KEEP


## A half-line crashing a Win Contest stoppage: he goes CONTEST_STAGGER after
## the wings, flat out.
func _crash_late(t: Dictionary, g: Vector2) -> void:
	g = MatchMotion.clamp_to_oval(g, 2.0)
	t["pending"] = g
	t["pending_urgency"] = 1.0
	t["react_left"] = maxf(float(t["react_left"]), CONTEST_STAGGER)


## Limits every shape keeps, whatever the call (the motion critic, 2026-10-18):
## in possession each line keeps LINE_WIDTH_MIN of spread across the ground; no
## two of a side's spots pile up (they part front to back, SPOT_GAP apart); at a
## Win Contest stoppage nobody but the pack stands inside CONTEST_KEEP of the
## ball; and every spot stays STRUCT_MARGIN inside the boundary and out of the
## pockets, clear of the bench's tab on a phone. `spots` is id -> spot, changed in place.
func _structure_limits(side: int, spots: Dictionary, ball_p: Vector2, crash: bool) -> void:
	for id in spots:
		spots[id] = _keep_in(spots[id])
	# No pile: two spots closer than SPOT_GAP part along the ground, the one
	# further up it going forward; a player the play is steering (a lead, the
	# ball's press and support) stands where he is and the spot gives way.
	var dir := _dir(side)
	# Attack Corridor: in its lanes, two in one lane stand a whole disc apart.
	var gap := LANE_SPACE if side == _poss and not crash and _plan_of(side) == "attacking" else SPOT_GAP
	var fixed := []
	for t in tokens:
		if int(t["side"]) == side and not spots.has(int(t["id"])):
			fixed.append(t["goal"])
	var ids2: Array = spots.keys()
	for pass_no in range(4):
		var moved := false
		for i in range(ids2.size()):
			var a: Vector2 = spots[ids2[i]]
			for j in range(i + 1, ids2.size()):
				var b: Vector2 = spots[ids2[j]]
				var dy := absf(b.y - a.y)
				if dy >= gap or absf(b.x - a.x) >= gap:
					continue
				var need := sqrt(gap * gap - dy * dy)
				var dx := (b.x - a.x) * dir
				if absf(dx) >= need:
					continue
				var fwd := 1.0 if dx > 0.0 or (dx == 0.0 and int(ids2[j]) > int(ids2[i])) else -1.0
				var half := (need - absf(dx)) * 0.5 * fwd * dir
				a.x -= half
				b.x += half
				spots[ids2[j]] = b
				moved = true
			for f in fixed:
				var dy2 := absf((f as Vector2).y - a.y)
				# Attack Corridor: a man on the run (a lead, the ball) in this very
				# lane gets two discs of room, so the lane never queues into a file.
				var room := gap * 2.0 if gap == LANE_SPACE and dy2 < 2.0 else gap
				if dy2 >= gap or absf((f as Vector2).x - a.x) >= room:
					continue
				var need2 := room if room > gap else sqrt(gap * gap - dy2 * dy2)
				var dx2 := (a.x - (f as Vector2).x) * dir
				if absf(dx2) < need2:
					a.x += (need2 - absf(dx2)) * (1.0 if dx2 >= 0.0 else -1.0) * dir
					moved = true
			spots[ids2[i]] = a
		if not moved:
			break
	for id in spots:
		var p: Vector2 = spots[id]
		if crash and (_crashes(side) or _crashes(1 - side)):
			var out := p - ball_p
			var here: Vector2 = (tokens[id]["pos"] as Vector2) - ball_p
			if here.length() < CONTEST_KEEP and here.length() > 0.01:
				# Inside the ring's ground: out the near way, never across the pack.
				out = here.normalized() * maxf(out.length(), CONTEST_KEEP) if out.dot(here) < 0.0 or out.length() < CONTEST_KEEP else out
			if out.length() < CONTEST_KEEP:
				p = ball_p + (out.normalized() if out.length() > 0.01 else Vector2(-dir, 0.0)) * CONTEST_KEEP
			else:
				p = ball_p + out
		spots[id] = _keep_in(p)
	if side != _poss or crash or _plan_of(side) == "attacking":
		return   # Attack Corridor keeps its lanes instead (_attack_lanes)
	# In possession each line keeps its width. Spread about the line's middle;
	# where the ground narrows toward an end and the boundary holds a spot in,
	# the line comes in toward the centre of the ground, where there is room.
	var lines := {"DEF": [], "MID": [], "FWD": []}
	for id in spots:
		var role := str(tokens[id]["role"])
		(lines["MID" if role == "RUCK" else (role if lines.has(role) else "MID")] as Array).append(id)
	for key in lines:
		var ids: Array = lines[key]
		if ids.size() < 3:
			continue
		for attempt in range(4):
			var mean := 0.0
			for id in ids:
				mean += (spots[id] as Vector2).y / float(ids.size())
			var sd := 0.0
			for id in ids:
				sd += pow((spots[id] as Vector2).y - mean, 2.0) / float(ids.size())
			sd = sqrt(sd)
			if sd >= LINE_WIDTH_MIN:
				break
			var centre := mean * (1.0 if attempt == 0 else 0.4)
			var base_sd := 0.0
			for id in ids:
				base_sd += pow((tokens[id]["base"] as Vector2).y, 2.0) / float(ids.size())
			base_sd = sqrt(base_sd)
			# A touch past the floor, so the boundary's last word still leaves it.
			var want := LINE_WIDTH_MIN * 1.02
			for id in ids:
				var p: Vector2 = spots[id]
				if sd > 1.0:
					p.y = centre + (p.y - mean) * want / sd
				elif base_sd > 0.5:
					p.y = centre + (tokens[id]["base"] as Vector2).y * want / base_sd
				spots[id] = _keep_in(p)


## A structure spot kept STRUCT_MARGIN inside the boundary line and out of the
## pockets (beyond POCKET_Y across, deeper than POCKET_X): a disc there would
## sit on the line or under the bench's tab on a phone.
static func _keep_in(p: Vector2) -> Vector2:
	p = MatchMotion.clamp_to_oval(p, STRUCT_MARGIN)
	if absf(p.y) > POCKET_Y and absf(p.x) > POCKET_X:
		p.x = POCKET_X * signf(p.x)
	return p


## Where a player stands when the ball is at `ball_p` and `poss` has it.
func _structure_spot(t: Dictionary, ball_p: Vector2, poss: int) -> Vector2:
	var side := int(t["side"])
	var dir := _dir(side)
	var bx := ball_p.x * dir
	var base: Vector2 = t["base"]
	var role := str(t["role"])
	var slot := str(t["slot"])
	var has := poss == side
	var x := base.x
	match role:
		"DEF":
			x += 0.5 * bx if bx > 0.0 else 0.22 * bx
		"FWD":
			x += 0.15 * bx if bx > 0.0 else 0.5 * bx
		_:
			x += (0.7 if slot.begins_with("W") else 0.78) * bx
	var width := 1.08 if has else 0.86
	var pull := 0.12 if slot.begins_with("W") else (0.3 if role == "MID" or role == "RUCK" else 0.2)
	if not has and _pressing(side, bx):
		width *= PRESS_NARROW
	# The coach's other structural calls (P-12; the notes above ATTACK_WIDTH):
	# what the engine does with each call, drawn.
	var plan := _plan_of(side)
	var mid := role == "MID" or role == "RUCK"
	if has:
		match plan:
			"controlled":
				width = CONTROL_WIDTH
				pull *= CONTROL_PULL
				x = lerpf(x, bx + CONTROL_AHEAD, CONTROL_SHORT)
		if _burst_on(side, "hold"):
			width = maxf(width, HOLD_WIDTH)
			pull *= CONTROL_PULL
	var hb_line := slot == "CHB" or slot == "HBL" or slot == "HBR"
	if has and (_burst_on(side, "surge") or _burst_on(side, "push")):
		# Throw numbers at it, and Push numbers forward (row 151): the midfield and the half-back line run past
		# the ball, the forwards stay ahead of it and the back pockets come up,
		# so the numbers are ahead of it. They run to where the chain is going
		# (the furthest lead already on), not where the ball is now, so a
		# quick chain does not leave them behind.
		var ahead := _surge_ref(side, bx)
		if mid:
			x = maxf(x, ahead + SURGE_AHEAD)
		elif hb_line:
			x = maxf(x + SURGE_PUSH, ahead + SURGE_HB_AHEAD)
		elif role == "FWD":
			x = maxf(x, ahead + SURGE_FWD_AHEAD)
		else:
			x += SURGE_PUSH * 0.5
		x = minf(x, MatchMotion.GOAL_X - SURGE_SHORT)
	if _burst_on(side, "hold"):
		# Slow it down: the whole side sits deeper, the midfield and forwards
		# most (numbers behind the ball, nobody bolting ahead).
		x -= HOLD_DEEP if role == "DEF" else HOLD_DEEP_UP
	var y := lerpf(base.y * width, ball_p.y, pull)
	if not has:
		x -= 3.0
	var press_up := not has and _pressing(side, bx)
	if press_up:
		# High Press: while the ball is in their opponents' back half or the
		# middle, the whole side compresses into one band around the ball
		# (V1, press pilot): the forwards on the opponents' last line just
		# ahead of it, the midfield within 25 m of it, the backs pushed up to
		# the wing line, front to back inside 70 m, and all of them narrower.
		# Honest: it is where the sim's zone-weighted pressure happens.
		match role:
			"FWD":
				# On the opponents' last line, but never more than the band's
				# length from the backs: a press with the ball at its own end
				# draws its forwards back toward the ball.
				var deep := slot == "FF" or slot == "FPL" or slot == "FPR"
				var line := PRESS_LAST_LINE + (PRESS_DEEP_EXTRA if deep else 0.0)
				x = minf(minf(line, bx - PRESS_BACK_BEHIND - 8.0 + PRESS_SPAN), MatchMotion.GOAL_X - 12.0)
			"DEF":
				var half_back := slot == "CHB" or slot == "HBL" or slot == "HBR"
				x = bx - (PRESS_BACK_BEHIND if half_back else PRESS_BACK_BEHIND + 8.0)
			_:
				x = bx + clampf(x - bx, -PRESS_MID_BAND, PRESS_MID_BAND * 0.4)
	var drift := Vector2(sin(time * 0.31 + float(t["phase"])), cos(time * 0.23 + float(t["phase"]) * 1.7)) * 2.0
	var world := Vector2(x * dir, y) + (t["jitter"] as Vector2) + drift
	if has and plan == "attacking" and _lane.has(int(t["id"])):
		# Attack Corridor: the whole side narrows into its lanes (_attack_lanes),
		# each line in its slot order (no habits across: the gaps hold).
		world.y = float(_lane[int(t["id"])])
		if slot.begins_with("W"):
			# ...the wings a little up the ground from the midfield, so they share
			# the outside lanes with the followers without standing on them.
			world.x = minf(world.x * dir + WING_AHEAD, WING_FURTHEST) * dir
	var shadowing := plan == "contest" and not _stoppage_on() and (_shadow[side] as Array).has(int(t["id"]))
	if plan == "contest" and (mid or shadowing):
		# Win Contest: the midfield stays on the ball, each on his own side of
		# it round a ring (never a pile on top of it), and in open play two of
		# the half lines shadow it with them: numbers round the ball.
		var ang := deg_to_rad(_contest_angle(slot) if not shadowing
				else CONTEST_SHADOW_ANGLE * (-1.0 if (_shadow[side] as Array).find(int(t["id"])) == 0 else 1.0))
		world = ball_p + Vector2(cos(ang) * dir, sin(ang)) * CONTEST_MID_RING + (t["jitter"] as Vector2) * 0.2 + drift * 0.4
	var own_goal := Vector2(-MatchMotion.GOAL_X * dir, 0.0)
	var chase := int(t.get("chasing", -1))
	if has and chase >= 0:
		# Sent to their loose man: he stands where the spare would sit.
		world = world.lerp((tokens[chase]["goal"] as Vector2), 0.6)
	if _stoppage_on() and CONTEST_CRASH.has(slot) and _crashes(side):
		# Win Contest at a stoppage (Stack the stoppage at a centre bounce): the
		# wings and both half-lines crash in round the contest, each from his
		# own side of it.
		var out := world - ball_p
		if out.length() > CONTEST_RING:
			world = world.lerp(ball_p + out.normalized() * CONTEST_RING, CONTEST_CRASH_SHARE)
	elif _stoppage_on() and STACK_HOLD.has(slot) and _burst_on(side, "stack") and _centre_stoppage():
		# ...and its keys and pockets hold up on the arcs, where the bounce set them.
		var ax := world.x * dir
		world.x = signf(ax) * minf(absf(ax), STACK_HOLD_X) * dir
	var flooding := not has and _flooding(side)
	if not has:
		var o := int(t["match"])
		if _is_loose(t, ball_p):
			# The spare defender sits in the hole between the ball and goal.
			world = ball_p.lerp(own_goal, 0.25 if press_up else 0.5)   # a press keeps even him inside the band
			world.y *= 0.6
		elif flooding and (role == "MID" or role == "RUCK") and not bool(t.get("tagging", false)):
			# Flood behind the ball (the match's call, from the timeline): the
			# midfielders leave their men and fold back into the space between
			# the ball and goal, across the corridor.
			var hole := ball_p.lerp(own_goal, FLOOD_DEPTH)
			hole.y = lerpf(ball_p.y, base.y * 0.55, 0.6)
			world = world.lerp(hole, FLOOD_MID_SHARE)
		elif o >= 0:
			var og: Vector2 = tokens[o]["goal"]
			if og.distance_to(world) < 35.0:
				var mark := og + (own_goal - og).normalized() * 2.5
				var w := 0.65 if role == "DEF" else (0.45 if role == "MID" else 0.3)
				if plan == "contest" and (mid or shadowing):
					w *= CONTEST_MAN   # Win Contest: the midfield hunts the ball, not the man
				if press_up:
					w *= 0.1   # the press holds its band; it does not follow men back
				if bool(t.get("tagging", false)):
					w = 0.85   # a tagger plays the man
				world = world.lerp(mark, w)
		if flooding and role == "FWD":
			# ...and the half-forward line drops back to just goal-side of the
			# ball, so the numbers are behind it wherever the ball is (row T2.4:
			# pulled toward the ball, they stayed in front of it when it was in
			# their own half); the full-forward line comes a third of the way
			# up after them (row T2.4: at a quarter of that the flood moved the
			# side 8.0 m, on the call floor).
			var half := slot == "CHF" or slot == "HFL" or slot == "HFR"
			var behind := ball_p.x - dir * FLOOD_HALF_BEHIND
			world.x = lerpf(world.x, behind, FLOOD_HALF_SHARE if half else FLOOD_PUSH)
	return _keep_in(world)


## The High Press, drawn (V1, press pilot). `bx` is the ball's distance
## up the ground from `side`'s own goal end (positive: in its opponents'
## back half). The shape is high while the ball is in the opponents' back half
## or the middle, and only for a side whose recorded plan is the press.
const PRESS_LAST_LINE := 46.0     # the opponents' last line, from the centre
const PRESS_DEEP_EXTRA := 12.0    # the full-forward line stands this much deeper
const PRESS_SPAN := 52.0          # front to back, at most
const PRESS_BACK_BEHIND := 20.0   # metres behind it
const PRESS_MID_BAND := 24.0      # midfield stays within this of the ball
const PRESS_NARROW := 0.62
const PRESS_FRAME_ZOOM := 1.1     # the camera widens a little while a press is on
const PRESS_FRAME_SHIFT := 9.0    # ...and looks toward its high line
const PRESS_FROM := -10.0


## The press zone, drawn: whether `side` plays the High Press right now.
## The tint follows the plan, with the ball only turning it up (director,
## 2026-10-14: it was seen in the first quarter and then "disappeared"). The old
## rule showed it only while the side was without the ball and the ball was up
## its opponents' end, so it flickered with every change of possession and sat
## at about a seventh of its strength on average, in any quarter.
func press_zone_on(side: int) -> bool:
	if _tac.size() < 2 or tokens.is_empty() or debug_no_press_shape:
		return false
	return str((_tac[side] as Dictionary).get("plan", "")) == "defensive"


## Whether `side` is hunting right now: its plan the press, without the ball,
## the ball in its opponents' back half or the middle.
func press_zone_hunting(side: int) -> bool:
	if not press_zone_on(side):
		return false
	return side != _poss and _pressing(side, (ball["pos"] as Vector2).x * _dir(side))


## How strong the wash should be: half while the plan is the press, full while
## the side is hunting, none under any other plan. The view eases to it.
const PRESS_ZONE_STANDING := 0.5
func press_zone_level(side: int) -> float:
	if not press_zone_on(side):
		return 0.0
	return 1.0 if press_zone_hunting(side) else PRESS_ZONE_STANDING


## How strongly the press side is hunting at `x_side` metres up the ground
## from its own goal end (positive: toward the opponents' goal), 0..1: the
## sim's PRESS_PLAN_ZONE for the carrier's zone, read as the part above
## "normal", relative to its heaviest zone. The opponents' back third is the
## full tint, the middle a quarter of it, their forward third none.
static func press_zone_strength(x_side: float) -> float:
	var table: Array = MatchSim.PRESS_PLAN_ZONE
	var zone := 0 if x_side > MatchSim.PRESS_ZONE_EDGE else (2 if x_side < -MatchSim.PRESS_ZONE_EDGE else 1)
	var heavy := float(table[0]) - 1.0
	return clampf((float(table[zone]) - 1.0) / heavy, 0.0, 1.0)


## The same field with soft edges: between two zones the strength eases across
## PRESS_ZONE_FEATHER metres either side of the edge, never a step.
const PRESS_ZONE_FEATHER := 14.0
static func press_zone_field(x_side: float) -> float:
	var e := MatchSim.PRESS_ZONE_EDGE
	var back := smoothstep(e - PRESS_ZONE_FEATHER, e + PRESS_ZONE_FEATHER, x_side)
	var fwd := smoothstep(-e - PRESS_ZONE_FEATHER, -e + PRESS_ZONE_FEATHER, x_side)
	var mid := press_zone_strength(0.0)
	return lerpf(lerpf(press_zone_strength(-e - 1.0), mid, fwd), press_zone_strength(e + 1.0), back)


# ---------------------------------------------------------------------------
# The oval marks two calls on the grass (P-12 pass 5, director 2026-10-18:
# "Merge, then mark the oval"). Attack Corridor and Win Contest meet their
# measures, but the busy players round the ball (leads, carrier, pack) crowd it
# on every call, so the shape alone can read as a swarm or a clump. A faint
# marking of the side's colour says the call where the discs cannot, like the
# press wash. Read here, drawn by PitchView; neither moves a player.
# - Attack Corridor: the corridor its lanes use (LANE_TABLE's outermost lane,
#   plus a disc in the view), from the side's defensive 50 to the goal square,
#   only while the side has the ball in play.
# - Win Contest: at a ball-up or throw-in, its pack's ring (PACK_RING) on the
#   contest spot from the moment it is called until the clearance; in open play,
#   the ring its midfield keeps round the ball (CONTEST_MID_RING) while the ball
#   is live.
const CORRIDOR_FROM := -35.0     # the side's defensive 50, from the centre (x up the ground)
const CORRIDOR_TO := 76.0        # the front of the goal square (GOAL_X less its 9 m)
const CORRIDOR_HALF := 14.25     # the outermost lane (LANE_TABLE)


## Whether `side`'s Attack Corridor is marked now: its plan, the ball its, in play.
func corridor_mark_on(side: int) -> bool:
	if _tac.size() < 2 or tokens.is_empty():
		return false
	return _plan_of(side) == "attacking" and side == _poss and not (mode in ["break", "centre", "stoppage"])


## `side`'s Win Contest ring now: {"at", "r", "stop"} (a stoppage's pack ring, or
## the midfield's ring round the ball in open play, the ball in play: not at a
## centre bounce, a stoppage, a set shot or a break), or {} when none shows.
func contest_mark(side: int) -> Dictionary:
	if _tac.size() < 2 or tokens.is_empty() or _plan_of(side) != "contest":
		return {}
	if _ring_at.is_finite():
		return {"at": _ring_at, "r": PACK_RING, "stop": true}
	var called := _contest_called()
	if called.is_finite():
		return {"at": called, "r": PACK_RING, "stop": true}
	if mode == "open" and not _stoppage_on():
		return {"at": ball["pos"], "r": CONTEST_MID_RING, "stop": false}
	return {}


## The contest spot from the moment the umpire calls a ball-up (the ball dead in
## a tackle or a pack), before the ball-up's own beat begins: where that beat will
## plant its ring (_start_beat), so the ring is on the spot from the call and never
## follows the ball in (motion critic, 2026-10-18). INF when no ball-up is called.
## Reads only: _peek_loc leaves every cache and the random stream as it found them.
func _contest_called() -> Vector2:
	if mode != "stoppage" or _beat.is_empty():
		return Vector2.INF
	var nk := _next_real(int(_beat["k"]))
	if nk < 0:
		return Vector2.INF
	var kind := str((events[nk] as Dictionary).get("kind", ""))
	if kind != "ballup" and kind != "throwin":
		return Vector2.INF
	if kind == "ballup" and _plan_of(0) != "contest" and _plan_of(1) != "contest":
		return Vector2.INF
	if kind == "ballup" and not _ballup_pin.has(nk):
		return Vector2.INF   # not called yet: the ball is not dead (_pin_called_ballup)
	var rat := _peek_loc(nk)
	return rat if kind == "ballup" else Vector2(rat.x, rat.y * 0.78)


## _loc(k) without keeping anything: the spot, the cache and the random stream as before.
func _peek_loc(k: int) -> Vector2:
	if _locs.has(k):
		return _locs[k]
	var st := _rng.state
	var p := _loc(k)
	_locs.erase(k)
	_rng.state = st
	return p

## Debug only (capture_match --noshape): draw the calls without their shapes
## (the press, the flood, the stack and every P-12 shape), the sim untouched,
## so a clip pair differs in the formation alone.
static var debug_no_press_shape := false


func _pressing(side: int, bx: float) -> bool:
	if debug_no_press_shape:
		return false
	return str((_tac[side] as Dictionary).get("plan", "")) == "defensive" and bx > PRESS_FROM


## How far back from the ball a flooding midfield sits (share of the way to
## its own goal), and how far its forwards come up toward the ball.
const FLOOD_DEPTH := 0.45
const FLOOD_PUSH := 0.35
## How far the midfield folds into that hole, how far goal-side of the ball the
## half-forward line drops (metres) and how much of the way it goes (row T2.4:
## at 0.75 and pushed toward the ball the flood moved the side 5.5 m, too little to see).
const FLOOD_MID_SHARE := 0.9
const FLOOD_HALF_BEHIND := 6.0
const FLOOD_HALF_SHARE := 0.8


## The side's recorded calls include a flood (MatchSim.BURSTS, on the timeline
## from the chain it was made until it runs out).
func _flooding(side: int) -> bool:
	return _burst_on(side, "flood")


# ---------------------------------------------------------------------------
# The coach's other structural calls, drawn (P-12, director 2026-10-18: "the
# oval answers a structural call"). Each shape is what the engine does with
# the call (MatchSim PLANS and BURSTS), never more:
# - Attack Corridor (more metres and shots, quicker legs, more turnovers):
#   with the ball the whole side narrows into the corridor, each player in his
#   own lane (ATTACK_SHARE of his Balanced width, each line in its slot order,
#   LANE_GAP apart); receivers lead up their lanes and the ball goes to the
#   lane ahead (no switch of play); it moves quicker.
# - Controlled Tempo (less pressure felt, fewer clangers, fewer metres,
#   slower legs): with the ball it spreads wide and its lines come in short
#   around the ball; it moves slower.
# - Win Contest (an edge at every stoppage, fewer metres): its midfield stays
#   on the ball, on a ring round it, with two of the half lines shadowing it in
#   open play; every centre bounce, ball-up and throw-in gets one more in the
#   pack, the wings crashing in at a sprint and both half-lines a beat later,
#   through the clearance out of it (the centre bounce set up as a stack, 6-6-6
#   kept until the ball is up). The pack is a ring, not a stack: two a side on
#   the ball, the rest PACK_RING round it, the crash outside that. The engine
#   gives the plan no edge in a marking contest, so neither does the oval.
# - Throw numbers at it (an edge at the contest, more shots, faster legs, more
#   goals against when the other side gets out): with the ball the midfield
#   and the half-back line run past where the chain is going, the forwards
#   stay ahead of it and the back pockets come up, a flood in reverse; it
#   moves quicker. (Without the ball it keeps its usual shape.)
# - Slow it down (less pressure felt, fewer clangers, fewer metres and fewer
#   shots at both ends): the side sits deeper, spreads wide with the ball and
#   moves slower, its leads shorter and slower. Its carriers hold the ball no
#   longer: the engine's hold
#   chains have more disposals (4.4 a possession against 3.7, 40 seeds) in the
#   same minutes, so each disposal takes less time, not more, and the log's
#   extra disposals already show it.
const ATTACK_SHARE := 0.4          # with the ball a lane is about this share of his Balanced width...
const LANE_GAP := 7.0              # ...no two of a line of three closer than this across the ground...
const LANE_SPACE := 9.5            # ...and in fact a disc apart (8.6 m on a phone), on a grid this wide
## How the corridor groups its lanes: the backs' and forwards' lines of three,
## the four inside midfielders (on the half-offset lanes) and the two wings.
## Each group's lanes, left to right: neighbouring lines along the ground
## (full-back, half-back, midfield, half-forward, full-forward) alternate between
## the LANE_SPACE grid and the grid offset by half, so where two lines meet no two of
## their players share a lane (a brick wall, never a column).
const LANE_TABLE := {"FB": [-14.25, -4.75, 4.75], "HB": [-9.5, 0.0, 9.5], "MID": [-14.25, -4.75, 4.75, 14.25],
		"W": [-13.25, 13.25], "HF": [-9.5, 0.0, 9.5], "FF": [-4.75, 4.75, 14.25]}
const CORRIDOR_INTO := 1.0        # how hard a side runs into its lanes when it wins the ball
const WING_AHEAD := 12.0          # the wings stand this far up from the midfield, sharing its outside lanes
const WING_FURTHEST := 60.0        # ...never so far up that the pocket squeezes his lane
const LANE_GROUP := {"FB": "FB", "BPL": "FB", "BPR": "FB", "CHB": "HB", "HBL": "HB", "HBR": "HB",
		"WL": "W", "WR": "W", "C": "MID", "R": "MID", "RR": "MID", "RV": "MID",
		"CHF": "HF", "HFL": "HF", "HFR": "HF", "FF": "FF", "FPL": "FF", "FPR": "FF"}
## The lines of three, as the tests hold them (no two closer than LANE_GAP).
const LANE_LINE := {"FB": "FB", "BPL": "FB", "BPR": "FB", "CHB": "HB", "HBL": "HB", "HBR": "HB",
		"WL": "C", "C": "C", "WR": "C", "R": "FOL", "RR": "FOL", "RV": "FOL",
		"CHF": "HF", "HFL": "HF", "HFR": "HF", "FF": "FF", "FPL": "FF", "FPR": "FF"}
const CONTROL_WIDTH := 1.5
const CONTROL_PULL := 0.5          # less drawn across to the ball: the width holds
const CONTROL_SHORT := 0.5         # each line comes this share of the way in...
const CONTROL_AHEAD := 10.0        # ...toward a point this far ahead of the ball
const CONTEST_MID_RING := 10.5     # the midfield stays this far round the ball: eight on it, about a disc apart
## ...each at his own angle (degrees; 0 is the way his side kicks), 45 apart, and
## in open play two of the half lines shadow it with them behind the ball.
const CONTEST_ANGLE := {"C": 0.0, "RR": 45.0, "RV": -45.0, "WR": 90.0, "WL": -90.0, "R": 180.0}
const CONTEST_SHADOW_ANGLE := 135.0
const CONTEST_SHADOWS := ["CHB", "HBL", "HBR", "CHF", "HFL", "HFR"]
const CONTEST_HUNT := 1.0         # how hard the ring keeps up with the ball in open play
const SHADOW_KEEP := 15.0          # metres nearer another must be to take over a shadow
## Win Contest's stoppage pack (_pack_ring): two a side on the ball, the rest
## round it this far off; a member is set once within PACK_SET of his spot.
const PACK_RING := 8.0
## ...the two rucks this far either side of the ball, and each side's second man
## this far off it across the ground: inside 3 m, his ruck 3.2 m from him.
const PACK_RUCK := 1.2
const PACK_SECOND := 2.9
const PACK_RING_WAIT := 2.0        # the longest a ring takes to set...
const PACK_RUCK_NEAR := 25.0      # a ruck further off than this when the ball-up is called stands on the ring
const PACK_SETTLE := 0.5          # ...and holds this long once set
const PACK_RUCK_WAIT := 4.0        # ...or to wait for a ruck still on his way (25 m off and running the other way takes 3.2 s: trace 2026-10-18)
const PACK_CLEAR_ARC := 0.45       # radians between two men clearing out the same way
const PACK_SET := 2.5
const PACK_INNER_SET := 0.4        # ...and the four on the ball within this of theirs
const CONTEST_PACK := 1            # extra players a side in a stoppage pack (with the ruck and the winner, six at most)
const CONTEST_MAN := 0.25          # share of a midfielder's usual hold on his man
## Win Contest at a stoppage: who crashes in, to how far off the ball, how far.
const CONTEST_CRASH := ["WL", "WR", "CHB", "HBL", "HBR", "CHF", "HFL", "HFR"]
const CONTEST_RING := 13.0         # ...round the pack, outside its ring
const CONTEST_CRASH_SHARE := 1.0
const CONTEST_STAGGER := 0.35      # the half-lines go this long after the wings
const CONTEST_KEEP := 13.0         # nobody but the pack inside this of the ball: the numbers stay readable
const SURGE_AHEAD := 32.0          # the midfield runs at least this far ahead of the ball
const SURGE_PUSH := 18.0           # the half-back line pushes up at least this far...
const SURGE_HB_AHEAD := 20.0       # ...and past the ball
const SURGE_SHORT := 14.0          # never closer to the goal line than this
const SURGE_LEGS := 1.3            # MatchSim: "surge" movement pace
const SURGE_RUNNERS := ["CHB", "HBL", "HBR"]   # with the midfield, they run past the ball
const SURGE_FWD_AHEAD := 14.0      # the forwards stay at least this far ahead of it
const HOLD_DEEP := 18.0            # Slow it down: the backs sit this much deeper...
const HOLD_DEEP_UP := 24.0         # ...the midfield and forwards this much
const HOLD_LEAD := 0.75            # a lead is this much slower, and starts only when it must
const HOLD_WIDTH := 1.5
## Limits every shape keeps (the motion critic, 2026-10-18; _structure_limits).
## LINE_WIDTH_MIN: in possession each line (backs, midfield, forwards) keeps at
## least this spread across the ground (standard deviation of where its players
## stand): Balanced's narrowest line in real playback measured 11.6 to 12.8 m.
const LINE_WIDTH_MIN := 12.0
## Two of a side's structure spots never closer than this: a disc on a phone is
## about 8.6 m across, and two numbers a little closer still both read.
const SPOT_GAP := 7.0
## Structure spots stay this far inside the boundary line (a phone disc is 4.3 m
## in radius, so the whole disc is on the ground)...
const STRUCT_MARGIN := 5.0
## ...and out of the pocket the bench's tab covers on a phone (the upright oval,
## 300 x 387: the tab's top edge is 74 m from the centre, from 25 m across out to
## the corner; less a disc's radius, 6.5 m since the bigger discs of 2026-11-12,
## when this was 68 under the old bench strip). Kept in all four pockets, so the
## ends match: beyond POCKET_Y across, never deeper than POCKET_X.
const POCKET_X := 67.0
const POCKET_Y := 11.0


## How briskly a side moves into its shape, from the pace the engine gives
## the call (PLANS "pace", the legs Throw numbers at it burns; Slow it down's
## quieter game).
const CALL_PACE := {"attacking": 1.15, "controlled": 0.85, "surge": 1.3, "hold": 0.7}
const CALL_PACE_TOP := 0.85


## The plan in `side`'s recorded calls ("" with none recorded, or with the
## shapes off for a capture).
func _plan_of(side: int) -> String:
	if debug_no_press_shape:
		return ""
	return str((_tac[side] as Dictionary).get("plan", ""))


## Whether `side`'s recorded calls include the burst `kind` (MatchSim.BURSTS).
func _burst_on(side: int, kind: String) -> bool:
	if debug_no_press_shape:
		return false
	return ((_tac[side] as Dictionary).get("bursts", []) as Array).has(kind)


func _call_pace(side: int) -> float:
	var m := float(CALL_PACE.get(_plan_of(side), 1.0))
	for kind in ["surge", "hold"]:
		if _burst_on(side, kind):
			m *= float(CALL_PACE[kind])
	return m


## How much longer a stoppage pack may take to form for each extra player in it.
const PACK_EXTRA_WAIT := 0.15


## Players a side sends into a stoppage pack (a ball-up, a throw-in).
func _pack_n(side: int) -> int:
	return 3 + (CONTEST_PACK if _plan_of(side) == "contest" else 0)


## Throw numbers at it: how far up the ground (from `side`'s own end) its
## chain is going, the furthest lead already on, or the ball when none is.
func _surge_ref(side: int, bx: float) -> float:
	var out := bx
	for id in _lead:
		if int(tokens[id]["side"]) == side and _locs.has(int(_lead[id])):
			out = maxf(out, (_locs[int(_lead[id])] as Vector2).x * _dir(side))
	return out


## Win Contest: where round the ball a midfielder stands (CONTEST_ANGLE; an
## extra midfielder fills the gaps between them).
static func _contest_angle(slot: String) -> float:
	if CONTEST_ANGLE.has(slot):
		return float(CONTEST_ANGLE[slot])
	var gaps := [22.5, -22.5, 157.5, -157.5, 67.5, -67.5]
	return float(gaps[int(slot.substr(1)) % gaps.size()]) if slot.begins_with("X") else 90.0


## Attack Corridor, a shape of the whole team (pass 4, the motion critic's third
## look: a receiver path piled eight discs on one column). Each group (the
## backs' and forwards' lines of three, the four inside midfielders, the wings)
## keeps its slot order across the ground, left to right, on the lanes of
## LANE_TABLE: about 40% of Balanced's width, a disc apart (LANE_SPACE; the
## tests hold LANE_GAP, 7 m, for every line of three), and neighbouring lines
## along the ground on grids half a lane apart, so where two lines meet no two
## of them share a lane (a brick wall, never a column). No pull to the ball and
## no habits: the corridor holds wherever the ball is. A group of another size
## (an extra man) keeps its order and the gap (pool adjacent violators about
## ATTACK_SHARE of his Balanced width). Sets _lane for `side`'s players
## (token id -> y).
func _attack_lanes(side: int) -> void:
	var lines := {}
	for t in tokens:
		if int(t["side"]) != side:
			continue
		var key := str(LANE_GROUP.get(str(t["slot"]), ""))
		if key == "":
			key = {"DEF": "HB", "FWD": "HF"}.get(str(t["role"]), "MID")
		if not lines.has(key):
			lines[key] = []
		(lines[key] as Array).append(t)
	for key in lines:
		var line: Array = lines[key]
		line.sort_custom(_lane_order)
		var want := []
		for i in range(line.size()):
			want.append(ATTACK_SHARE * (line[i]["base"] as Vector2).y * 1.08 - LANE_SPACE * float(i))
		var fit := _isotonic(want)
		var table: Array = LANE_TABLE.get(key, [])
		for i in range(line.size()):
			# A full line takes its lanes from the table; any other keeps its
			# order and gaps (an extra man, a short line).
			_lane[int(line[i]["id"])] = float(table[i]) if table.size() == line.size() 					else float(fit[i]) + LANE_SPACE * float(i)


## Left to right by slot, then by id: the order a line keeps across the ground.
static func _lane_order(a: Dictionary, b: Dictionary) -> bool:
	var ya: float = (a["base"] as Vector2).y
	var yb: float = (b["base"] as Vector2).y
	return ya < yb or (ya == yb and int(a["id"]) < int(b["id"]))


## The closest non-decreasing sequence to `v` (least squares).
static func _isotonic(v: Array) -> Array:
	var blocks := []   # [sum, count]
	for x in v:
		blocks.append([float(x), 1])
		while blocks.size() > 1 and float(blocks[-2][0]) / float(blocks[-2][1]) > float(blocks[-1][0]) / float(blocks[-1][1]):
			var last: Array = blocks.pop_back()
			var prev: Array = blocks[-1]
			prev[0] = float(prev[0]) + float(last[0])
			prev[1] = int(prev[1]) + int(last[1])
	var out := []
	for b in blocks:
		for i in range(int(b[1])):
			out.append(float(b[0]) / float(b[1]))
	return out


## Win Contest in open play: the two of the half lines nearest the ball shadow
## it with the midfield (kept until another is SHADOW_KEEP nearer, so they do not
## swap every beat), the left one first.
func _pick_shadows(bp: Vector2) -> void:
	for side in range(2):
		if _plan_of(side) != "contest":
			_shadow[side] = []
			continue
		var cands := []
		for t in tokens:
			if int(t["side"]) == side and CONTEST_SHADOWS.has(str(t["slot"])):
				var dd := (t["pos"] as Vector2).distance_to(bp)
				if (_shadow[side] as Array).has(int(t["id"])):
					dd -= SHADOW_KEEP
				cands.append([dd, int(t["id"])])
		cands.sort()
		var pick := []
		for i in range(mini(2, cands.size())):
			pick.append(int(cands[i][1]))
		pick.sort_custom(func(a, b): return (tokens[a]["base"] as Vector2).y < (tokens[b]["base"] as Vector2).y \
				or ((tokens[a]["base"] as Vector2).y == (tokens[b]["base"] as Vector2).y and a < b))
		_shadow[side] = pick


## Win Contest's stoppage pack, readable (the motion critic, 2026-10-18: eight to
## ten discs stacked in 15 m, numbers hidden): each side's ruck and its nearest
## other man on the ball, inside 3 m and 2.5 m from each other; the rest of the
## pack round it PACK_RING off, between them. Id -> spot.
func _pack_ring(at: Vector2, members: Array, winner: int) -> Dictionary:
	var spots := {}
	var rest := [[], []]
	var ruck := [false, false]
	for id in members:
		var sd := int(tokens[id]["side"])
		# A ruck still well off (more than PACK_RUCK_NEAR) goes to the ring; the
		# side's nearest man stands in for him on the ball.
		if str(tokens[id]["role"]) == "RUCK" and not ruck[sd] 				and (tokens[id]["pos"] as Vector2).distance_to(at) <= PACK_RUCK_NEAR:
			ruck[sd] = true
			spots[id] = at + Vector2(-PACK_RUCK * _dir(sd), 0.0)
		else:
			(rest[sd] as Array).append(id)
	for sd in range(2):
		var list0: Array = rest[sd]
		if not ruck[sd] and list0.size() > 1:
			var stand_in: int = int(list0[0])
			var bestd := INF
			for id in list0:
				var dd := (tokens[id]["pos"] as Vector2).distance_to(at)
				if dd < bestd:
					bestd = dd
					stand_in = int(id)
			list0.erase(stand_in)
			spots[stand_in] = at + Vector2(-PACK_RUCK * _dir(sd), 0.0)
	var ring := []   # [bearing, id]
	for sd in range(2):
		var list: Array = rest[sd]
		if list.is_empty():
			continue
		# The second on the ball: the nearest (members come nearest first), so
		# nobody crosses the pack to get there; the winner runs onto the tap.
		var second: int = int(list[0])
		var bd := INF
		for id in list:
			var dd2 := (tokens[id]["pos"] as Vector2).distance_to(at)
			if dd2 < bd:
				bd = dd2
				second = int(id)
		spots[second] = at + Vector2(0.0, PACK_SECOND * (1.0 if sd == 0 else -1.0))
		for i in range(1, list.size()):
			var off: Vector2 = (tokens[list[i]]["pos"] as Vector2) - at
			ring.append([off.angle() if off.length() > 0.5 else float(list[i]), int(list[i])])
	# The rest on the ring, on the bearings between the four on the ball (where
	# the discs drawn apart do not push into them), each near his own bearing
	# and in the order they stand round it, so nobody runs through the pack;
	# evenly round it with a crowd.
	for r in ring:
		r[0] = wrapf(float(r[0]), -PI, PI)
	ring.sort()
	var m := ring.size()
	var slots := []
	var n_slots := 4 if m <= 4 else 8
	if m > 8:
		n_slots = m
	for q in range(n_slots):
		slots.append(TAU * (float(q) + 0.5) / float(n_slots))
	var bearings := []
	for r in ring:
		bearings.append(float(r[0]))
	var pick := _ring_slots(bearings, slots)
	for i in range(m):
		spots[int(ring[i][1])] = at + Vector2.from_angle(float(slots[int(pick[i])])) * PACK_RING
	return spots


## Which of `slots` (bearings round the ring, ascending) each of `bearings`
## (ascending) takes: the men keep their order round the ring, so no two paths
## cross and nobody is sent to the far side through the pack (taking the nearest
## free slot one by one could leave the last man a slot across the ball: seed 43,
## 2026-11-10), and the squared turns from their own bearings are least.
static func _ring_slots(bearings: Array, slots: Array) -> Array:
	var m := bearings.size()
	var n := slots.size()
	var best_cost := INF
	var best: Array = []
	for o in range(n):
		# dp[i][j]: the least cost with the first i men on the first j slots from o.
		var dp := []
		var from := []
		for i in range(m + 1):
			var row := []
			var frow := []
			for j in range(n + 1):
				row.append(0.0 if i == 0 else INF)
				frow.append(false)
			dp.append(row)
			from.append(frow)
		for i in range(1, m + 1):
			for j in range(i, n + 1):
				var skip: float = dp[i][j - 1]
				var dev := wrapf(float(slots[(o + j - 1) % n]) - float(bearings[i - 1]), -PI, PI)
				var take: float = float(dp[i - 1][j - 1]) + dev * dev
				if take <= skip:
					dp[i][j] = take
					from[i][j] = true
				else:
					dp[i][j] = skip
		if float(dp[m][n]) < best_cost - 1e-9:
			best_cost = dp[m][n]
			var out := []
			out.resize(m)
			var i2 := m
			var j2 := n
			while i2 > 0:
				if from[i2][j2]:
					out[i2 - 1] = (o + j2 - 1) % n
					i2 -= 1
				j2 -= 1
			best = out
	return best


## Win Contest's crash at every stoppage, or a stack's at a centre bounce.
func _crashes(side: int) -> bool:
	return _plan_of(side) == "contest" or (_burst_on(side, "stack") and _centre_stoppage())


## The stoppage on is a centre bounce (its set-up or its clearance), where a
## stacked side crashes in (row T2.4: with only its wings in, the stack moved
## the side 2.8 m from Balanced, too little to see).
func _centre_stoppage() -> bool:
	if _beat.is_empty():
		return false
	var k := int(_beat["k"])
	if _restart(k) == "centre":
		return true
	var pk := _prev_real(k)
	return pk >= 0 and _possession(str((events[pk] as Dictionary).get("kind", ""))) and _restart(pk) == "centre"


## A stoppage is on: a ball-up or throw-in being set, and the clearance out
## of it (or out of a centre bounce) until the next disposal is under way.
func _stoppage_on() -> bool:
	if _beat.is_empty():
		return false
	var k := int(_beat["k"])
	var kind := str(_beat.get("kind", ""))
	if kind == "ballup" or kind == "throwin":
		return true
	if not _possession(kind):
		return false
	if _restart(k) in ["centre", "ballup", "throwin"]:
		return true
	var pk := _prev_real(k)
	return pk >= 0 and _possession(str((events[pk] as Dictionary).get("kind", ""))) and _restart(pk) in ["centre", "ballup", "throwin"]


## The loose defender while his side defends: the one the match named
## (timeline), or for a result without one, the half-back whose forward is
## further from the ball.
func _is_loose(t: Dictionary, ball_p: Vector2) -> bool:
	if not (_tac[int(t["side"])] as Dictionary).is_empty():
		# The match recorded its calls: the loose man is the one it named.
		return bool(t.get("loose", false))
	var slot := str(t["slot"])
	if slot != "HBL" and slot != "HBR":
		return false
	var other := "HBR" if slot == "HBL" else "HBL"
	for o in tokens:
		if int(o["side"]) == int(t["side"]) and str(o["slot"]) == other:
			var mine := int(t["match"])
			var theirs := int(o["match"])
			if mine < 0 or theirs < 0:
				return false
			return (tokens[mine]["pos"] as Vector2).distance_to(ball_p) \
					> (tokens[theirs]["pos"] as Vector2).distance_to(ball_p)
	return false


## Around the ball: the nearest two defenders press (one on the ball, one
## goal-side), the nearest two attackers give options. The two men of a tackle are
## left to its take until they are back on their feet (sent to press, the tackler
## walked up and stood 1.2 m off a loose ball while it was gathered).
func _ball_zone(ball_p: Vector2) -> void:
	var def_side := 1 - _poss
	var own := Vector2(-MatchMotion.GOAL_X * _dir(def_side), 0.0)
	var to_goal := (own - ball_p).normalized()
	var skip := _busy.keys()
	for t in tokens:
		if not _on_feet(int(t["id"])):
			skip.append(int(t["id"]))
	var press := _nearest(ball_p, def_side, 2, skip)
	for i in range(press.size()):
		var g := ball_p + to_goal * (3.0 if i == 0 else 9.0) \
				+ to_goal.orthogonal() * (1.0 if i == 0 else 6.0 * signf(ball_p.y + 0.1))
		MatchMotion.set_goal(tokens[press[i]], _clear_of_pack(g), 0.8 if i == 0 else 0.6)
		_busy[press[i]] = true
	var dir := _dir(_poss)
	skip += press
	var sup := _nearest(ball_p, _poss, 2, skip)
	if _plan_of(_poss) == "attacking":
		return   # Attack Corridor: the lanes are the options; nobody comes onto the ball
	for i in range(sup.size()):
		var g2 := ball_p + (Vector2(dir * 9.0, -9.0) if i == 0 else Vector2(-dir * 5.0, 10.0))
		MatchMotion.set_goal(tokens[sup[i]], _clear_of_pack(g2), 0.6)
		_busy[sup[i]] = true


## Centre-bounce position for a token; `carrier` is moved into the square.
func _centre_spot(t: Dictionary, carrier: int) -> Vector2:
	var side := int(t["side"])
	var slot := str(t["slot"])
	var spot: Vector2 = CENTRE.get(slot, Vector2(-25, 15 if int(t["id"]) % 2 == 0 else -15))
	if carrier >= 0 and int(tokens[carrier]["side"]) == side:
		var cslot := str(tokens[carrier]["slot"])
		var swap := "C" if not SQUARE.has(cslot) else ""
		if int(t["id"]) == carrier:
			spot = Vector2(-3, 5 if spot.y >= 0.0 else -5) if SQUARE.has(cslot) else Vector2(-3, -5)
		elif swap != "" and slot == swap:
			spot = CENTRE.get(cslot, spot)
	# The side's centre ball-up call, as the match recorded it (2026 rules:
	# a ball-up, 6-6-6 still holds, so the wings stay outside the square and
	# the forwards inside their arc until the ball is up).
	if int(t["id"]) != carrier:
		match _centre_setup(side):
			"stack":
				# Attacking: the wings on the square's edge, ready to crash
				# the contest, and both half-lines up to their arcs.
				if slot == "WL" or slot == "WR":
					spot = Vector2(-2.0, 27.0 * signf(spot.y))
				elif _burst_on(side, "stack") and STACK_ARC.has(slot):
					# Stack the stoppage throws the whole side at it: all six of
					# each line on the arc's edge, just inside it (6-6-6), the
					# keys and pockets up beside the half-lines (row T2.4: with
					# the pockets at 48 m and the keys home, the stack moved the
					# side 4.0 m front to back, too little to see).
					spot = _on_arc(float(STACK_ARC[slot]), spot.x >= 0.0)
				elif slot == "CHF" or slot == "HFL" or slot == "HFR":
					spot.x = ARC_EDGE
				elif slot == "CHB" or slot == "HBL" or slot == "HBR":
					spot.x = -ARC_EDGE
			"flood":
				# Defensive: the wings goal-side of the square, and the
				# centreman at its back edge, behind the ball.
				if slot == "WL" or slot == "WR":
					spot = Vector2(-18.0, 30.0 * signf(spot.y))
				elif slot == "C":
					spot = Vector2(-14.0, -4.0)
			"push":
				# Push numbers forward (row 151), the flood turned round: the
				# wings ahead of the square, the centreman at its front edge
				# and both half-lines up to their arcs.
				if slot == "WL" or slot == "WR":
					spot = Vector2(18.0, 30.0 * signf(spot.y))
				elif slot == "C":
					spot = Vector2(14.0, -4.0)
				elif slot == "CHF" or slot == "HFL" or slot == "HFR":
					spot.x = ARC_EDGE
				elif slot == "CHB" or slot == "HBL" or slot == "HBR":
					spot.x = -ARC_EDGE
	return Vector2(spot.x * _dir(side), spot.y)


## Just inside the forward 50 arc, in a side's attacking frame.
const ARC_EDGE := 37.0   # MatchMotion.GOAL_X (85) - 48
## Stack the stoppage at a centre bounce: each line's six on its arc, at this
## distance across the ground (forward frame; a back line mirrors it), from the
## key in the middle to the pockets on the flanks.
const STACK_ARC := {"CHF": -5.0, "FF": 5.0, "HFL": -16.0, "HFR": 16.0, "FPL": -27.0, "FPR": 27.0,
		"CHB": -5.0, "FB": 5.0, "HBL": -16.0, "HBR": 16.0, "BPL": -27.0, "BPR": 27.0}
## ...and after the bounce the keys and pockets hold up there, no deeper than this
## from the centre (the half-lines crash the contest: _crashes).
const STACK_HOLD := ["FF", "FPL", "FPR", "FB", "BPL", "BPR"]
const STACK_HOLD_X := 44.0


## A spot just inside the 50 m arc at `y` across the ground, in a side's
## attacking frame: its forward arc when `forward`, else its back one.
static func _on_arc(y: float, forward: bool) -> Vector2:
	var x := MatchMotion.GOAL_X - sqrt(maxf(0.0, 2500.0 - y * y)) + 1.0
	return Vector2(x if forward else -x, y)


## A side's centre ball-up setup from its recorded calls: "stack" (extra
## numbers at the contest), "flood" (numbers behind the ball), "push"
## (numbers ahead of it) or "".
func _centre_setup(side: int) -> String:
	if _burst_on(side, "stack"):
		return "stack"
	if _burst_on(side, "push"):
		return "push"
	if _burst_on(side, "flood"):
		return "flood"
	# Win Contest: an edge at every stoppage, so numbers at the centre bounce too.
	return "stack" if _plan_of(side) == "contest" else ""


# ---------------------------------------------------------------------------
# Skip and helpers
# ---------------------------------------------------------------------------
## Release every event not yet released, without animating, and leave the
## view in a settled end state. Returns the released events in order.
func flush() -> Array:
	var out := events.slice(emitted)
	for ev in out:
		if str((ev as Dictionary).get("kind", "")) == "sub":
			_sub(ev)
	emitted = events.size()
	cursor = events.size()
	_beat = {}
	_phases = []
	_busy = {}
	_lead = {}
	_end_reset_pace()
	var last := Vector2.ZERO
	for i in range(events.size() - 1, -1, -1):
		var ev2: Dictionary = events[i]
		if not ["quarter", "final", "sub", "moment", "injury"].has(str(ev2.get("kind", ""))):
			last = Vector2(clampf(float(ev2.get("fp", 0.0)), -MatchMotion.GOAL_X, MatchMotion.GOAL_X), 0.0)
			break
	ball["mode"] = "dead"
	ball["holder"] = -1
	ball["pos"] = last
	ball["h"] = 0.0
	_struct_ball = last
	for t in tokens:
		var g := _structure_spot(t, last, _poss)
		t["pos"] = g
		t["vel"] = Vector2.ZERO
		t["down"] = 0.0
		MatchMotion.set_goal(t, g, 0.0, true)
	flash = {}
	mode = "break"
	return out


func _actor_id(ev: Dictionary) -> int:
	var side := int(ev.get("side", -1))
	if side < 0 or side > 1:
		return -1
	return int((_ids[side] as Dictionary).get(int(ev.get("num", -1)), -1))


## The token an event is about (-1 for none): the scorer of a goal, say.
func token_of(ev: Dictionary) -> int:
	return _actor_id(ev)


## A surname for a name over a player: the database row when there is one (real
## names carry their own last name), else the last word of what the log says.
func _surname(pid: String, display: String) -> String:
	var pl = GameDB.player_by_id(pid)
	if pl != null:
		return GameDB.player_surname(pl)
	return GameDB.player_surname({"name": display})


func _nearest(at: Vector2, side: int, n: int, exclude: Array) -> Array:
	var cands := []
	for t in tokens:
		var id := int(t["id"])
		if int(t["side"]) == side and not exclude.has(id):
			cands.append([(t["pos"] as Vector2).distance_squared_to(at), id])
	cands.sort_custom(func(a, b): return a[0] < b[0])
	var out := []
	for i in range(mini(n, cands.size())):
		out.append(cands[i][1])
	return out


static func _dir(side: int) -> float:
	return 1.0 if side == 0 else -1.0


## Focus point and zoom hint for the camera.
func focus() -> Vector2:
	var p: Vector2 = ball["pos"]
	if str(ball["mode"]) == "flight":
		p = p.lerp(ball["to"], 0.45)
	# A press on: frame a little toward its high line, so the men up the ground
	# are not cut off (press pilot).
	var pd := press_view()
	if pd != 0.0:
		p.x += pd * PRESS_FRAME_SHIFT
	return p


## While a side presses without the ball and the ball is in its attacking
## half: the direction (+1 / -1 along x) that side is pressing toward, else 0.
func press_view() -> float:
	if debug_no_press_shape or tokens.is_empty() or _tac.size() < 2:
		return 0.0
	for side in [0, 1]:
		if side != _poss and _pressing(side, (ball["pos"] as Vector2).x * _dir(side)):
			return float(_dir(side))
	return 0.0


func zoom_hint() -> float:
	if press_view() != 0.0 and mode != "break":
		return minf(_zoom_for_mode(), PRESS_FRAME_ZOOM)
	return _zoom_for_mode()


func _zoom_for_mode() -> float:
	match mode:
		"centre":
			return 1.5
		"stoppage":
			return 1.5
		"shot":
			return 1.35
		"kickin":
			return 1.2
		"break":
			return 1.0
	return 1.3


## Positions for tools and tests.
func snapshot() -> Dictionary:
	var ps := []
	for t in tokens:
		ps.append({"side": t["side"], "num": t["num"], "pos": t["pos"], "down": t["down"]})
	return {"tokens": ps, "ball": ball["pos"], "h": ball["h"], "mode": mode}
