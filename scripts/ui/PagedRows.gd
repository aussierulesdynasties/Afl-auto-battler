extends Container
## Rows top to bottom in `columns` columns, as many as the room holds; the rest
## wait for the next page. The PC layouts never scroll (director, 2026-11-26:
## "No scrolling: split a screen into stages instead"), so a list too long for
## its room turns pages instead. `first` is the first row on the page; rows
## before it and past the room are hidden. Emits `paged` whenever the page or
## the rows on it change, so a pager line can say "1-14 of 37".

signal paged

var columns := 1
var col_gap := 32.0
## Space between rows in a column.
var gap := 0.0
var first := 0
## Rows on this page, and rows in all.
var shown := 0
var total := 0
var _back: Array = []
var _said := Vector3i(-1, -1, -1)


func _init() -> void:
	clip_contents = true


func _get_minimum_size() -> Vector2:
	return Vector2.ZERO   # fills the room it is given; never pushes the screen


func _notification(what: int) -> void:
	if what == NOTIFICATION_SORT_CHILDREN:
		_lay()


func rows() -> Array:
	var out := []
	for c in get_children():
		if c is Control and not (c as Control).top_level and not c.is_queued_for_deletion() \
				and not str(c.name).begins_with("Leaving_"):
			out.append(c)
	return out


func can_next() -> bool:
	return first + shown < total


func can_prev() -> bool:
	return first > 0


## The rows the next page would show, as far as is known: a page's worth.
func next_count() -> int:
	return mini(maxi(shown, 1), total - first - shown)


## `force`: the caller has just added the rows the next page shows.
func next_page(force := false) -> void:
	if not force and not can_next():
		return
	_back.append(first)
	first += maxi(shown, 1)
	queue_sort()


func prev_page() -> void:
	first = int(_back.pop_back()) if not _back.is_empty() else 0
	queue_sort()


func to_start() -> void:
	first = 0
	_back.clear()
	queue_sort()


## Lay the page out again and say so even when nothing moved (the words around
## it changed).
func repage() -> void:
	_said = Vector3i(-1, -1, -1)
	queue_sort()


func _lay() -> void:
	var kids := rows()
	total = kids.size()
	if first >= total:
		first = 0
		_back.clear()
	var cols := maxi(1, columns)
	var w := (size.x - col_gap * (cols - 1)) / cols
	var col := 0
	var y := 0.0
	var n := 0
	for i in range(kids.size()):
		var c: Control = kids[i]
		if i < first or col >= cols:
			c.visible = false
			continue
		c.size.x = w
		var h := c.get_combined_minimum_size().y
		if y > 0.0 and y + h > size.y:
			col += 1
			y = 0.0
			if col >= cols:
				c.visible = false
				continue
		c.visible = true
		fit_child_in_rect(c, Rect2(col * (w + col_gap), y, w, h))
		y += h + gap
		n += 1
	shown = n
	var now := Vector3i(first, shown, total)
	if now != _said:
		_said = now
		paged.emit.call_deferred()
