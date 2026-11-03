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
## Switches (international_prospects ships ON since 2026-10-18; preseason, speccy_front, training_report, top_attributes ship off):
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
##   club_almanac   the club almanac (Almanac.gd, AlmanacScene): a page per
##               season of your career, reached from the Hub and the season wrap.
##               Off, no entry is shown and no almanac page is written.
##   match_story   the match makes the story (director, 2026-11-03, plan step 1b): each
##               match's hero, turning point and why it was won or lost (MatchStory.gd),
##               at the top of the full-time Summary, on the news front, in the press
##               question, and kept on GameState.match_stories. Off, none of it shows
##               and nothing is written.
##   top_attributes   every player card (profile sheet, draft detail) shows his top three
##               rated attributes, and Needs work says how he sits against players of
##               his position (PlayerProfile.top_attributes / needs_work_line). Off,
##               the cards show the graded strengths and the old Needs work line.
##   coach_arcs   the coach's career arcs (director, 2026-11-03, phase 1): stories that
##               run across seasons (hot seat, a protege, a drought, a legacy...),
##               started by real game state and told as Hub event cards
##               (CoachArcs.gd, ClubArcs.gd, data/arcs/coach_arcs.json). Phase 2:
##               the coach changes clubs (ClubMoves.gd): sacked, he takes a job
##               elsewhere; poached, he leaves; his old club and assistant
##               come back in arcs. Off, no arc starts, no card shows,
##               GameState.coach_arcs stays empty and the sack ends the career.
##   finals_cards_2  the finals cards' second slice (rows 35, 36): A3, A9, A14, B7 in
##               finals weeks, and one card the week your season ends (A15, A16, B8,
##               B9). Off, those cards are not in the deck and nothing is written.
##   player_looks   register row 6 (director 2026-10-10: "they look like clones"): ten more
##               hair styles drawn (VignetteLooks.HAIR_STYLES) and a minimal face - eyes and
##               brows, the brows one of five chosen by his id, in his hair colour, the eyes
##               near black. Off, those styles draw the short crop and no face is drawn.

##   kick_range  row 10 (director, 2026-11-03): a kick's receiver must be within the
##               kicker's reach (MatchSim.kick_range: 30 m + 0.35 x disposal), nearest
##               teammate when nobody is; every match path shares MatchSim.kick_receiver.
##               Off, the receiver is the old zone pick from the whole ground.
##   match_flow  row 11 (director, 2026-10-10): stoppages come from contests that lock up
##               (a held tackle, a rushed kick into a pack, a spoil in the pocket), a won ball
##               after an intercept or a free is played on, chains are shorter and more
##               numerous (Ratings.FLOW, MatchSim LOCKUP_*, TACKLE_SPILL). Changes match
##               output. Off, a match is exactly as before.
##   ballup_two  row 15 (director, 2026-11-04): the late centre ball-up call is two
##               distinct choices, Stack the stoppage or Flood behind the ball, each
##               with its upside, downside, size and length; "Play it straight" is
##               gone. A call skipped or left unanswered is no call (nothing is
##               stacked or flooded). Off, the call keeps its three options.
##   ui_motion   menu juice, first prototype (director, 2026-11-04): the UiKit.Motion tokens
##               in the helpers, a hardened reveal / count_up / land / attention (an earlier
##               tween on the same node is stopped first), the Router fade easing out, every
##               modal sheet fading in with a 6 px rise (UiKit.sheet_in), UiKit.fill_bar, and
##               the Sim the week result sheet: Verdict lands on a win and fades in on a loss,
##               the Norm Smith, Injured and MRO lines come in one after another. Scores are
##               never delayed. Cosmetic only; Reduced motion still stills all of it. Off,
##               every screen is exactly as before.
const KNOWN := ["preseason", "speccy_front", "training_report", "international_prospects", "expansion_package", "club_almanac", "match_story", "finals_cards_2", "player_looks", "coach_arcs", "top_attributes", "kick_range", "match_flow", "ballup_two", "ui_motion"]

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
