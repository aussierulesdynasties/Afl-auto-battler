extends Control
## After the Fitzroy merger your list is over the era's spots: you pick who
## goes (director 2026-11-15: "I pick, delist screen"). Rival clubs cut by
## their own rule (GameState._era_trim_rivals). The hub opens this screen until
## the list fits; a career that reaches Round 1 without it has the club delist
## the rest by that rule (GameState._merger_cut_by_club).

var _root: VBoxContainer
var _going: Array = []   # ids you marked to go
var _notice := ""


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if GameState.season == null:
		Router.replace("main")
		return
	# Your club's colour behind the page, as on the hub and match day.
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)
	_root = UiKit.vbox(8)
	margin.add_child(_root)
	get_viewport().size_changed.connect(func():
		if is_inside_tree() and not UiKit.keyboard_resize(self):
			_build())
	_build()


func _list() -> Array:
	return GameState.season.lists.get(GameState.my_club, GameState.my_list)


func _player(id: String) -> Dictionary:
	for p in _list():
		if str(p["id"]) == id:
			return p
	return {}


## Marked to go, per list kind ("" senior, "A" Category A rookie).
func _picked(kind: String) -> int:
	var n := 0
	for id in _going:
		if str(_player(id).get("rookie_list", "")) == kind:
			n += 1
	return n


func _build() -> void:
	if not is_inside_tree():
		return
	UiKit.clear(_root)
	# No way round it: Back leaves for the title, as the hub's does.
	_root.add_child(UiKit.top_bar("After the merger", false))
	var needs := GameState.merger_cut_needs()
	var body := UiKit.vbox(6)
	body.name = "MergerRows"
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(_hero())
	body.add_child(_lead(needs))
	if _notice != "":
		var n := _para(_notice, UiKit.SECONDARY, UiKit.BAD)
		n.name = "MergerNotice"
		body.add_child(n)
	for kind in needs:
		var head := UiKit.lbl(("Senior list" if kind == "" else "Category A rookies") + "  (%d to go)" % int(needs[kind]),
				UiKit.H2, UiKit.EMPH, true)
		head.name = "MergerHead_" + ("senior" if kind == "" else "rookie")
		body.add_child(UiKit.spacer(4))
		body.add_child(head)
		var rows := _list().filter(func(q): return str(q.get("rookie_list", "")) == kind)
		rows.sort_custom(func(a, b):
			if int(Rating.ovr(a, 0)) != int(Rating.ovr(b, 0)):
				return int(Rating.ovr(a, 0)) > int(Rating.ovr(b, 0))
			return str(a["id"]) < str(b["id"]))
		var full := _picked(kind) >= int(needs[kind])
		for p in rows:
			body.add_child(_row(p, full))
	_root.add_child(UiKit.scroll(body))
	_root.add_child(_footer(needs))


## The one figure the screen is about: how many are still to go.
func _hero() -> Control:
	var left := maxi(0, GameState.merger_cut_left() - _going.size())
	var h := UiKit.hbox(12)
	h.name = "MergerLeft"
	h.add_child(UiKit.club_marker(GameState.my_club, 36.0))
	var fig := UiKit.figure(str(left), UiKit.HERO, UiKit.club_vivid(GameState.my_club))
	fig.name = "LeftFigure"
	h.add_child(fig)
	var v := UiKit.vbox(0)
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_child(UiKit.lbl("still to pick" if left > 0 else "picked: confirm below", UiKit.NAME, UiKit.TEXT, true))
	v.add_child(UiKit.lbl("of %d to delist" % GameState.merger_cut_left(), UiKit.SECONDARY, UiKit.MUTED))
	h.add_child(v)
	return h


func _lead(needs: Dictionary) -> Control:
	var list := _list()
	var from_fit := list.filter(func(q): return str(q.get("merged_from", "")) != "").size()
	var text := "%d of %s's players have joined our list. A club can list %d senior players in %d, and we have %d." % [
			from_fit, GameDB.club_name(LegacyRollover.MERGED),
			RookieList.senior_spots(), GameState.season_year, RookieList.senior_count(list)]
	if needs.has("A"):
		text += " We have %d Category A rookies for %d spots." % [RookieList.cat_a_count(list), RookieList.cat_a_spots()]
	text += " The ones we delist are free to sign with any club."
	var l := _para(text, UiKit.BODY, UiKit.TEXT)
	l.name = "MergerLead"
	return l


