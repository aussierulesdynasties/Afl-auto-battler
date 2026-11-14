extends SceneTree
## godot --headless --path . --script tests/run_nameink_tests.gd
## A player's name in running text wears his club's colour (director,
## 2026-10-14: "Josh Worrell is roaming the backline" has to show whose side he
## is on without "(Giants)"). NameInk's index, the markup it makes, every club's
## ink readable on the dark page, and the match screen's talk carrying both
## clubs' colours.

var NI
var UK
const NB := "\u00A0"  # a name's spaces in the text drawn (NameInk.NBSP)
var _state: Node
var _db: Node
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle(n := 6) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	await process_frame
	NI = load("res://scripts/ui/NameInk.gd")
	UK = load("res://scripts/ui/UiKit.gd")
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://test_nameink.save"
	_state.settings_path = "user://test_nameink.cfg"
	# Return visits: the first-visit intros (FirstVisitIntro.gd) have their own suite.
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.delete_saved_career()
	_t("_test_helper")
	_t("_test_tinted_ink")
	_t("_test_club_names")
	_t("_test_red_club_players")
	await _t("_test_match_screen")
	print(Ran.line("Name colour", self))
	quit(0 if _failures.is_empty() else 1)


func _html(club: String) -> String:
	return NI.player_ink(club).to_html(false)


func _test_helper() -> void:
	var idx: Dictionary = NI.from_clubs(["FRE", "GWS"])
	var fre: Dictionary = _db.club_list("FRE")[0]
	var gws: Dictionary = _db.club_list("GWS")[0]
	var fre_name: String = _db.player_display_name(fre)
	var gws_name: String = _db.player_display_name(gws)
	_check(str(idx.get(fre_name, "")) == "FRE" and str(idx.get(gws_name, "")) == "GWS",
			"The index knows each player's club from his record (%s, %s)" % [fre_name, gws_name])
	var line := "%s is roaming loose behind the ball, %s's man [on him]." % [fre_name, gws_name]
	var bb: String = NI.markup(line, idx)
	_check(bb.contains("[color=#%s]%s[/color]" % [_html("FRE"), fre_name.replace(" ", NB)]),
			"The Fremantle player's name carries Fremantle's ink")
	_check(bb.contains("[color=#%s]%s[/color]" % [_html("GWS"), gws_name.replace(" ", NB)]),
			"The Giants player's name carries the Giants' ink")
	_check(bb.contains("[lb]on him[rb]") and not bb.contains("[on him]"),
			"Square brackets in the words are escaped, never read as tags")
	_check(NI.markup("Scores level.", idx) == "", "A line naming no one is left alone")
	var clash: Dictionary = NI.from_squads([[{"name": "Sam Day", "generic_name": "Sam Day"}], [{"name": "Sam Day", "generic_name": "Sam Day"}]], ["FRE", "GWS"])
	_check(not clash.has("Sam Day"), "A name two clubs both carry is not guessed at")
	var one: Dictionary = NI.from_squads([[{"name": "Sam Worrell", "generic_name": "Sam Worrell"}]], ["GWS"])
	_check(NI.spans_in("Worrell took it. Not Worrellson.", one).size() == 1,
			"A surname alone is tinted, a longer word is not")
	var lbl: Control = NI.label(line, idx, UK.BODY, UK.TEXT)
	_check(lbl is RichTextLabel and NI.plain(lbl) == line, "A tinted line is a RichTextLabel that still carries its words")
	_check(NI.label("Scores level.", idx) is Label, "A line with no names stays a plain Label")
	var rich: RichTextLabel = lbl as RichTextLabel
	_check(rich.fit_content and rich.mouse_filter == Control.MOUSE_FILTER_IGNORE and not rich.scroll_active,
			"A tinted line takes up its own height and lets swipes through")
	lbl.free()
	var btn := Button.new()
	btn.text = "%s on %s" % [fre_name, gws_name]
	root.add_child(btn)
	NI.dress_button(btn, idx)
	var found := btn.find_children("*", "RichTextLabel", true, false)
	var over: RichTextLabel = found[0] as RichTextLabel if not found.is_empty() else null
	_check(btn.text == "%s on %s" % [fre_name, gws_name] and over != null
			and over.text.contains("[color=#%s]%s[/color]" % [_html("GWS"), gws_name.replace(" ", NB)]),
			"A button naming two players keeps its words and draws each in his club's ink")
	_check(btn.get_theme_color("font_color").a == 0.0, "The button's own text is made clear under the tinted copy")
	var plain_btn := Button.new()
	plain_btn.text = "Close"
	NI.dress_button(plain_btn, idx)
	_check(plain_btn.get_child_count() == 0, "A button naming no one is left alone")
	btn.free()
	plain_btn.free()
	var live: RichTextLabel = NI.rich(UK.BODY, UK.TEXT, true, false)
	NI.set_line(live, "%s on %s" % [fre_name, gws_name], idx)
	_check(live.text.contains(_html("FRE")) and NI.plain(live) == "%s on %s" % [fre_name, gws_name],
			"A line whose words change is set again with each name in its club's ink")
	live.free()
	# Every club's ink reads on the dark page, so no name is lost on it.
	var worst := 99.0
	var worst_club := ""
	for c in _db.club_order:
		var ratio: float = UK.contrast(UK.club_ink(str(c)), UK.BG)
		if ratio < worst:
			worst = ratio
			worst_club = str(c)
	_check(worst >= 4.5, "Every club's ink reads on the dark page (lowest %.1f, %s)" % [worst, worst_club])
	_check(UK.club_ink("ADE").to_html(false).to_upper() == "FFC83A",
			"Adelaide's name ink is the Crows' gold, not a red that reads as Melbourne or Essendon (director, 2026-10-14)")


