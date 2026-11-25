// The 3D view's far crowd (row 202 step 2c, Bible 2.92; Oval3DCrowd, beyond 55 m): one supporter
// per instance as a flat card that turns to face the camera (upright, turning only round the
// vertical), cut from an atlas of the 3D supporter drawn from the front (oval3d_crowd_people, mode 1). Columns 0-7 are his idle,
// 8-15 his cheer. The atlas holds which part each pixel is (top red, pants green, skin blue,
// hair and shoes black) times the light, so each card wears its own clothes from one picture:
// the same clothes as his 3D self (oval3d_crowd_dress.gdshaderinc), the parts the atlas cannot
// tell apart (arms from legs, the scarf round his neck) told by their height on the card.
// INSTANCE_CUSTOM as for the 3D people: x time offset, y side + 4 x zone, z seed; w which body.
shader_type spatial;
render_mode skip_vertex_transform, cull_disabled;

#include "res://scripts/ui/match/oval3d_crowd_dress.gdshaderinc"

uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform float columns = 16.0;
// Atlas rows: one body each; a card's body is its fourth instance number (w).
uniform float bodies = 1.0;
uniform float card_fps = 4.0;
uniform float cheer_dur = 2.0;   // s: the cheer clip's length, over its 8 columns
uniform float now = 0.0;
// The reactions, as the 3D people's (oval3d_crowd_people): the card shows only the cheer.
uniform vec4 react[4];
uniform float react_cheer = 3.2;
uniform float cheer_from = -100.0;
uniform float cheer_len = 4.0;
uniform float cheer_side = 0.0;
// The card's size and foot in the body's own metres (the atlas camera's frame).
uniform float card_w = 1.0;
uniform float card_h = 2.0;
uniform float card_y0 = 0.0;
uniform float card_x0 = 0.0;
// The picture stands this far in front of the body's origin (m), toward the camera: a seated
// supporter's knees reach forward over the bench, so a card at his hips hides his legs behind it.
uniform float card_fwd = 0.0;
// The atlas already holds its own light; the stand lights it again, so lift it back.
uniform float shade_lift = 1.0;
// Each body's heights (m): its collar and its pants' lowest point (Oval3DCrowdDress), and which
// bodies are children (from this one on).
uniform float neck_y[8];
uniform float legs_y[8];
uniform float torso_lo[8];
uniform float kids_from = 6.0;

varying float body;
varying vec2 local;     // where on the card: x across, y up (m, the body's own)
varying flat int top_kind;
varying flat vec3 c_top;
varying flat vec3 c_sleeve;
varying flat vec3 c_bottom;
varying flat vec3 c_skin;
varying flat vec3 c_hair;
varying flat vec3 c_club_a;
varying flat vec3 c_club_b;
varying flat vec3 c_gb;
varying flat vec3 c_gp;
varying flat int g_design;
varying flat vec4 flags;

