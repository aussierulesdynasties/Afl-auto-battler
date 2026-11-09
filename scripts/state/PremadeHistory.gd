class_name PremadeHistory
extends RefCounted
## Pre-simulated years for a new career (director, row 137): the seasons played
## without you ship with the game, so a start after 2027 opens in moments.
## Each file is the league at the point Choose your club opens, so one history
## serves every club. tools/histories/regen.sh makes them from the current sim;
## tests/run_premade_history_tests.gd fails when the save format or lists move.

const DIR := "res://data/histories/"
## Histories for each start. A new career takes one at random.
const COUNT := 2
## The first seasons that have years played without you: Canberra's 2030 start
## (real lists, Canberra on) and Tasmania's 2028 (real lists, Canberra off).
const STARTS := [2030, 2028]
## What feeds the years besides the code: a change here is a stale history.
const LIST_FILES := ["data/*.csv", "data/international_prospects.json"]
const SIM_CODE := ["scripts/sim/*.gd", "scripts/state/*.gd", "scripts/core/*.gd"]


static func path_for(first_season: int, real_names: bool, n: int) -> String:
	return "%s%d_%s_%d.hist" % [DIR, first_season, "real" if real_names else "fict", n]


## A fresh history for this start, or "" (then the years are played live).
static func pick(first_season: int, real_names: bool) -> String:
	var fresh := []
	for n in COUNT:
		var p := path_for(first_season, real_names, n)
		if FileAccess.file_exists(p) and problem(CareerSave.read_packed_meta(p)) == "":
			fresh.append(p)
	return "" if fresh.is_empty() else str(fresh[randi() % fresh.size()])


## Why a history with this header can't be used, or "". Cheap enough for the
## new-career tap: the game checks the format and the lists as loaded; the test
## also checks the source files themselves.
static func problem(meta: Dictionary) -> String:
	if int(meta.get("save_version", 0)) != CareerSave.VERSION:
		return "save format"
	if int(meta.get("career_version", 0)) != _career_version():
		return "career format"
	if str(meta.get("list_stamp", "")) != list_stamp():
		return "real lists"
	return ""


## The real 2026 lists as the game loaded them.
static func list_stamp() -> String:
	var db = _autoload("GameDB")
	var rows := PackedStringArray()
	for code in db.club_order:
		for p in db.club_list(str(code)) + db.club_additions(str(code)):
			rows.append("%s|%s" % [code, p.get("id")])
	rows.sort()
	return "\n".join(rows).md5_text()


## By lookup, not by name: the generator is a --script tool, and such a script's
## classes compile before the autoload names exist.
static func _autoload(n: String) -> Node:
	return (Engine.get_main_loop() as SceneTree).root.get_node(n)


static func _career_version() -> int:
	return _autoload("GameState").CAREER_VERSION


## A hash of files by pattern, line endings ignored (Windows and CI agree).
static func files_stamp(patterns: Array) -> String:
	var ctx := HashingContext.new()
	ctx.start(HashingContext.HASH_MD5)
	for pat in patterns:
		var dir := (pat as String).get_base_dir()
		var names := Array(DirAccess.get_files_at("res://" + dir))
		names.sort()
		for f in names:
			if not (f as String).match((pat as String).get_file()):
				continue
			ctx.update((f as String).to_utf8_buffer())
			ctx.update(FileAccess.get_file_as_string("res://%s/%s" % [dir, f]).replace("\r", "").to_utf8_buffer())
	return ctx.finish().hex_encode()


static func stamps() -> Dictionary:
	return {"save_version": CareerSave.VERSION, "career_version": _career_version(),
			"list_stamp": list_stamp(), "list_files": files_stamp(LIST_FILES),
			"sim_code": files_stamp(SIM_CODE)}
