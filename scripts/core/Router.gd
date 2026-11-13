extends Node
## Router (autoload) - scene navigation with a back stack, so the back button
## works the same on desktop and mobile.

const SCENES := {
	"main": "res://scenes/Main.tscn",
	"draft": "res://scenes/DraftScene.tscn",
	"hub": "res://scenes/HubScene.tscn",
	"match": "res://scenes/MatchScene.tscn",
	"preview": "res://scenes/MatchPreviewScene.tscn",
	"stats": "res://scenes/StatsHubScene.tscn",
	"list": "res://scenes/ListScene.tscn",
	"scouting": "res://scenes/ScoutingScene.tscn",
	"selection": "res://scenes/SelectionScene.tscn",
	"offseason": "res://scenes/OffseasonScene.tscn",
	"training": "res://scenes/TrainingScene.tscn",
	"staff": "res://scenes/StaffScene.tscn",
	"coaching": "res://scenes/CoachingScene.tscn",
	"season_review": "res://scenes/SeasonReviewScene.tscn",
	"forge": "res://scenes/ClubForgeScene.tscn",
	"preseason": "res://scenes/PreSeasonScene.tscn",
	"almanac": "res://scenes/AlmanacScene.tscn",
	"press": "res://scenes/PressScene.tscn",
	"interview": "res://scenes/InterviewScene.tscn",
}

## Screens whose opening takes a while on a phone (their _ready builds a lot):
## the cover says what is coming before the work starts (Android pass,
## 2026-11-07: My list took 6-16 s on desktop with a frozen screen). Every
## line on the cover says what is happening now, in the same shape:
## "Loading your list...", "Playing Round 7...", "Starting the new season...".
const LINES := {
	"draft": "Opening the draft room...",
	"list": "Loading your list...",
	"selection": "Loading the team...",
	"offseason": "Opening the trade period...",
	"season_review": "Looking back on the season...",
	"preseason": "Starting the pre-season...",
}
## A screen load still going after this long shows ScreenTransition.LOADING.
const SLOW_MS := 150

var stack: Array = []
## Tests: load the next screen as a browser build without threads does.
var test_main_thread_load := false


func go(key: String) -> void:
	var path := str(SCENES.get(key, key))
	if not ResourceLoader.exists(path):
		push_error("Router: scene not found for '%s' (%s)" % [key, path])
		return
	stack.append(key)
	# Under the cover (ScreenTransition; still with Reduced motion) the save
	# and the swap happen after the cover is drawn, and the scene loads on a
	# thread while the dots sweep in. A headless test run swaps at once.
	var wipe := get_node_or_null("/root/ScreenTransition")
	if wipe != null and bool(wipe.call("cover_on")):
		# A browser build has no threads: the "threaded" load would run on the
		# main thread while the dots sweep in and freeze them half way. There it
		# starts under full cover, once the line is on screen (_covered_swap).
		if not load_on_main_thread():
			ResourceLoader.load_threaded_request(path)
		wipe.call("cover", _covered_swap.bind(key, path, wipe), str(LINES.get(key, "")))
		return
	_swap(key, path, true)


## True where loading a scene blocks the main thread (a browser build without
## threads). Tests set test_main_thread_load.
func load_on_main_thread() -> bool:
	return test_main_thread_load or (OS.has_feature("web") and not OS.has_feature("threads"))


## Under full cover: save, wait for the threaded load (LOADING goes up if it
## is slow and no line is on the cover yet), then swap. A named line
## ("Loading your list...") is never replaced by the generic one.
func _covered_swap(key: String, path: String, wipe: Node) -> void:
	if GameState._dirty and not bool(wipe.call("line_visible")):
		wipe.call("show_line", ScreenTransition.LOADING)
		await wipe.call("drawn")
	GameState.autosave_if_dirty()
	if load_on_main_thread():
		if not bool(wipe.call("line_visible")):
			wipe.call("show_line", ScreenTransition.LOADING)
			await wipe.call("drawn")
		ResourceLoader.load_threaded_request(path)
	var started := Time.get_ticks_msec()
	while ResourceLoader.load_threaded_get_status(path) == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
		if Time.get_ticks_msec() - started >= SLOW_MS and not bool(wipe.call("line_visible")):
			wipe.call("show_line", ScreenTransition.LOADING)
		await get_tree().process_frame
	var packed: PackedScene = null
	if ResourceLoader.load_threaded_get_status(path) == ResourceLoader.THREAD_LOAD_LOADED:
		packed = ResourceLoader.load_threaded_get(path) as PackedScene
	if packed == null:
		_swap(key, path, false)
		return
	var err := get_tree().change_scene_to_packed(packed)
	if err != OK:
		push_error("Router: change_scene_to_packed failed (%d) for %s" % [err, path])
		return
	MusicManager.set_context(key)


