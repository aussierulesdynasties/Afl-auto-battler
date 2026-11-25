class_name PremiershipCeremony
extends Control
## The premiership ceremony (director, 2026-11-25; design bible 161, row 170):
## the Grand Final's siren opens a stage in the premiers' colours before full
## time. The final frame: the stripes band with the cup, the club's ribbons and
## that year's flag; the guernsey crest; "Premiers" with the club's name under
## it; four facts (the score, the Norm Smith, the captain, the club's history).
## Whoever wins the flag gets it, in their colours.
##
## His answers (2026-11-25): the cup comes first, then the legend's farewell,
## then the full-time sheet, still. Another club's flag plays in full,
## skippable. A tap anywhere but Continue jumps to the final frame; Continue
## and Android Back leave. Reduced motion shows the final frame at once with
## only the sting.
##
## His pick of three (2026-11-25): Full goosebumps, the light leads. The
## scorebug beats, the roar and a light sweep in the club's colours, the cup,
## the ribbons coloured, the flag unfurls, the year and "Premiers" stamp, the
## streamers (in front of the words); still at 6.3 s. The crowd does not dip.
## Presentation only: nothing here is read by the match or the season.

signal done

const FullTimeMotion := preload("res://scripts/ui/match/FullTimeMotion.gd")

const MAX_W := 430.0        ## the column on a wide screen
const PAD := 16.0
const BTN_H := 48.0
const BAND_H := 236.0       ## the band at full size; it scales down to fit
const BAND_MIN := 150.0
const CUP_H := 200.0
const FLAG_H := 170.0
const ROD_Y := 36.0         ## the flag's rod, in its art's 512 square
const CREST := 56.0
const SW := 150.0           ## a stripe across (ClubBackdrop)
const RUN := 0.55           ## the stripes' lean: across this share of the height
const SWEEP_W := 120.0      ## the light, across
const SWEEP_PEAK := 0.35
const GREY := Color(0.8, 0.8, 0.8)   ## the ribbons as drawn, before the tint
const PULSE := 1.06         ## the scorebug's one beat
const DUR_PULSE := 0.3
const DUR_PAGE := 0.4
const ROAR_DB := -6.0
const SIREN_DB := -6.0

const STRIPES := """
shader_type canvas_item;
// The premiers' guernsey stripes (ClubBackdrop's lean), uncovered from the left
// behind the light and settled into the band behind the cup: [top, bottom] in
// pixels.
uniform vec2 area = vec2(390.0, 844.0);
uniform float sw = 150.0;
uniform float run = 464.0;
uniform vec4 col_a : source_color = vec4(1.0);
uniform vec4 col_b : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float top = 0.0;
uniform float bottom = 844.0;
uniform float wipe = 0.0;
void fragment() {
	vec2 p = UV * area;
	float s = p.x + run * p.y / area.y;
	float u = s / sw;
	float f = fract(u);
	float cosine = area.y / sqrt(area.y * area.y + run * run);
	float t = min(f, 1.0 - f) * sw * cosine;
	bool even = mod(floor(u), 2.0) < 1.0;
	vec4 here = even ? col_a : col_b;
	vec4 other = even ? col_b : col_a;
	float cover = clamp(0.5 + (wipe - s) * cosine, 0.0, 1.0);
	cover *= clamp(0.5 + p.y - top, 0.0, 1.0) * clamp(0.5 + bottom - p.y, 0.0, 1.0);
	COLOR = vec4(mix(other, here, clamp(0.5 + t, 0.0, 1.0)).rgb, cover);
}
"""

## Sounds this ceremony started ("siren", "roar"), for tests.
var heard: Array = []
## True once everything is in its final place (the end of the beats, or a tap).
var at_rest := false

var _facts := {}
var _premier := ""
var _pulse: Array = []
var _siren := false
var _page: ColorRect
var _stripes: ColorRect
var _mat: ShaderMaterial
var _sweep: Control
var _flash: Control
var _content: Control
var _eyebrow: Label
var _band: Control
var _trophy: Control
var _tint: ShaderMaterial
var _flag: Control
var _flag_art: Control
var _year: Control
var _crest: Control
var _premiers: Label
var _club: Label
var _callouts: Array[Label] = []
var _continue: Button
var _streamers: Control
var _tweens: Array[Tween] = []
var _wipe_s := 0.0
var _settle_k := 0.0
var _sweep_c := 0.0
var _sweeping := false
var _crest_lit := false
var _flash_a := 0.0
var _band_top := 0.0
var _band_bottom := 0.0
var _left := false


