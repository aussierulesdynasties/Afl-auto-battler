// What each supporter wears (row 202 2c; the MCG crowd brought up to standard, 2026-11-21), shared
// by the 3D people (oval3d_crowd_people) and the cards (oval3d_crowd_card) so a supporter wears the
// same clothes when he turns from one to the other at 55 m. A winter footy crowd, as broadcasts show
// it: mostly dark jackets and jeans, club guernseys over a long-sleeved top, scarves and beanies in
// club colours, and the cheer squads nearly all in club colours. Looks only.
// INSTANCE_CUSTOM.y = side + 4 x zone: side 0 home, 1 away, 0.5 nobody's; zone 0 the general
// stands, 1 a cheer squad, 2 the members' reserve. INSTANCE_CUSTOM.z is his seed.

uniform vec4 home_a : source_color;
uniform vec4 home_b : source_color;
uniform vec4 away_a : source_color;
uniform vec4 away_b : source_color;
// Each club's guernsey (GameDB.club_guernsey): its base and pattern colours and the design, drawn
// simply (Oval3DCrowd.DESIGNS: 0 plain, 1 stripes, 2 hoops, 3 sash, 4 yoke, 5 one band, 6 sides).
uniform vec4 home_gb : source_color;
uniform vec4 home_gp : source_color;
uniform vec4 away_gb : source_color;
uniform vec4 away_gp : source_color;
uniform int home_design = 0;
uniform int away_design = 0;

vec3 lin(vec3 c) { return pow(c, vec3(2.2)); }
float hash(float n) { return fract(sin(n * 12.9898) * 43758.5453); }

float crowd_side(vec4 ic) { return mod(ic.y, 4.0); }
float crowd_zone(vec4 ic) { return floor(ic.y / 4.0 + 0.01); }

// A winter jacket or jumper: mostly black, charcoal and navy, then greys, olive, tan and a few
// brighter ones.
vec3 jacket(float h) {
	return h < 0.22 ? vec3(0.05, 0.05, 0.06) : h < 0.38 ? vec3(0.14, 0.14, 0.15)
			: h < 0.52 ? vec3(0.07, 0.09, 0.17) : h < 0.62 ? vec3(0.32, 0.32, 0.33)
			: h < 0.70 ? vec3(0.22, 0.24, 0.16) : h < 0.77 ? vec3(0.52, 0.41, 0.28)
			: h < 0.83 ? vec3(0.62, 0.62, 0.6) : h < 0.88 ? vec3(0.33, 0.08, 0.1)
			: h < 0.93 ? vec3(0.85, 0.85, 0.82) : h < 0.97 ? vec3(0.12, 0.25, 0.35) : vec3(0.55, 0.12, 0.1);
}

// Trousers: jeans most of all, then black, grey and beige.
vec3 trousers(float h) {
	return h < 0.36 ? vec3(0.16, 0.22, 0.36) : h < 0.56 ? vec3(0.08, 0.1, 0.18)
			: h < 0.8 ? vec3(0.05, 0.05, 0.06) : h < 0.9 ? vec3(0.3, 0.3, 0.31) : vec3(0.55, 0.48, 0.36);
}

vec3 skin_tone(float sk) {
	return sk < 0.55 ? vec3(0.85, 0.68, 0.55) : sk < 0.8 ? vec3(0.72, 0.53, 0.4)
			: sk < 0.92 ? vec3(0.55, 0.38, 0.27) : vec3(0.36, 0.24, 0.17);
}

// Hair: dark brown, brown, black, blonde or grey, each with a little spread of its own.
vec3 hair_tone(float hh, float spread) {
	vec3 hc = hh < 0.3 ? vec3(0.16, 0.1, 0.06) : hh < 0.55 ? vec3(0.32, 0.21, 0.12)
			: hh < 0.75 ? vec3(0.04, 0.035, 0.03) : hh < 0.9 ? vec3(0.62, 0.5, 0.3) : vec3(0.55, 0.53, 0.5);
	return hc * mix(0.8, 1.15, spread);
}

// One supporter's clothes, all linear colour. top_kind: 0 a jacket or jumper (sleeves the same),
// 1 his club's guernsey (sleeves his top underneath), 2 a t-shirt (bare forearms).
struct Outfit {
	int top_kind;
	vec3 top;
	vec3 sleeve;
	vec3 bottom;
	vec3 skin;
	vec3 hair;
	bool long_legs;
	bool scarf;
	bool beanie;
	bool scalp_hair;
	vec3 club_a;
	vec3 club_b;
	vec3 g_base;
	vec3 g_pat;
	int design;
};

