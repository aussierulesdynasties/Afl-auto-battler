class_name RookieDraftSheet
extends RefCounted
## The Rookie Draft, your turn (row 88): the best eight left, Pick or Pass.
## Shown over the pre-season screen (or the hub when there is no pre-season).
## Starting the pre-season week (over the hub: the next round) without picking
## passes it; the host names that action in `pass_line`. Back closes the sheet
## and leaves the pick open.

const NAME := "RookieDraft"
const SHOWN := 8
const PASS_PRESEASON := "Starting the pre-season week without picking passes it."
const PASS_HUB := "Starting the next round without picking passes it."


## Open the sheet over `host` if the Rookie Draft waits on you. `on_done`
## runs once the sheet closes for good (your draft over, or Back).
static func open(host: Control, on_done: Callable, pass_line := PASS_PRESEASON) -> Control:
	if not RookieList.waiting(GameState):
		return null
	var old := host.get_node_or_null(NAME)
	if old != null and is_instance_valid(old) and not old.is_queued_for_deletion():
		return old
	var box := UiKit.modal_box(host, 560.0, 0.0)
	var overlay: Control = box["overlay"]
	overlay.name = NAME
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.heading("Rookie Draft", UiKit.TITLE))
	var list: Array = GameState.my_list
	var year := GameState.season_year
	var note := UiKit.lbl(("Round %d, your pick. Rookie list %d / %d. A rookie is paid the rookie wage, %s a season: " +
			"two seasons for a player under 21, one for anyone older. " +
			"Pass and your Rookie Draft is over. %s") % [
			RookieList.round_now(GameState), RookieList.rookie_count(list), RookieList.CAT_A_SPOTS,
			Contracts.money(RookieList.wage(year)), pass_line], 15, UiKit.TEXT)
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(note)
	var shown := MidseasonDraft.pool(GameState).slice(0, SHOWN)
	if shown.is_empty():
		v.add_child(UiKit.lbl("Nobody is left to take.", 15, UiKit.TEXT))
	for p in shown:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 12)
		var txt := UiKit.lbl("%s  %d\n%s, %d, %s" % [GameDB.player_display_name(p), int(p.get("overall", 0)),
				DraftNight.position_words(p), int(p.get("age", 0)), MidseasonDraft.from_word(GameState, p)], 14, UiKit.TEXT)
		txt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		txt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		row.add_child(txt)
		var pick := UiKit.btn("Pick", UiKit.NAME)
		pick.name = "RookiePick_%s" % str(p["id"])
		pick.custom_minimum_size = Vector2(88, 48)
		# Your challenge bars him (Youth only): said on the button, not hidden.
		if Challenge.block_reason(GameState, p) != "":
			pick.text = "Over %d" % Challenge.MAX_AGE if Challenge.over_age(p) else "Barred"
			pick.disabled = true
			pick.tooltip_text = Challenge.block_reason(GameState, p)
		pick.pressed.connect(_choose.bind(host, overlay, str(p["id"]), on_done, pass_line))
		row.add_child(pick)
		v.add_child(row)
	var pass_btn := UiKit.btn("Pass", UiKit.NAME, true)
	pass_btn.name = "RookiePass"
	pass_btn.custom_minimum_size = Vector2(0, 48)
	pass_btn.pressed.connect(_choose.bind(host, overlay, "", on_done, pass_line))
	(box["footer"] as VBoxContainer).add_child(pass_btn)
	return overlay


## Back: close the sheet, the pick stays open.
static func close_open(host: Control) -> bool:
	var s := host.get_node_or_null(NAME)
	if s == null or not is_instance_valid(s) or s.is_queued_for_deletion():
		return false
	s.queue_free()
	return true


static func _choose(host: Control, overlay: Control, player_id: String, on_done: Callable, pass_line: String) -> void:
	RookieList.choose(GameState, player_id)
	GameState.autosave()
	if is_instance_valid(overlay):
		overlay.name = NAME + "Closed"
		overlay.queue_free()
	# Your next pick in a later round opens straight away.
	if RookieList.waiting(GameState) and is_instance_valid(host):
		open(host, on_done, pass_line)
	elif on_done.is_valid():
		on_done.call()