## One player: who he is, which side he came from, and Delist or Keep.
func _row(p: Dictionary, full: bool) -> Control:
	var id := str(p["id"])
	var marked := _going.has(id)
	var card := PanelContainer.new()
	card.name = "MergerRow_" + id
	var quiet := UiKit.style(Color.TRANSPARENT, 8, 0)
	quiet.set_border_width_all(0)
	quiet.border_width_bottom = 1
	quiet.border_color = UiKit.LINE
	quiet.content_margin_top = 8
	quiet.content_margin_bottom = 8
	card.add_theme_stylebox_override("panel", quiet)
	var v := UiKit.vbox(3)
	card.add_child(v)
	var top := UiKit.hbox(8)
	v.add_child(top)
	var info := UiKit.vbox(2)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(info)
	# The name gets the row's full width; the role and the side sit under it.
	var who := UiKit.ellipsis(GameDB.player_display_name(p), UiKit.NAME, UiKit.BAD if marked else UiKit.TEXT, true)
	who.name = "PlayerName_" + id
	info.add_child(NameLink.tappable(who, id))
	var h := UiKit.hbox(8)
	info.add_child(h)
	h.add_child(UiKit.role_chip(Ratings.role_tag(p)))
	# Which side he came from, in that club's colour: the merger's two halves.
	var side := str(p.get("merged_from", GameState.my_club))
	var from := UiKit.lbl(("From " if side != GameState.my_club else "") + GameDB.club_name(side),
			UiKit.FINE, UiKit.club_ink(side), true)
	from.name = "From"
	from.autowrap_mode = TextServer.AUTOWRAP_OFF
	from.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(from)
	var left := int(p.get("contract_years", 1))
	# Two lines, broken at a fixed place, so no line ends or starts with a "·".
	info.add_child(UiKit.lbl("%d OVR  ·  %d POT  ·  age %d" % [
			int(Rating.ovr(p, 0)), int(p.get("potential", Rating.ovr(p, 0))), int(p.get("age", 0))],
			UiKit.SECONDARY, UiKit.MUTED))
	info.add_child(UiKit.lbl("%s  ·  %s" % [
			"%d season%s left" % [left, "" if left == 1 else "s"] if left > 0 else "out of contract",
			Contracts.money(int(p.get("salary", 0)))], UiKit.SECONDARY, UiKit.MUTED))
	info.add_child(PlayerSheet.top_three(p, UiKit.FINE, true))
	if ListStings.release_held(p, GameState.season_year):
		var held := _para(ListCosts.HELD_LINE, UiKit.FINE, UiKit.TEXT)
		held.name = "ReleaseHeld"
		v.add_child(held)
		return card
	var act := UiKit.btn("Keep" if marked else "Delist", UiKit.NAME)
	act.name = "Keep" if marked else "Delist"
	act.custom_minimum_size = Vector2(96, 44)
	act.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	act.disabled = not marked and full
	act.pressed.connect(func():
		_notice = ""
		if marked:
			_going.erase(id)
		else:
			_going.append(id)
		_build())
	top.add_child(act)
	if marked:
		# The gate's two sides, as every delisting states them.
		# The club's voice: we and our (ruling 38); "you" is only the coach.
		v.add_child(UiKit.stake_row(GateOdds.gain(ListCosts.RELEASE_GAIN % Contracts.money(int(p.get("salary", 0)))), "DelistGain"))
		v.add_child(UiKit.stake_row(GateOdds.cost("%s leaves us for nothing, free for any club to sign" % GameDB.player_display_name(p)), "DelistCost"))
	return card


func _footer(needs: Dictionary) -> Control:
	var ready := not needs.is_empty()
	for kind in needs:
		if _picked(kind) != int(needs[kind]):
			ready = false
	var go := UiKit.btn("Delist %d player%s" % [_going.size(), "" if _going.size() == 1 else "s"] if ready \
			else "Pick %d more" % maxi(0, GameState.merger_cut_left() - _going.size()), UiKit.NAME, true)
	go.name = "ConfirmCut"
	go.custom_minimum_size.y = 52
	go.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	go.disabled = not ready
	go.pressed.connect(_confirm)
	return go


func _confirm() -> void:
	var out := GameState.merger_delist(_going)
	if not bool(out["ok"]):
		_notice = str(out["reason"])
		_build()
		return
	GameState.autosave()
	Router.replace("hub")


func _para(text: String, size: int, colour: Color) -> Label:
	var l := UiKit.lbl(text, size, colour)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


## Back leaves for the title, as from the hub: the cut waits for your return.
func handle_back() -> bool:
	Router.to_main_menu(false)
	return true
