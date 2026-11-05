extends RefCounted
## Draftee bands audit (row 65, director 4.Q9): what does a draftee rate on draft night, by the
## pick he goes at? Measurement only. Runs a National Draft (every club AI, the real 2026 lists'
## list shapes) for the real 2026 class and for n generated classes, and prints OVR and POT by
## pick band: 1-5, 6-20, 21-40, 41+. The target (4.Q9): picks 1-5 about 60-62, 6-20 about 55-58,
## POT kept.
##   BAND|class|band|picks|mean OVR|median OVR|p10 OVR|p90 OVR|mean POT|median POT
##   READY|class|band|ready|typical|project   (readiness counts, generated classes)
## godot --headless --path . --script tools/audit/run_audit.gd -- draftee_bands_impl 30

const BANDS := [[1, 5, "1-5"], [6, 20, "6-20"], [21, 40, "21-40"], [41, 999, "41+"]]
var _rows := {}   # class -> band -> [[ovr, pot, readiness], ...]


static func _band(pick: int) -> String:
	for b in BANDS:
		if pick >= int(b[0]) and pick <= int(b[1]):
			return str(b[2])
	return "41+"


static func _q(xs: Array, f: float) -> float:
	if xs.is_empty():
		return 0.0
	var s := xs.duplicate()
	s.sort()
	var i := f * float(s.size() - 1)
	var lo := int(floor(i))
	var hi := mini(lo + 1, s.size() - 1)
	return float(s[lo]) * (1.0 - (i - lo)) + float(s[hi]) * (i - lo)


func _draft(cls: Array, label: String, s: int) -> void:
	var clubs: Array = GameDB.active_clubs(GameDB.START_YEAR).duplicate()
	var rng := RandomNumberGenerator.new()
	rng.seed = s * 7919
	var order := clubs.duplicate()
	for i in range(order.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = order[i]
		order[i] = order[j]
		order[j] = t
	var sizes := {}
	var counts := {}
	var pairs := {}
	for code in clubs:
		var arr: Array = GameState.league_lists.get(code, [])
		sizes[code] = arr.size()
		var c := {"RUCK": 0, "MID": 0, "DEF": 0, "FWD": 0}
		var pr: Array = []
		for p in arr:
			c[str(p["role"])] = int(c.get(str(p["role"]), 0)) + 1
			pr.append([str(p["role"]), str(p.get("role2", ""))])
		counts[code] = c
		pairs[code] = pr
	var d := Draft.build_intake(cls, clubs, order, s, sizes, counts, pairs)
	d.start_for_user("")
	var by_id := {}
	for p in d.pool:
		by_id[str(p["id"])] = p
	if not _rows.has(label):
		_rows[label] = {}
	for e in d.pick_history:
		var p: Dictionary = by_id.get(str(e["player_id"]), {})
		if p.is_empty():
			continue
		var b := _band(int(e["pick"]))
		if not _rows[label].has(b):
			_rows[label][b] = []
		var o := int(p["overall"])
		_rows[label][b].append([o, maxi(o, int(p.get("potential", o))), str(p.get("readiness", ""))])


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var n := int(args[1]) if args.size() > 1 else 20
	if GameState.league_lists.is_empty():
		GameState.begin_real_lists()
	var real: Array = []
	for p in GameDB.draftees:
		real.append((p as Dictionary).duplicate(true))
	_draft(real, "real2026", 1)
	for s in range(1, n + 1):
		_draft(Prospects.generate_class(2027 + (s % 12), s), "generated", s)
	for label in ["real2026", "generated"]:
		for b in BANDS:
			var rows: Array = _rows.get(label, {}).get(str(b[2]), [])
			if rows.is_empty():
				continue
			var ov: Array = []
			var po: Array = []
			var rd := {"ready": 0, "typical": 0, "project": 0}
			for r in rows:
				ov.append(float(r[0]))
				po.append(float(r[1]))
				if rd.has(str(r[2])):
					rd[str(r[2])] += 1
			var mo := 0.0
			var mp := 0.0
			for i in range(ov.size()):
				mo += ov[i]
				mp += po[i]
			print("BAND|%s|%s|%d|%.1f|%.1f|%.1f|%.1f|%.1f|%.1f" % [label, str(b[2]), rows.size(),
					mo / ov.size(), _q(ov, 0.5), _q(ov, 0.1), _q(ov, 0.9), mp / po.size(), _q(po, 0.5)])
			print("READY|%s|%s|%d|%d|%d" % [label, str(b[2]), rd["ready"], rd["typical"], rd["project"]])
