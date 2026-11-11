extends SceneTree
## Freezes a career save written by THIS build as a test fixture (row T7.R84):
##   godot --headless --path . --script tools/make_save_fixture.gd
## writes tests/fixtures/career_v<VERSION>_<today>.save.gz: Fremantle on the
## real lists, two rounds played, and prints the header and ladder that
## tests/run_save_release_tests.gd pins for it (paste them into FROZEN there).
##
## Run it BEFORE the change that bumps CareerSave.VERSION, on the build that
## still writes the old layout, so every save version ever shipped keeps a
## real file that must go on loading. A fixture is never edited or remade
## once it is committed: a save that old builds wrote cannot change either.

const SEED := 2027


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	gs.autosave_enabled = false
	gs.save_path = "user://make_save_fixture_%d.save" % OS.get_process_id()
	gs.settings_path = "user://make_save_fixture_%d.cfg" % OS.get_process_id()
	gs.show_real_names = false
	gs.replay_seed = SEED
	gs.reset()
	gs.career_seed = SEED
	gs.start_season("FRE", db.club_list("FRE"))
	gs.advance()
	gs.advance()
	var cs = load("res://scripts/state/CareerSave.gd")
	if not gs.save_career():
		push_error("the career did not save")
		quit(1)
		return
	var raw := FileAccess.get_file_as_bytes(gs.save_path)
	var out := "res://tests/fixtures/career_v%d_%s.save.gz" % [int(cs.VERSION),
			Time.get_date_string_from_system()]
	var f := FileAccess.open(out, FileAccess.WRITE)
	f.store_buffer(raw.compress(FileAccess.COMPRESSION_GZIP))
	f.close()
	var ladder: Array = gs.season.ladder_sorted().map(
			func(r): return "%s %d" % [r["code"], int(r["pts"])])
	print("wrote %s (%d bytes raw)" % [out, raw.size()])
	print("meta: %s" % [gs.saved_career_meta()])
	print("ladder: %s" % [JSON.stringify(ladder)])
	cs.delete(gs.save_path)
	DirAccess.remove_absolute(gs.settings_path)
	quit(0)