void vertex() {
	vec3 o = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float sc = length(MODEL_MATRIX[1].xyz);
	vec3 r = INV_VIEW_MATRIX[0].xyz;
	r = normalize(vec3(r.x, 0.0, r.z));
	vec3 fwd = CAMERA_POSITION_WORLD - o;
	o += normalize(vec3(fwd.x, 0.0, fwd.z)) * card_fwd * sc;
	local = vec2(card_x0 + VERTEX.x * card_w, card_y0 + VERTEX.y * card_h);
	vec3 w = o + r * local.x * sc + vec3(0.0, 1.0, 0.0) * local.y * sc;
	VERTEX = (VIEW_MATRIX * vec4(w, 1.0)).xyz;
	vec3 to_cam = CAMERA_POSITION_WORLD - o;
	to_cam = normalize(vec3(to_cam.x, 0.0, to_cam.z));
	NORMAL = normalize((VIEW_MATRIX * vec4(normalize(to_cam + vec3(0.0, 0.15, 0.0)), 0.0)).xyz);
	vec4 ic = INSTANCE_CUSTOM;
	float s = ic.z * 97.0;
	float fr = mod(floor((now * mix(0.8, 1.2, hash(s + 21.0)) + ic.x * 30.0) * card_fps), 8.0);
	float side = crowd_side(ic);
	// The latest cheer he rises for, a beat apart from his neighbours, as the 3D people do.
	float since = -1.0;
	float best = -1.0;
	for (int k = 0; k < 4; k++) {
		vec4 e = react[k];
		if (e.x < -50.0 || int(e.z + 0.5) != 0 || abs(side - e.y) > 0.01 || e.x < best) {
			continue;
		}
		if (hash(s + 31.0 * float(k) + fract(e.x * 0.137) * 50.0) >= e.w) {
			continue;
		}
		float dt = now - e.x - mix(0.05, 0.7, hash(s + 41.0 + float(k)));
		if (dt > 0.0 && dt < react_cheer * mix(0.8, 1.25, hash(s + 47.0))) {
			best = e.x;
			since = dt;
		}
	}
	float old = now - cheer_from;
	if (since < 0.0 && abs(side - cheer_side) < 0.01 && old > 0.0 && old < cheer_len) {
		since = old + ic.x * 0.3;
	}
	if (since >= 0.0) {
		fr = 8.0 + min(7.0, floor(clamp(since, 0.0, cheer_dur) / cheer_dur * 8.0));
	}
	body = min(bodies - 1.0, floor(ic.w * bodies));
	UV = vec2((fr + UV.x) / columns, (body + UV.y) / bodies);
	Outfit d = crowd_outfit(ic, body >= kids_from);
	top_kind = d.top_kind;
	c_top = d.top;
	c_sleeve = d.sleeve;
	c_bottom = d.bottom;
	c_skin = d.skin;
	c_hair = d.hair;
	c_club_a = d.club_a;
	c_club_b = d.club_b;
	c_gb = d.g_base;
	c_gp = d.g_pat;
	g_design = d.design;
	flags = vec4(d.long_legs ? 1.0 : 0.0, d.scarf ? 1.0 : 0.0, d.beanie ? 1.0 : 0.0, d.scalp_hair ? 1.0 : 0.0);
}

void fragment() {
	vec4 c = texture(atlas, UV);
	// The atlas's empty pixels are black: at a distance its smaller copies mix that black into
	// each edge, so take the colour back out of the coverage.
	c.rgb /= max(c.a, 0.05);
	float s = max(max(c.r, c.g), c.b);
	int b = int(body + 0.5);
	float neck = neck_y[b];
	vec3 base = local.y > neck + 0.16 && flags.z > 0.5 ? c_club_a : c_hair * 0.7;
	if (s > 0.03) {
		if (c.r >= c.g && c.r >= c.b) {
			base = c_top;
			Outfit o;
			o.club_a = c_club_a;
			o.club_b = c_club_b;
			o.g_base = c_gb;
			o.g_pat = c_gp;
			o.design = g_design;
			if (flags.y > 0.5 && local.y > neck - 0.1) {
				base = crowd_scarf(o, vec3(local.x, local.y, 0.0));
			} else if (top_kind == 1) {
				base = crowd_guernsey(o, vec3(local.x, local.y, 0.0), vec2(torso_lo[b], neck));
			}
		} else if (c.g >= c.b) {
			base = c_bottom;
		} else {
			// Skin: the head above the collar, legs below the pants, arms between.
			base = c_skin;
			if (local.y < legs_y[b] + 0.03) {
				base = flags.x > 0.5 ? c_bottom : c_skin;
			} else if (local.y < neck - 0.04 && top_kind != 2) {
				base = c_sleeve;
			}
		}
	}
	ALBEDO = base * clamp((s > 0.03 ? s : 0.6) * shade_lift, 0.0, 1.0);
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 0.9;
	SPECULAR = 0.1;
}
