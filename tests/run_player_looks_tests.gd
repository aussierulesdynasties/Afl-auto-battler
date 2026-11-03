extends SceneTree
## godot --headless --path . --script tests/run_player_looks_tests.gd
## Register row 6 (director 2026-10-10: "they look like clones"; 2026-11-03: faces minimal -
## eyes, brows, skin tones; brows vary per player): the new hair styles and the face overlay
## (VignetteLooks), behind Features "player_looks". Off, the figures draw exactly what they
## drew before; on, the new styles and a face.

## Loaded at run time: the vignette scripts need the autoloads.
var SV: GDScript
const SUITE_SEED := 6061

var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	seed(SUITE_SEED)
	SV = load("res://scripts/ui/match/StoppageVignette.gd")
	_t("_test_atlases")
	_t("_test_cells")
	_t("_test_brows")
	await _t("_test_switch_off")
	await _t("_test_switch_on")
	Features.clear("player_looks")
	print(Ran.line("Player looks", self))
	for f in _failures:
		print("ERROR: " + f)
	quit(0 if _failures.is_empty() else 1)


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## Every new atlas loads, and none shares its size with another figure texture: the figure
## shader tells an overlay from the sheet by size (figure.gdshader is_hair).
func _test_atlases() -> void:
	var n := VignetteLooks.LOOK_FILES.size()
	_check(n == VignetteLooks.HAIR_STYLES.size() + VignetteLooks.FACES.size() and n == VignetteLooks.LOOK_TEXTURES.size(),
			"One atlas per new style and face (%d)" % n)
	_check(VignetteLooks.FACES.size() == 5, "Five faces, one per brow (face_lib.EYEBROWS)")
	var sizes := {Vector2i(VignetteFigures.SHEET_SIZE): "sheet"}
	for tex in VignetteFigures.HAIR_TEXTURES + VignetteLooks.LOOK_TEXTURES:
		var t := tex as Texture2D
		_check(t != null, "Every hair and look atlas loads")
		if t == null:
			continue
		var s := Vector2i(t.get_size())
		_check(not sizes.has(s), "Atlas size %s is its own (also %s)" % [s, sizes.get(s, "")])
		sizes[s] = t.resource_path
	_check(sizes.size() - 1 <= 32, "The shader holds every overlay size (32)")
	for id in VignetteLooks.HAIR_STYLES:
		_check(Appearance.HAIR_STYLES.has(id) and not VignetteFigures.HAIR_STYLE_INDEX.has(id)
				and not VignetteFigures.HAIR_NONE.has(id), "%s is a new style a player can have" % id)


## Every new style and every face has art on the strips a match shows most.
func _test_cells() -> void:
	for spec in [["average", "idle", "front"], ["average", "jog", "side_l"], ["ruck", "idle", "front"],
			["small", "idle", "front"]]:
		if not VignetteFigures.has(spec[0], spec[1], spec[2]):
			continue
		var s := VignetteFigures.strip(spec[0], spec[1], spec[2])
		for id in VignetteLooks.HAIR_STYLES + VignetteLooks.FACES:
			var c := VignetteLooks.cell(s, id)
			_check(not c.is_empty() and int(c["frames"]) == int(s["frames"]),
					"%s has its own cells on %s" % [id, "/".join(spec)])
	# No face from behind: the head hides it.
	var back := VignetteFigures.strip("average", "idle", "back")
	for id in VignetteLooks.FACES:
		_check(VignetteLooks.cell(back, id).is_empty(), "%s draws nothing from behind" % id)


## His brows come from his id alone, the same every time, and all five are used.
func _test_brows() -> void:
	var seen := {}
	for i in 400:
		var id := "p%d" % i
		var b := Appearance.brows_for(id)
		_check(b == Appearance.brows_for(id) and b >= 0 and b < 5, "%s's brows are fixed" % id)
		seen[b] = true
	_check(seen.size() == 5, "All five brows are worn (%d)" % seen.size())
	Features.set_on("player_looks", false)
	_check(not Appearance.full({"skin": 2, "hair": 1}, "p1", true).has("brows"), "Off, a look has no brows")
	Features.set_on("player_looks", true)
	var look := Appearance.full({"skin": 2, "hair": 1}, "p1", true)
	_check(int(look.get("brows", -1)) == Appearance.brows_for("p1"), "On, a look carries his brows")


class Fig extends Control:
	var sv: GDScript
	var style := "afro"
	var face := 2
	func _draw() -> void:
		var info := VignetteFigures.strip("average", "idle", "front")
		sv.draw_frame(self, Vector2(200, 400), info, 0, 1.5,
				sv.look_colour(0, {"skin": 2, "hair": 1}), false, Color(0, 0, 0, 0),
				Transform2D.IDENTITY, style, face)


func _draw_once(style: String, face: int) -> void:
	SV.hair_log.clear()
	SV.face_log.clear()
	SV.log_frames = true
	var f := Fig.new()
	f.sv = SV
	f.style = style
	f.face = face
	f.size = Vector2(400, 500)
	root.add_child(f)
	await process_frame
	await process_frame
	f.queue_free()
	await process_frame
	SV.log_frames = false


## Off: a new style draws the short crop, no face is drawn, and face_of says none.
func _test_switch_off() -> void:
	Features.set_on("player_looks", false)
	_check(SV.face_of({"brows": 3}) == -1, "Off, no face")
	for id in VignetteLooks.HAIR_STYLES:
		await _draw_once(id, 3)
		var h: Array = SV.hair_log
		_check(h.size() == 1 and h[0]["texture"] == VignetteFigures.HAIR_TEXTURES[VignetteFigures.HAIR_STYLE_INDEX["short_crop"]],
				"Off, %s draws the short crop as before" % id)
		_check(SV.face_log.is_empty(), "Off, %s draws no face" % id)


## On: each new style draws its own atlas, and his face is drawn from its own.
func _test_switch_on() -> void:
	Features.set_on("player_looks", true)
	_check(SV.face_of({"brows": 3}) == 3 and SV.face_of({}) == 0, "On, face_of gives his brows")
	for i in VignetteLooks.HAIR_STYLES.size():
		var id: String = VignetteLooks.HAIR_STYLES[i]
		var face := i % VignetteLooks.FACES.size()
		await _draw_once(id, face)
		var h: Array = SV.hair_log
		_check(h.size() == 1 and h[0]["texture"] == VignetteLooks.texture(
				VignetteLooks.cell(VignetteFigures.strip("average", "idle", "front"), id)), "On, %s draws its own hair" % id)
		var fl: Array = SV.face_log
		_check(fl.size() == 1 and fl[0]["texture"] == VignetteLooks.LOOK_TEXTURES[
				VignetteLooks.LOOK_FILES.find("look_%s.png" % VignetteLooks.FACES[face])], "On, %s wears face %d" % [id, face])
	# The original styles still draw their own atlases.
	await _draw_once("dreadlocks", 0)
	_check(SV.hair_log.size() == 1 and SV.hair_log[0]["texture"] == VignetteFigures.HAIR_TEXTURES[2], "On, dreadlocks as before")
	await _draw_once("buzz", 0)
	_check(SV.hair_log.is_empty() and SV.face_log.size() == 1, "On, buzz has a face and still no hair overlay")
