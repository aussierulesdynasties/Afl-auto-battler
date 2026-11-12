extends SceneTree
## godot --headless --path . --script tools/plays_like_sample.gd -- [first_year] [classes] [out_file]
## Who generated draft prospects "play like" (scripts/sim/PlaysLike.gd): for
## `classes` generated draft classes from `first_year` (default 2045, 11), how
## many different real players are named, how close the named player's peak
## overall is to the prospect's POT, how close his height is, how wide the
## rating gap is, how often the named player lacks the prospect's best
## attribute, and how the rucks spread over the few real rucks. With an
## out_file, also writes the first 40 prospects of `first_year` as
## "name, position, Plays like: X"; the same 40 are printed with the facts
## ("name, position, height, POT -> Plays like: X (his position, height, peak)").


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var PL = load("res://scripts/sim/PlaysLike.gd")
	var Pr = load("res://scripts/sim/Prospects.gd")
	var db := root.get_node("GameDB")
	var args := OS.get_cmdline_user_args()
	var first := int(args[0]) if args.size() > 0 else 2045
	var classes := int(args[1]) if args.size() > 1 else 11
	var out_file := str(args[2]) if args.size() > 2 else ""
	var pool: Array = db.plays_like_pool
	var names := {}
	var n := 0
	var gaps := [0, 0, 0, 0, 0, 0]   # within 0..5 points of POT
	var far := 0
	var near_cm := 0
	var gap_sum := 0.0
	var gap_max := 0.0
	var cm_max := 0.0
	var lacks := 0
	var rating_sum := 0.0
	var rating_max := 0.0
	var wide := 0
	var ruck_names := {}
	var rucks := 0
	var small_stars: PackedStringArray = []
	var lines: PackedStringArray = []
	var plain: PackedStringArray = []
	for y in range(first, first + classes):
		for p in Pr.generate_class(y, 7):
			var e: Dictionary = PL.nearest(p, pool)
			if e.is_empty():
				continue
			n += 1
			names[str(e["real_name"])] = int(names.get(str(e["real_name"]), 0)) + 1
			var gap := absf(float(e["peak"]) - float(p["potential"]))
			gap_sum += gap
			gap_max = maxf(gap_max, gap)
			for k in range(6):
				if gap <= float(k):
					gaps[k] += 1
			if gap > 5.0:
				far += 1
			var cm := absf(float(e["height"]) - float(p["height_cm"]))
			cm_max = maxf(cm_max, cm)
			if cm <= 4.0:
				near_cm += 1
			var me: Dictionary = PL.profile(p)
			var mine: PackedFloat32Array = me["vec"]
			var top := 0
			for i in range(mine.size()):
				if mine[i] > mine[top]:
					top = i
			if mine[top] - float((e["vec"] as PackedFloat32Array)[top]) >= 15.0:
				lacks += 1
			var rg: float = PL.rating_gap(me, e)
			rating_sum += rg
			rating_max = maxf(rating_max, rg)
			if rg > 12.0:
				wide += 1
			if str(p["role"]) == "RUCK":
				rucks += 1
				ruck_names[str(e["real_name"])] = int(ruck_names.get(str(e["real_name"]), 0)) + 1
			if str(p["role"]) == "FWD" and float(p["height_cm"]) <= 180.0 and int(p["potential"]) >= 86:
				small_stars.append("%d cm POT %d -> %s (%d cm, peak %d)" % [int(p["height_cm"]), int(p["potential"]),
						str(e["real_name"]), int(e["height"]), int(e["peak"])])
			if y == first and lines.size() < 40:
				plain.append("%s, %s, %s" % [db.player_display_name(p), str(p["role"]), PL.line(p)])
				lines.append("%s, %s, %d cm, POT %d -> Plays like: %s (%s, %d cm, peak %d)" % [
						db.player_display_name(p), str(p["role"]), int(p["height_cm"]), int(p["potential"]),
						str(e["real_name"]), str(e["role"]), int(e["height"]), int(e["peak"])])
	var top := names.keys()
	top.sort_custom(func(a, b): return int(names[a]) > int(names[b]))
	print("PLAYS LIKE: %d prospects, %d real players in the pool, %d different names" % [n, pool.size(), names.size()])
	print("  peak within 0/1/2/3/4/5 of POT: %s; further: %d; mean gap %.2f; widest %d" % [str(gaps), far, gap_sum / maxf(1.0, n), int(gap_max)])
	print("  height within 4 cm: %d of %d; widest %d cm" % [near_cm, n, int(cm_max)])
	print("  rating gap (weighted rms, points): mean %.1f, widest %.1f, over 12: %d" % [rating_sum / maxf(1.0, n), rating_max, wide])
	print("  named player 15+ points under the prospect's best attribute: %d of %d" % [lacks, n])
	var ruck_top := 0
	for k in ruck_names:
		ruck_top = maxi(ruck_top, int(ruck_names[k]))
	print("  rucks: %d prospects name %d real rucks, the most named %d times" % [rucks, ruck_names.size(), ruck_top])
	print("  forwards 180 cm or under with POT 86+: " + "; ".join(small_stars))
	var most: PackedStringArray = []
	for i in range(mini(8, top.size())):
		most.append("%s x%d" % [top[i], int(names[top[i]])])
	print("  most named: " + ", ".join(most))
	for l in lines:
		print(l)
	if out_file != "":
		var f := FileAccess.open(out_file, FileAccess.WRITE)
		f.store_string("\n".join(plain) + "\n")
		f.close()
	quit(0)
