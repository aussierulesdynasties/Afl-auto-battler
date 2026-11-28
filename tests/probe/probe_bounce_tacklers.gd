extends SceneTree
## Scratch probe (never commit): over many seeded matches, who MatchSim names for the tackle
## on the centre-bounce clearance winner (the first possession after a goal or quarter start,
## tackled straight away), by the tackler's role.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	var db = root.get_node("GameDB")
	db.reload()
	var MS = load("res://scripts/sim/MatchSim.gd")
	var SQ = load("res://scripts/sim/Squad.gd")
	var clubs: Array = []
	for c in db.clubs.keys():
		if (db.club_list(c) as Array).size() >= 22:
			clubs.append(c)
	print("BOUNCE clubs %s" % str(clubs))
	var by_role := {}
	var all_roles := {}
	var clear_n := 0
	var tackled_n := 0
	var matches := 0
	for s in range(1, 61):
		var a: String = clubs[s % clubs.size()]
		var b: String = clubs[(s * 7 + 3) % clubs.size()]
		if a == b:
			continue
		var sa = SQ.new(a, db.club_list(a), true, a)
		var sb = SQ.new(b, db.club_list(b), false, b)
		var role := {}
		for sq in [sa, sb]:
			for p in sq.ground:
				role[str(p.get("id", ""))] = str(p["role"])
		var res: Dictionary = MS.new(sa, sb, s).run()
		matches += 1
		var evs: Array = res["events"]
		var after_restart := true
		for i in range(evs.size()):
			var ev: Dictionary = evs[i]
			var kind := str(ev.get("kind", ""))
			if kind == "sub" or kind == "moment" or kind == "injury":
				continue
			if kind == "tackle":
				var r: String = role.get(str(ev.get("player_id", "")), "?")
				all_roles[r] = int(all_roles.get(r, 0)) + 1
			if after_restart and (kind == "kick" or kind == "handball") and absf(float(ev.get("fp", 1.0))) < 0.5:
				clear_n += 1
				var j := i + 1
				while j < evs.size() and str((evs[j] as Dictionary).get("kind", "")) in ["sub", "moment", "injury"]:
					j += 1
				if j < evs.size() and str((evs[j] as Dictionary).get("kind", "")) == "tackle":
					tackled_n += 1
					var r2: String = role.get(str((evs[j] as Dictionary).get("player_id", "")), "?")
					by_role[r2] = int(by_role.get(r2, 0)) + 1
			after_restart = kind in ["goal", "quarter"]
	print("BOUNCE matches %d centre clearances %d tackled at once %d" % [matches, clear_n, tackled_n])
	print("BOUNCE tackler roles on the clearance winner %s" % str(by_role))
	print("BOUNCE all tackles by role %s" % str(all_roles))
	quit(0)
