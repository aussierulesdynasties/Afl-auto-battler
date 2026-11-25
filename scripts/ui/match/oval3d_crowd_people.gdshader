// The 3D view's near crowd (row 202 step 2c, Bible 2.92; Oval3DCrowd): one supporter per instance,
// posed from a baked vertex animation table (tools/oval3d/bake_crowd_vat.py, packed into
// assets/oval3d/crowd_set.res by tools/oval3d/build_crowd_set.gd): every frame's vertex positions are a row
// of pos_tex, so thousands of people move with no skeletons. The mesh's UV.x holds each vertex's
// column; its vertex colour says what the vertex is (R top, G pants, B skin, A hair). UV.y and UV2.x
// say which part of the body it is (Oval3DCrowdDress: arm, shin, neck, scalp), so each supporter is
// dressed his own way (oval3d_crowd_dress.gdshaderinc).
// INSTANCE_CUSTOM: x = this person's own time offset (0-1), y = side + 4 x zone (the include),
// z = a seed for clothes, skin and how he reacts, w = which idle clip (0-1).
// mode 0 = in the stand; 1 = drawn into the cards' atlas (row atlas_row of the table).
shader_type spatial;
render_mode cull_back;

#include "res://scripts/ui/match/oval3d_crowd_dress.gdshaderinc"

uniform sampler2D pos_tex : filter_nearest;
uniform sampler2D nrm_tex : filter_nearest;
uniform float fps = 15.0;
uniform float now = 0.0;
// Idle clips (row, frames); n_idle of the four are used.
uniform ivec2 idle0; uniform ivec2 idle1; uniform ivec2 idle2; uniform ivec2 idle3;
uniform int n_idle = 1;
// The reactions' clips (row, frames): 0 the cheer (up out of his seat), 1 both hands to his head
// (a near miss, or the other side's goal), 2 one arm up (a fist pump).
uniform ivec2 cheer;
uniform ivec2 head_clip;
uniform ivec2 pump_clip;
// The last four moments the crowd reacted to (Oval3DCrowd.react): x when (s of match), y whose
// supporters (side), z which reaction (0-2), w the share of them who react; x < -50 is none.
uniform vec4 react[4];
// How long each reaction holds him (s): the cheer, hands on head, the fist pump.
uniform vec3 react_len = vec3(3.2, 2.6, 3.3);
// The older single goal (capture_crowd3d's prototype board): the scoring side all cheer.
uniform float cheer_from = -100.0;
uniform float cheer_len = 4.0;
uniform float cheer_side = 0.0;
// This body's top, from waist to collar (m), for the guernsey's design; and whether a child.
uniform vec2 torso = vec2(0.45, 1.05);
uniform bool child = false;
uniform int mode = 0;
uniform int atlas_row = 0;

varying vec4 role;
varying vec4 part;      // arm, shin, neck, scalp (one-hot at each vertex)
varying float tip;      // along the arm from his fingertips, in hands (Oval3DCrowdDress)
varying vec3 rest;      // where this point sits on him seated (the idle's first frame)
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
varying flat vec4 flags;  // long trousers, scarf, beanie, hair on the scalp

vec3 pose(ivec2 clip, float t, bool loop, out vec3 nrm, int vid) {
	float f = t * fps;
	float fr = float(clip.y);
	f = loop ? mod(f, fr) : clamp(f, 0.0, fr - 1.0);
	int a = int(floor(f));
	int b = loop ? (a + 1) % clip.y : min(a + 1, clip.y - 1);
	float k = fract(f);
	vec3 pa = texelFetch(pos_tex, ivec2(vid, clip.x + a), 0).xyz;
	vec3 pb = texelFetch(pos_tex, ivec2(vid, clip.x + b), 0).xyz;
	nrm = normalize(mix(texelFetch(nrm_tex, ivec2(vid, clip.x + a), 0).xyz,
			texelFetch(nrm_tex, ivec2(vid, clip.x + b), 0).xyz, k));
	return mix(pa, pb, k);
}