## What the ceremony says for a Grand Final result, or {} when there is no
## flag to present: any other match, a draw to be replayed, a level Grand Final
## with no extra time. {premier, loser, year, eyebrow, callouts}.
static func facts(res: Dictionary) -> Dictionary:
	if str(res.get("tag", "")) != "GF" or bool(res.get("replay_due", false)):
		return {}
	var sc: Array = res.get("score", [])
	if sc.size() < 2:
		return {}
	var home := str(res.get("home", ""))
	var away := str(res.get("away", ""))
	var level := int(sc[0]) == int(sc[1])
	var premier := ""
	if not level:
		premier = home if int(sc[0]) > int(sc[1]) else away
	elif bool(res.get("extra_time", false)) or bool(res.get("decided_on_ladder", false)):
		premier = _on_ladder(home, away)
	if premier == "":
		return {}
	var loser := away if premier == home else home
	var year := GameState.season_year
	var lines: Array = [_score_line(res, premier, loser, level)]
	var ns := GameState.norm_smith_for(res)
	if not ns.is_empty():
		var medal := "Norm Smith Medal: %s" % str(ns.get("name", ""))
		if str(ns.get("club", "")) != premier:
			medal += " (%s)" % GameDB.club_name(str(ns["club"]))
		lines.append(medal)
	lines.append(_captains(premier))
	lines.append(ClubStories.history_line(premier, year, GameState.honour_roll, true))
	return {"premier": premier, "loser": loser, "year": year,
		"eyebrow": "%d Grand Final" % year,
		"callouts": lines.filter(func(s: Variant) -> bool: return str(s) != "")}


## A Grand Final level after extra time goes to the higher-ranked side
## (Season.record_final): the bracket's winner when it is recorded, else the
## ladder.
static func _on_ladder(home: String, away: String) -> String:
	if GameState.season == null:
		return ""
	var fin: Dictionary = GameState.season.finals
	var w := str((fin.get("slots", {}) as Dictionary).get("W_GF", ""))
	if w == home or w == away:
		return w
	var top: Array = fin.get("top", [])
	if top.has(home) and top.has(away):
		return home if top.find(home) < top.find(away) else away
	return ""


static func _score_line(res: Dictionary, premier: String, loser: String, level: bool) -> String:
	var p := 0 if str(res.get("home", "")) == premier else 1
	var g: Array = res.get("goals", [0, 0])
	var b: Array = res.get("behinds", [0, 0])
	var mine := UiKit.scoreline(int(g[p]), int(b[p]))
	var theirs := UiKit.scoreline(int(g[1 - p]), int(b[1 - p]))
	if level:
		var after := " after extra time" if bool(res.get("extra_time", false)) else ""
		return "Level with %s%s, %s apiece: premiers as the higher-ranked side." % [GameDB.club_name(loser), after, mine]
	var margin := absi(int(res["score"][0]) - int(res["score"][1]))
	var by := "1 point" if margin == 1 else "%d points" % margin
	var et := " after extra time" if bool(res.get("extra_time", false)) else ""
	return "Beat %s by %s%s, %s to %s." % [GameDB.club_name(loser), by, et, mine, theirs]


static func _captains(club: String) -> String:
	var names: Array = []
	for id in Captaincy.ids(GameState.captaincy_record(club), "captain"):
		var n := GameDB.player_display_name_by_id(str(id), "")
		if n != "":
			names.append(n)
	if names.is_empty():
		return ""
	if names.size() == 1:
		return "Captain: %s" % names[0]
	return "Captains: %s and %s" % [", ".join(names.slice(0, names.size() - 1)), names[-1]]


