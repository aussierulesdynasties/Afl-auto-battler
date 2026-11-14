class_name Achievements
extends RefCounted
## The game's 100 achievements (director, 2026-11-14: "scrap all those
## achievements ... make 100 more, 2 for every possible club including your
## own Forge club, and various others").
##
##   44 club achievements: two for each of the 22 clubs a career can field
##      (the 20 of 2026 to 2030, Fitzroy in a 1990s Legacy start, and the
##      career's Club Forge club, "FORGE" below). Any club can earn its own,
##      whoever coaches it: they are written into the league's history.
##   56 coach achievements ("club": ""): yours alone, earned at whichever
##      club you coach that season.
##
## Pure data and checks - no simulation, no effect on play. GameState calls
## check_season() once, after the Grand Final settles and the season's
## honour-roll entry is written, with the context built in
## GameState._close_season_achievements():
##   year, premier, runner_up, ladder (code -> row), finalists, finals_slots,
##   enter (code -> entry year), my_club, forge ([codes]), matches (this
##   season's results in order, finals last, each {home, away, score, tag}),
##   gf ({home, away, score} or {}), roll (the honour roll, this season's entry
##   last) and yours ({player id: [draft year, pick, kind]} for this season's
##   honoured players and premiership side that you drafted).

const FORGE := "FORGE"