void vertex() {
	int vid = int(UV.x);
	role = COLOR;
	int k = int(UV.y + 0.5);
	part = vec4(k == 1 ? 1.0 : 0.0, k == 2 ? 1.0 : 0.0, k == 3 ? 1.0 : 0.0, k == 4 ? 1.0 : 0.0);
	tip = UV2.x;
	rest = texelFetch(pos_tex, ivec2(vid, idle0.x), 0).xyz;
	vec3 n1;
	vec3 p;
	vec4 ic = INSTANCE_CUSTOM;
	float s = ic.z * 97.0;
	if (mode != 0) {
		p = texelFetch(pos_tex, ivec2(vid, atlas_row), 0).xyz;
		n1 = texelFetch(nrm_tex, ivec2(vid, atlas_row), 0).xyz;
	} else {
		int pick = int(floor(ic.w * float(n_idle) * 0.999));
		ivec2 clip = pick == 0 ? idle0 : pick == 1 ? idle1 : pick == 2 ? idle2 : idle3;
		// Each sits at his own pace, so neighbours never move together.
		float t = now * mix(0.8, 1.2, hash(s + 21.0)) + ic.x * 30.0;
		p = pose(clip, t, true, n1, vid);
		// The latest moment he reacts to: not everyone does, and each a beat apart.
		float side = crowd_side(ic);
		float best = -1.0;
		float since = 0.0;
		float len = 0.0;
		int kind = 0;
		for (int r = 0; r < 4; r++) {
			vec4 e = react[r];
			if (e.x < -50.0 || abs(side - e.y) > 0.01 || e.x < best) {
				continue;
			}
			if (hash(s + 31.0 * float(r) + fract(e.x * 0.137) * 50.0) >= e.w) {
				continue;
			}
			int kk = int(e.z + 0.5);
			float delay = kk == 0 ? mix(0.05, 0.7, hash(s + 41.0 + float(r))) : mix(0.1, 0.9, hash(s + 43.0 + float(r)));
			float l = (kk == 0 ? react_len.x : (kk == 1 ? react_len.y : react_len.z)) * mix(0.8, 1.25, hash(s + 47.0));
			float dt = now - e.x - delay;
			if (dt > 0.0 && dt < l) {
				best = e.x;
				since = dt;
				len = l;
				kind = kk;
			}
		}
		// The prototype board's single goal, as before.
		float since_old = now - cheer_from - ic.x * 0.3;
		if (best < 0.0 && abs(side - cheer_side) < 0.01 && since_old > 0.0 && since_old < cheer_len) {
			best = cheer_from;
			since = since_old;
			len = cheer_len;
			kind = 0;
		}
		ivec2 rc = kind == 0 ? cheer : (kind == 1 ? head_clip : pump_clip);
		if (best >= 0.0 && rc.y > 0) {
			// Up out of the idle over a quarter of a second, back down over half a second.
			float w = clamp(since / 0.25, 0.0, 1.0) * clamp((len - since) / 0.5, 0.0, 1.0);
			vec3 n2;
			vec3 q = pose(rc, since, false, n2, vid);
			p = mix(p, q, w);
			n1 = normalize(mix(n1, n2, w));
		}
	}
	VERTEX = p;
	NORMAL = n1;
	Outfit o = crowd_outfit(ic, child);
	top_kind = o.top_kind;
	c_top = o.top;
	c_sleeve = o.sleeve;
	c_bottom = o.bottom;
	c_skin = o.skin;
	c_hair = o.hair;
	c_club_a = o.club_a;
	c_club_b = o.club_b;
	c_gb = o.g_base;
	c_gp = o.g_pat;
	g_design = o.design;
	flags = vec4(o.long_legs ? 1.0 : 0.0, o.scarf ? 1.0 : 0.0, o.beanie ? 1.0 : 0.0, o.scalp_hair ? 1.0 : 0.0);
}

void fragment() {
	if (mode == 1) {
		// The card atlas: the part (top red, pants green, skin blue; hair and shoes black) times a
		// simple light from high in front, so one picture carries both (crowd3d_card.gdshader).
		ALBEDO = vec3(0.0);
		SPECULAR = 0.0;
		ROUGHNESS = 1.0;
		vec3 n = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
		float d = clamp(dot(n, normalize(vec3(0.3, 0.8, 0.5))), 0.0, 1.0);
		EMISSION = role.rgb * (0.35 + 0.65 * d);
	} else {
		// A beanie covers the crown: above his collar by this much (m, as for a man).
		float crown = torso.y + (child ? 0.15 : 0.18);
		vec3 c = lin(vec3(0.1, 0.1, 0.11));   // shoes
		float m = max(max(role.r, role.g), max(role.b, role.a));
		Outfit o;
		o.club_a = c_club_a;
		o.club_b = c_club_b;
		o.g_base = c_gb;
		o.g_pat = c_gp;
		o.design = g_design;
		if (m < 0.5) {
			c = lin(vec3(0.1, 0.1, 0.11));
		} else if (role.r == m) {
			c = c_top;
			if (flags.y > 0.5 && part.z > 0.5) {
				c = crowd_scarf(o, rest);
			} else if (top_kind == 1) {
				c = crowd_guernsey(o, rest, torso);
			}
		} else if (role.g == m) {
			c = c_bottom;
		} else if (role.b == m) {
			c = c_skin;
			if (part.x > 0.5 && tip > 1.0 && top_kind != 2) {
				c = c_sleeve;
			} else if (part.y > 0.5 && flags.x > 0.5) {
				c = c_bottom;
			} else if (part.w > 0.5) {
				c = flags.z > 0.5 && rest.y > crown ? c_club_a : (flags.w > 0.5 ? c_hair : c_skin);
			}
		} else {
			c = flags.z > 0.5 && rest.y > crown ? c_club_a : c_hair;
		}
		ALBEDO = c;
		ROUGHNESS = 0.9;
		SPECULAR = 0.1;
	}
}