Outfit crowd_outfit(vec4 ic, bool child) {
	Outfit o;
	float s = ic.z * 97.0;
	float side = crowd_side(ic);
	float zone = crowd_zone(ic);
	bool home = side < 0.25;
	bool nobody = abs(side - 0.5) < 0.01;
	o.club_a = lin(home ? home_a.rgb : away_a.rgb);
	o.club_b = lin(home ? home_b.rgb : away_b.rgb);
	o.g_base = lin(home ? home_gb.rgb : away_gb.rgb);
	o.g_pat = lin(home ? home_gp.rgb : away_gp.rgb);
	o.design = home ? home_design : away_design;
	// The top: shares for a supporter in the general stands, a cheer squad or the members' reserve.
	float g = zone > 1.5 ? 0.12 : (zone > 0.5 ? 0.6 : 0.28);     // his club's guernsey
	float ca = zone > 1.5 ? 0.13 : (zone > 0.5 ? 0.25 : 0.17);   // a jacket in the club's first colour
	float cb = zone > 1.5 ? 0.0 : (zone > 0.5 ? 0.1 : 0.05);     // in its second
	float tee = zone > 1.5 ? 0.0 : 0.1;                          // a t-shirt
	if (nobody) { g = 0.0; ca = 0.0; cb = 0.0; }
	float h = hash(s);
	vec3 plain = lin(jacket(hash(s + 1.0)));
	if (h < g) {
		o.top_kind = 1;
		o.top = o.g_base;
		float u = hash(s + 8.0);
		o.sleeve = u < 0.6 ? lin(vec3(0.05, 0.05, 0.06)) : (u < 0.85 ? lin(vec3(0.85, 0.85, 0.82)) : o.club_b);
	} else if (h < g + ca) {
		o.top_kind = 0;
		o.top = o.club_a;
		o.sleeve = o.top;
	} else if (h < g + ca + cb) {
		o.top_kind = 0;
		o.top = o.club_b;
		o.sleeve = o.top;
	} else if (h < g + ca + cb + tee) {
		o.top_kind = 2;
		o.top = nobody || hash(s + 9.0) < 0.5 ? lin(mix(vec3(0.12), vec3(0.8), hash(s + 10.0))) : o.club_a;
		o.sleeve = o.top;
	} else {
		o.top_kind = 0;
		o.top = plain;
		o.sleeve = plain;
	}
	o.bottom = lin(trousers(hash(s + 2.0)));
	o.long_legs = hash(s + 11.0) < (child ? 0.75 : 0.93);
	o.skin = lin(skin_tone(hash(s + 3.0)));
	o.hair = lin(hair_tone(hash(s + 4.0), hash(s + 5.0)));
	float sc = zone > 1.5 ? 0.3 : (zone > 0.5 ? 0.75 : 0.45);
	o.scarf = !nobody && hash(s + 12.0) < sc;
	o.beanie = !nobody && hash(s + 13.0) < (zone > 0.5 && zone < 1.5 ? 0.25 : 0.13);
	o.scalp_hair = hash(s + 14.0) < 0.8;
	return o;
}

// His club's guernsey at a point of his top: p is the point on the seated body (its own metres),
// torso the top's waist and collar heights.
vec3 crowd_guernsey(Outfit o, vec3 p, vec2 torso) {
	float u = clamp((p.y - torso.x) / max(0.05, torso.y - torso.x), 0.0, 1.0);
	bool pat = false;
	if (o.design == 1) {
		pat = fract(p.x * 9.0) < 0.5;
	} else if (o.design == 2) {
		pat = fract(u * 4.5) < 0.5;
	} else if (o.design == 3) {
		pat = abs(p.x + (u - 0.55) * 0.55) < 0.075;
	} else if (o.design == 4) {
		pat = u > 0.78;
	} else if (o.design == 5) {
		pat = u > 0.36 && u < 0.56;
	} else if (o.design == 6) {
		pat = abs(p.x) > 0.13;
	}
	return pat ? o.g_pat : o.g_base;
}

// A scarf's colour at a point round his neck: the club's two colours in bars across it.
vec3 crowd_scarf(Outfit o, vec3 p) {
	return fract((p.x * 0.7 + p.y) * 9.0) < 0.5 ? o.club_a : o.club_b;
}