## Open the ceremony over `host` (the space under the scoreboard). `opts`:
## "pulse" the scorebug's two score labels (they beat once), "siren" true where
## nothing else has sounded the siren (the hub's sim path).
static func open(host: Control, f: Dictionary, opts := {}) -> PremiershipCeremony:
	var c := PremiershipCeremony.new()
	c.name = "PremiershipCeremony"
	c._facts = f
	c._premier = str(f.get("premier", ""))
	c._pulse = opts.get("pulse", [])
	c._siren = bool(opts.get("siren", false))
	c._build()
	host.add_child(c)
	c.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	c._layout()
	c.resized.connect(c._layout)
	c._start()
	return c


# --- The build ------------------------------------------------------------
func _build() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	clip_contents = true
	var cols := GameDB.club_colours(_premier)
	_page = ColorRect.new()
	_page.name = "Page"
	_page.color = UiKit.BG
	_page.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_page)
	_page.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_stripes = ColorRect.new()
	_stripes.name = "Stripes"
	_stripes.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = STRIPES
	_mat = ShaderMaterial.new()
	_mat.shader = sh
	_mat.set_shader_parameter("sw", SW)
	_mat.set_shader_parameter("col_a", cols[0])
	_mat.set_shader_parameter("col_b", cols[1])
	_stripes.material = _mat
	add_child(_stripes)
	_stripes.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_sweep = _layer("Sweep", _draw_sweep)
	_flash = _layer("Flash", _draw_flash)
	_content = Control.new()
	_content.name = "Content"
	_content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_content)
	_content.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_eyebrow = UiKit.line(str(_facts.get("eyebrow", "")), UiKit.SECONDARY, UiKit.MUTED, true)
	_eyebrow.name = "CeremonyEyebrow"
	_band = Control.new()
	_band.name = "Band"
	_band.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_content.add_child(_band)
	_trophy = FinalsBracket._cup(CUP_H)
	_trophy.name = "CeremonyCup"
	var rib := FinalsBracket._ribbons(_premier, CUP_H)
	if rib != null:
		_trophy.add_child(rib)
		var rib_art := rib.find_child("Art_premiership_ribbons", true, false) as CanvasItem
		if rib_art != null:
			_tint = rib_art.material as ShaderMaterial
	_band.add_child(_trophy)
	_flag = HonoursArt.view("premiership_flag", FLAG_H, _premier, int(_facts.get("year", 0)), "Premiership flag")
	_flag.name = "CeremonyFlag"
	_flag_art = _flag.find_child("Art_premiership_flag", true, false) as Control
	_year = _flag.find_child("Year", true, false) as Control
	_band.add_child(_flag)
	for slot in [_trophy, _flag]:
		(slot as Control).size = (slot as Control).custom_minimum_size
	if _flag_art != null:
		_flag_art.pivot_offset = Vector2(_flag_art.size.x / 2.0, ROD_Y * FLAG_H / 512.0)
	if _year != null:
		_year.pivot_offset = _year.size / 2.0
	_content.add_child(_eyebrow)
	_crest = UiKit.club_marker(_premier, CREST)
	_crest.name = "CeremonyCrest"
	_content.add_child(_crest)
	_premiers = UiKit.figure("Premiers", UiKit.HERO, UiKit.TEXT)
	_premiers.name = "CeremonyPremiers"
	_content.add_child(_premiers)
	_club = UiKit.line(GameDB.club_name(_premier), UiKit.H1, UiKit.club_name_colour(UiKit.club_ink(_premier)), true)
	_club.name = "CeremonyClub"
	_content.add_child(_club)
	var i := 0
	for s in _facts.get("callouts", []):
		var l := UiKit.lbl(str(s), UiKit.BODY, UiKit.TEXT)
		l.name = "CeremonyCallout%d" % i
		_content.add_child(l)
		_callouts.append(l)
		i += 1
	for l in [_eyebrow, _premiers, _club] + _callouts:
		(l as Label).horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_quiet(_content)
	_continue = UiKit.btn("Continue", UiKit.NAME, true)
	_continue.name = "CeremonyContinue"
	_continue.mouse_filter = Control.MOUSE_FILTER_STOP
	UiKit.feel(_continue, "main")
	_continue.pressed.connect(finish_now)
	add_child(_continue)


func _layer(n: String, painter: Callable) -> Control:
	var c := Control.new()
	c.name = n
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(c)
	c.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	c.draw.connect(painter)
	return c


