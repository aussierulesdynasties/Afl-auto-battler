class_name Oval3DCrowdSet
extends Resource
## The 3D view's supporters, baked once (tools/oval3d/build_crowd_set.gd) and loaded by
## Oval3DCrowd: eight Mixamo bodies, each a low-poly mesh with its seated idle and its goal cheer
## as a baked vertex animation, and the cards' atlas (each body drawn from the front, eight frames
## of the idle then eight of the cheer). Director, 2026-11-17 (Bible 2.92): the 3D crowd is a mix,
## 3D people near the camera and cards beyond.

## One per body: {name, share, mesh, pos_tex, nrm_tex, fps, idle: Vector2i(row, frames),
## cheer: Vector2i(row, frames)}. share is the body's part of the seats (Bible 2.87: men and women
## 62/38 of the adults, 10 in 100 children).
@export var bodies: Array = []
@export var atlas: Texture2D
## The cards' frame, in the bodies' own metres: one frame for every body, so a child's card
## stands shorter than a man's.
@export var card_w := 1.0
@export var card_h := 2.0
@export var card_x0 := 0.0
@export var card_y0 := 0.0
@export var cheer_s := 2.0      # s: the cheer clip's length (the cards' 8 cheer columns)