const DEFINITIONS := [
	# --- Club achievements: per club, a rivalry and a dynasty-sized feat ----
	{"id": "ade_showdown_double", "club": "ADE", "name": "Showdown double",
		"desc": "Adelaide beat Port Adelaide twice in a season.",
		"type": "beat_twice", "opp": "PAD"},
	{"id": "ade_crows_98", "club": "ADE", "name": "The '98 Crows",
		"desc": "Adelaide win two premierships in a row, the second from fifth or lower on the ladder, as in 1997 and 1998.",
		"type": "flags_window", "count": 2, "span": 2, "from_pos": 5},
	{"id": "brl_qclash_double", "club": "BRL", "name": "QClash double",
		"desc": "Brisbane beat Gold Coast twice in a season.",
		"type": "beat_twice", "opp": "GCS"},
	{"id": "brl_three_peat", "club": "BRL", "name": "Lions three-peat",
		"desc": "Brisbane win three premierships in a row, as in 2001, 2002 and 2003.",
		"type": "flags_window", "count": 3, "span": 3},
	{"id": "car_over_pies", "club": "CAR", "name": "Blues over Pies",
		"desc": "Carlton beat Collingwood twice in a season.",
		"type": "beat_twice", "opp": "COL"},
	{"id": "car_blues_95", "club": "CAR", "name": "The '95 Blues",
		"desc": "Carlton win the premiership losing two games or fewer all season, finals included. The 1995 Blues lost two.",
		"type": "flag_max_losses", "n": 2},
	{"id": "col_over_blues", "club": "COL", "name": "Pies over Blues",
		"desc": "Collingwood beat Carlton twice in a season.",
		"type": "beat_twice", "opp": "CAR"},
	{"id": "col_four_in_a_row", "club": "COL", "name": "Four in a row",
		"desc": "Collingwood win four premierships in a row, as only the 1927-30 Magpies have.",
		"type": "flags_window", "count": 4, "span": 4},
	{"id": "ess_over_pies", "club": "ESS", "name": "Bombers over Pies",
		"desc": "Essendon beat Collingwood twice in a season.",
		"type": "beat_twice", "opp": "COL"},
	{"id": "ess_bombers_2000", "club": "ESS", "name": "The 2000 Bombers",
		"desc": "Essendon win 21 home-and-away games and the premiership. The 2000 side lost one game all year.",
		"type": "wins_flag", "n": 21},
	{"id": "fre_derby_double", "club": "FRE", "name": "Derby double",
		"desc": "Fremantle beat West Coast twice in a season.",
		"type": "beat_twice", "opp": "WCE"},
	{"id": "fre_top_and_flag", "club": "FRE", "name": "Unfinished business",
		"desc": "Fremantle finish top of the ladder and win the premiership in the same season. The 2015 Dockers topped the ladder and lost a preliminary final.",
		"type": "grand_slam"},
	{"id": "gee_over_hawks", "club": "GEE", "name": "Cats over Hawks",
		"desc": "Geelong beat Hawthorn twice in a season.",
		"type": "beat_twice", "opp": "HAW"},
	{"id": "gee_three_in_five", "club": "GEE", "name": "Cats' dynasty",
		"desc": "Geelong win three premierships in five seasons, as in 2007, 2009 and 2011.",
		"type": "flags_window", "count": 3, "span": 5},
	{"id": "gcs_over_lions", "club": "GCS", "name": "Suns over Lions",
		"desc": "Gold Coast beat Brisbane twice in a season.",
		"type": "beat_twice", "opp": "BRL"},
	{"id": "gcs_flag_and_brownlow", "club": "GCS", "name": "Gold on the Coast",
		"desc": "Gold Coast win the premiership in a season a Suns player wins the Brownlow Medal. The club's first Brownlow came in 2013.",
		"type": "flag_and_award", "key": "brownlow"},
	{"id": "gws_derby_double", "club": "GWS", "name": "Sydney Derby double",
		"desc": "GWS beat Sydney twice in a season.",
		"type": "beat_twice", "opp": "SYD"},
	{"id": "gws_redemption", "club": "GWS", "name": "Redemption",
		"desc": "GWS lose a Grand Final, then win the premiership the next season. The Giants lost the 2019 Grand Final.",
		"type": "flag_after_gf_loss"},
	{"id": "haw_over_cats", "club": "HAW", "name": "Hawks over Cats",
		"desc": "Hawthorn beat Geelong twice in a season.",
		"type": "beat_twice", "opp": "GEE"},
	{"id": "haw_three_peat", "club": "HAW", "name": "Hawks three-peat",
		"desc": "Hawthorn win three premierships in a row, as in 2013, 2014 and 2015.",
		"type": "flags_window", "count": 3, "span": 3},
	{"id": "mel_over_pies", "club": "MEL", "name": "Demons over Pies",
		"desc": "Melbourne beat Collingwood twice in a season.",
		"type": "beat_twice", "opp": "COL"},
	{"id": "mel_the_fifties", "club": "MEL", "name": "The '50s",
		"desc": "Melbourne win five premierships in six seasons, as the Demons did from 1955 to 1960.",
		"type": "flags_window", "count": 5, "span": 6},
	{"id": "nth_over_hawks", "club": "NTH", "name": "Roos over Hawks",
		"desc": "North Melbourne beat Hawthorn twice in a season, the side they met in three Grand Finals in the '70s.",
		"type": "beat_twice", "opp": "HAW"},
	{"id": "nth_five_grand_finals", "club": "NTH", "name": "Five Grand Finals",
		"desc": "North Melbourne play in five Grand Finals in a row, as from 1974 to 1978.",
		"type": "gf_streak", "n": 5},
	{"id": "pad_showdown_sweep", "club": "PAD", "name": "Showdown sweep",
		"desc": "Port Adelaide beat Adelaide twice in a season.",
		"type": "beat_twice", "opp": "ADE"},
	{"id": "pad_three_minors", "club": "PAD", "name": "Power on top",
		"desc": "Port Adelaide finish top of the ladder three seasons in a row, as in 2002, 2003 and 2004.",
		"type": "top_streak", "n": 3},
	{"id": "ric_over_blues", "club": "RIC", "name": "Tigers over Blues",
		"desc": "Richmond beat Carlton twice in a season.",
		"type": "beat_twice", "opp": "CAR"},
	{"id": "ric_three_in_four", "club": "RIC", "name": "Tigers' era",
		"desc": "Richmond win three premierships in four seasons, as in 2017, 2019 and 2020.",
		"type": "flags_window", "count": 3, "span": 4},
	{"id": "stk_over_cats", "club": "STK", "name": "Saints over Cats",
		"desc": "St Kilda beat Geelong twice in a season, the side that beat them in the 2009 Grand Final.",
		"type": "beat_twice", "opp": "GEE"},
	{"id": "stk_back_to_back", "club": "STK", "name": "Saints go marching",
		"desc": "St Kilda win two premierships in a row. The Saints have one flag, from 1966.",
		"type": "flags_window", "count": 2, "span": 2},
	{"id": "syd_over_giants", "club": "SYD", "name": "Swans over Giants",
		"desc": "Sydney beat GWS twice in a season.",
		"type": "beat_twice", "opp": "GWS"},
	{"id": "syd_bloods", "club": "SYD", "name": "Bloods culture",
		"desc": "Sydney make the finals ten seasons in a row and win a premiership along the way.",
		"type": "finals_streak", "n": 10, "with_flag": true},
	{"id": "wce_derby_sweep", "club": "WCE", "name": "Derby sweep",
		"desc": "West Coast beat Fremantle twice in a season.",
		"type": "beat_twice", "opp": "FRE"},
	{"id": "wce_two_in_three", "club": "WCE", "name": "Eagles soar",
		"desc": "West Coast win two premierships in three seasons, as in 1992 and 1994.",
		"type": "flags_window", "count": 2, "span": 3},
	{"id": "wbd_over_giants", "club": "WBD", "name": "Dogs over Giants",
		"desc": "Western Bulldogs beat GWS twice in a season, as on the way to the 2016 flag.",
		"type": "beat_twice", "opp": "GWS"},
	{"id": "wbd_back_to_back", "club": "WBD", "name": "Doggies' double",
		"desc": "Western Bulldogs win two premierships in a row, something the club has never done.",
		"type": "flags_window", "count": 2, "span": 2},
	{"id": "fit_over_pies", "club": "FIT", "name": "Roys over Pies",
		"desc": "Fitzroy beat Collingwood twice in a season.",
		"type": "beat_twice", "opp": "COL"},
	{"id": "fit_flag", "club": "FIT", "name": "Fitzroy flag",
		"desc": "Fitzroy win a premiership, their first since 1944.",
		"type": "premiership"},
	{"id": "tas_expansion_double", "club": "TAS", "name": "Expansion Cup double",
		"desc": "Tasmania beat Canberra twice in a season.",
		"type": "beat_twice", "opp": "CANB"},
	{"id": "tas_early_flag", "club": "TAS", "name": "Apple Isle flag",
		"desc": "Tasmania win a premiership in their first five seasons.",
		"type": "flag_within", "n": 5},
	{"id": "canb_expansion_double", "club": "CANB", "name": "Thunder over Devils",
		"desc": "Canberra beat Tasmania twice in a season.",
		"type": "beat_twice", "opp": "TAS"},
	{"id": "canb_early_flag", "club": "CANB", "name": "Capital flag",
		"desc": "Canberra win a premiership in their first five seasons.",
		"type": "flag_within", "n": 5},
	{"id": "forge_giant_killers", "club": FORGE, "name": "Giant-killers",
		"desc": "Your Club Forge club beats last season's premiers twice in a season.",
		"type": "beat_twice", "opp": "PREMIER"},
	{"id": "forge_dynasty", "club": FORGE, "name": "Forge dynasty",
		"desc": "Your Club Forge club wins three premierships in five seasons.",
		"type": "flags_window", "count": 3, "span": 5},

	# --- Coach achievements: your career ------------------------------------
	{"id": "coach_seasons_5", "club": "", "name": "Five seasons",
		"desc": "Coach five seasons.", "type": "seasons", "n": 5},
	{"id": "coach_seasons_10", "club": "", "name": "Ten-year man",
		"desc": "Coach ten seasons.", "type": "seasons", "n": 10},
	{"id": "coach_seasons_20", "club": "", "name": "Twenty years on",
		"desc": "Coach twenty seasons.", "type": "seasons", "n": 20},
	{"id": "coach_one_club", "club": "", "name": "One-club coach",
		"desc": "Coach ten seasons at the same club.", "type": "one_club", "n": 10},
	{"id": "coach_three_clubs", "club": "", "name": "Journeyman",
		"desc": "Coach three different clubs.", "type": "clubs", "n": 3},
	{"id": "coach_finals", "club": "", "name": "September football",
		"desc": "Make the finals.", "type": "finals"},
	{"id": "coach_top_four", "club": "", "name": "Double chance",
		"desc": "Finish in the top four.", "type": "top_n", "n": 4},
	{"id": "coach_minor_premiers", "club": "", "name": "Minor premiers",
		"desc": "Finish top of the ladder.", "type": "top_ladder"},
	{"id": "coach_grand_final", "club": "", "name": "Grand Final day",
		"desc": "Coach in a Grand Final.", "type": "grand_final"},
	{"id": "coach_flag", "club": "", "name": "Premiership coach",
		"desc": "Win a premiership.", "type": "premiership"},
	{"id": "coach_back_to_back", "club": "", "name": "Back-to-back",
		"desc": "Win two premierships in a row.", "type": "flags_window", "count": 2, "span": 2},
	{"id": "coach_three_peat", "club": "", "name": "Three-peat",
		"desc": "Win three premierships in a row.", "type": "flags_window", "count": 3, "span": 3},
	{"id": "coach_five_flags", "club": "", "name": "Dynasty",
		"desc": "Win five premierships as a coach.", "type": "flags_total", "n": 5},
	{"id": "coach_two_club_flags", "club": "", "name": "Flags at two clubs",
		"desc": "Win premierships at two different clubs.", "type": "flags_clubs", "n": 2},
	{"id": "coach_grand_slam", "club": "", "name": "Top and flag",
		"desc": "Finish top of the ladder and win the premiership in the same season.", "type": "grand_slam"},
	{"id": "coach_long_way", "club": "", "name": "The long way",
		"desc": "Lose a qualifying final, then win the premiership.", "type": "second_chance"},
	{"id": "coach_outside_four", "club": "", "name": "From outside the four",
		"desc": "Win the premiership from fifth or lower on the ladder.", "type": "premier_from", "pos": 5},
	{"id": "coach_bottom_to_finals", "club": "", "name": "Last to September",
		"desc": "Finish last, then make the finals the next season at the same club.", "type": "bottom_to_finals"},
	{"id": "coach_worst_to_first", "club": "", "name": "Spoon to flag",
		"desc": "Finish last, then win the premiership the next season at the same club.", "type": "worst_to_first"},
	{"id": "coach_rise", "club": "", "name": "Out of nowhere",
		"desc": "Win the premiership a season after missing the finals at the same club.", "type": "rise"},
	{"id": "coach_five_septembers", "club": "", "name": "Five straight Septembers",
		"desc": "Make the finals five seasons in a row.", "type": "finals_streak", "n": 5},
	{"id": "coach_ten_septembers", "club": "", "name": "Ten straight Septembers",
		"desc": "Make the finals ten seasons in a row.", "type": "finals_streak", "n": 10},
	{"id": "coach_three_minors", "club": "", "name": "Three on top",
		"desc": "Finish top of the ladder three seasons in a row.", "type": "top_streak", "n": 3},
	{"id": "coach_twenty_wins", "club": "", "name": "Twenty wins",
		"desc": "Win 20 home-and-away games in a season.", "type": "wins", "n": 20},
	{"id": "coach_home_unbeaten", "club": "", "name": "Fortress",
		"desc": "Win every home game of a home-and-away season.", "type": "home_unbeaten"},
	{"id": "coach_perfect_season", "club": "", "name": "Unbeaten",
		"desc": "Go through a home-and-away season without a loss or a draw.", "type": "perfect_ha"},
	{"id": "coach_flawless", "club": "", "name": "The perfect year",
		"desc": "Win every game of a season, finals included, and the premiership.", "type": "flawless"},
	{"id": "coach_streak_10", "club": "", "name": "Ten on the trot",
		"desc": "Win ten games in a row in a season.", "type": "streak", "n": 10},
	{"id": "coach_ton_up", "club": "", "name": "Hundred-point win",
		"desc": "Win a game by 100 points or more.", "type": "margin", "n": 100},
	{"id": "coach_150", "club": "", "name": "The 150 club",
		"desc": "Kick 150 points or more in a game.", "type": "score", "n": 150},
	{"id": "coach_beat_them_all", "club": "", "name": "Beat them all",
		"desc": "Beat every other club at least once in a season.", "type": "beat_all"},
	{"id": "coach_best_attack", "club": "", "name": "Best attack",
		"desc": "Kick the most points in the home-and-away season.", "type": "best_attack"},
	{"id": "coach_best_defence", "club": "", "name": "Best defence",
		"desc": "Concede the fewest points in the home-and-away season.", "type": "best_defence"},
	{"id": "coach_pct_150", "club": "", "name": "Percentage 150",
		"desc": "Finish the home-and-away season with a percentage of 150 or better.", "type": "pct", "n": 150.0},
	{"id": "coach_gf_thriller", "club": "", "name": "Under a goal",
		"desc": "Win a Grand Final by five points or fewer.", "type": "gf_win_by_max", "n": 5},
	{"id": "coach_gf_romp", "club": "", "name": "Grand Final romp",
		"desc": "Win a Grand Final by 60 points or more.", "type": "gf_win_by_min", "n": 60},
	{"id": "coach_heartbreak", "club": "", "name": "Heartbreak",
		"desc": "Lose a Grand Final by five points or fewer.", "type": "gf_loss_by_max", "n": 5},
	{"id": "coach_beat_premiers", "club": "", "name": "Dethroned",
		"desc": "Beat last season's premiers in a final.", "type": "beat_premier_final"},
	{"id": "coach_brownlow", "club": "", "name": "Brownlow night",
		"desc": "One of your players wins the Brownlow Medal.", "type": "award", "key": "brownlow"},
	{"id": "coach_faith_repaid", "club": "", "name": "Faith repaid",
		"desc": "A player you drafted wins the Brownlow Medal at your club.", "type": "award", "key": "brownlow", "drafted": true},
	{"id": "coach_late_pick_brownlow", "club": "", "name": "The steal",
		"desc": "A player you drafted with pick 30 or later wins the Brownlow Medal at your club.",
		"type": "award", "key": "brownlow", "drafted": true, "min_pick": 30},
	{"id": "coach_dual_brownlow", "club": "", "name": "Dual medallist",
		"desc": "The same player of yours wins a second Brownlow Medal at your club.", "type": "dual_brownlow"},
	{"id": "coach_coleman", "club": "", "name": "Coleman Medal",
		"desc": "One of your players kicks the most goals in the home-and-away season.", "type": "award", "key": "coleman"},
	{"id": "coach_coleman_drafted", "club": "", "name": "Your spearhead",
		"desc": "A player you drafted wins the Coleman Medal at your club.", "type": "award", "key": "coleman", "drafted": true},
	{"id": "coach_century", "club": "", "name": "The ton",
		"desc": "One of your players kicks 100 goals in a home-and-away season.", "type": "century", "n": 100},
	{"id": "coach_rising_star", "club": "", "name": "Rising Star",
		"desc": "One of your players wins the Rising Star.", "type": "award", "key": "rising_star"},
	{"id": "coach_rising_star_drafted", "club": "", "name": "Your Rising Star",
		"desc": "A player you drafted wins the Rising Star at your club.", "type": "award", "key": "rising_star", "drafted": true},
	{"id": "coach_coaches_award", "club": "", "name": "Coaches' pick",
		"desc": "One of your players wins the coaches' award for the season's best player.", "type": "award", "key": "coaches_award"},
	{"id": "coach_norm_smith", "club": "", "name": "Norm Smith in a flag",
		"desc": "One of your players wins the Norm Smith Medal in a Grand Final you win.", "type": "norm_smith_flag"},
	{"id": "coach_all_australian", "club": "", "name": "All-Australian",
		"desc": "One of your players is named in the All-Australian team.", "type": "aa_count", "n": 1},
	{"id": "coach_five_all_australians", "club": "", "name": "Half the team sheet",
		"desc": "Five of your players are named in the same All-Australian team.", "type": "aa_count", "n": 5},
	{"id": "coach_medal_sweep", "club": "", "name": "Clean sweep",
		"desc": "Your players win the Brownlow, the Coleman and the Rising Star in the same season.", "type": "medal_sweep"},
	{"id": "coach_coleman_flag", "club": "", "name": "Spearhead and flag",
		"desc": "Win the premiership in a season one of your players wins the Coleman Medal.", "type": "coleman_flag"},
	{"id": "coach_home_grown", "club": "", "name": "Built it yourself",
		"desc": "Win a premiership with ten or more players you drafted in the Grand Final side.", "type": "home_grown", "n": 10},
	{"id": "coach_rookie_aa", "club": "", "name": "From the rookie list",
		"desc": "A player you took in the rookie draft is named All-Australian at your club.", "type": "aa_drafted", "kind": "rookie"},
	{"id": "coach_bf_late_pick", "club": "", "name": "Diamond in the rough",
		"desc": "A player you drafted with pick 30 or later wins your club best and fairest.", "type": "bf_drafted", "min_pick": 30},
]


