extends RefCounted
## Does training train? (director 2026-11-16: "train marking and your player
## gets better at marking"). Paired autopilot careers on the real lists: the
## same seed, your club's young players (22 and under at the start) given one
## stat focus every season in arm "focus", none in arm "none". Every other
## club is left alone. Pair the two arms by seed and player id.
## Args after the impl name: arm seed club seasons stat
##   godot --headless --path . --script tools/audit/run_audit.gd -- training_promise_impl focus 301 MEL 4 contested_marking
## Prints, per tracked player, at each season's start (S), end (E, before the
## off-season) and so on:
##   TP|arm|seed|year|phase|id|name|role|age|stat value|OVR|POT|league mean of the stat for his role
## and once a season the league's mean OVR (LG).

var club := "MEL"
var arm := "none"
var stat := "contested_marking"


func _run_draft(d: Draft) -> void:
	var guard := 0
	while not d.is_finished() and guard < 5000:
		guard += 1
		var c := d._best_ai_pick(d.current_club())
		if c.is_empty() or not d._draft_pick(d.current_club(), c):
			d._skip_current_pick()


func run() -> void:
	var args := OS.get_cmdline_user_args()
	arm = str(args[1]) if args.size() > 1 else "none"
	var seed := int(args[2]) if args.size() > 2 else 301
	club = str(args[3]) if args.size() > 3 else "MEL"
	var seasons := int(args[4]) if args.size() > 4 else 4
	stat = str(args[5]) if args.size() > 5 else "contested_marking"
	GameState.reset()
	GameState.autosave_enabled = false
	GameState.career_seed = seed
	GameState.replay_seed = seed
	GameState.start_season(club, GameDB.club_list(club))
	var tracked := {}
	for p in GameState.my_list:
		if float(p.get("age", 30.0)) <= 22.0:
			tracked[str(p["id"])] = true
	for s in range(seasons):
		if arm == "focus":
			for p in GameState.my_list:
				if tracked.has(str(p["id"])):
					GameState.set_stat_focus(str(p["id"]), stat)
		_report(seed, "S", tracked)
		var guard := 0
		while not GameState.season.is_season_over() and guard < 60:
			guard += 1
			GameState.advance()
		_report(seed, "E", tracked)
		if s == seasons - 1:
			break
		GameState.open_offseason()
		if GameState.begin_intake_draft():
			_run_draft(GameState.draft)
			GameState.finish_intake_draft()
		else:
			GameState.start_next_season()


func _report(seed: int, phase: String, tracked: Dictionary) -> void:
	var sums := {}
	var counts := {}
	var ovr := 0.0
	var n := 0
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			var role := str(p.get("role", "MID"))
			var a: Dictionary = p.get("attr", {})
			if a.has(stat):
				sums[role] = float(sums.get(role, 0.0)) + float(a[stat])
				counts[role] = int(counts.get(role, 0)) + 1
			ovr += float(p.get("overall", 0))
			n += 1
	print("LG|%s|%d|%d|%s|mean OVR %.2f" % [arm, seed, GameState.season_year, phase, ovr / maxf(1.0, n)])
	for p in GameState.my_list:
		var id := str(p["id"])
		if not tracked.has(id):
			continue
		var role := str(p.get("role", "MID"))
		var a: Dictionary = p.get("attr", {})
		print("TP|%s|%d|%d|%s|%s|%s|%s|%d|%d|%d|%d|%.2f" % [arm, seed, GameState.season_year, phase, id,
				GameDB.player_display_name(p), role, int(float(p.get("age", 0))), int(a.get(stat, 0)),
				int(p.get("overall", 0)), int(p.get("potential", 0)),
				float(sums.get(role, 0.0)) / maxf(1.0, float(counts.get(role, 0)))])