## Club ink on a club-tinted panel (row 109, 6.Q18): the news lead's panel, a
## training card and a sheet's wash carry a share of a club's colour, and any
## club's ink on any of them reads at 4.5:1 or better, both inks, every pairing
## (a home wash can carry the away side's names).
## Every club's name in running text wears a colour of its own (director
## 2026-11-06, rulings 51a): its strongest real colour, never white, read at
## 4.5:1 on the page and a panel. Essendon, St Kilda and Melbourne are red.
## A black-and-white club (Collingwood) reads plain white (director
## 2026-11-07, "white").
func _test_club_names() -> void:
	var idx: Dictionary = NI.from_clubs([])
	var whites := []
	for code in _db.clubs:
		var name: String = _db.club_name(str(code))
		var m: String = NI.markup("A win against %s." % name, idx)
		var want: Color = load("res://scripts/ui/ClubLink.gd").colour(str(code))
		if not m.contains("[color=#%s]" % want.to_html(false)):
			whites.append("%s (%s)" % [name, m])
			continue
		if UK.club_is_black(str(code)):
			if not want.is_equal_approx(UK.TEXT):
				whites.append("%s not white #%s" % [name, want.to_html(false)])
			continue
		if want.is_equal_approx(UK.TEXT) or (want.v > 0.9 and want.s < 0.15) 				or UK.contrast(want, UK.BG) < 4.5 or UK.contrast(want, UK.PANEL) < 4.5:
			whites.append("%s #%s" % [name, want.to_html(false)])
	_check(whites.is_empty(), "Every club's name is in its strongest real colour, never white (%s)" % ", ".join(whites))
	var ess: Color = load("res://scripts/ui/ClubLink.gd").colour("ESS")
	_check(ess.s > 0.4 and (ess.h < 0.06 or ess.h > 0.92), "Essendon's name is red, not white (#%s)" % ess.to_html(false))


## A player at a red club wears its red, as its name does (row 174, director
## 2026-11-12, "sanders uncoloured?": an Essendon player drawn white beside a
## red "Essendon"). Every club in turn: his name is in the club's ink, never the
## plain text white (a black-and-white club, Collingwood, reads white as its ink is).
func _test_red_club_players() -> void:
	var bad := []
	var reds := 0
	for code in _db.clubs:
		var c := str(code)
		var squad: Array = _db.club_list(c)
		if squad.is_empty():
			continue
		var who: String = _db.player_display_name(squad[0])
		var m: String = NI.markup("%s kicked two." % who, NI.from_clubs([c]))
		var want: Color = UK.club_ink(c)
		if not m.contains("[color=#%s]%s" % [want.to_html(false), who.replace(" ", NB)]):
			bad.append("%s %s" % [c, m])
		if UK.club_name_colour(want) == UK.TEXT and not UK.club_is_black(c):
			reds += 1
			if m.contains("[color=#%s]" % UK.TEXT.to_html(false)):
				bad.append("%s drawn white" % c)
	_check(bad.is_empty() and reds >= 5, "Every club's player is in its ink, the %d red clubs' players red, never white (%s)" % [reds, ", ".join(bad)])