static func definition(id: String) -> Dictionary:
	for d in DEFINITIONS:
		if str(d["id"]) == id:
			return d
	return {}


## A club's two achievements ("FORGE" for the career's created club).
static func for_club(code: String) -> Array:
	var out := []
	for d in DEFINITIONS:
		if str(d["club"]) == code:
			out.append(d)
	return out


## The coach's own achievements.
static func coach_list() -> Array:
	return for_club("")


static func is_coach(d: Dictionary) -> bool:
	return str(d.get("club", "")) == ""


## The definitions to show for a real club code: its own two, or the Forge
## pair when the code is the career's created club.
static func for_code(code: String, forge: Array) -> Array:
	return for_club(FORGE) if forge.has(code) else for_club(code)


## The ids that become true this season, given what is already unlocked, as
## {id: club code} (the club that earned it; for a coach achievement, the club
## you coached).
static func check_season(unlocked: Dictionary, ctx: Dictionary) -> Dictionary:
	var out := {}
	for d in DEFINITIONS:
		var id := str(d["id"])
		if unlocked.has(id):
			continue
		var code := _code(d, ctx)
		if code != "" and _met(d, code, ctx):
			out[id] = code
	return out


## The club an achievement is checked for this season ("" when none).
static func _code(d: Dictionary, ctx: Dictionary) -> String:
	var club := str(d["club"])
	if club == "":
		return str(ctx.get("my_club", ""))
	if club == FORGE:
		var forge: Array = ctx.get("forge", [])
		return str(forge[0]) if not forge.is_empty() else ""
	return club