func _swap(key: String, path: String, ease_in: bool) -> void:
	# Every screen change is a safe point to save (GameState skips it while a
	# live match is half played). With the wipe on, this runs under full
	# cover, so the dots answer the tap at once and the save happens behind
	# them, still before the next screen reads anything.
	GameState.autosave_if_dirty()
	var err := get_tree().change_scene_to_file(path)
	if err != OK:
		push_error("Router: change_scene_to_file failed (%d) for %s" % [err, path])
		return
	MusicManager.set_context(key)
	if ease_in:
		_ease_in()


## The new screen eases in rather than cutting (director, 2026-10-08: motion).
func _ease_in() -> void:
	if not UiKit.motion_on():
		return
	await get_tree().process_frame
	await get_tree().process_frame
	var scene := get_tree().current_scene as CanvasItem
	if scene == null:
		return
	scene.modulate.a = 0.0
	# Never linear: an ease-out, quick at first and settling.
	scene.create_tween().tween_property(scene, "modulate:a", 1.0, UiKit.Motion.DUR_FAST) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)


## Replace the current entry instead of pushing - used for boot -> menu.
func replace(key: String) -> void:
	if not stack.is_empty():
		stack.pop_back()
	# Going "back" to a screen already under this one must not stack it twice
	# (draft -> menu left the menu in the stack two deep).
	while not stack.is_empty() and str(stack[stack.size() - 1]) == key:
		stack.pop_back()
	go(key)


func back() -> void:
	if stack.size() <= 1:
		return
	# Take both this screen and the one we return to off the stack: go()
	# pushes the target again. Leaving it on made it appear twice, so every
	# later back landed on the same screen.
	stack.pop_back()
	go(str(stack.pop_back()))


func current() -> String:
	return str(stack[stack.size() - 1]) if not stack.is_empty() else ""


func can_go_back() -> bool:
	return stack.size() > 1


# ---------------------------------------------------------------------------
# Back button (Android back gesture, Escape on desktop)
# ---------------------------------------------------------------------------
var _web_back = null    # keeps the browser callback alive


func _ready() -> void:
	# Long-press a football word for its rule (row T3.R43, P-61), on every screen.
	var words := WordPress.new()
	words.name = "WordPress"
	add_child(words)
	if OS.has_feature("web"):
		_hook_browser_back()


## In a browser the Back button / Android back gesture would leave the page
## (and the career with it). Keep one history entry ahead: a Back press lands
## on it, is turned into the game's own Back, and the entry is put back.
func _hook_browser_back() -> void:
	_web_back = JavaScriptBridge.create_callback(func(_args): handle_back(false))
	JavaScriptBridge.get_interface("window").set("__aflBack", _web_back)
	JavaScriptBridge.eval("history.pushState({afl:1},'');"
			+ "window.addEventListener('popstate',function(){history.pushState({afl:1},'');"
			+ "if(window.__aflBack){window.__aflBack();}});")


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST:
		handle_back(true)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		handle_back(false)


## The mouse's back button (the thumb button on most mice) steps back like
## Escape. It is read before the GUI, so it works over any panel or overlay,
## not only over empty ground.
func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_XBUTTON1:
		get_viewport().set_input_as_handled()
		handle_back(false)


## The current scene gets first say through an optional handle_back() -> bool
## (close a popup, refuse to leave a live match). Otherwise step back one
## screen. Only the OS back button on the main menu leaves the app; Escape on
## desktop never quits.
func handle_back(from_os := false) -> void:
	var wipe := get_node_or_null("/root/ScreenTransition")
	if wipe != null and bool(wipe.get("busy")):
		return
	var scene := get_tree().current_scene
	if NameLink.close_open(scene):
		return
	if scene != null and scene.has_method("handle_back") and bool(scene.call("handle_back")):
		return
	match current():
		"main", "":
			if from_os:
				quit_game()
		"hub", "preseason":
			to_main_menu(false)
		"draft":
			# The draft knows whether it is on Choose your club (one step back is
			# the New career options) or on its board (the title).
			if scene != null and scene.has_method("back_to_menu"):
				scene.call("back_to_menu")
			else:
				replace("main")
		_:
			if can_go_back():
				back()
			else:
				to_main_menu(false)


## A test stands in here for leaving the app (it cannot quit the test run).
var quit_hook := Callable()


## Leave the game: save first if there is anything unsaved (the same save a
## close request or the OS pausing the app makes), then quit. Nothing is lost:
## every step of a career saves as it happens, and a match half played keeps
## the save from before it, as on any other way out.
func quit_game() -> void:
	GameState.autosave_if_dirty()
	if quit_hook.is_valid():
		quit_hook.call()
	else:
		get_tree().quit()


## Clears history and returns to the main menu, resetting the season.
## The career stays on disk: the main menu offers Continue Career.
func to_main_menu(wipe_save := true) -> void:
	if wipe_save:
		GameState.autosave()
		GameState.reset()
	stack = []
	go("main")


## Open New career setup from inside a career without deleting the existing
## save. The normal New career confirmation remains the destructive gate.
func to_new_career_setup() -> void:
	GameState.autosave()
	# The season picked on the year step stays picked (Legacy mode, row 142 L2).
	GameState.reset(GameState.dataset)
	GameState.new_career_setup_requested = true
	stack = []
	go("main")