## Nothing the ceremony draws takes a touch: a tap on it is a tap on the stage.
func _quiet(n: Node) -> void:
	if n is Control:
		(n as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	for k in n.get_children():
		_quiet(k)


## Every piece that comes in, in reading order.
func _items() -> Array:
	return [_eyebrow, _trophy, _flag, _crest, _premiers, _club] + _callouts


# --- The layout (one phone screen, no scroll) ------------------------------
func _layout() -> void:
	if _content == null or size.x <= 0.0 or size.y <= 0.0:
		return
	var w := size.x
	var h := size.y
	var cw := minf(w, MAX_W) - 2.0 * PAD
	var cx := (w - cw) / 2.0
	_continue.position = Vector2(cx, h - PAD - BTN_H)
	_continue.size = Vector2(cw, BTN_H)
	var avail := h - 3.0 * PAD - BTN_H
	var eh := _fit(_eyebrow, cw)
	var ph := _fit(_premiers, cw)
	var nh := _fit(_club, cw)
	var ch := 0.0
	for l in _callouts:
		ch += _fit(l, cw)
	ch += 6.0 * maxf(0.0, _callouts.size() - 1.0)
	var fixed := eh + 6.0 + 10.0 + CREST + 4.0 + ph + nh + 12.0 + ch
	var bh := clampf(avail - fixed, BAND_MIN, BAND_H)
	var y := PAD + maxf(0.0, (avail - fixed - bh) / 2.0)
	_base(_eyebrow, Vector2(cx, y))
	y += eh + 6.0
	var k := bh / BAND_H
	_band.size = Vector2(w, BAND_H)
	_band.pivot_offset = Vector2(w / 2.0, 0.0)
	_band.scale = Vector2(k, k)
	_band.position = Vector2(0.0, y)
	_band_top = y
	_band_bottom = y + bh
	y += bh + 10.0
	_crest.size = Vector2(CREST, CREST)
	_base(_crest, Vector2((w - CREST) / 2.0, y))
	y += CREST + 4.0
	_base(_premiers, Vector2(cx, y))
	y += ph
	_base(_club, Vector2(cx, y))
	y += nh + 12.0
	for l in _callouts:
		_base(l, Vector2(cx, y))
		y += l.size.y + 6.0
	# The cup and the flag side by side, tops level (the pennant hangs from its
	# rod): the cup's picture is 160 wide in its 200 slot, the flag's 127.5 in
	# its 170, 16 apart.
	var left := (w - 303.5) / 2.0
	_base(_trophy, Vector2(left - 20.0, 18.0))
	_base(_flag, Vector2(left + 154.75, 21.0))
	_apply_stripes()
	_sweep.queue_redraw()


func _fit(l: Label, cw: float) -> float:
	l.size = Vector2(cw, 0.0)
	l.size = Vector2(cw, l.get_minimum_size().y)
	return l.size.y


## A piece's place at rest; its lift (meta "_pc_dy") moves it from there.
func _base(c: Control, p: Vector2) -> void:
	c.set_meta("_pc_base", p)
	c.pivot_offset = c.size / 2.0
	_apply(c)


## Not laid out yet (no base): leave it, or each lift would add to the last.
func _apply(c: Control) -> void:
	if not c.has_meta("_pc_base"):
		return
	var b: Vector2 = c.get_meta("_pc_base")
	var dy: float = float(c.get_meta("_pc_dy")) if c.has_meta("_pc_dy") else 0.0
	c.position = b + Vector2(0.0, dy)


func _dy(c: Control, v: float) -> void:
	if not is_instance_valid(c):
		return
	c.set_meta("_pc_dy", v)
	_apply(c)


func _dy_setter(c: Control) -> Callable:
	return func(v: float) -> void: _dy(c, v)


# --- The stage's own layers -------------------------------------------------
func _apply_stripes() -> void:
	if _mat == null:
		return
	var h := size.y
	_mat.set_shader_parameter("area", size)
	_mat.set_shader_parameter("run", h * RUN)
	_mat.set_shader_parameter("top", lerpf(0.0, _band_top, _settle_k))
	_mat.set_shader_parameter("bottom", lerpf(h, _band_bottom, _settle_k))
	_mat.set_shader_parameter("wipe", _wipe_s)


## Full screen (0) into the band behind the cup (1).
func _set_settle(k: float) -> void:
	_settle_k = k
	_apply_stripes()


## The light: its middle at `s` across the lean; the stripes are
## uncovered behind it and the crest comes up as it passes.
func _set_sweep(s: float) -> void:
	_sweep_c = s
	_wipe_s = s
	_apply_stripes()
	_sweep.queue_redraw()
	if not _crest_lit:
		var mid := _crest.position + _crest.size / 2.0
		if s >= mid.x + size.y * RUN * mid.y / maxf(1.0, size.y):
			_crest_lit = true
			var tw := _tw()
			tw.tween_property(_crest, "modulate:a", 1.0, UiKit.Motion.DUR_BASE) \
					.set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE)