static func _met(d: Dictionary, code: String, ctx: Dictionary) -> bool:
	var coach := is_coach(d)
	var premier := str(ctx.get("premier", "")) == code
	match str(d["type"]):
		"premiership":
			return premier
		"grand_final":
			return premier or str(ctx.get("runner_up", "")) == code
		"finals":
			return (ctx.get("finalists", []) as Array).has(code)
		"top_n":
			var p := _position(ctx, code)
			return p > 0 and p <= int(d.get("n", 4))
		"top_ladder":
			return _position(ctx, code) == 1
		"grand_slam":
			return premier and _position(ctx, code) == 1
		"wins":
			return int(_row(ctx, code).get("w", 0)) >= int(d.get("n", 0))
		"wins_flag":
			return premier and int(_row(ctx, code).get("w", 0)) >= int(d.get("n", 0))
		"flags_window":
			var year := int(ctx.get("year", 0))
			var span := int(d.get("span", 2))
			var flags := 0
			for y in _flag_years(ctx, code, coach):
				if int(y) > year - span and int(y) <= year:
					flags += 1
			if d.has("from_pos") and _position(ctx, code) < int(d["from_pos"]):
				return false
			return premier and flags >= int(d.get("count", 2))
		"flag_max_losses":
			if not premier:
				return false
			var losses := 0
			for m in ctx.get("matches", []):
				var side := _side(m, code)
				if side >= 0 and _result(m, side) == "L":
					losses += 1
			return losses <= int(d.get("n", 2))
		"flag_and_award":
			return premier and str(_winner(ctx, str(d.get("key", ""))).get("club", "")) == code
		"flag_after_gf_loss":
			return premier and str(_prev(ctx, code, coach).get("runner_up", "")) == code
		"flag_within":
			var enter: Dictionary = ctx.get("enter", {})
			return premier and enter.has(code) \
					and int(ctx.get("year", 0)) - int(enter[code]) < int(d.get("n", 5))
		"gf_streak":
			return _streak(ctx, code, coach, func(e: Dictionary, c: String) -> bool:
				return str(e.get("premier", "")) == c or str(e.get("runner_up", "")) == c) \
					>= int(d.get("n", 5))
		"beat_twice":
			var opp := str(d.get("opp", ""))
			if opp == "PREMIER":
				opp = str(_entry(ctx, int(ctx.get("year", 0)) - 1).get("premier", ""))
			if opp == "" or opp == code:
				return false
			var wins := 0
			for m in ctx.get("matches", []):
				var side := _side(m, code)
				if side >= 0 and _other(m, side) == opp and _result(m, side) == "W":
					wins += 1
			return wins >= 2
		"flags_total":
			return premier and _flag_years(ctx, code, coach).size() >= int(d.get("n", 1))
		"flags_clubs":
			var clubs := {}
			for e in _roll(ctx):
				var m := str(e.get("my_club", ""))
				if m != "" and str(e.get("premier", "")) == m:
					clubs[m] = true
			return premier and clubs.size() >= int(d.get("n", 2))
		"second_chance":
			return _second_chance(ctx, code)
		"premier_from":
			return premier and _position(ctx, code) >= int(d.get("pos", 5))
		"debut_finals":
			return _is_debut_season(ctx, code) and (ctx.get("finalists", []) as Array).has(code)
		"debut_top":
			var n := int(_ladder_sorted(ctx).size() / 2.0)
			var p := _position(ctx, code)
			return _is_debut_season(ctx, code) and p > 0 and p <= n
		"sweep":
			var opp := str(d.get("opp", ""))
			var met := 0
			for m in ctx.get("matches", []):
				var side := _side(m, code)
				if side < 0 or _other(m, side) != opp:
					continue
				met += 1
				if _result(m, side) != "W":
					return false
			return met >= 2
		"gf_beat":
			return premier and str(ctx.get("runner_up", "")) == str(d.get("opp", ""))
		"home_unbeaten":
			var home := 0
			for m in _regular(ctx):
				if str(m.get("home", "")) == code:
					home += 1
					if _result(m, 0) != "W":
						return false
			return home > 0
		"finals_streak":
			var run := _streak(ctx, code, coach, func(e: Dictionary, c: String) -> bool:
				return (e.get("finalists", []) as Array).has(c))
			if run < int(d.get("n", 5)):
				return false
			if not bool(d.get("with_flag", false)):
				return true
			var year := int(ctx.get("year", 0))
			for y in _flag_years(ctx, code, coach):
				if int(y) > year - run and int(y) <= year:
					return true
			return false
		"top_streak":
			return _streak(ctx, code, coach, func(e: Dictionary, c: String) -> bool:
				var order: Array = e.get("ladder_order", [])
				return not order.is_empty() and str(order[0]) == c) >= int(d.get("n", 3))
		"rise":
			var prev := _prev(ctx, code, coach)
			return premier and prev.has("finalists") \
					and not (prev["finalists"] as Array).has(code)
		"bottom_to_finals":
			return _was_last(ctx, code, coach) and (ctx.get("finalists", []) as Array).has(code)
		"worst_to_first":
			return premier and _was_last(ctx, code, coach)
		"perfect_ha":
			var r := _row(ctx, code)
			return int(r.get("p", 0)) > 0 and int(r.get("l", 0)) == 0 and int(r.get("d", 0)) == 0
		"flawless":
			if not premier:
				return false
			var played := 0
			for m in ctx.get("matches", []):
				var side := _side(m, code)
				if side < 0:
					continue
				played += 1
				if _result(m, side) != "W":
					return false
			return played > 0
		"streak":
			var best := 0
			var run := 0
			for m in ctx.get("matches", []):
				var side := _side(m, code)
				if side < 0:
					continue
				run = run + 1 if _result(m, side) == "W" else 0
				best = maxi(best, run)
			return best >= int(d.get("n", 10))
		"margin":
			for m in ctx.get("matches", []):
				var side := _side(m, code)
				if side >= 0 and _margin(m, side) >= int(d.get("n", 100)):
					return true
			return false
		"score":
			for m in ctx.get("matches", []):
				var side := _side(m, code)
				if side >= 0 and int((m["score"] as Array)[side]) >= int(d.get("n", 150)):
					return true
			return false
		"beat_all":
			var beaten := {}
			for m in ctx.get("matches", []):
				var side := _side(m, code)
				if side >= 0 and _result(m, side) == "W":
					beaten[_other(m, side)] = true
			var others := 0
			for c in ctx.get("ladder", {}):
				if str(c) != code:
					others += 1
					if not beaten.has(str(c)):
						return false
			return others > 0
		"best_attack":
			return _extreme(ctx, code, "pf", true)
		"best_defence":
			return _extreme(ctx, code, "pa", false)
		"pct":
			var r := _row(ctx, code)
			return int(r.get("p", 0)) > 0 and float(r.get("pct", 0.0)) >= float(d.get("n", 150.0))
		"gf_win_by_max":
			var g := _gf_margin(ctx, code)
			return premier and g > 0 and g <= int(d.get("n", 5))
		"gf_win_by_min":
			return premier and _gf_margin(ctx, code) >= int(d.get("n", 60))
		"gf_loss_by_max":
			var g := _gf_margin(ctx, code)
			return str(ctx.get("runner_up", "")) == code and g < 0 and -g <= int(d.get("n", 5))
		"beat_premier_final":
			var prev := _entry(ctx, int(ctx.get("year", 0)) - 1)
			var champ := str(prev.get("premier", ""))
			if champ == "" or champ == code:
				return false
			for m in ctx.get("matches", []):
				var side := _side(m, code)
				if side >= 0 and str(m.get("tag", "")) != "" and _other(m, side) == champ \
						and _result(m, side) == "W":
					return true
			return false
		"award":
			var row := _winner(ctx, str(d.get("key", "")))
			if row.is_empty() or str(row.get("club", "")) != code:
				return false
			if not bool(d.get("drafted", false)):
				return true
			return _drafted_ok(ctx, str(row.get("id", "")), d)
		"dual_brownlow":
			var row := _winner(ctx, "brownlow")
			if row.is_empty() or str(row.get("club", "")) != code:
				return false
			var id := str(row.get("id", ""))
			var year := int(ctx.get("year", 0))
			for e in _roll(ctx):
				if int(e.get("year", 0)) >= year or str(e.get("my_club", "")) == "":
					continue
				var rows: Array = e.get("brownlow", [])
				if not rows.is_empty() and str((rows[0] as Dictionary).get("id", "")) == id \
						and str((rows[0] as Dictionary).get("club", "")) == str(e.get("my_club", "")):
					return true
			return false
		"century":
			var row := _winner(ctx, "coleman")
			return str(row.get("club", "")) == code and int(row.get("goals", 0)) >= int(d.get("n", 100))
		"norm_smith_flag":
			return premier and str(_winner(ctx, "norm_smith").get("club", "")) == code
		"aa_count":
			return (_this_entry(ctx).get("my_aa", []) as Array).size() >= int(d.get("n", 1))
		"aa_drafted":
			for id in _this_entry(ctx).get("my_aa", []):
				if _drafted_ok(ctx, str(id), d):
					return true
			return false
		"bf_drafted":
			var bf: Array = _this_entry(ctx).get("my_bf", [])
			return not bf.is_empty() and _drafted_ok(ctx, str((bf[0] as Dictionary).get("id", "")), d)
		"medal_sweep":
			for key in ["brownlow", "coleman", "rising_star"]:
				if str(_winner(ctx, key).get("club", "")) != code:
					return false
			return true
		"coleman_flag":
			return premier and str(_winner(ctx, "coleman").get("club", "")) == code
		"home_grown":
			if not premier:
				return false
			var yours: Dictionary = ctx.get("yours", {})
			var n := 0
			for id in _this_entry(ctx).get("premier_side", []):
				if yours.has(str(id)):
					n += 1
			return n >= int(d.get("n", 10))
		"seasons":
			return _coached(ctx).size() >= int(d.get("n", 1))
		"one_club":
			var n := 0
			for e in _coached(ctx):
				if str(e.get("my_club", "")) == code:
					n += 1
			return n >= int(d.get("n", 10))
		"clubs":
			var clubs := {}
			for e in _coached(ctx):
				clubs[str(e.get("my_club", ""))] = true
			return clubs.size() >= int(d.get("n", 3))
	return false


