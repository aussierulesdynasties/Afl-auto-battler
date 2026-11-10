extends RefCounted
## Audit 29: runs of goals, the margin spread, and how often a close finish reaches its scenes.
## Measurement only; no rule or tuning is changed.
##   godot --headless --path . --script tools/audit/run_audit.gd -- goal_runs_impl <mode> <seed0> <n>
## mode  ai     both clubs are AI coaches, no calls asked (the league's simulated matches)
##       coach  side 0 is asked every call (moment_side 0) and takes the call's default, as a
##              coach who lets the card time out would; both sides keep the AI's plans. This is
##              where the call cards (the late centre bounce, the close set shot, the run of
##              goals) can fire.
## seed0 batch: match i uses seed seed0 * 100000 + i; pairing and weather come from seed0 alone,
##       so the same (seed0, n) is the same set of fixtures in both modes.
## One line a match:
##   G|mode|seed|home|away|weather|hs|as|seq|siren|m100|bwin|calls
## seq    goal order, H home / A away, "|" at each quarter break
## siren  1 when BroadcastVignette.pick_kind gives the after-the-siren scene on the match's own
##        event list (a Q4 set-shot score straight before the final siren, within 6 points before it)
## m100   home margin at the last event of Q4 before minute 100 (the late bounce's window opens)
## bwin   1 when a Q4 goal at minute 100+ left the margin within 12 (a centre bounce the late
##        bounce call could fire on follows every goal), whatever the call budget
## calls  the cards side 0 was asked, kind@q:min:margin[:run], ";"-separated (coach mode)
## siren2 the siren test again with the "End of quarter 4" line skipped (the match's event list
##        puts it between the last score and "final", so siren is always 0; audit 29)

const WEATHERS := ["perfect", "perfect", "perfect", "perfect", "wet", "windy", "hot"]


func _squad(code: String, home: bool) -> Squad:
	var s := Squad.new(code, GameDB.club_list(code), home, code)
	s.ai_plans = true
	return s


func _pair(rng: RandomNumberGenerator, codes: Array) -> Array:
	var a: int = rng.randi() % codes.size()
	var b: int = rng.randi() % (codes.size() - 1)
	if b >= a:
		b += 1
	return [codes[a], codes[b]]


func _play(mode: String, seed: int, pr: Array, weather: String) -> String:
	var sim := MatchSim.new(_squad(pr[0], true), _squad(pr[1], false), seed)
	sim.weather = weather
	var calls := []
	if mode == "coach":
		sim.moment_side = 0
	while sim.current_quarter <= 4:
		sim.begin_quarter()
		while not sim.continue_quarter():
			var m: Dictionary = sim.pending_moment
			var mg := sim.score(0) - sim.score(1)
			var tag := "%s@%d:%d:%d" % [str(m.get("kind", "")), int(m.get("q", 0)), int(m.get("min", 0)), mg]
			if str(m.get("kind", "")) == "momentum":
				tag += ":%d" % int(sim._run[1])
			calls.append(tag)
			sim.resolve_moment(int(m.get("default", 0)))
		sim.end_quarter()
	var ev: Array = sim.events
	var seq := ""
	var q := 1
	var siren := 0
	var siren2 := 0
	var m100 := 0
	var bwin := 0
	for i in range(ev.size()):
		var e: Dictionary = ev[i]
		var k := str(e.get("kind", ""))
		var eq := int(e.get("q", 0))
		var sc: Array = e.get("score", [0, 0])
		if eq == 4 and int(e.get("min", 0)) < 100:
			m100 = int(sc[0]) - int(sc[1])
		if k == "goal":
			while q < eq:
				seq += "|"
				q += 1
			seq += "H" if int(e.get("side", 0)) == 0 else "A"
			if eq == 4 and int(e.get("min", 0)) >= 100 and absi(int(sc[0]) - int(sc[1])) <= 12:
				bwin = 1
		if k == "goal" or k == "behind":
			var prev: Dictionary = ev[i - 1] if i > 0 else {}
			# As MatchScene asks it: the next play event (T3.F-defects).
			var nxt := BroadcastVignette.next_play_event(ev, i)
			if BroadcastVignette.pick_kind(e, prev, nxt, {}) == BroadcastVignette.AFTER_SIREN:
				siren = 1
			# The same test with the end-of-quarter line skipped: the next event that is not one.
			var j := i + 1
			while j < ev.size() and str((ev[j] as Dictionary).get("kind", "")) == "quarter":
				j += 1
			var nxt2: Dictionary = ev[j] if j < ev.size() else {}
			if BroadcastVignette.pick_kind(e, prev, nxt2, {}) == BroadcastVignette.AFTER_SIREN:
				siren2 = 1
	while q < 4:
		seq += "|"
		q += 1
	return "G|%s|%d|%s|%s|%s|%d|%d|%s|%d|%d|%d|%s|%d" % [mode, seed, pr[0], pr[1], weather,
			sim.score(0), sim.score(1), seq, siren, m100, bwin, ";".join(calls), siren2]


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var mode := str(args[1])
	var seed0 := int(args[2])
	var n := int(args[3])
	var lb = load("res://tools/balance/league_balance.gd").new()
	var codes: Array = lb.clubs()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed0 * 7919 + 13
	for i in range(n):
		var pr := _pair(rng, codes)
		var weather: String = WEATHERS[rng.randi() % WEATHERS.size()]
		print(_play(mode, seed0 * 100000 + i, pr, weather))
	print("SUMMARY goal_runs mode %s seed0 %d n %d" % [mode, seed0, n])
