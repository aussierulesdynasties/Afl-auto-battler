extends SceneTree
## Writes the rival coach's calls in seeded matches (tests/rival_identity.gd)
## to a file, for a one-off proof that a change leaves them alone: run it on a
## main checkout and on the branch (copy tests/rival_identity.gd and this tool
## into the main checkout if it has none) and diff the two files.
##   godot --headless --path . --script tools/rival_identity_dump.gd -- <out.json>
## It records on the suites' data (tools/run_tests.sh: no hand-set OVR rows,
## no save touched), so it plays the matches the suite reads.

## Loaded at run time: the autoloads (GameDB) must exist before it compiles.
const IDENTITY_PATH := "res://tests/rival_identity.gd"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		push_error("Usage: --script tools/rival_identity_dump.gd -- <out.json>")
		quit(1)
		return
	var db = root.get_node("GameDB")
	if not db.skip_ovr_overrides:
		db.skip_ovr_overrides = true
		db.reload()
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://rival_identity_dump.save"
	gs.settings_path = "user://rival_identity_dump.cfg"
	var identity: GDScript = load(IDENTITY_PATH)
	var rows: Array = identity.play_all()
	var f := FileAccess.open(str(args[0]), FileAccess.WRITE)
	if f == null:
		push_error("Cannot write %s" % args[0])
		quit(1)
		return
	f.store_string(JSON.stringify(rows, "\t") + "\n")
	f.close()
	print("Wrote %s (%d matches)" % [args[0], rows.size()])
	quit(0)
