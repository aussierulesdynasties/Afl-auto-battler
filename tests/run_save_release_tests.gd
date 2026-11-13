extends SceneTree
## godot --headless --path . --script tests/run_save_release_tests.gd
## Release engineering for saves (row T7.R84):
##  - every save version this game has written keeps a frozen fixture, a real
##    file from that build, and each one still opens, plays on and saves;
##  - "Restore last good save" on the main menu goes back to the save before
##    the last one (real taps), and can be undone the same way;
##  - a version's patch notes open once on the menu, close with a tap, and
##    never open by themselves again; the quiet version line reopens them.

var _state: Node
var _db: Node
var _checks := 0
var _failures: Array[String] = []

const Tap := preload("res://tests/tap.gd")
const SUITE_SEED := 2027
const FIXTURE_DIR := "res://tests/fixtures"
## What each frozen fixture held when its build saved it (the make script,
## tools/make_save_fixture.gd, prints these). Never edited afterwards.
const FROZEN := {
	"career_v1_2026-09-30.save.gz": {"version": 1, "club": "STK", "stage": "Round 3",
		"ladder": ["GWS 8", "PAD 8", "CAR 8", "ADE 6", "BRL 6", "FRE 4", "RIC 4", "GEE 4", "WCE 4",
			"GCS 4", "ESS 4", "HAW 4", "STK 4", "WBD 4", "NTH 0", "SYD 0", "COL 0", "MEL 0"]},
	"career_v2_2026-11-11.save.gz": {"version": 2, "club": "FRE", "stage": "Round 3",
		"ladder": ["STK 8", "NTH 8", "GCS 8", "ADE 8", "SYD 8", "FRE 8", "WCE 6", "CAR 4", "GEE 4",
			"RIC 4", "WBD 4", "MEL 2", "COL 0", "ESS 0", "BRL 0", "GWS 0", "PAD 0", "HAW 0"]},
}


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)

