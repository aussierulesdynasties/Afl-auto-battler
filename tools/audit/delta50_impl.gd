extends RefCounted
## What one attribute at one AFL position does to the margin (director 2026-11-28,
## plan step 3: "mirror teams + a Δ50 split (30 vs 80, not +10)", "a fixed full-role
## lineup (including Mid-Forward explicitly in a MID + FWD split)", "drop the binary
## > 2 se cliff and inspect the actual Δ50 margin table first as a MatchSim
## diagnostic"). Measurement only.
##
## Both sides are the same average side: every player is the league's median
## regular (8+ games in the data season) at his AFL position, attribute by attribute,
## with that position's median height and weight, in a fixed lineup:
##   ruck: 1 Ruck
##   midfield (5): 3 Midfielder, 2 Mid-Forward
##   back (6): 3 Key Defender, 3 Gen. Defender
##   forward (6): 2 Key Forward, 3 Gen. Forward, 1 Mid-Forward
##   bench (5): Ruck, Midfielder, Mid-Forward, Gen. Defender, Gen. Forward
## In a cell, every player at the position has the attribute at HI on one side and
## LO on the other; which side is HI alternates match by match (home and away even),
## neither side at its home ground. The margin is the HI side's score minus the LO
## side's. Nothing is paired and nothing is cut at 2 se: each cell prints its mean
## margin, its standard error and the two sides' mean scores. A NULL cell (no
## difference at all) checks the mirror: its mean margin should be 0 within its se.
## Matches are seeded 700000 + match index, the same seeds in every cell.
##
## Args after the impl name:
##   positions  comma list ("Key_Defender,Ruck"; "_" for a space) or "all"
##   matches    per cell (default 200)
##   attributes comma list, "weighted" (the position's OVR weights + work_rate,
##              the default) or "all" (all 18)
##   levels     "30:80" (default); "30:55" or "55:80" for a linearity check
##   part       "k/n": only cells k, k+n, k+2n, ... (0-based), to split a run
##              over n processes; the NULL cell is cell 0
##   traits     "on" (default: worked out from the cell's attributes, as in a real
##              match), "median" (each player keeps the traits of the median player
##              at his position, whatever the cell sets; director review 3,
##              2026-11-28, option A) or "off" (no traits). The synergies follow,
##              since they are counted from the same traits when the match starts.
##              Traits.of reads the fixed list, so every trait read sees it.
##   from       first match index (default 0), to split one cell's matches over
##              processes: "250 ... 0", "250 ... 250", ... give seeds 700000+i.
## Prints: CELL|position|attribute|lo|hi|matches|mean margin|se|mean HI score|mean LO score
## and STATS|position|attribute|each STATS key, HI side minus LO side a match
## godot --headless --path . --script tools/audit/run_audit.gd -- delta50_impl Ruck 200 weighted 30:80 0/1 median

const LINEUP := {
	"RUCK": ["Ruck"],
	"MID": ["Midfielder", "Midfielder", "Midfielder", "Mid-Forward", "Mid-Forward"],
	"DEF": ["Key Defender", "Key Defender", "Key Defender", "Gen. Defender", "Gen. Defender", "Gen. Defender"],
	"FWD": ["Key Forward", "Key Forward", "Gen. Forward", "Gen. Forward", "Gen. Forward", "Mid-Forward"],
	"BENCH": ["Ruck", "Midfielder", "Mid-Forward", "Gen. Defender", "Gen. Forward"],
}
const REGULAR_GAMES := 8.0
## The direct stats printed beside the margin (HI side minus LO side, a match):
## what each skill should move before it reaches the scoreboard.
const STATS := ["hitouts", "clearances", "contested_possessions", "inside50", "marks", "contested_marks",
		"tackles", "pressure_acts", "intercepts", "spoils", "one_percenters", "clangers", "goals", "behinds"]

var _median := {}     # apos -> {attr: median}
var _template := {}   # apos -> a real player of that position (for the fields a match reads)
var _size := {}       # apos -> [height, weight]
var _traits_mode := "on"


func _build_medians() -> void:
	var by := {}
	for p in GameDB.players:
		if float(p.get("gm", 0.0)) < REGULAR_GAMES or (p.get("attr", {}) as Dictionary).is_empty():
			continue
		var apos := Rating.apos_of(p)
		if not by.has(apos):
			by[apos] = []
			_template[apos] = p
		(by[apos] as Array).append(p)
	for apos in by:
		var m := {}
		for k in Attributes.KEYS:
			var v := []
			for p in by[apos]:
				v.append(int(p["attr"].get(k, 50)))
			m[k] = _mid(v)
		_median[apos] = m
		var h := []
		var w := []
		for p in by[apos]:
			h.append(float(p.get("height_cm", 185.0)))
			w.append(float(p.get("weight_kg", 85.0)))
		_size[apos] = [_mid(h), _mid(w)]
		print("MEDIAN|%s|%d regulars|%s|height %.0f" % [apos, (by[apos] as Array).size(), JSON.stringify(m), float(_size[apos][0])])


static func _mid(v: Array) -> float:
	v.sort()
	if v.is_empty():
		return 50.0
	var n := v.size()
	return float(v[n / 2]) if n % 2 == 1 else (float(v[n / 2 - 1]) + float(v[n / 2])) / 2.0