# --- Season helpers ----------------------------------------------------------
static func _row(ctx: Dictionary, code: String) -> Dictionary:
	return (ctx.get("ladder", {}) as Dictionary).get(code, {})


## 1-based ladder position, 0 when the club is not on the ladder.
static func _position(ctx: Dictionary, code: String) -> int:
	var rows := _ladder_sorted(ctx)
	for i in range(rows.size()):
		if str(rows[i].get("code", "")) == code:
			return i + 1
	return 0


static func _ladder_sorted(ctx: Dictionary) -> Array:
	var ladder: Dictionary = ctx.get("ladder", {})
	var rows: Array = []
	for code in ladder:
		rows.append(ladder[code])
	rows.sort_custom(func(a, b):
		if int(a["pts"]) != int(b["pts"]):
			return int(a["pts"]) > int(b["pts"])
		if not is_equal_approx(float(a["pct"]), float(b["pct"])):
			return float(a["pct"]) > float(b["pct"])
		return int(a["pf"]) > int(b["pf"]))
	return rows


## Best (or least) of a ladder column; ties count for every club on it.
static func _extreme(ctx: Dictionary, code: String, key: String, most: bool) -> bool:
	var ladder: Dictionary = ctx.get("ladder", {})
	if not ladder.has(code) or int(ladder[code].get("p", 0)) == 0:
		return false
	var mine := int(ladder[code].get(key, 0))
	for c in ladder:
		var v := int(ladder[c].get(key, 0))
		if (most and v > mine) or (not most and v < mine):
			return false
	return true


