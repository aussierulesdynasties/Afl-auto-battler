extends RefCounted
## Row 178: what a midfielder's touches are in the sim with nobody on him, man by
## man, so the tag card can say "usually gets N" from the right basis. Plays
## balance_body's matches (same seeds, lists and Gather Round venue) with no tag and
## prints one line per taggable midfielder: his sim disposals a match beside his
## listed stat line (di / gm) and the ratings the carrier pick reads.
##
##   gh workflow run audit.yml --ref <branch> -f impl=tag_usual_impl -f args="<from> <count> [<arm>]"
##
## Roles.USUAL_TOUCHES_FIT and TAG_LOSS_INSIDE / TAG_LOSS_WING come from it (row 178):
## the TU lines of a run with no arm (matches 0-319) and the TL lines of arm none fit
## his usual touches on Disposal, Carry and a wing; the TL lines of arms none, 0.42 and
## 0.66 (matches 0-399 each) give what a hold takes off him.
##
## One line a man: TU id games sim_di_pg listed_di_pg disposal contested carry wing
##
## With a third argument, a multiplier such as 0.42, side i % 2 also tags one of the
## rival's midfielders (each match the next one along, by id, so every kind of
## midfielder is tagged) with the carry multiplier held there all match, and one line
## a match says what he got: TL i target disposals disposal contested carry wing.
## Run it beside "none" (the same man followed, untagged) on the same seeds: what
## share of his own touches does a tag leave each kind of man? (Roles.TAG_TOUCHES was
## measured on the busiest man only.)


class HeldTag extends MatchSim:
	var held := -1.0

	func _init(home: Squad, away: Squad, match_seed: int = 0) -> void:
		super(home, away, match_seed)

	func _tag_share(side: int) -> float:
		return held if held >= 0.0 else super(side)


func run() -> void:
	var a := OS.get_cmdline_user_args()
	var from := int(a[1]) if a.size() > 1 else 0
	var count := int(a[2]) if a.size() > 2 else 10
	var arm := str(a[3]) if a.size() > 3 else ""
	GameDB.skip_ovr_overrides = true
	GameDB.reload()
	var codes: Array = GameDB.active_clubs(2026).duplicate()
	var pairs := []
	for x in range(codes.size()):
		for y in range(x + 1, codes.size()):
			pairs.append([codes[x], codes[y]])
	var ground: Callable = func(c): return str(GameDB.club(str(c)).get("ground", ""))
	var men := {}
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
		var quiet := {}
		if arm != "":
			var theirs: Array = (sim.squads[1 - side] as Squad).ground
			var pool := theirs.filter(func(t): return MatchSim.taggable(t))
			pool.sort_custom(func(x, y): return str(x["id"]) < str(y["id"]))
			if not pool.is_empty():
				quiet = pool[(i * 7) % pool.size()]
			var order := MatchSim.tag_order((sim.squads[side] as Squad).ground)
			if arm.is_valid_float() and not quiet.is_empty() and not order.is_empty():
				sim.held = float(arm)
				sim.set_tactics(side, {"gameplan": "balanced", "tag_id": str(quiet["id"]),
						"tagger_id": str(order[order.size() / 2]["id"]), "tag_set": true})
		var on: Array = []
		for sq in [sq_h, sq_a]:
			for t in (sq as Squad).ground:
				if MatchSim.taggable(t):
					on.append(t)
		while sim.current_quarter <= 4:
			sim.run_quarter()
		if sim.needs_extra_time():
			sim.run_extra_time()
		var r: Dictionary = sim.result()
		if not quiet.is_empty():
			var qa: Dictionary = quiet.get("attr", {})
			print("TL %d %s %d %d %d %d %d" % [i, str(quiet["id"]),
					int((r["players"] as Dictionary).get(str(quiet["id"]), {}).get("disposals", 0)),
					int(qa.get("disposal", 0)), int(qa.get("contested", 0)), int(qa.get("carry", 0)),
					1 if Roles.on_wing(quiet) else 0])
		for t in on:
			var id := str(t.get("id", ""))
			var di := int((r["players"] as Dictionary).get(id, {}).get("disposals", 0))
			if not men.has(id):
				men[id] = {"p": t, "g": 0, "di": 0}
			men[id]["g"] += 1
			men[id]["di"] += di
	for id in men:
		var m: Dictionary = men[id]
		var t: Dictionary = m["p"]
		var at: Dictionary = t.get("attr", {})
		var gm := float(t.get("gm", 0.0))
		print("TU %s %d %.2f %.2f %d %d %d %d" % [id, int(m["g"]), float(m["di"]) / float(m["g"]),
				float(t.get("di", 0.0)) / gm if gm > 0.0 else -1.0,
				int(at.get("disposal", 0)), int(at.get("contested", 0)), int(at.get("carry", 0)),
				1 if Roles.on_wing(t) else 0])
	print("SUMMARY tag_usual from %d count %d men %d" % [from, count, men.size()])