## One side: 23 players, ids `tag`_0.., the cell's position at `level` on `key`
## (no change when key is "").
func _side(tag: String, apos_bump: String, key: String, level: int) -> Dictionary:
	var list := []
	var sel := {"RUCK": [], "MID": [], "DEF": [], "FWD": [], "BENCH": []}
	var n := 0
	for line in ["RUCK", "MID", "DEF", "FWD", "BENCH"]:
		for apos in LINEUP[line]:
			var t: Dictionary = _template[apos]
			var p: Dictionary = t.duplicate(true)
			for drop in ["traits", "learned", "project", "expects_game", "injury_weeks", "suspension_weeks",
					"season_ban", "rested", "rehab", "unicorn", "backing", "promise"]:
				p.erase(drop)
			p["id"] = "%s_%d" % [tag, n]
			p["club"] = tag
			p["apos"] = apos
			p["role"] = Rating.line_of(apos)
			p["role2"] = ""
			p["height_cm"] = float(_size[apos][0])
			p["weight_kg"] = float(_size[apos][1])
			var a := {}
			for k in Attributes.KEYS:
				a[k] = clampi(int(round(float(_median[apos][k]))), 1, 99)
			if key != "" and apos == apos_bump:
				a[key] = level
			p["attr"] = a
			list.append(p)
			(sel[line] as Array).append(p["id"])
			n += 1
	return {"list": list, "sel": sel}


## Traits held fixed on a match-day player (the slotted copy, so his slot and
## position count as they do in a real match): off, none; median, the traits he
## would have with his position's median attributes.
func _fix_traits(p: Dictionary) -> void:
	if _traits_mode == "off":
		p["traits_fixed"] = []
		return
	var base := p.duplicate()
	base.erase("traits_fixed")
	var a := {}
	for k in Attributes.KEYS:
		a[k] = clampi(int(round(float(_median[str(p["apos"])][k]))), 1, 99)
	base["attr"] = a
	p["traits_fixed"] = Traits.of(base)


func _match(i: int, apos: String, key: String, lo: int, hi: int) -> Array:
	var hi_home := i % 2 == 0
	var h := _side("HOM", apos, key, hi if hi_home else lo)
	var a := _side("AWY", apos, key, lo if hi_home else hi)
	var sq_h := Squad.new("HOM", h["list"], false, "HOM", h["sel"])
	var sq_a := Squad.new("AWY", a["list"], false, "AWY", a["sel"])
	if _traits_mode != "on":
		for sq in [sq_h, sq_a]:
			for p in (sq as Squad).ground + (sq as Squad).bench + (sq as Squad).sub:
				_fix_traits(p)
	var sim := MatchSim.new(sq_h, sq_a, 700000 + i)
	sim.season_plans = ["steady", "steady"]
	sim.run()
	var r: Dictionary = sim.result()
	var s: Array = r["score"]
	var tag_hi := "HOM_" if hi_home else "AWY_"
	var d := {}
	for k in STATS:
		d[k] = 0.0
	for id in (r.get("players", {}) as Dictionary):
		var st: Dictionary = r["players"][id]
		var sign := 1.0 if str(id).begins_with(tag_hi) else -1.0
		for k in STATS:
			d[k] += sign * float(st.get(k, 0.0))
	return [int(s[0]), int(s[1]), d] if hi_home else [int(s[1]), int(s[0]), d]


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var pos_arg := str(args[1]) if args.size() > 1 else "all"
	var n := int(args[2]) if args.size() > 2 else 200
	var attr_arg := str(args[3]) if args.size() > 3 else "weighted"
	var levels := (str(args[4]) if args.size() > 4 else "30:80").split(":")
	var part := (str(args[5]) if args.size() > 5 else "0/1").split("/")
	var lo := int(levels[0])
	var hi := int(levels[1])
	var k_part := int(part[0])
	var n_part := int(part[1])
	_traits_mode = str(args[6]) if args.size() > 6 else "on"
	var from := int(args[7]) if args.size() > 7 else 0
	if not ["on", "median", "off"].has(_traits_mode):
		push_error("delta50: traits must be on, median or off, not %s" % _traits_mode)
		return
	print("TRAITS|%s" % _traits_mode)
	GameDB.reload()
	_build_medians()
	var positions: Array = Rating.POSITIONS.duplicate() if pos_arg == "all" else \
			Array(pos_arg.split(",")).map(func(s): return str(s).replace("_", " "))
	var cells := []
	cells.append(["NULL", ""])  # cell 0, so it runs in part 0
	for apos in positions:
		var keys: Array
		if attr_arg == "weighted":
			keys = (Rating.WEIGHTS[apos] as Dictionary).keys()
			if not keys.has("work_rate"):
				keys.append("work_rate")
		elif attr_arg == "all":
			keys = Attributes.KEYS.duplicate()
		else:
			keys = Array(attr_arg.split(","))
		for k in keys:
			cells.append([apos, str(k)])
	for c in range(cells.size()):
		if c % n_part != k_part:
			continue
		var apos := str(cells[c][0])
		var key := str(cells[c][1])
		var margins := []
		var sum_hi := 0.0
		var sum_lo := 0.0
		var sum_d := {}
		for k in STATS:
			sum_d[k] = 0.0
		for i in range(from, from + n):
			var sc := _match(i, apos, key, lo, hi)
			margins.append(float(sc[0] - sc[1]))
			sum_hi += float(sc[0])
			sum_lo += float(sc[1])
			for k in STATS:
				sum_d[k] += float(sc[2][k])
		var mean := 0.0
		for m in margins:
			mean += m
		mean /= float(n)
		var ss := 0.0
		for m in margins:
			ss += (m - mean) * (m - mean)
		var se := sqrt(ss / float(maxi(1, n - 1))) / sqrt(float(n))
		print("CELL|%s|%s|%d|%d|%d|%.2f|%.2f|%.1f|%.1f" % [apos, key if key != "" else "-", lo, hi, n, mean, se,
				sum_hi / float(n), sum_lo / float(n)])
		var parts := []
		for k in STATS:
			parts.append("%s %+.1f" % [k, sum_d[k] / float(n)])
		print("STATS|%s|%s|%s" % [apos, key if key != "" else "-", ", ".join(parts)])