func _draw_sweep() -> void:
	if not _sweeping:
		return
	var h := size.y
	var run := h * RUN
	var c := Color(UiKit.club_ink(_premier), SWEEP_PEAK)
	var none := Color(c, 0.0)
	for side in [-1.0, 1.0]:
		var s1: float = _sweep_c + side * SWEEP_W / 2.0
		_sweep.draw_polygon(
				PackedVector2Array([Vector2(_sweep_c, 0), Vector2(s1, 0), Vector2(s1 - run, h), Vector2(_sweep_c - run, h)]),
				PackedColorArray([c, none, none, c]))


func _set_flash(a: float) -> void:
	_flash_a = a
	_flash.queue_redraw()


func _draw_flash() -> void:
	if _flash_a <= 0.001:
		return
	_flash.draw_rect(Rect2(Vector2.ZERO, size), Color(UiKit.club_ink(_premier), _flash_a))


## The ribbons from the art's grey (0) to the club's colours (1).
func _set_tint(k: float) -> void:
	if _tint == null:
		return
	var cols := GameDB.club_colours(_premier)
	_tint.set_shader_parameter("primary", GREY.lerp(cols[0], k))
	_tint.set_shader_parameter("secondary", GREY.lerp(cols[1], k))


# --- The run ----------------------------------------------------------------
func _start() -> void:
	at_rest = false
	if not UiKit.motion_on():
		_rest()
		Feel.press("land")
		return
	_prime()
	if _siren:
		_sound("siren", "crowd_siren.wav", SIREN_DB)
	_beats()


## Everything at its start: nothing on the stage yet.
func _prime() -> void:
	_page.modulate.a = 0.0
	_wipe_s = -SW
	_settle_k = 0.0
	_sweeping = false
	_crest_lit = false
	_flash_a = 0.0
	_content.position.x = 0.0
	for c in _items():
		(c as Control).modulate.a = 0.0
		(c as Control).scale = Vector2.ONE
		_dy(c, 0.0)
	if _flag_art != null:
		_flag_art.scale = Vector2.ONE
	if _year != null:
		_year.modulate.a = 0.0
		_year.scale = Vector2.ONE
	_set_tint(0.0)
	_apply_stripes()
	_sweep.queue_redraw()
	_flash.queue_redraw()


## The final frame, at once.
func _rest() -> void:
	_kill()
	_page.modulate.a = 1.0
	_wipe_s = 1e6
	_settle_k = 1.0
	_sweeping = false
	_crest_lit = true
	_flash_a = 0.0
	_content.position.x = 0.0
	for c in _items():
		(c as Control).modulate.a = 1.0
		(c as Control).scale = Vector2.ONE
		_dy(c, 0.0)
	if _flag_art != null:
		_flag_art.scale = Vector2.ONE
	if _year != null:
		_year.modulate.a = 1.0
		_year.scale = Vector2.ONE
	_set_tint(1.0)
	_apply_stripes()
	_sweep.queue_redraw()
	_flash.queue_redraw()
	if is_instance_valid(_streamers):
		_streamers.queue_free()
	_streamers = null
	_restore()
	at_rest = true


## A tap anywhere but Continue (director, 2026-11-25): every tween stops, every
## piece takes its final place, the streamers stop, and it waits for Continue.
func jump_to_rest() -> void:
	if _left:
		return
	Feel.moved.append("pc_rest")
	_rest()


