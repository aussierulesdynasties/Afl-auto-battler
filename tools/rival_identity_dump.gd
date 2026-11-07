extends SceneTree
## Records the rival coach's calls in seeded matches (tests/rival_identity.gd)
## to tests/fixtures/rival_identity.json. Run it on main before a change that
## must not move the sim; tests/test_rival_read.gd checks the change against it.
##   godot --headless --path . --script tools/rival_identity_dump.gd

## Loaded at run time: the autoloads (GameDB) must exist before it compiles.
const IDENTITY_PATH := "res://tests/rival_identity.gd"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var identity: GDScript = load(IDENTITY_PATH)
	var rows: Array = identity.play_all()
	var f := FileAccess.open(ProjectSettings.globalize_path(identity.FIXTURE), FileAccess.WRITE)
	f.store_string(JSON.stringify(rows, "\t") + "\n")
	f.close()
	print("Wrote %s (%d matches)" % [identity.FIXTURE, rows.size()])
	quit(0)