const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	# Its own files per process: every worktree shares one user:// folder.
	var tag := OS.get_process_id()
	_state.save_path = "user://test_save_release_%d.save" % tag
	_state.settings_path = "user://test_save_release_%d.cfg" % tag
	_state.replay_seed = SUITE_SEED
	_state.delete_saved_career()
	root.size = Vector2i(390, 844)
	await _t("_test_frozen_fixtures")
	await _t("_test_restore_backup")
	await _t("_test_restore_when_newest_is_damaged")
	await _t("_test_restore_from_menu")
	await _t("_test_patch_notes_rule")
	await _t("_test_this_version_has_notes")
	await _t("_test_patch_notes_once")
	_state.delete_saved_career()
	DirAccess.remove_absolute(_state.settings_path)
	print(Ran.line("Save release", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


# ---------------------------------------------------------------------------
# Frozen fixtures
# ---------------------------------------------------------------------------
func _fixtures() -> Array:
	var out := []
	for name in DirAccess.get_files_at(FIXTURE_DIR):
		if name.begins_with("career_v") and name.ends_with(".save.gz"):
			out.append(name)
	out.sort()
	return out


func _put_fixture(name: String) -> void:
	_state.delete_saved_career()
	var gz := FileAccess.get_file_as_bytes(FIXTURE_DIR + "/" + name)
	var f := FileAccess.open(_state.save_path, FileAccess.WRITE)
	f.store_buffer(gz.decompress_dynamic(-1, FileAccess.COMPRESSION_GZIP))
	f.close()


func _version_on_disk() -> int:
	var f := FileAccess.open(_state.save_path, FileAccess.READ)
	var raw = f.get_var()
	f.close()
	return int(raw.get("version", 0)) if raw is Dictionary else 0


func _ladder() -> Array:
	return _state.season.ladder_sorted().map(func(r): return "%s %d" % [r["code"], int(r["pts"])])


## A build that bumps CareerSave.VERSION without freezing a save from the
## build before it fails here, as does any fixture that stops opening.
func _test_frozen_fixtures() -> void:
	var names := _fixtures()
	var versions := {}
	for name in names:
		versions[int(name.trim_prefix("career_v").get_slice("_", 0))] = true
	for v in range(1, CareerSave.VERSION + 1):
		_check(versions.has(v), "Save version %d has a frozen fixture in tests/fixtures (tools/make_save_fixture.gd)" % v)
	for name in names:
		_check(FROZEN.has(name), "%s has its frozen facts in FROZEN" % name)
		if not FROZEN.has(name):
			continue
		var want: Dictionary = FROZEN[name]
		_put_fixture(name)
		_check(_version_on_disk() == int(want["version"]) and name.begins_with("career_v%d_" % int(want["version"])),
				"%s really is a version %d save" % [name, int(want["version"])])
		_check(_state.has_saved_career() and _state.saved_career_problem() == "",
				"%s: the menu offers Continue, with no problem line" % name)
		var meta: Dictionary = _state.saved_career_meta()
		_check(str(meta.get("club", "")) == str(want["club"]) and str(meta.get("stage", "")) == str(want["stage"]),
				"%s: its header reads %s, %s: %s" % [name, want["club"], want["stage"], meta])
		_state.reset()
		_check(_state.load_career(), "%s opens" % name)
		if _state.season == null:
			_check(false, "%s loads a season" % name)
			continue
		_check(_state.my_club == str(want["club"]) and _state.season.round_index == 2,
				"%s is the same career: %s, two rounds played" % [name, want["club"]])
		_check(_ladder() == want["ladder"], "%s: the ladder is as it was saved: %s" % [name, _ladder()])
		_check(_state.my_list.size() > 30 and _state.my_list[0] is Dictionary, "%s: its list is back" % name)
		# Traits come from the stats, not the file: a save from the two-trait
		# days opens with every man carrying each trait he clears, up to five
		# (director, 2026-11-12).
		var most := 0
		var over_two := 0
		for code in _state.season.lists:
			for p in _state.season.lists[code]:
				var good := 0
				for t in Traits.of(p):
					if not Traits.is_bad(str(t)) and not ["unicorn", "wet_weather"].has(str(t)):
						good += 1
				most = maxi(most, good)
				over_two += 1 if good > 2 else 0
		_check(over_two > 0 and most <= Traits.MAX_GOOD,
				"%s: its players carry up to five traits (%d carry three or more, the most %d)" % [name, over_two, most])
		_state.advance()
		_check(_state.season.round_index == 3, "%s plays on" % name)
		_check(_state.save_career() and _version_on_disk() == CareerSave.VERSION,
				"%s saves again as the current version" % name)
		_state.reset()
		_check(_state.load_career() and _state.season.round_index == 3, "%s reloads after that" % name)
	_state.delete_saved_career()


# ---------------------------------------------------------------------------
# Restore last good save
# ---------------------------------------------------------------------------
## A Fremantle career saved after round 1 and again after round 2: the save
## in place is "Round 3", the one before it "Round 2". Played once: the files
## it leaves (the save, its backup, earlier saves, their index) are kept and
## written back for every later test that needs the same two saves.
var _two_saves_files := {}


func _two_saves() -> void:
	_state.delete_saved_career()
	if not _two_saves_files.is_empty():
		for path in _two_saves_files:
			var w := FileAccess.open(path, FileAccess.WRITE)
			w.store_buffer(_two_saves_files[path])
			w.close()
		_state.reset()
		return
	_state.reset()
	_state.career_seed = SUITE_SEED
	_state.start_season("FRE", _db.club_list("FRE"))
	_state.advance()
	_state.save_career()
	_state.advance()
	_state.save_career()
	_state.reset()
	var dir: String = _state.save_path.get_base_dir()
	for name in DirAccess.get_files_at(dir):
		if name.begins_with(_state.save_path.get_file()):
			_two_saves_files[dir.path_join(name)] = FileAccess.get_file_as_bytes(dir.path_join(name))


func _stage() -> String:
	return str(_state.saved_career_meta().get("stage", ""))


func _test_restore_backup() -> void:
	_state.delete_saved_career()
	_check(not CareerSave.has_backup(_state.save_path) and not bool(CareerSave.backup(_state.save_path)["ok"])
			and not CareerSave.restore_backup(_state.save_path), "No career: nothing to restore")
	_two_saves()
	_check(_stage() == "Round 3", "Continue opens the newest save (%s)" % _stage())
	_check(CareerSave.has_backup(_state.save_path), "The save before it is kept")
	var bak := CareerSave.backup(_state.save_path)
	_check(bool(bak["ok"]) and str(bak["meta"].get("stage", "")) == "Round 2" and str(bak["meta"].get("club", "")) == "FRE",
			"...and reads Fremantle, Round 2: %s" % [bak["meta"]])
	_check(CareerSave.restore_backup(_state.save_path), "It restores")
	_check(_stage() == "Round 2", "Continue now opens the round 2 save (%s)" % _stage())
	_check(_state.load_career() and _state.season.round_index == 1 and _state.my_club == "FRE",
			"...and it loads: Fremantle with one round played")
	_state.advance()
	_check(_state.season.round_index == 2, "The restored career plays on")
	_state.reset()
	_check(str(CareerSave.backup(_state.save_path)["meta"].get("stage", "")) == "Round 3",
			"The save it replaced is now the one kept")
	_check(CareerSave.restore_backup(_state.save_path) and _stage() == "Round 3"
			and _state.load_career() and _state.season.round_index == 2,
			"Restoring again returns to it")
	_state.reset()
	# A backup that cannot be read changes nothing.
	var f := FileAccess.open(_state.save_path + CareerSave.BACKUP_SUFFIX, FileAccess.WRITE)
	f.store_string("not a save")
	f.close()
	_check(not bool(CareerSave.backup(_state.save_path)["ok"]) and not CareerSave.restore_backup(_state.save_path),
			"A damaged backup does not restore")
	_check(_stage() == "Round 3" and _state.load_career() and _state.season.round_index == 2,
			"...and the career is unchanged")
	_state.delete_saved_career()


func _test_restore_when_newest_is_damaged() -> void:
	_two_saves()
	var f := FileAccess.open(_state.save_path, FileAccess.WRITE)
	f.store_string("not a save")
	f.close()
	_check(_state.has_saved_career() and _stage() == "Round 2", "A damaged newest save: Continue falls back to the one before")
	_check(CareerSave.restore_backup(_state.save_path), "Restore works from there")
	_check(bool(CareerSave._checked(_state.save_path)["ok"]) and _stage() == "Round 2",
			"...and the save in place is the good one again")
	var readable := true
	for h in _state.saved_career_history():
		readable = readable and not CareerSave._blob_at(CareerSave._history_path(_state.save_path, int(h["slot"]))).is_empty()
	_check(readable, "The damaged file is not kept as an earlier save")
	_check(_state.load_career() and _state.season.round_index == 1, "It loads")
	# The app killed while the old save was stepping aside: the backup still restores.
	_two_saves()
	_state.load_career()
	_state.advance()
	CareerSave.fail_at = "after_backup"
	_state.save_career()
	CareerSave.fail_at = ""
	_state.reset()
	_check(not FileAccess.file_exists(_state.save_path) and _stage() == "Round 4",
			"A save cut short at the swap: the new one waits in the temp file")
	_check(CareerSave.restore_backup(_state.save_path) and _stage() == "Round 3"
			and _state.load_career() and _state.season.round_index == 2,
			"...and the save before it restores (%s)" % _stage())
	_state.delete_saved_career()


func _menu() -> Control:
	var main: Control = load("res://scenes/Main.tscn").instantiate()
	root.add_child(main)
	for i in range(6):
		await process_frame
	return main


func _close_menu(main: Control) -> void:
	root.remove_child(main)
	main.free()
	await process_frame


func _test_restore_from_menu() -> void:
	_state.set_setting(PatchNotes.SEEN_KEY, PatchNotes.version())
	# One save only: nothing to go back to, so no entry.
	_state.delete_saved_career()
	_state.reset()
	_state.career_seed = SUITE_SEED
	_state.start_season("FRE", _db.club_list("FRE"))
	_state.save_career()
	_state.reset()
	var main: Control = await _menu()
	_check(main.find_child("ContinueCareer", true, false) != null and main.find_child("RestoreLastGood", true, false) == null,
			"A career saved once: Continue, and no restore entry")
	await _close_menu(main)

	_two_saves()
	main = await _menu()
	var entry := main.find_child("RestoreLastGood", true, false) as Button
	_check(entry != null and entry.text == "Restore last good save", "The menu has Restore last good save")
	if entry == null:
		await _close_menu(main)
		return
	var win := Rect2(Vector2.ZERO, Vector2(root.size))
	_check(win.encloses(entry.get_global_rect()) and entry.size.y >= 44.0,
			"...on the 390x844 screen without scrolling, thumb-sized (%s)" % entry.get_global_rect())
	var build := main.find_child("BuildLabel", true, false) as Control
	_check(build != null and win.encloses(build.get_global_rect()),
			"The version line still fits under it (%s)" % (build.get_global_rect() if build != null else Rect2()))
	_check((main.find_child("CareerMeta", true, false) as Label).text.contains("Round 3"), "Continue names round 3")
	# Cancel first: nothing changes.
	var why: String = await Tap.tap(entry)
	_check(why == "", "A tap reaches the entry (%s)" % why)
	var sheet := main.find_child("RestoreConfirm", true, false)
	var which := main.find_child("RestoreWhich", true, false) as Label
	_check(sheet != null and which != null and which.text.contains("Fremantle") and which.text.contains("Round 2")
			and which.text.contains("saved "), "It asks first, naming the save it goes back to: %s" % (which.text if which != null else ""))
	why = await Tap.tap(main.find_child("CancelRestore", true, false) as Button)
	await process_frame
	_check(why == "" and main.find_child("RestoreConfirm", true, false) == null and _stage() == "Round 3",
			"Cancel closes it and the career is unchanged (%s)" % why)
	# Then for real.
	entry = main.find_child("RestoreLastGood", true, false) as Button
	why = await Tap.tap(entry)
	var go := main.find_child("ConfirmRestore", true, false) as Button
	_check(why == "" and go != null and go.size.y >= 44.0, "The sheet opens again (%s)" % why)
	why = await Tap.tap(go)
	for i in range(4):
		await process_frame
	_check(why == "", "A tap reaches Restore (%s)" % why)
	_check(main.find_child("RestoreConfirm", true, false) == null, "The sheet closes")
	var meta_line := main.find_child("CareerMeta", true, false) as Label
	var note := main.find_child("RestoreNote", true, false) as Label
	_check(meta_line != null and meta_line.text.contains("Round 2"), "Continue now names round 2: %s" % (meta_line.text if meta_line != null else ""))
	_check(note != null and note.visible and note.text == "Last good save restored.", "The menu says it restored")
	_check(_stage() == "Round 2", "The save on disk is the round 2 one")
	# Back the same way: the save it replaced was kept.
	entry = main.find_child("RestoreLastGood", true, false) as Button
	_check(entry != null, "The entry is still there to undo it")
	why = await Tap.tap(entry)
	which = main.find_child("RestoreWhich", true, false) as Label
	_check(why == "" and which != null and which.text.contains("Round 3"), "It now offers round 3 back (%s)" % why)
	main.handle_back()
	await process_frame
	_check(main.find_child("RestoreConfirm", true, false) == null, "Back closes the sheet")
	await _close_menu(main)
	_state.reset()
	_check(_state.load_career() and _state.season.round_index == 1, "Continue opens the restored career")
	_state.reset()

	# A backup that cannot be read says so and changes nothing.
	var f := FileAccess.open(_state.save_path + CareerSave.BACKUP_SUFFIX, FileAccess.WRITE)
	f.store_string("not a save")
	f.close()
	main = await _menu()
	why = await Tap.tap(main.find_child("RestoreLastGood", true, false) as Button)
	var line := main.find_child("SaveProblem", true, false) as Label
	_check(why == "" and main.find_child("RestoreConfirm", true, false) == null and line != null and line.visible
			and line.text.contains("could not be read") and line.text.contains("unchanged"),
			"A damaged backup says so instead of asking (%s)" % why)
	_check(_stage() == "Round 2", "...and the career is unchanged")
	await _close_menu(main)
	_state.delete_saved_career()


# ---------------------------------------------------------------------------
# Patch notes
# ---------------------------------------------------------------------------
func _test_patch_notes_rule() -> void:
	var v := PatchNotes.version()
	_check(not PatchNotes.due("", v), "A first run shows nothing")
	_check(not PatchNotes.due(v, v), "The same version again shows nothing")
	_check(PatchNotes.due("0.0.1", v), "A new version after an older one shows its notes")
	_check(not PatchNotes.due("0.0.1", "9.9.9") and PatchNotes.lines("9.9.9").is_empty(),
			"A version with no notes shows nothing")


## The version in project.godot always has notes, written for a coach.
func _test_this_version_has_notes() -> void:
	var v := PatchNotes.version()
	var lines := PatchNotes.lines()
	_check(lines.size() >= 1 and lines.size() <= 6,
			"Version %s has 1 to 6 lines of patch notes in data/patch_notes.json (add them with the version bump)" % v)
	var tracker := RegEx.new()
	tracker.compile("#\\d|\\bPR\\b|\\brow \\d|\\bT\\d\\.")
	for ver in PatchNotes.notes():
		for text in PatchNotes.notes()[ver]:
			var s := str(text)
			_check(s.strip_edges() == s and s.length() >= 20 and s.length() <= 130 and s.ends_with("."),
					"%s: a note is one plain sentence: %s" % [ver, s])
			_check(tracker.search(s) == null, "%s: no tracker numbers in a note: %s" % [ver, s])


func _test_patch_notes_once() -> void:
	_state.delete_saved_career()
	_state.reset()
	var v := PatchNotes.version()
	# A first run: nothing opens, the version is recorded.
	DirAccess.remove_absolute(_state.settings_path)
	var main: Control = await _menu()
	_check(main.find_child("PatchNotes", true, false) == null, "A first run opens no patch notes")
	_check(str(_state.get_setting(PatchNotes.SEEN_KEY, "")) == v, "...and records the version")
	await _close_menu(main)
	# The next version's first run: the notes open over the menu.
	_state.set_setting(PatchNotes.SEEN_KEY, "0.0.1")
	main = await _menu()
	for i in range(30):   # the sheet rises into place
		await process_frame
	var sheet := main.find_child("PatchNotes", true, false) as Control
	_check(sheet != null and sheet.is_visible_in_tree(), "A new version opens its patch notes on the menu")
	if sheet == null:
		await _close_menu(main)
		return
	var shown := []
	for l in main.find_child("PatchNotesLines", true, false).get_children():
		shown.append((l as Label).text)
	_check(shown == PatchNotes.lines(), "...with this version's lines: %s" % [shown])
	_check(str(_state.get_setting(PatchNotes.SEEN_KEY, "")) == v, "...and records that they were shown")
	var close := main.find_child("PatchNotesClose", true, false) as Button
	var win := Rect2(Vector2.ZERO, Vector2(root.size))
	_check(close != null and close.size.y >= 44.0 and win.encloses(close.get_global_rect()),
			"Close is thumb-sized and on the 390x844 screen")
	var sc := main.find_child("PatchNotesLines", true, false).get_parent().get_parent() as ScrollContainer
	_check(sc == null or sc.get_v_scroll_bar().max_value <= sc.size.y + 1.0, "The notes fit without scrolling")
	# The menu under the sheet cannot be tapped through it.
	var under := main.find_child("NewCareer", true, false) as Button
	var why: String = await Tap.tap(under)
	_check(why != "" and main.find_child("PatchNotes", true, false) != null, "The menu under the sheet takes no tap")
	why = await Tap.tap(close)
	await process_frame
	await process_frame
	_check(why == "", "A tap reaches Close (%s)" % why)
	_check(main.find_child("PatchNotes", true, false) == null, "...and the sheet is gone")
	# The quiet version line opens them again, and Back closes them.
	var build := main.find_child("BuildLabel", true, false) as Button
	_check(build != null and build.text.begins_with("Build " + v) and build.text.ends_with("What's new")
			and build.size.y >= 44.0, "The version line reads Build %s and What's new" % v)
	why = await Tap.tap(build)
	_check(why == "" and main.find_child("PatchNotes", true, false) != null, "A tap on it opens the notes again (%s)" % why)
	_check(main.handle_back(), "Back closes them")
	await process_frame
	await process_frame
	_check(main.find_child("PatchNotes", true, false) == null, "...and they are gone")
	await _close_menu(main)
	# Never again for this version.
	main = await _menu()
	_check(main.find_child("PatchNotes", true, false) == null, "The next visit to the menu opens nothing")
	await _close_menu(main)