## Continue and Android Back: the ceremony goes and full time comes up.
func finish_now() -> void:
	if _left:
		return
	_left = true
	_kill()
	_restore()
	Feel.moved.append("pc_leave")
	done.emit()
	queue_free()


func _exit_tree() -> void:
	_kill()
	_restore()


## The scorebug back to its size.
func _restore() -> void:
	for l in _pulse:
		if is_instance_valid(l) and l is Control:
			(l as Control).scale = Vector2.ONE


func _gui_input(event: InputEvent) -> void:
	var mb := event as InputEventMouseButton
	if mb != null and mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
		accept_event()
		jump_to_rest()


# --- Beats ------------------------------------------------------------------
func _kill() -> void:
	for tw in _tweens:
		if tw != null and tw.is_valid():
			tw.kill()
	_tweens.clear()


## Run `f` at `t` seconds from the siren.
func _at(t: float, f: Callable) -> void:
	var tw := create_tween()
	_tweens.append(tw)
	if t > 0.0:
		tw.tween_interval(t)
	tw.tween_callback(f)


func _tw(parallel := true) -> Tween:
	var tw := create_tween()
	if parallel:
		tw.set_parallel(true)
	_tweens.append(tw)
	return tw


func _settled() -> void:
	at_rest = true
	Feel.moved.append("pc_settled")


func _settle_in(secs: float) -> void:
	Feel.moved.append("pc_settle")
	_tw().tween_method(_set_settle, 0.0, 1.0, secs).set_trans(UiKit.Motion.TRANS_IN).set_ease(Tween.EASE_IN_OUT)


## Fade in, rising `by` px into place.
func _rise(c: Control, by: float, secs := UiKit.Motion.DUR_BASE) -> void:
	_dy(c, by)
	var tw := _tw()
	tw.tween_method(_dy_setter(c), by, 0.0, secs).set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE)
	tw.tween_property(c, "modulate:a", 1.0, secs).set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE)


## Fade in, growing from `from` to its size.
func _grow(c: Control, from: float, secs: float, by := 0.0) -> void:
	c.scale = Vector2.ONE * from
	_dy(c, by)
	var tw := _tw()
	tw.tween_property(c, "scale", Vector2.ONE, secs).set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE)
	tw.tween_property(c, "modulate:a", 1.0, secs).set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE)
	if by != 0.0:
		tw.tween_method(_dy_setter(c), by, 0.0, secs).set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE)


## The stamp: from LAND_FROM down to its size with the one overshoot.
func _stamp(c: Control, secs: float) -> void:
	c.scale = Vector2.ONE * UiKit.Motion.LAND_FROM
	_dy(c, 0.0)
	var tw := _tw()
	tw.tween_property(c, "scale", Vector2.ONE, secs).set_trans(UiKit.Motion.TRANS_STAMP).set_ease(UiKit.Motion.EASE_STAMP)
	tw.tween_property(c, "modulate:a", 1.0, UiKit.Motion.DUR_LAND_FADE).set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)


## The impact: the sting and its buzz, the club's flash, the shake.
func _impact() -> void:
	Feel.press("land")
	Feel.moved.append("pc_flash")
	var tw := _tw(false)
	tw.tween_method(_set_flash, 0.0, FullTimeMotion.FLASH_PEAK, FullTimeMotion.DUR_FLASH_IN) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)
	tw.tween_method(_set_flash, FullTimeMotion.FLASH_PEAK, 0.0, FullTimeMotion.DUR_FLASH_OUT) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)
	if not GameState.screen_shake_on():
		return
	Feel.moved.append("pc_shake")
	var sh := _tw(false)
	var step := FullTimeMotion.DUR_SHAKE / float(FullTimeMotion.SHAKE.size())
	for dx in FullTimeMotion.SHAKE:
		sh.tween_property(_content, "position:x", float(dx), step) \
				.set_trans(UiKit.Motion.TRANS_PULSE).set_ease(Tween.EASE_IN_OUT)


