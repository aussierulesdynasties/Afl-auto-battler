extends RefCounted
## Row 120: what a tag really leaves a man. Roles.tag_keep is a multiplier on the
## chance he is picked as the carrier; the card has to show his disposals kept. Plays
## balance_body's matches (same seeds, lists and Gather Round venue): side i % 2 tags
## the rival's biggest midfielder from the first bounce. Measurement only: the forced
## arms hold the multiplier from a subclass, so MatchSim itself is untouched.
##
##   gh workflow run audit.yml --ref <branch> -f impl=tag_keep_impl -f args="<arm> <from> <count>"
##   python tools/audit/tag_keep_report.py <dir with one audit.log per arm>
##
## <arm>: none (no tag, the same man followed: the paired baseline); a number such as
## 0.42 (the median man on tag_order goes, with the multiplier held at that all match);
## first, median or last (that man goes and the sim's own multiplier plays, his legs
## and all, to check the table against a real tag).
## One line a match: TK i target tagger specialist target_disposals mean_multiplier.
## mean_multiplier is read at each quarter's siren and the first bounce.


class HeldTag extends MatchSim:
	var held := -1.0

	func _init(home: Squad, away: Squad, match_seed: int = 0) -> void:
		super(home, away, match_seed)

	func _tag_share(side: int) -> float:
		return held if held >= 0.0 else super(side)


func run() -> void:
	var a := OS.get_cmdline_user_args()
	var arm := str(a[1]) if a.size() > 1 else "none"
	var from := int(a[2]) if a.size() > 2 else 0
	var count := int(a[3]) if a.size() > 3 else 10
	GameDB.skip_ovr_overrides = true
	GameDB.reload()
	var codes: Array = GameDB.active_clubs(2026).duplicate()
	var pairs := []
	for x in range(codes.size()):
		for y in range(x + 1, codes.size()):
			pairs.append([codes[x], codes[y]])
	var ground: Callable = func(c): return str(GameDB.club(str(c)).get("ground", ""))
	var total := 0
	for i in range(from, from + count):
		var p: Array = pairs[i % pairs.size()]
		var flip := (i / pairs.size()) % 2 == 1
		var h := str(p[1] if flip else p[0])
		var w := str(p[0] if flip else p[1])
		var v := str(GatherRound.venues_for([{"home": h, "away": w}], 500000 + i, ground)[0])
		var sq_h := Squad.new(h, GameDB.club_list(h), ground.call(h) == v, h)
		var sq_a := Squad.new(w, GameDB.club_list(w), ground.call(w) == v, w)
		var sim := HeldTag.new(sq_h, sq_a, 500000 + i)
		sim.weather = "perfect"
		var side := i % 2
		var theirs: Array = (sim.squads[1 - side] as Squad).ground
		var target := {}
		var most := -1.0
		for t in theirs:
			if MatchSim.taggable(t) and MatchSim.tag_give_up(t, theirs) > most:
				most = MatchSim.tag_give_up(t, theirs)
				target = t
		var order := MatchSim.tag_order((sim.squads[side] as Squad).ground)
		var who := {}
		if arm != "none" and not order.is_empty():
			match arm:
				"first": who = order[0]
				"last": who = order[order.size() - 1]
				_: who = order[order.size() / 2]
		if arm.is_valid_float():
			sim.held = float(arm)
		if not who.is_empty() and not target.is_empty():
			sim.set_tactics(side, {"gameplan": "balanced", "tag_id": str(target["id"]),
					"tagger_id": str(who["id"]), "tag_set": true})
		var reads := [sim._tag_share(side)]
		while sim.current_quarter <= 4:
			sim.run_quarter()
			reads.append(sim._tag_share(side))
		if sim.needs_extra_time():
			sim.run_extra_time()
		var r: Dictionary = sim.result()
		var di := int((r["players"] as Dictionary).get(str(target.get("id", "")), {}).get("disposals", 0))
		var mean := 0.0
		for m in reads:
			mean += float(m)
		mean /= float(reads.size())
		print("TK %d %s %s %s %d %.3f" % [i, str(target.get("id", "-")), str(who.get("id", "-")),
				"1" if not who.is_empty() and Roles.is_tagger(who) else "0", di, mean])
		total += di
	print("SUMMARY tag_keep arm %s from %d count %d disposals %d" % [arm, from, count, total])
