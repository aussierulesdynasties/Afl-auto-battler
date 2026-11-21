extends RefCounted
## The position probe of the shape harness (tools/balance.sh shape, row 201).
##
## Plays a finished match's event log through MatchDirector headless, as the
## match screen does, and measures where the 36 men stand: each side's length,
## width and area, men behind the ball, men near it, spacing to the nearest
## opponent, and every kick's length and how far it moves the ball across the
## ground. It reads the director and never steers it.
##
## Snapshots (one per moment, both sides):
##   centre     the umpire's bounce at a centre bounce
##   stoppage   the throw-up at a ball-up or throw-in around the ground
##   kickin     the kick-in's kick after a behind
##   set_shot   a set shot's kick
## Open play is sampled every SAMPLE seconds of presentation time and filed per
## side by possession and by where the ball is in that side's frame:
##   att_<zone>  the side has the ball      (zone: d50, dmid, amid, f50)
##   def_<zone>  the other side has it
##   con_<zone>  nobody has it: the ball is loose (the papers' "contest" phase,
##               Alexander et al. 2019)
## A side's frame has x toward the goal it attacks (MatchDirector._dir).
##
## Each bucket keeps sums, so a match's line adds up across matches; the report
## (shape_report.py) divides. Metres throughout.

const SAMPLE := 0.5
const DT := 1.0 / 15.0
const ZONES := [[-999.0, -35.0, "d50"], [-35.0, 0.0, "dmid"], [0.0, 35.0, "amid"], [35.0, 999.0, "f50"]]
## The measures each snapshot adds per side (sums; "n" counts snapshots).
const KEYS := ["len", "wid", "len_p", "wid_p", "area", "spread", "cen_dx", "behind",
		"own_10", "own_20", "opp_10", "opp_20", "near_opp", "free_5", "carrier_opp", "carrier_n",
		"cen_gap", "cen_x", "in_zone"]


## Play `res` (MatchSim.result with home/away/label) through a director and
## return {buckets: {name: [side0 sums, side1 sums]}, kicks: [...sums], calls: ...}.
static func measure(res: Dictionary) -> Dictionary:
	var d := MatchDirector.new()
	d.want_contacts = true
	d.setup(res, (res["events"] as Array).duplicate())
	var out := {"buckets": {}, "kicks": [_kick_sums(), _kick_sums()], "tag": [_tag_sums(), _tag_sums()],
			"secs": 0.0}
	# The named pair (res.probe_pair = [our man's id, his opponent's id]): a tag or
	# a switch, sampled with the rest of open play.
	var pair := []
	if res.has("probe_pair"):
		out["pair"] = {"n": 0, "dist": 0.0, "within5": 0, "goal": 0.0, "def_n": 0, "def_dist": 0.0, "def_within5": 0, "held_n": 0, "held_dist": 0.0, "held_within5": 0}
		pair = res["probe_pair"]
	var next_sample := 0.0
	var guard := 0
	var shot_k := -1
	while not d.idle() and guard < 400000:
		guard += 1
		d.advance(DT)
		_scan_phases(d, out)
		for c in d.contacts:
			_on_contact(d, c as Dictionary, out)
		d.contacts.clear()
		if d.time >= next_sample:
			next_sample = d.time + SAMPLE
			if d.mode == "open" and str(d.ball["mode"]) in ["held", "flight", "carry", "loose"]:
				var bp: Vector2 = d.ball["pos"]
				for side in range(2):
					# The zones are the standard oval's: the ball put back there from this ground.
					var xs := MatchMotion.sx(bp.x * MatchDirector._dir(side))
					var zone := ""
					for z in ZONES:
						if xs >= float(z[0]) and xs < float(z[1]):
							zone = str(z[2])
					var phase := "att_" if d._poss == side else "def_"
					if str(d.ball["mode"]) == "loose":
						phase = "con_"
					var name := phase + zone
					_add(out, name, side, _measure_side(d, side, bp))
				_tag_sample(d, out)
				if not pair.is_empty():
					_pair_sample(d, pair, out)
	out["secs"] = d.time
	out.erase("_kickin_by")
	return out


## Phases the director entered this step that no contact reports: a throw-up
## (a ball-up or throw-in around the ground) is measured as the ball goes up; a
## kick-in's set-up names its kicker, whose next kick is the kick-in.
static func _scan_phases(d: MatchDirector, out: Dictionary) -> void:
	for p in d._phases:
		if not bool(p.get("_entered", false)) or p.has("_probe"):
			continue
		p["_probe"] = true
		var t := str(p.get("t", ""))
		if t == "throwup":
			for side in range(2):
				_add_stoppage(out, side, _measure_side(d, side, p["at"]), p["at"])
		elif t == "setup" and str(p.get("mode", "")) == "kickin":
			out["_kickin_by"] = int(p.get("keep", -1))


