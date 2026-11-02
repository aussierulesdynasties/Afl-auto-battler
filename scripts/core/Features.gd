class_name Features
extends RefCounted
## Feature switches (director, 2026-10-14: "Fixes as they land, features at
## 0.2.0"). A feature that is merged but not finished stays hidden from
## players behind one named switch here until its patch is ready and he has
## played it. With a switch off the game behaves exactly as it did before
## the feature existed, and writes none of its state.
##
## A switch is ON when any of these says so, in this order:
##   1. code forced it (set_on): the feature's own tests, capture tools and
##      audits turn it on for themselves;
##   2. the command line names it after "--": a dev run,
##        godot --path . -- --features preseason
##      (several: --features preseason,other);
##   3. the project setting features/<name> is true (project.godot). This is
##      what an exported build reads. international_prospects ships ON since
##      2026-10-18 (director: "Names fine, switch on"); every other switch ships off.
## Otherwise it is OFF: every test suite that does not ask for it, and a plain
## editor run, for any switch whose project setting is false.
##
## Switches (international_prospects ships ON since 2026-10-18; preseason, speccy_front, training_report ship off):
##   preseason   the eight-week pre-season between the wrap and Round 1
##               (PreSeason.gd, PreSeasonScene), and everything built on it
##               for patch 0.2.0 (the pre-season match comes next).
##   speccy_front   the low, tight front-on speccy shot that freezes on the grab
##               (BroadcastVignette). Off, a spectacular mark plays the earlier shot.
##   international_prospects   one or two prospects from Ireland, New Zealand, the USA
##               and Africa in each generated draft class (InternationalProspects.gd),
##               and their story beats. Off, generated classes are exactly as before.
##   training_report   the report after every fourth round: who improved, who
##               fell back, and who can learn a new position (TrainingReport.gd).
##   expansion_package   how a new club builds its list (director, 2026-10-14):
##               state-league signings, early draft picks, one out-of-contract
##               player per rival club, and Canberra as a career choice
##               (ExpansionBuild). Off, a new club arrives with the 36
##               generated players it always did and Canberra always joins.
##   milestone_games   the week's milestones (games, debuts, goals, your games
##               as coach, first win, first final) on the Hub, in the news and
##               on the full-time screen (Milestones.gd). The record itself is
##               always kept; off, nothing of it is shown.
##   club_almanac   the club almanac (Almanac.gd, AlmanacScene): a page per
##               season of your career, reached from the Hub and the season wrap.
##               Off, no entry is shown and no almanac page is written.
##   match_story   the match makes the story (director, 2026-11-03, plan step 1b): each
##               match's hero, turning point and why it was won or lost (MatchStory.gd),
##               at the top of the full-time Summary, on the news front, in the press
##               question, and kept on GameState.match_stories. Off, none of it shows
##               and nothing is written.

##   ai_draft_buff   rival clubs' National Draft picks lean on the best player
##               available (roadmap row 37): scarcity ramps in over two rounds and
##               counts for at most 5 points, a covered position keeps 97% of a
##               prospect's worth (was 92%). Rivals only: the user's Pick for me is
##               unchanged. Off, rival drafting is exactly as before.
##               Balance-gated: the director's call.
##   finals_cards_2  the finals cards' second slice (rows 35, 36): A3, A9, A14, B7 in
##               finals weeks, and one card the week your season ends (A15, A16, B8,
##               B9). Off, those cards are not in the deck and nothing is written.

const KNOWN := ["preseason", "speccy_front", "training_report", "international_prospects", "expansion_package", "milestone_games", "club_almanac", "match_story", "ai_draft_buff", "finals_cards_2"]

static var _forced := {}
static var _from_args := {}
static var _args_read := false


static func on(feature: String) -> bool:
	if _forced.has(feature):
		return bool(_forced[feature])
	if not _args_read:
		_read_args()
	if _from_args.has(feature):
		return true
	return bool(ProjectSettings.get_setting("features/" + feature, false))


## Force a switch for this run (tests, capture tools, audits).
static func set_on(feature: String, value: bool) -> void:
	_forced[feature] = value


## Back to what the command line and the project setting say.
static func clear(feature: String) -> void:
	_forced.erase(feature)


static func _read_args() -> void:
	_args_read = true
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		var names := ""
		if str(a[i]) == "--features" and i + 1 < a.size():
			names = str(a[i + 1])
		elif str(a[i]).begins_with("--features="):
			names = str(a[i]).substr(11)
		for n in names.split(",", false):
			if KNOWN.has(n.strip_edges()):
				_from_args[n.strip_edges()] = true
