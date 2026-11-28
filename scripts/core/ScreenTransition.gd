extends CanvasLayer
## ScreenTransition (autoload) - the wipe between screens (director,
## 2026-11-05: "Yes, add it"), and the cover for every long wait. A field of
## dots sweeps across left to right in the raised surface colour, the work
## (a screen swap, a week's sim, loading a career) runs under full cover, then
## the dots sweep away. Presentation only.
##
## A long wait shows one line on the cover ("Playing Round 7...") drawn before
## the work starts, so a phone never sits on a dead screen (Android pass,
## 2026-11-07). With Reduced motion on the cover still goes up, still: a line
## saying the game is busy is information, not motion. Headless test runs skip
## the cover (instant, as before) unless a test turns `test_cover` on. While
## the cover is up no tap, click or key reaches the game, so a second tap on
## Sim the week cannot start a second week.

const SHADER := preload("res://assets/shaders/transition.gdshader")
## Each way: cover, then reveal. The brief's 0.25-0.35 s band.
const DUR := 0.28
## About one dot per this many pixels, at any window size.
const DOT_PX := 36.0
## The line a slow screen load shows when the caller gave none.
const LOADING := "Loading..."

## While blocking work runs the cover is drawn by hand no more often than this
## (keep_moving): about 12 frames a second, which costs the work only the draw.
const PUMP_MS := 80
const FLAIR := preload("res://scripts/ui/LoadFlair.gd")

## Tests: put the cover up in a headless run (still, as with Reduced motion).
static var test_cover := false

enum Phase { IDLE, COVERING, HELD, REVEALING }

var busy := false
## How many lines were drawn on the cover; tests read it.
var lines_shown := 0
## Frames keep_moving drew by hand and the time they took; tests read them.
var pumped_frames := 0
var pumped_us := 0
## False draws no frames by hand, for measuring a wait without them.
var pump_on := true
var _phase := Phase.IDLE
var _rect: ColorRect
var _label: Label
var _flair: Control
var _last_pump_ms := 0
var _pumping := false
var _mat: ShaderMaterial
var _tween: Tween
var _swap := Callable()
var _text := ""
var _ramp_in: GradientTexture2D
var _ramp_out: GradientTexture2D


func _ready() -> void:
	layer = 128
	process_mode = Node.PROCESS_MODE_ALWAYS
	_mat = ShaderMaterial.new()
	_mat.shader = SHADER
	_ramp_in = _ramp(false)
	_ramp_out = _ramp(true)
	_mat.set_shader_parameter("gradient_texture", _ramp_in)
	_mat.set_shader_parameter("shape_texture", _dot())
	_mat.set_shader_parameter("width", 0.4)
	_mat.set_shader_parameter("shape_feathering", 0.1)
	_mat.set_shader_parameter("shape_treshold", 1.0)
	_mat.set_shader_parameter("factor", 0.0)
	_rect = ColorRect.new()
	_rect.name = "TransitionRect"
	_rect.material = _mat
	_rect.color = Color.WHITE
	_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rect.visible = false
	add_child(_rect)
	_flair = FLAIR.new()
	add_child(_flair)
	# The one line on a long wait: the house heading type, in your club's
	# colour, centred on the cover.
	_label = UiKit.lbl("", UiKit.H1, UiKit.TEXT, true)
	_label.name = "CoverLine"
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	_label.offset_left = 16.0
	_label.offset_right = -16.0
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_label.visible = false
	add_child(_label)
	get_viewport().size_changed.connect(_fit)
	_fit()


## Whether the cover sweeps (motion) or simply goes up (Reduced motion).
func should_run() -> bool:
	return UiKit.motion_on()


## Whether a cover goes up at all: everywhere but a headless test run.
func cover_on() -> bool:
	return DisplayServer.get_name() != "headless" or Feel.test_motion or test_cover


## Cover the screen, call swap under full cover, then reveal. `text`, when
## given, is drawn on the full cover before swap runs; swap may await (Router
## polls a threaded load). A second call while covering or held replaces the
## pending swap (the last screen asked for wins) and runs under the same
## cover; during the reveal it covers again from where the dots are.
func cover(swap: Callable, text := "") -> void:
	_swap = swap
	_text = text
	if _phase == Phase.COVERING or _phase == Phase.HELD:
		return
	_start()


## Blocking work the player started with a tap (a week's sim, loading a
## career): the cover and `text` go up and are drawn, then work runs, then the
## screen comes back. With no cover (headless) work runs at once, so a caller
## that does not await still sees it done. A call while the cover is up is
## ignored: that is a second tap. Work that changes screen (Router.go) joins
## the same cover.
func run(text: String, work: Callable) -> void:
	if not cover_on():
		work.call()
		return
	if busy and _phase != Phase.REVEALING:
		return
	var finished := [false]
	cover(func():
		await work.call()
		finished[0] = true, text)
	while not finished[0]:
		await get_tree().process_frame


## Draw `text` on the cover (a load that turned out slow shows LOADING).
func show_line(text: String) -> void:
	if _phase != Phase.HELD or text == "":
		return
	if _label.visible and _label.text == text:
		return
	_label.text = text
	var club := str(GameState.my_club)
	_label.add_theme_color_override("font_color",
			UiKit.club_ink(club, UiKit.PANEL_ALT) if club != "" else UiKit.TEXT)
	if not _label.visible:
		_flair.call("open", club, not should_run())
		_label.offset_top = float(_flair.call("fit"))
		Season.wait_hook = keep_moving
	_label.visible = true
	lines_shown += 1


