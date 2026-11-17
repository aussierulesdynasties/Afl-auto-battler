extends SceneTree
## The second step of data/copy_pool.csv (after tools/wheelo/copy_pool.py): adds the
## column fit_shift, the points the game's own fit (Prospects.fit_attributes, 14 games)
## adds to every rated skill of that player-season so he rates at that season's overall,
## as a listed player's skills are. The skills themselves stay the season's real ratings
## (generated players copy those); PlaysLike adds the shift to compare a past season with
## a listed player. Done here once: 9,600 fits took ~3 s every load.
##   godot --headless --path . --script tools/wheelo/fit_copy_pool.gd

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var Pr = load("res://scripts/sim/Prospects.gd")
	var path := "res://data/copy_pool.csv"
	var f := FileAccess.open(path, FileAccess.READ)
	var head := f.get_csv_line()
	if head.has("fit_shift"):
		head.remove_at(head.find("fit_shift"))
	var col := {}
	for i in head.size():
		col[head[i]] = i
	var lines := []
	var off := 0
	while not f.eof_reached():
		var line := f.get_csv_line()
		if line.size() < head.size():
			continue
		line.resize(head.size())
		var sk := {}
		for key in Pr.ATTR_KEYS:
			sk[key] = float(line[col[key]])
		var role := str(line[col["line"]])
		var target := float(line[col["ovr"]])
		# fit_attributes' own bisection, keeping the shift it settles on.
		var lo := -40.0
		var hi := 40.0
		for i in range(14):
			var mid := (lo + hi) * 0.5
			if Pr._shifted_overall(sk, role, mid, 14.0) < target:
				lo = mid
			else:
				hi = mid
		var shift := (lo + hi) * 0.5
		var want: Dictionary = Pr.fit_attributes(sk, role, target)
		for key in Pr.ATTR_KEYS:
			var got := int(round(sk[key])) if key in Pr.UNRATED_KEYS else clampi(int(round(sk[key] + shift)), 1, 99)
			if got != int(want[key]):
				off += 1
		line.append("%.10f" % shift)
		lines.append(line)
	f.close()
	if off > 0:
		push_error("fit_shift does not reproduce fit_attributes on %d skills" % off)
		quit(1)
		return
	head.append("fit_shift")
	var out := FileAccess.open(path, FileAccess.WRITE)
	out.store_string(",".join(_quoted(head)) + "\n")
	for line in lines:
		out.store_string(",".join(_quoted(line)) + "\n")
	out.close()
	print("fit_shift written for %d player-seasons (matches fit_attributes)" % lines.size())
	quit(0)


func _quoted(line: PackedStringArray) -> PackedStringArray:
	var out := PackedStringArray()
	for v in line:
		out.append("\"%s\"" % v.replace("\"", "\"\"") if v.contains(",") or v.contains("\"") else v)
	return out