func _test_tinted_ink() -> void:
	var clubs: Array = _db.club_order
	_check(clubs.size() >= 18, "Every club is in the loop (%d)" % clubs.size())
	var kinds: Array = UK.TINT_SHARE.keys()
	_check(kinds.size() == 3, "Three tinted panel kinds: the news lead, a training card, a sheet's wash")
	for kind in kinds:
		var worst := 99.0
		var worst_pair := ""
		var under_old := 0
		for tint_club in clubs:
			var surface: Color = UK.tinted(str(kind), UK.club_ink(str(tint_club)))
			for code in clubs:
				for which in 2:
					var ink: Color = UK.club_ink(str(code), surface) if which == 0 							else UK.club_ink_second(str(code), surface)
					var ratio: float = UK.contrast(ink, surface)
					if ratio < worst:
						worst = ratio
						worst_pair = "%s ink %d on %s" % [code, which + 1, tint_club]
					var hand: Color = UK.club_ink(str(code)) if which == 0 else UK.club_ink_second(str(code))
					if UK.contrast(hand, surface) < 4.5:
						under_old += 1
		_check(worst >= 4.5, "Every club's ink reads at 4.5:1 on a %s tinted panel (lowest %.2f, %s)" % [kind, worst, worst_pair])
		# The check has teeth: the hand-picked inks as they were drawn before
		# (not lifted for the surface) fall under 4.5:1 here.
		_check(under_old > 0, "The unlifted inks fall short on a %s panel (%d pairs), so the lift is what passes" % [kind, under_old])
	# The lift keeps the club's hue: Melbourne's red on its own lead panel stays red.
	var mel_surface: Color = UK.tinted("story", UK.club_ink("MEL"))
	var mel: Color = UK.club_ink("MEL", mel_surface)
	_check(absf(mel.h - UK.club_ink("MEL").h) < 0.02 and mel.s > 0.5,
			"A lifted ink keeps its club's hue (Melbourne %s)" % mel.to_html(false))
	# The screens draw these surfaces, not their own mix.
	var NF = load("res://scripts/ui/NewsFront.gd")
	_check((NF._wash("NTH") as Color).is_equal_approx(UK.tinted("story", UK.club_ink("NTH"))),
			"The news lead's panel is the shared story tint")
	var TS = load("res://scripts/ui/TrainingScene.gd")
	var card: StyleBoxFlat = TS._card_style(false, UK.club_ink("CAR"))
	_check(card.bg_color.is_equal_approx(UK.tinted("card", UK.club_ink("CAR"))),
			"A training card's surface is the shared card tint")


func _test_match_screen() -> void:
	_state.reset()
	_state.replay_seed = 2027
	root.size = Vector2i(390, 844)
	_state.start_season("FRE", _db.club_list("FRE"))
	_check(_state.prepare_interactive_match(), "A live match is prepared")
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _settle()
	var sim = _state.pending_sim
	var home := str(_state.pending_match["home"])
	var away := str(_state.pending_match["away"])
	var a: Dictionary = sim.squads[0].ground[0]
	var b: Dictionary = sim.squads[1].ground[0]
	var an: String = _db.player_display_name(a)
	var bn: String = _db.player_display_name(b)
	m.call("_feed_text", "Q2 9'  Coach's call: Take the shot - GOAL to %s! %s was beaten." % [an, bn],
			UK.TEXT, false, "PlayLine")
	await _settle()
	var feed: Node = m.get("_feed")
	var row: Control = feed.get_child(feed.get_child_count() - 1)
	var text := ""
	if row is RichTextLabel:
		text = (row as RichTextLabel).text
	_check(row is RichTextLabel and text.contains("[color=#%s]%s[/color]" % [_html(home), an.replace(" ", NB)]),
			"A feed line colours the %s player in %s's ink" % [home, home])
	_check(text.contains("[color=#%s]%s[/color]" % [_html(away), bn.replace(" ", NB)]),
			"... and the %s player in %s's ink in the same line" % [away, away])
	_check(NI.plain(row).contains("GOAL to " + an), "The words of the line are unchanged")
	var goal: Control = m.call("_goal_row", {"side": 0, "name": an, "goals": [1, 0], "behinds": [0, 0]}, "Q1 3'")
	feed.add_child(goal)
	var head: Node = goal.get_child(1).get_child(0)
	_check(head is RichTextLabel and (head as RichTextLabel).text.contains("[color=#%s]%s[/color]" % [_html(home), an.replace(" ", NB)]),
			"A goal row's scorer wears his club's ink")
	m.queue_free()
	await _settle()
