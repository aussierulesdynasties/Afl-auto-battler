extends SceneTree
## Records the rival coach's calls in seeded matches (tests/rival_identity.gd)
## to tests/fixtures/rival_identity.json. Run it on main before a change that
## must not move the sim; tests/test_rival_read.gd checks the change against it.
## A change meant to move the match re-records it on its own branch.
##   godot --headless --path . --script tools/rival_identity_dump.gd
## It records on the suites' data (tools/run_tests.sh: no hand-set OVR rows,
## generic names, no save touched), so the suite reads the same matches.

## Loaded at run time: the autoloads (GameDB) must exist before it compiles.
const IDENTITY_PATH := "res://tests/rival_identity.gd"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var db = root.get_node("GameDB")
	if not db.skip_ovr_overrides:
		db.skip_ovr_overrides = true
		db.reload()
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://rival_identity_dump.save"
	gs.settings_path = "user://rival_identity_dump.cfg"
	gs.show_real_names = false
	var identity: GDScript = load(IDENTITY_PATH)
	var rows: Array = identity.play_all()
	var f := FileAccess.open(ProjectSettings.globalize_path(identity.FIXTURE), FileAccess.WRITE)
	f.store_string(JSON.stringify(rows, "\t") + "\n")
	f.close()
	print("Wrote %s (%d matches)" % [identity.FIXTURE, rows.size()])
	quit(0)
