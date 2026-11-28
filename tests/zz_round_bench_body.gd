extends RefCounted
## Scratch (bug bash, never commit): time the pieces of the round finish on their own.
## Each piece is pure (or idempotent after its first call), run REPS times over every rival list.

const REPS := 5
var T := {}


func _add(k: String, t0: int) -> void:
	T[k] = float(T.get(k, 0.0)) + (Time.get_ticks_usec() - t0) / 1000.0


func run(tree: SceneTree) -> void:
	var root := tree.root
	var st: Node = root.get_node("GameState")
	var db: Node = root.get_node("GameDB")
	st.replay_seed = 2026
	st.reset()
	st.start_season("COL", db.club_list("COL"))
	# Advance into the season (three played rounds) so lists carry form, XP banks and stories.
	var played := 0
	for i in range(60):
		var before: int = st.get("season").round_index
		st.advance()
		if st.get("season").round_index > before:
			played += 1
		if played >= 3:
			break
	print("round_index ", st.get("season").round_index, " phase ", ClubStories.phase(st))
	var season = st.get("season")
	var coaches: Dictionary = st.get("coaches")
	var my: String = st.get("my_club")
	var year: int = st.get("season_year")
	var CE = load("res://scripts/state/CoachEffects.gd") if ResourceLoader.exists("res://scripts/state/CoachEffects.gd") else null
	print("coaches ", coaches.size(), " lists ", season.lists.size(), " CE ", CE != null)
	var t0 := 0
	for rep in range(REPS):
		t0 = Time.get_ticks_usec()
		var staffs = CoachEffects.staffs(coaches) if not coaches.is_empty() else null
		_add("staffs (once a round)", t0)
		for code in season.lists:
			if code == my:
				continue
			var list: Array = season.lists[code]
			t0 = Time.get_ticks_usec()
			var side := Ratings.select_side(list, season.selections.get(code, {}))
			_add("select_side (17 clubs)", t0)
			t0 = Time.get_ticks_usec()
			var plan: String = st.fitness_plan(code)
			_add("fitness_plan (17 clubs)", t0)
			var staff: Dictionary = staffs.get(code, {}) if staffs != null else {}
			for p in list:
				t0 = Time.get_ticks_usec()
				st.call("_club_mult", code, p, staff, true, plan)
				_add("_club_mult whole", t0)
				if staffs != null:
					t0 = Time.get_ticks_usec()
					CoachEffects.xp_mult(staff, p, true)
					_add("  CoachEffects.xp_mult", t0)
					t0 = Time.get_ticks_usec()
					CoachEffects.philosophical(staff, false)
					_add("  CoachEffects.philosophical", t0)
				t0 = Time.get_ticks_usec()
				Conditioning.xp_mult(plan, p)
				_add("  Conditioning.xp_mult", t0)
				t0 = Time.get_ticks_usec()
				var yg := Culture.young_for_growth(p, year)
				_add("  Culture.young_for_growth", t0)
				t0 = Time.get_ticks_usec()
				st.culture_effect(code, "young_growth")
				_add("  culture_effect", t0)
				t0 = Time.get_ticks_usec()
				Growth.match_xp(p, 1.0)
				Growth.train_xp(p)
				_add("Growth match+train xp", t0)
				t0 = Time.get_ticks_usec()
				st.call("_ai_trait_focus", p)
				_add("_ai_trait_focus", t0)
				t0 = Time.get_ticks_usec()
				Traits.near(p)
				_add("  Traits.near", t0)
				t0 = Time.get_ticks_usec()
				st.call("_development_pick", code, p, {})
				_add("_development_pick", t0)
			t0 = Time.get_ticks_usec()
			st.call("_ai_project_choice", list)
			_add("_ai_project_choice (17 clubs)", t0)
		t0 = Time.get_ticks_usec()
		var ctx: Dictionary = ClubStories.context(st)
		_add("ClubStories.context", t0)
		t0 = Time.get_ticks_usec()
		ClubStories.club_facts(st, int(ctx["week"]), str(ctx["phase"]))
		_add("  club_facts", t0)
		t0 = Time.get_ticks_usec()
		ClubStories.player_facts(st)
		_add("  player_facts", t0)
		t0 = Time.get_ticks_usec()
		season.finals_math(my)
		_add("    finals_math", t0)
		t0 = Time.get_ticks_usec()
		var deck: Array = StoryDeck.all()
		_add("StoryDeck.all", t0)
		var story: Dictionary = (st.get("story") as Dictionary).duplicate(true)
		t0 = Time.get_ticks_usec()
		StoryEngine.pick_week(deck, ctx, story)
		_add("StoryEngine.pick_week (copy of story)", t0)
		t0 = Time.get_ticks_usec()
		st.call("_save_state")
		_add("save: _save_state", t0)
		t0 = Time.get_ticks_usec()
		st.call("_save_meta")
		_add("save: _save_meta", t0)
		t0 = Time.get_ticks_usec()
		st.call("autosave")
		_add("save: autosave whole", t0)
	var keys := T.keys()
	for k in keys:
		print("BENCH %8.1f ms a round  %s" % [float(T[k]) / REPS, k])
	print("done")