## A ball-up or throw-in around the ground: filed as "stoppage", and again by
## where it is (stp_50 in either 50, stp_mid between them; Alexander 2021 counts
## 23 men in the ball's zone at a stoppage in either 50, 17 in midfield).
static func _add_stoppage(out: Dictionary, side: int, m: Dictionary, at: Vector2) -> void:
	_add(out, "stoppage", side, m)
	_add(out, "stp_50" if absf(at.x) >= 35.0 else "stp_mid", side, m)


static func _on_contact(d: MatchDirector, c: Dictionary, out: Dictionary) -> void:
	var kind := str(c["kind"])
	var at: Vector2 = c["at"]
	if kind == "bounce":
		# The umpire's bounce: a centre bounce (a ball-up around the ground is a
		# throw-up, _scan_phases).
		for side in range(2):
			if d.mode == "centre":
				_add(out, "centre", side, _measure_side(d, side, at))
			else:
				_add_stoppage(out, side, _measure_side(d, side, at), at)
		return
	if kind != "kick":
		return
	var who := int(c["who"])
	if who < 0:
		return
	var t: Dictionary = d.tokens[who]
	var side := int(t["side"])
	var from: Vector2 = t["pos"]
	var bk := str(d._beat.get("kind", ""))
	var k := int(d._beat.get("k", -1))
	if who == int(out.get("_kickin_by", -2)):
		out.erase("_kickin_by")
		for s in range(2):
			_add(out, "kickin", s, _measure_side(d, s, from))
	elif (bk == "goal" or bk == "behind") and k >= 0 and bool((d.events[k] as Dictionary).get("set_shot", true)):
		for s in range(2):
			_add(out, "set_shot", s, _measure_side(d, s, from))
		return
	elif bk == "goal" or bk == "behind":
		return
	# General-play kicks (and the kick-in's): length, ground made, the ball's move across.
	var ks: Dictionary = out["kicks"][side]
	var dirv := MatchDirector._dir(side)
	var length := from.distance_to(at)
	var gain := (at.x - from.x) * dirv
	var across := absf(at.y - from.y)
	ks["n"] += 1
	ks["len"] += length
	ks["len2"] += length * length
	ks["gain"] += gain
	ks["across"] += across
	ks["long40"] += 1 if length >= 40.0 else 0
	ks["back"] += 1 if gain < 0.0 else 0
	# A switch: the ball goes from one side of the ground to the other, across at
	# least 25 m (the report states the definition it is marked against).
	ks["switch"] += 1 if signf(at.y) != signf(from.y) and across >= 25.0 and absf(from.y) >= 10.0 else 0
	ks["into_f50"] += 1 if at.x * dirv >= 35.0 and from.x * dirv < 35.0 else 0


## Our man's distance to his named opponent, and to the goal he defends.
static func _pair_sample(d: MatchDirector, pair: Array, out: Dictionary) -> void:
	var a := {}
	var b := {}
	for t in d.tokens:
		if str(t["pid"]) == str(pair[0]):
			a = t
		elif str(t["pid"]) == str(pair[1]):
			b = t
	if a.is_empty() or b.is_empty():
		return
	var ps: Dictionary = out["pair"]
	var dist := (a["pos"] as Vector2).distance_to(b["pos"])
	ps["n"] += 1
	ps["dist"] += dist
	ps["within5"] += 1 if dist <= 5.0 else 0
	var own_goal := Vector2(-MatchMotion.GOAL_X * MatchDirector._dir(int(a["side"])), 0.0)
	ps["goal"] += (a["pos"] as Vector2).distance_to(own_goal)
	# The same, only while our man's side is defending (the other side has the ball).
	if d._poss != int(a["side"]):
		ps["def_n"] += 1
		ps["def_dist"] += dist
		ps["def_within5"] += 1 if dist <= 5.0 else 0
		# ...and only while the match-up shows on the ground: he is on his man
		# (a forward rotated out of the forward line is handed over until he is back).
		if (bool(a.get("duel", false)) or bool(a.get("tagging", false))) and int(a["match"]) == int(b["id"]):
			ps["held_n"] += 1
			ps["held_dist"] += dist
			ps["held_within5"] += 1 if dist <= 5.0 else 0


static func _kick_sums() -> Dictionary:
	return {"n": 0, "len": 0.0, "len2": 0.0, "gain": 0.0, "across": 0.0, "long40": 0, "back": 0,
			"switch": 0, "into_f50": 0}


static func _tag_sums() -> Dictionary:
	return {"n": 0, "dist": 0.0, "within5": 0}


