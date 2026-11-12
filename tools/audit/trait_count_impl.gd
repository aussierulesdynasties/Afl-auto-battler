extends RefCounted
## How many traits players carry across the league (director, 2026-11-12: "up
## to 5 traits + unicorn"). A real-lists career (every club's real list), then
## seasons played as the balance dynasty plays them (tools/balance/dynasty.gd).
## At each season start, over every listed player of every club:
##   COUNT <year> | players N | good traits mean m | 0: a% 1: b% 2: c% 3: d% 4: e% 5: f%
##   TRAIT <year> | <trait> <pct> ...    share of players carrying each trait
## "Good traits" leaves out Unicorn, Wet-weather player and Hothead.
## Args after the impl name: seasons (default 3, so four snapshots); the
## career seed is AUDIT_SEED (default 301), so a main-vs-branch pair matches.
##   godot --headless --path . --script tools/audit/run_audit.gd -- trait_count_impl 3
var dyn = load("res://tools/balance/dynasty.gd").new()
const OTHER := ["unicorn", "wet_weather", "hothead"]


func _snapshot(gs) -> void:
	var hist := {}
	var per := {}
	var n := 0
	var total := 0
	for c in gs.season.lists:
		for p in gs.season.lists[c]:
			n += 1
			var good := 0
			for t in Traits.of(p):
				per[t] = int(per.get(t, 0)) + 1
				if not OTHER.has(t):
					good += 1
			total += good
			hist[good] = int(hist.get(good, 0)) + 1
	var parts := []
	for k in range(0, 8):
		if hist.has(k):
			parts.append("%d: %.1f%%" % [k, 100.0 * int(hist[k]) / maxi(1, n)])
	print("COUNT %d | players %d | good traits mean %.2f | %s" % [gs.season_year, n, float(total) / maxi(1, n), "  ".join(parts)])
	var keys := per.keys()
	keys.sort_custom(func(a, b): return int(per[a]) > int(per[b]))
	var tp := []
	for k in keys:
		tp.append("%s %.1f%%" % [k, 100.0 * int(per[k]) / maxi(1, n)])
	print("TRAIT %d | %s" % [gs.season_year, ", ".join(tp)])


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seasons := int(args[1]) if args.size() > 1 else 3
	var gs := GameDB.get_tree().root.get_node("GameState")
	gs.autosave_enabled = false
	gs.reset()
	var env := OS.get_environment("AUDIT_SEED")
	var s := int(env) if env != "" else 301
	gs.career_seed = s
	gs.replay_seed = s
	var user := "MEL"
	gs.start_season(user, GameDB.club_list(user))
	for y in range(seasons + 1):
		_snapshot(gs)
		if y == seasons:
			break
		while not gs.season.is_season_over():
			dyn._play_week(gs, user, true)
		var mgmt: Dictionary = dyn._manage(gs, user, "full")
		gs.set_selection({})
		if not dyn._offseason(gs, user, mgmt):
			break