## Blocking work calls this as it goes (a match waiting on its threads, a long
## screen build), so the ball keeps turning instead of freezing mid-air: moves
## the ball and draws one frame by hand, at most every PUMP_MS. Nothing else in
## the game runs, only the frame. A browser cannot show a frame until the script
## returns, and with Reduced motion nothing moves, so there it does nothing.
func keep_moving() -> void:
	if _pumping or not pump_on or not _label.visible or not should_run():
		return
	if OS.has_feature("web") or DisplayServer.get_name() == "headless":
		return
	var now := Time.get_ticks_msec()
	if now - _last_pump_ms < PUMP_MS:
		return
	_pumping = true
	var t0 := Time.get_ticks_usec()
	_flair.call("tick")
	RenderingServer.force_draw(true, 0.0)
	pumped_us += Time.get_ticks_usec() - t0
	pumped_frames += 1
	_last_pump_ms = Time.get_ticks_msec()
	_pumping = false


## The flair on the cover; tests read it.
func flair() -> Control:
	return _flair


## Whether the line is on the cover; tests read it.
func line_visible() -> bool:
	return _label.visible and _rect.visible


## Wait until a frame with the line on it has reached the screen. A headless
## run draws nothing, so two process frames stand in.
func drawn() -> void:
	if DisplayServer.get_name() == "headless":
		await get_tree().process_frame
		await get_tree().process_frame
		return
	_last_pump_ms = Time.get_ticks_msec()
	await RenderingServer.frame_post_draw


func _start() -> void:
	busy = true
	_phase = Phase.COVERING
	_fit()
	_mat.set_shader_parameter("base_color", UiKit.PANEL_ALT)
	_rect.visible = true
	_rect.mouse_filter = Control.MOUSE_FILTER_STOP
	if _tween != null and _tween.is_valid():
		_tween.kill()
	if not should_run():
		_hold()     # Reduced motion: the cover is simply up
		return
	# Mid-reveal, cover again from about as much as the dots still cover.
	var from: float = float(_mat.get_shader_parameter("factor"))
	_mat.set_shader_parameter("gradient_texture", _ramp_in)
	_tween = create_tween()
	_tween.tween_method(_set_factor, from, 1.0, DUR * (1.0 - from)) \
			.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_callback(_hold)


## Full cover: run every pending swap (one asked for meanwhile joins this
## cover), each after its line is on screen, then reveal.
func _hold() -> void:
	_phase = Phase.HELD
	_set_factor(1.0)
	while _swap.is_valid():
		var swap := _swap
		var text := _text
		_swap = Callable()
		_text = ""
		if text != "":
			show_line(text)
			await drawn()
		await swap.call()
	# Two frames for the new screen to lay itself out before it shows.
	await get_tree().process_frame
	await get_tree().process_frame
	if _swap.is_valid():
		_hold()     # asked for during those frames
		return
	_hide_line()
	if not should_run():
		_done()
		return
	_phase = Phase.REVEALING
	# The reversed ramp clears the left first, so the dots carry on to the
	# right instead of rewinding.
	_mat.set_shader_parameter("gradient_texture", _ramp_out)
	_tween = create_tween()
	_tween.tween_method(_set_factor, 1.0, 0.0, DUR) \
			.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_callback(_done)


func _done() -> void:
	_phase = Phase.IDLE
	_rect.visible = false
	_hide_line()
	_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_set_factor(0.0)
	busy = false


func _hide_line() -> void:
	_label.visible = false
	_flair.call("close")
	Season.wait_hook = Callable()


func _set_factor(f: float) -> void:
	_mat.set_shader_parameter("factor", f)


## Keys and touches never reach the game under the cover.
func _input(event: InputEvent) -> void:
	if busy:
		get_viewport().set_input_as_handled()


## node_resolution keeps the dots round, and the tiling keeps them a steady
## size, at 1280x720, 390x844 or any resize.
func _fit() -> void:
	var size := get_viewport().get_visible_rect().size
	if size.x <= 0.0 or size.y <= 0.0:
		return
	_mat.set_shader_parameter("node_resolution", size)
	if _flair != null and _flair.visible:
		_label.offset_top = float(_flair.call("fit"))
	_mat.set_shader_parameter("shape_tiling", maxf(8.0, size.x / DOT_PX))


## Left to right, with a slight lean so the edge is not a ruler line.
## Reversed (white on the left) for the reveal.
static func _ramp(reversed: bool) -> GradientTexture2D:
	var g := Gradient.new()
	g.set_color(0, Color.WHITE if reversed else Color.BLACK)
	g.set_color(1, Color.BLACK if reversed else Color.WHITE)
	var t := GradientTexture2D.new()
	t.gradient = g
	t.width = 256
	t.height = 64
	t.fill_from = Vector2(0.0, 0.0)
	t.fill_to = Vector2(1.0, 0.15)
	return t


## One round dot, brightest at its centre. The rim stays a little above black
## so the dots meet and leave no gap at full cover.
static func _dot() -> GradientTexture2D:
	var g := Gradient.new()
	g.set_color(0, Color.WHITE)
	g.set_color(1, Color(0.15, 0.15, 0.15))
	var t := GradientTexture2D.new()
	t.gradient = g
	t.width = 64
	t.height = 64
	t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5)
	t.fill_to = Vector2(0.5, 0.0)
	return t