static func _regular(ctx: Dictionary) -> Array:
	return (ctx.get("matches", []) as Array).filter(func(m): return str(m.get("tag", "")) == "")


static func _side(m: Dictionary, code: String) -> int:
	if str(m.get("home", "")) == code:
		return 0
	if str(m.get("away", "")) == code:
		return 1
	return -1


static func _other(m: Dictionary, side: int) -> String:
	return str(m.get("away", "")) if side == 0 else str(m.get("home", ""))


static func _margin(m: Dictionary, side: int) -> int:
	var s: Array = m.get("score", [0, 0])
	return int(s[side]) - int(s[1 - side])


static func _result(m: Dictionary, side: int) -> String:
	var g := _margin(m, side)
	return "W" if g > 0 else ("L" if g < 0 else "D")


## The Grand Final margin from `code`'s side: + won, - lost, 0 not in it.
static func _gf_margin(ctx: Dictionary, code: String) -> int:
	var gf: Dictionary = ctx.get("gf", {})
	if gf.is_empty():
		return 0
	var side := _side(gf, code)
	return _margin(gf, side) if side >= 0 else 0


static func _is_debut_season(ctx: Dictionary, code: String) -> bool:
	var enter: Dictionary = ctx.get("enter", {})
	return enter.has(code) and int(enter[code]) == int(ctx.get("year", 0))


