extends CanvasLayer
## ScreenTransition (autoload) - the wipe between screens (director,
## 2026-11-05: "Yes, add it"). A field of dots sweeps across left to right in
## the raised surface colour, the screen swaps under full cover, then the dots
## sweep away. Router.go() is the only caller. Presentation only.
##
## Off (an instant swap) in headless runs and with Reduced motion on, the same
## rule as every other motion (UiKit.motion_on()). While the dots cover any of
## the screen, no tap, click or key reaches the game.

const SHADER := preload("res://assets/shaders/transition.gdshader")
## Each way: cover, then reveal. The brief's 0.25-0.35 s band.
const DUR := 0.28
## About one dot per this many pixels, at any window size.
const DOT_PX := 36.0

var busy := false
var _rect: ColorRect
var _mat: ShaderMaterial
var _tween: Tween
var _swap := Callable()
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
	get_viewport().size_changed.connect(_fit)
	_fit()


## Whether a screen change wipes or cuts.
func should_run() -> bool:
	return UiKit.motion_on()


## Cover the screen, call swap under full cover, then reveal. A second call
## while covering replaces the pending swap (the last screen asked for wins);
## during the reveal it covers again from where the dots are.
func cover(swap: Callable) -> void:
	_swap = swap
	if busy and _tween != null and _tween.is_valid() and _covering:
		return
	_start()


var _covering := false


func _start() -> void:
	busy = true
	_covering = true
	_fit()
	_mat.set_shader_parameter("base_color", UiKit.PANEL_ALT)
	_rect.visible = true
	_rect.mouse_filter = Control.MOUSE_FILTER_STOP
	if _tween != null and _tween.is_valid():
		_tween.kill()
	# Mid-reveal, cover again from about as much as the dots still cover.
	var from: float = float(_mat.get_shader_parameter("factor"))
	_mat.set_shader_parameter("gradient_texture", _ramp_in)
	_tween = create_tween()
	_tween.tween_method(_set_factor, from, 1.0, DUR * (1.0 - from)) \
			.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_callback(_at_full_cover)


func _at_full_cover() -> void:
	_covering = false
	var swap := _swap
	_swap = Callable()
	if swap.is_valid():
		swap.call()
	# Two frames for the new screen to lay itself out before it shows.
	await get_tree().process_frame
	await get_tree().process_frame
	if _covering:
		return    # another change started meanwhile; it owns the wipe now
	# The reversed ramp clears the left first, so the dots carry on to the
	# right instead of rewinding.
	_mat.set_shader_parameter("gradient_texture", _ramp_out)
	_tween = create_tween()
	_tween.tween_method(_set_factor, 1.0, 0.0, DUR) \
			.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_callback(_done)


func _done() -> void:
	_rect.visible = false
	_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	busy = false


func _set_factor(f: float) -> void:
	_mat.set_shader_parameter("factor", f)


## Keys and touches never reach the game under the dots.
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
