class_name LeagueNews
extends RefCounted
## The AFL knowledge layer (row 76, T5.Q11d; Director Bible 5.129 and 8.80):
## history the save can prove, told as football news on the existing news feed.
##
## One placement so far, the smallest the brief allows: the premiership. When a
## club wins the flag, the feed's "X are the YEAR premiers." item carries one
## more sentence of the club's history: its first flag ever, back-to-back or
## more in a row, or the first in ClubStories.DROUGHT_YEARS seasons or longer
## ("Their first flag since 1990, a 41-year wait."). NewsFront shows that
## sentence as the premiership story's standfirst.
##
## Every claim is computed: flags before the career from
## data/club_premierships.csv (sourced, ClubHistory), flags since from the save's
## honour roll (ClubStories.flag_record, which the Grand Final card also reads).
## Where the record cannot know, nothing is said. Reads only: no rating, morale,
## list or match changes.


## The premiers' history in one sentence, or "" when there is nothing true and
## notable to say. `roll` is the honour roll (this season's entry is ignored).
static func flag_history(club: String, year: int, roll: Array) -> String:
	if club == "":
		return ""
	var rec := ClubStories.flag_record(club, year, roll)
	var flags: Dictionary = rec["flags"]
	if flags.is_empty():
		return "The club's first premiership." if bool(rec["known"]) else ""
	var run := 1
	while flags.has(year - run):
		run += 1
	if run == 2:
		return "Back-to-back flags."
	if run >= 3:
		return "%s flags in a row." % str(ClubStories.RUN_WORDS.get(run, str(run)))
	var last := int(rec["last_flag"])
	if last > 0 and year - last >= ClubStories.DROUGHT_YEARS:
		return "Their first flag since %d, %s %d-year wait." % [last, LeagueStories.an(year - last), year - last]
	return ""


## The feed's premiership line: "X are the YEAR premiers." plus the history
## sentence when there is one.
static func premiers_line(club: String, year: int, roll: Array) -> String:
	var line := "%s are the %d premiers." % [GameDB.club_name(club), year]
	var more := flag_history(club, year, roll)
	return line if more == "" else line + " " + more
