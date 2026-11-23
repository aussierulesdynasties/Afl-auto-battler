class_name TalkDice
extends Control
## Two dice for a quarter-break talk (BreakTalks): they tumble for a moment,
## then land on the roll the match already made. Looks only: the faces shown
## while tumbling are a flourish, the landed faces are the sim's.

const SIDE := 52.0
const GAP := 14.0
const TUMBLE := 0.9
const STEP := 0.07
## Pips on a face, in thirds of the face (0..2 each way).
const PIPS := {
	1: [[1, 1]], 2: [[0, 0], [2, 2]], 3: [[0, 0], [1, 1], [2, 2]],
	4: [[0, 0], [2, 0], [0, 2], [2, 2]], 5: [[0, 0], [2, 0], [1, 1], [0, 2], [2, 2]],
	6: [[0, 0], [2, 0], [0, 1], [2, 1], [0, 2], [2, 2]],
}

var faces := [1, 1]
var edge := Color.WHITE
var _tilt := [0.0, 0.0]
var _hop := [0.0, 0.0]
var _landed := true


func _init() -> void:
	custom_minimum_size = Vector2(SIDE * 2.0 + GAP + 12.0, SIDE + 16.0)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false


## Show these faces at rest, with no roll (a talk already made).
func show_faces(values: Array) -> void:
	faces = [int(values[0]), int(values[1])]
	_tilt = [0.0, 0.0]
	_hop = [0.0, 0.0]
	_landed = true
	visible = true
	queue_redraw()


## Tumble, then land on `values`; `done` runs once they have landed.
func roll(values: Array, done: Callable = Callable()) -> void:
	visible = true
	_landed = false
	var steps := int(TUMBLE / STEP)
	var tw := create_tween()
	for i in steps:
		var left := 1.0 - float(i) / float(steps)
		tw.tween_callback(func():
			faces = [randi_range(1, 6), randi_range(1, 6)]
			_tilt = [randf_range(-0.5, 0.5) * left, randf_range(-0.5, 0.5) * left]
			_hop = [absf(sin(float(i) * 1.3)) * 10.0 * left, absf(cos(float(i) * 1.1)) * 10.0 * left]
			queue_redraw())
		tw.tween_interval(STEP)
	tw.tween_callback(func():
		show_faces(values)
		if done.is_valid():
			done.call())


func is_landed() -> bool:
	return _landed


func _draw() -> void:
	var y0 := 8.0
	for k in 2:
		var x0 := 6.0 + float(k) * (SIDE + GAP)
		var centre := Vector2(x0 + SIDE / 2.0, y0 + SIDE / 2.0 - float(_hop[k]))
		draw_set_transform(centre, float(_tilt[k]), Vector2.ONE)
		var r := Rect2(-SIDE / 2.0, -SIDE / 2.0, SIDE, SIDE)
		var face := StyleBoxFlat.new()
		face.bg_color = Color("f4f1e8")
		face.set_corner_radius_all(9)
		face.set_border_width_all(3)
		face.border_color = edge
		face.draw(get_canvas_item(), r)
		var pip := SIDE * 0.095
		var step := SIDE * 0.27
		for p in PIPS.get(int(faces[k]), []):
			draw_circle(Vector2((float(p[0]) - 1.0) * step, (float(p[1]) - 1.0) * step), pip, Color("161512"))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
