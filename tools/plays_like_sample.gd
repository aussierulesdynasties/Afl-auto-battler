extends SceneTree
## godot --headless --path . --script tools/plays_like_sample.gd -- [first_year] [classes] [out_file]
## Who generated draft prospects "play like" (scripts/sim/PlaysLike.gd): for
## `classes` generated draft classes from `first_year` (default 2045, 11), how
## many different real players are named, how close the named player's peak
## overall is to the prospect's POT and how close his height is. With an
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
			if absf(float(e["height"]) - float(p["height_cm"])) <= 4.0:
				near_cm += 1
			if y == first and lines.size() < 40:
				plain.append("%s, %s, Plays like: %s" % [db.player_display_name(p), str(p["role"]), str(e["real_name"])])
				lines.append("%s, %s, %d cm, POT %d -> Plays like: %s (%s, %d cm, peak %d)" % [
						db.player_display_name(p), str(p["role"]), int(p["height_cm"]), int(p["potential"]),
						str(e["real_name"]), str(e["role"]), int(e["height"]), int(e["peak"])])
	var top := names.keys()
	top.sort_custom(func(a, b): return int(names[a]) > int(names[b]))
	print("PLAYS LIKE: %d prospects, %d real players in the pool, %d different names" % [n, pool.size(), names.size()])
	print("  peak within 0/1/2/3/4/5 of POT: %s; further: %d; mean gap %.2f; widest %d" % [str(gaps), far, gap_sum / maxf(1.0, n), int(gap_max)])
	print("  height within 4 cm: %d of %d" % [near_cm, n])
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