## The tagger's distance to his man, sampled in open play (the side that tags).
static func _tag_sample(d: MatchDirector, out: Dictionary) -> void:
	for t in d.tokens:
		if not bool(t.get("tagging", false)) or int(t.get("match", -1)) < 0:
			continue
		var m: Dictionary = d.tokens[int(t["match"])]
		var dist := (t["pos"] as Vector2).distance_to(m["pos"])
		var ts: Dictionary = out["tag"][int(t["side"])]
		ts["n"] += 1
		ts["dist"] += dist
		ts["within5"] += 1 if dist <= 5.0 else 0


static func _add(out: Dictionary, name: String, side: int, m: Dictionary) -> void:
	var b: Dictionary = out["buckets"]
	if not b.has(name):
		var pair := []
		for s in range(2):
			var z := {"n": 0}
			for key in KEYS:
				z[key] = 0.0
			pair.append(z)
		b[name] = pair
	var sums: Dictionary = (b[name] as Array)[side]
	sums["n"] += 1
	for key in m:
		sums[key] += float(m[key])


static func _zone_ix(x: float) -> int:
	return 0 if x < -35.0 else (1 if x < 0.0 else (2 if x < 35.0 else 3))


## One side's shape around the ball at `bp`, in its attacking frame.
static func _measure_side(d: MatchDirector, side: int, bp: Vector2) -> Dictionary:
	var dirv := MatchDirector._dir(side)
	var own := PackedVector2Array()
	var opp := PackedVector2Array()
	for t in d.tokens:
		var p: Vector2 = t["pos"]
		if int(t["side"]) == side:
			own.append(Vector2(p.x * dirv, p.y))
		else:
			opp.append(Vector2(p.x * dirv, p.y))
	var b := Vector2(bp.x * dirv, bp.y)
	var xs := []
	var ys := []
	var cen := Vector2.ZERO
	for p in own:
		xs.append(p.x)
		ys.append(p.y)
		cen += p
	cen /= maxf(1.0, own.size())
	var ocen := Vector2.ZERO
	for p in opp:
		ocen += p
	ocen /= maxf(1.0, opp.size())
	xs.sort()
	ys.sort()
	var spread := 0.0
	var behind := 0
	var own_10 := 0
	var own_20 := 0
	var near_sum := 0.0
	var free_5 := 0
	for p in own:
		spread += p.distance_to(cen)
		behind += 1 if p.x < b.x else 0
		var db := p.distance_to(b)
		own_10 += 1 if db <= 10.0 else 0
		own_20 += 1 if db <= 20.0 else 0
		var nearest := INF
		for q in opp:
			nearest = minf(nearest, p.distance_to(q))
		near_sum += nearest
		free_5 += 1 if nearest > 5.0 else 0
	# Both teams' men in the ball's quarter of the ground (either 50 or either
	# half-midfield), as Alexander et al. 2021 count them.
	var bz := _zone_ix(b.x)
	var in_zone := 0
	for p in own:
		in_zone += 1 if _zone_ix(p.x) == bz else 0
	for q in opp:
		in_zone += 1 if _zone_ix(q.x) == bz else 0
	var opp_10 := 0
	var opp_20 := 0
	for q in opp:
		var db := q.distance_to(b)
		opp_10 += 1 if db <= 10.0 else 0
		opp_20 += 1 if db <= 20.0 else 0
	var m := {"len": xs[-1] - xs[0], "wid": ys[-1] - ys[0],
			"len_p": _pct(xs, 0.9) - _pct(xs, 0.1), "wid_p": _pct(ys, 0.9) - _pct(ys, 0.1),
			"area": _hull_area(own), "spread": spread / own.size(), "cen_dx": cen.x - b.x,
			"behind": behind, "own_10": own_10, "own_20": own_20, "opp_10": opp_10, "opp_20": opp_20,
			"near_opp": near_sum / own.size(), "free_5": free_5, "cen_gap": cen.distance_to(ocen),
			"cen_x": cen.x, "in_zone": in_zone}
	# The man with the ball: his nearest opponent.
	if str(d.ball["mode"]) == "held" and int(d.ball["holder"]) >= 0:
		var h: Dictionary = d.tokens[int(d.ball["holder"])]
		if int(h["side"]) == side:
			var hp := Vector2((h["pos"] as Vector2).x * dirv, (h["pos"] as Vector2).y)
			var nearest := INF
			for q in opp:
				nearest = minf(nearest, hp.distance_to(q))
			m["carrier_opp"] = nearest
			m["carrier_n"] = 1
	return m


static func _pct(sorted: Array, q: float) -> float:
	var f := q * (sorted.size() - 1)
	var i := int(floor(f))
	var j := mini(i + 1, sorted.size() - 1)
	return lerpf(float(sorted[i]), float(sorted[j]), f - i)


static func _hull_area(pts: PackedVector2Array) -> float:
	var hull := Geometry2D.convex_hull(pts)
	var a := 0.0
	for i in range(hull.size() - 1):
		a += hull[i].x * hull[i + 1].y - hull[i + 1].x * hull[i].y
	return absf(a) * 0.5
