extends RefCounted
## The rival coach's calls from seeded matches, both sides AI clubs, every
## coach tendency and box from slow to sharp. tools/rival_identity_dump.gd
## wrote tests/fixtures/rival_identity.json from main before the rival coach
## read (director, 2026-11-08); tests/test_rival_read.gd plays the same
## matches and checks the scores and every call are unchanged. The words added
## to the record since ("why") are left out of the comparison.

const FIXTURE := "res://tests/fixtures/rival_identity.json"
const MATCHES := 40
const STYLES := ["balanced", "stubborn", "reactive", "gambler", "cautious"]
## Box reads from the worst to the best (CoachEffects.level's range), with
## the sharp-box cut (0.4) on both sides.
const READS := [-0.75, -0.2, 0.39, 0.4, 1.0]
## The calls a rival coach makes each quarter (MatchSim.ai_tactics).
const KEYS := ["gameplan", "pep", "interceptor_id", "spare_accountable", "spare_minder_id", "tag_id"]


## Match i, set up and not yet bounced.
static func stage(i: int) -> MatchSim:
	var order: Array = GameDB.active_clubs(2026)
	var h := str(order[i % order.size()])
	var a := str(order[(i + 5 + i / order.size()) % order.size()])
	var home := Squad.new(h, GameDB.club_list(h), true, h)
	var away := Squad.new(a, GameDB.club_list(a), false, a)
	home.ai_plans = true
	away.ai_plans = true
	home.coach_style = STYLES[i % STYLES.size()]
	away.coach_style = STYLES[(i + 2) % STYLES.size()]
	home.tactics_read = READS[i % READS.size()]
	away.tactics_read = READS[(i * 3 + 1) % READS.size()]
	var sim := MatchSim.new(home, away, 9100 + i)
	# A league match as the balance harness stages it (tools/balance).
	sim.season_plans = ["steady", "steady"]
	sim.moment_side = -1
	return sim


## Plays the rest of the quarter begun, taking every moment's default.
static func finish_quarter(sim: MatchSim) -> void:
	while not sim.continue_quarter():
		sim.resolve_moment(int(sim.pending_moment.get("default", 0)))
	sim.end_quarter()


static func play(i: int) -> Dictionary:
	var sim := stage(i)
	var home: Squad = sim.squads[0]
	var away: Squad = sim.squads[1]
	var h := home.code
	var a := away.code
	var quarters := []
	while sim.current_quarter <= 4:
		sim.begin_quarter()
		var rec: Dictionary = sim.tactics_history[sim.tactics_history.size() - 1]
		var row := []
		for side in range(2):
			var t: Dictionary = (rec["plans"] as Array)[side]
			var calls := {}
			for k in KEYS:
				calls[k] = str(t.get(k, ""))
			calls["loose"] = str(sim.interceptor[side])
			calls["rotation"] = str((rec["rotations"] as Array)[side])
			row.append(calls)
		quarters.append(row)
		finish_quarter(sim)
	var res: Dictionary = sim.result()
	return {
		"match": "%s v %s, seed %d, %s/%s, box %.2f/%.2f" % [h, a, 9100 + i, home.coach_style, away.coach_style, home.tactics_read, away.tactics_read],
		"score": [int(res["score"][0]), int(res["score"][1])],
		"q_goals": str(res["q_goals"]),
		"q_behinds": str(res["q_behinds"]),
		"quarters": quarters,
	}


static func play_all() -> Array:
	var out := []
	for i in range(MATCHES):
		out.append(play(i))
	return out