## The QF-loser path: QF -> SF -> PF -> GF, bracket positions are fixed.
## The semi winners cross over (Season, #964): W_SF1 plays PF2, W_SF2 plays PF1.
static func _second_chance(ctx: Dictionary, code: String) -> bool:
	var s: Dictionary = ctx.get("finals_slots", {})
	if str(s.get("L_QF1", "")) == code:
		return str(s.get("W_SF1", "")) == code \
				and str(s.get("W_PF2", "")) == code and str(s.get("W_GF", "")) == code
	if str(s.get("L_QF2", "")) == code:
		return str(s.get("W_SF2", "")) == code \
				and str(s.get("W_PF1", "")) == code and str(s.get("W_GF", "")) == code
	return false


# --- History helpers (the honour roll) ----------------------------------------
static func _roll(ctx: Dictionary) -> Array:
	return ctx.get("roll", [])


static func _entry(ctx: Dictionary, year: int) -> Dictionary:
	for e in _roll(ctx):
		if int(e.get("year", 0)) == year:
			return e
	return {}


static func _this_entry(ctx: Dictionary) -> Dictionary:
	return _entry(ctx, int(ctx.get("year", 0)))


## The seasons you coached, oldest first.
static func _coached(ctx: Dictionary) -> Array:
	return _roll(ctx).filter(func(e): return str(e.get("my_club", "")) != "")


