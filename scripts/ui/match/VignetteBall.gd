class_name VignetteBall
extends RefCounted
## The football in the match scenes: a Sherrin rendered in Blender (ard-asset-pipeline
## tools/blender/ball_sprite.py, packed by tools/pack_ball.py) - leather panels, seams,
## white laces and a thin dark rim so a small ball still reads. ball.png holds FRAMES
## frames of it spinning end over end, a whole turn, left to right: row 0 the red ball,
## row 1 the yellow one the AFL plays with under lights (director, 2026-10-06): the red
## ball by day, the yellow one at twilight and at night (VignetteKickoff). Each
## frame is CELL px square with the ball LENGTH px long in it.

const TEX := preload("res://assets/vignette/ball.png")
const FRAMES := 16
const CELL := 64.0
const LENGTH := 57.0
## Turns a second end over end in flight (a punt).
const SPIN := 2.0
## How far a kick drifts sideways in a strong breeze, as a share of its length.
const DRIFT := 0.06


## The yellow ball under lights (night and twilight), the red one by day: by the slot the
## ground was last drawn in (VignetteKickoff.shown).
static func night() -> bool:
	return VignetteKickoff.shown != VignetteKickoff.DAY


## A kick's sideways drift in the wind, u of the way along its flight (0 the boot, 1 where
## it lands): from and to are the flight's ends on screen, wind_px the wind's direction on
## screen (VignetteWeather.flag_stream). Nothing at either end, so the ball still leaves
## the boot and lands exactly where the match says; most in the middle. Zero unless windy.
static func drift(u: float, from: Vector2, to: Vector2, wind_px: Vector2, weather: String) -> Vector2:
	if weather != "windy":
		return Vector2.ZERO
	var line := to - from
	if line.length() < 0.001:
		return Vector2.ZERO
	var across := line.orthogonal().normalized()
	return across * across.dot(wind_px) * line.length() * DRIFT * sin(clampf(u, 0.0, 1.0) * PI)


## The ball centred at centre, length px long end to end. In flight it spins with the
## scene's time t; held or bouncing it sits laces up, a little turned (frame).
static func draw(ci: CanvasItem, centre: Vector2, length: float, t := 0.0, spinning := false,
		frame := 1) -> void:
	var f := posmod(int(floor(t * SPIN * FRAMES)), FRAMES) if spinning else frame
	var size := Vector2(CELL, CELL) * (length / LENGTH)
	var src := Rect2(f * CELL, (CELL if night() else 0.0), CELL, CELL)
	ci.draw_texture_rect_region(TEX, Rect2(centre - size * 0.5, size), src)
