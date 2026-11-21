extends SceneTree
## Applies the shared seat rule (tools/grounds/seat_rule.gd) to every ground with instanced seats,
## after its build: a seat a supporter could not sit in (no floor, no headroom, inside the fence,
## alone) is taken out of its seats_*.bin. Run it after copying a rebuilt ground into
## assets/grounds/<slug>/ (and after `godot --headless --import`, so the model read is the new one).
##   godot --headless --path . --script tools/grounds/seat_check.gd -- [--write] [--out=DIR] [slug ...]
## Without --write it only reports. --out saves DIR/<slug>.json with every failing seat's spot
## (tools/grounds/seat_shots.gd films them). No slugs: every ground that has seats_*.bin.

const SeatRule := preload("res://tools/grounds/seat_rule.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var write := args.has("--write")
	var out := ""
	var only := []
	for a in args:
		if str(a).begins_with("--out="):
			out = str(a).trim_prefix("--out=")
		elif not str(a).begins_with("--"):
			only.append(str(a))
	if out != "":
		DirAccess.make_dir_recursive_absolute(out)
	var total := 0
	var gone := 0
	for slug in SeatRule.grounds():
		if not only.is_empty() and not only.has(slug):
			continue
		var r: Dictionary = SeatRule.new().check(str(slug), root, write)
		total += int(r["seats"])
		gone += int(r["removed"])
		var line := r.duplicate()
		line.erase("spots")
		print("SEATS %s %s" % [slug, JSON.stringify(line)])
		if out != "":
			var f := FileAccess.open(out.path_join("%s.json" % slug), FileAccess.WRITE)
			f.store_string(JSON.stringify(r, " "))
			f.close()
	print("SEATS total %d %s %d" % [total, "removed" if write else "failing (report only)", gone])
	quit(0)