## The seasons `code` won the flag (a coach's: the flags won at the club he
## coached that season), this season included.
static func _flag_years(ctx: Dictionary, code: String, coach: bool) -> Array:
	var out := []
	for e in _roll(ctx):
		var p := str(e.get("premier", ""))
		if p == "":
			continue
		if (coach and p == str(e.get("my_club", ""))) or (not coach and p == code):
			out.append(int(e.get("year", 0)))
	return out


## Last season's entry for `code` ({} when it is missing, or when a coach was
## at another club or not coaching).
static func _prev(ctx: Dictionary, code: String, coach: bool) -> Dictionary:
	var prev := _entry(ctx, int(ctx.get("year", 0)) - 1)
	if prev.is_empty() or (coach and str(prev.get("my_club", "")) != code):
		return {}
	return prev


static func _was_last(ctx: Dictionary, code: String, coach: bool) -> bool:
	var prev := _prev(ctx, code, coach)
	var order: Array = prev.get("ladder_order", [])
	return not order.is_empty() and str(order[-1]) == code


## Seasons in a row, ending this one, that `test` holds for (a coach's: at the
## club he coached each season).
static func _streak(ctx: Dictionary, code: String, coach: bool, test: Callable) -> int:
	var n := 0
	var year := int(ctx.get("year", 0))
	while true:
		var e := _entry(ctx, year - n)
		if e.is_empty():
			break
		var c := str(e.get("my_club", "")) if coach else code
		if c == "" or not bool(test.call(e, c)):
			break
		n += 1
	return n


## This season's winner row of an award ({} when none).
static func _winner(ctx: Dictionary, key: String) -> Dictionary:
	var rows: Array = _this_entry(ctx).get(key, [])
	return rows[0] if not rows.is_empty() and rows[0] is Dictionary else {}


## The player was drafted by you, and the draft matches `d`'s min_pick / kind.
static func _drafted_ok(ctx: Dictionary, id: String, d: Dictionary) -> bool:
	var yours: Dictionary = ctx.get("yours", {})
	if id == "" or not yours.has(id):
		return false
	var draft: Array = yours[id]
	if d.has("min_pick") and int(draft[1]) < int(d["min_pick"]):
		return false
	if d.has("kind") and str(draft[2]) != str(d["kind"]):
		return false
	return true
