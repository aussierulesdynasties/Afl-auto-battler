extends SceneTree
## Scratch probe (stays out of git): the two match_game checks at this commit.

func _initialize() -> void:
	_run.call_deferred()


func _sim(seed: int):
	var MS = load("res://scripts/sim/MatchSim.gd")
	var SQ = load("res://scripts/sim/Squad.gd")
	var db = root.get_node("GameDB")
	return MS.new(SQ.new("GEE", db.club_list("GEE"), true, "GEE"), SQ.new("COL", db.club_list("COL"), false, "COL"), seed)


func _run() -> void:
	await process_frame
	var MS = load("res://scripts/sim/MatchSim.gd")
	for seed in range(299, 306):
		var sim = _sim(seed)
		sim.moment_side = 0
		var res: Dictionary = sim.run()
		print("PROBE skip seed %d moments=%d pending=%s" % [seed, (res["moments"] as Array).size(), str(not sim.pending_moment.is_empty())])
	MS.tune = {"WX_miss_behind": 0.0}
	var kinds := {}
	var set_opts := {}
	var lead_shots := 0
	var turn := 0
	for seed in range(830, 838):
		var live = _sim(seed)
		live.weather = "windy"
		live.moment_side = 0
		while live.current_quarter <= 4:
			live.begin_quarter()
			while not live.continue_quarter():
				var m: Dictionary = live.pending_moment
				var k := str(m["kind"])
				kinds[k] = int(kinds.get(k, 0)) + 1
				var pick := int(m.get("default", 0))
				if k == "set_shot":
					var keys := []
					for o in m["options"]:
						keys.append(str(o["key"]))
					set_opts[",".join(keys)] = int(set_opts.get(",".join(keys), 0)) + 1
					var key: String = ["bomb", "pass"][turn % 2]
					turn += 1
					for i in range(keys.size()):
						if keys[i] == key:
							pick = i
				live.resolve_moment(pick)
			live.end_quarter()
		for shot in live.shot_log:
			if str(shot[4]) == "lead":
				lead_shots += 1
	MS.tune = {}
	print("PROBE windy moment kinds=%s set_shot options=%s lead shots=%d" % [str(kinds), str(set_opts), lead_shots])
	quit(0)