func _streamers_now() -> void:
	var s := PremiershipStreamers.play_over(self, _premier, _continue)
	if s == null:
		return
	move_child(s, _continue.get_index())
	_streamers = s
	Feel.moved.append("pc_streamers")


## A sound of the crowd's own (CrowdSound's files and bus), kept by the host so
## it plays on after Continue.
func _sound(kind: String, file: String, db: float) -> void:
	var s := load(CrowdSound.DIR + file) as AudioStream
	var host := get_parent()
	if s == null or host == null:
		return
	var p := AudioStreamPlayer.new()
	p.name = "Ceremony_" + kind
	p.bus = AudioLevels.bus(AudioLevels.CROWD)
	p.stream = s
	p.volume_db = db
	host.add_child(p)
	p.finished.connect(p.queue_free)
	p.play()
	heard.append(kind)


func _roar() -> void:
	_sound("roar", "crowd_goal.wav", ROAR_DB)


# --- The beats, in seconds from the siren: the light leads ------------------
func _beats() -> void:
	_at(0.0, func() -> void:
		_beat_scorebug()
		_tw().tween_property(_page, "modulate:a", 1.0, DUR_PAGE).set_trans(UiKit.Motion.TRANS_IN).set_ease(Tween.EASE_IN_OUT))
	_at(1.20, func() -> void:
		_roar()
		Feel.moved.append("pc_sweep")
		_sweeping = true
		var tw := _tw(false)
		tw.tween_method(_set_sweep, -SWEEP_W / 2.0, size.x + size.y * RUN + SWEEP_W / 2.0, UiKit.Motion.DUR_MILESTONE) \
				.set_trans(UiKit.Motion.TRANS_IN).set_ease(Tween.EASE_IN_OUT)
		tw.tween_callback(func() -> void:
			_sweeping = false
			_wipe_s = 1e6
			_apply_stripes()
			_sweep.queue_redraw()))
	_at(2.10, func() -> void:
		_settle_in(UiKit.Motion.DUR_BASE)
		_grow(_trophy, 0.92, UiKit.Motion.DUR_MILESTONE, 24.0))
	_at(2.60, func() -> void:
		Feel.moved.append("pc_tint")
		_tw().tween_method(_set_tint, 0.0, 1.0, UiKit.Motion.DUR_BASE).set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE))
	_at(2.90, func() -> void:
		Feel.moved.append("pc_unfurl")
		_flag.modulate.a = 1.0
		if _flag_art != null:
			_flag_art.scale = Vector2(1.0, 0.0)
			_tw().tween_property(_flag_art, "scale:y", 1.0, UiKit.Motion.DUR_HERO).set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE))
	_at(3.40, func() -> void:
		if _year != null:
			Feel.press("tick")
			_stamp(_year, UiKit.Motion.DUR_FAST))
	_at(3.70, func() -> void: _stamp(_premiers, UiKit.Motion.DUR_BASE))
	_at(3.80, func() -> void:
		_impact()
		_streamers_now())
	_at(4.10, func() -> void:
		_rise(_club, UiKit.Motion.RISE)
		_rise(_eyebrow, UiKit.Motion.RISE))
	var end := 4.10 + UiKit.Motion.DUR_BASE
	for i in range(_callouts.size()):
		var l: Label = _callouts[i]
		var t := 4.60 + 0.45 * i
		_at(t, func() -> void:
			Feel.press("tick")
			_rise(l, UiKit.Motion.RISE))
		end = t + UiKit.Motion.DUR_BASE
	_at(end, _settled)


## The scorebug's score beats once, 1.0 -> 1.06 -> 1.0.
func _beat_scorebug() -> void:
	Feel.moved.append("pc_pulse")
	for l in _pulse:
		if not is_instance_valid(l) or not (l is Control):
			continue
		var c := l as Control
		c.pivot_offset = c.size / 2.0
		var tw := _tw(false)
		tw.tween_property(c, "scale", Vector2.ONE * PULSE, DUR_PULSE).set_trans(UiKit.Motion.TRANS_PULSE).set_ease(Tween.EASE_IN_OUT)
		tw.tween_property(c, "scale", Vector2.ONE, DUR_PULSE).set_trans(UiKit.Motion.TRANS_PULSE).set_ease(Tween.EASE_IN_OUT)
