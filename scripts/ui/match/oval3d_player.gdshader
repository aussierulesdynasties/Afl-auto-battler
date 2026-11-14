// PROTOTYPE: the 3D footballer's kit. The pipeline packs the same smooth region fields the
// sprite masks use (kit_<region>): COLOR = guernsey, shorts, sock, boot; UV2.x = hair. Each
// region draws where its field passes 0.5, per pixel, so a hem or armhole is a clean curve.
// The club's guernsey design and the number come from the guernsey coordinates the sprites'
// design pass renders (ard_body._store_guernsey_coords): UV = (across from the wearer's right,
// up from the hem), UV2.y = front 1 / back 0. The design and number functions below are
// copied unchanged from assets/vignette/figure.gdshader, so a club wears the same guernsey
// in 3D as in the vignettes; change them there first and copy them back.
// On the socks UV.y is where the sock band sits (0..1, 17 to 11 cm below the knee).
shader_type spatial;

uniform vec4 skin : source_color = vec4(0.76, 0.57, 0.45, 1.0);
uniform vec4 hair : source_color = vec4(0.15, 0.10, 0.07, 1.0);
uniform vec4 shorts : source_color;
uniform vec4 boot : source_color = vec4(0.06, 0.06, 0.07, 1.0);
// The club's kit (GameDB.club_guernsey) as the vignettes' figure material takes it, one kit.
uniform vec4 kit_base[1];
uniform vec4 kit_pattern[1];
uniform vec4 kit_pattern2[1];
uniform vec4 kit_pattern3[1];
uniform float kit_design[1];
uniform sampler2D digits_tex : filter_linear, repeat_disable;   // 0-9: R fill, G outline
uniform sampler2D kit_atlas : filter_linear, repeat_disable;
uniform ivec2 kit_grid = ivec2(1, 1);
// The player's own number (0-99), per figure; -1 for none.
instance uniform int number = -1;

const vec2 NUMBER_ACROSS = vec2(0.24, 0.76);   // about 26 cm for two digits
const vec2 NUMBER_UP = vec2(0.34, 0.80);       // about 27 cm tall, as AFL numbers are

float region(float f) {
	float aa = max(fwidth(f), 1e-3);
	return smoothstep(0.5 - aa, 0.5 + aa, f);
}

// 1 where x is past edge, 0 before it, anti-aliased over a pixel.
float over(float x, float edge) {
	float w = max(fwidth(x), 1e-4);
	return clamp((x - edge) / w + 0.5, 0.0, 1.0);
}

// 1 on alternate bands of a coordinate (count bands across 0..1).
float bands(float x, float count) {
	float t = abs(fract(x * count * 0.5) - 0.5) * 2.0;   // triangle wave, 0..1
	float w = max(fwidth(x * count), 1e-4);
	return clamp((t - 0.5) / w + 0.5, 0.0, 1.0);
}

// Pattern weights on the guernsey: x = pattern colour, y = second pattern colour.
// g = (across 0..1 from the wearer's right, up 0..1 from the hem, front 1 / back 0).
vec2 design_core(int d, vec3 g) {
	if (d == 1) {          // stripes
		return vec2(bands(g.x, 7.0), 0.0);
	} else if (d == 2) {   // hoops
		return vec2(bands(g.y, 9.0), 0.0);
	} else if (d == 3) {   // sash: wearer's left shoulder to right hip
		float off = g.x - (0.14 + 0.72 * g.y);
		return vec2(over(0.11, abs(off)), 0.0);
	} else if (d == 4) {   // yoke: across the shoulders, to a V at the chest
		return vec2(over(g.y, 0.62 + 0.8 * abs(g.x - 0.5)), 0.0);
	} else if (d == 5) {   // band: three hoops round the middle, the centre one in the second colour
		float inside = over(g.y, 0.40) * over(0.64, g.y);
		float centre = over(g.y, 0.48) * over(0.56, g.y);
		return vec2(inside - centre, centre);
	} else if (d == 6) {   // chevrons on the front
		float c = g.y - 0.9 * abs(g.x - 0.5);
		float on = over(c, 0.38) * over(0.86, c) * g.z;
		return vec2(bands(c, 6.0) * on, 0.0);
	} else if (d == 7) {   // panels: wearer's right third, middle third, left third, on the front
		float mid = over(g.x, 0.36) * over(0.64, g.x);
		float right = over(0.36, g.x);
		return vec2(mid, right) * g.z;   // the back plain, as St Kilda's is
	} else if (d == 8) {   // chevron: a deep V from the shoulders, pattern colour outside, second colour inside
		float c = g.y - 2.0 * abs(g.x - 0.5);
		float band = over(c, 0.44) * over(0.76, c);
		float inside = over(c, 0.60);
		return vec2(band * (1.0 - inside), band * inside) * g.z;
	} else if (d == 9) {   // sides: panels down each side, widening to the hem
		return vec2(over(abs(g.x - 0.5), 0.33 - 0.06 * (1.0 - g.y)), 0.0);
	} else if (d == 10) {  // tiers: the top in the pattern colour, a band below it, the base under that
		float top = over(g.y, 0.62);
		float band = over(g.y, 0.52) * over(0.62, g.y);
		return vec2(top, band);
	} else if (d == 11) {  // shoulders: panels over each shoulder, from beside the neck to the armpit
		return vec2(over(g.y, 1.18 - 2.27 * abs(g.x - 0.5)), 0.0);
	} else if (d == 12) {  // map: Tasmania on the chest in the pattern colour, a T on it in the second colour
		float a = (g.x - 0.5) / 0.17;          // -1..1 across the map, west on the wearer's right
		float b = (g.y - 0.47) / 0.35;         // 0 at the southern tip, 1 along the north coast
		float lean = 0.12 * (1.0 - b);         // the south tip sits east of centre
		float half_w = 1.0 - pow(1.0 - clamp(b, 0.0, 1.0), 2.6);   // full and blunt, not a shield
		float land = over(half_w, abs(a - lean)) * over(b, 0.0) * over(1.0 - 0.06 * a, b) * g.z;
		float bar = over(b, 0.62) * over(0.80, b) * over(0.55, abs(a));
		float stem = over(b, 0.22) * over(0.80, b) * over(0.17, abs(a));
		float t = max(bar, stem) * land;
		return vec2(land - t, t);
	} else if (d == 13) {  // suit (the coach): the jacket open at the collar on the shirt (pattern), a tie (second colour)
		float open = over(g.y, 0.58 + 1.9 * abs(g.x - 0.5)) * g.z;
		float tie = open * over(0.028, abs(g.x - 0.5)) * over(0.93, g.y);
		return vec2(open - tie, tie);
	} else if (d == 14) {  // lowhoops (Adelaide): plain top, hoops below the chest - pattern, second, base, repeating
		float f = mod((0.57 - g.y) / 0.071, 3.0);
		float low = over(0.57, g.y);
		return vec2(over(f, 0.0) * over(1.0, f), over(f, 1.0) * over(2.0, f)) * low;
	} else if (d == 15) {  // giants (GWS): the top in the pattern colour, a G on the front below it in the second
		float top = over(g.y, 0.56);
		float dx = (g.x - 0.5) / 0.26;     // + towards the wearer's left
		float dy = (0.27 - g.y) / 0.20;    // + down
		float r = length(vec2(dx, dy));
		float ring = over(r, 0.55) * over(1.0, r);
		float ang = atan(dy, dx);
		float gap = over(ang, -0.70) * over(0.17, ang);
		float bar = over(dx, 0.0) * over(1.0, dx) * over(dy, -0.05) * over(0.25, dy);
		float mark = clamp(ring * (1.0 - gap) + bar, 0.0, 1.0) * g.z;
		return vec2(top, mark * (1.0 - top));
	} else if (d == 16) {  // wings (West Coast): the top in the pattern colour, its lower edge arching up in the middle
		float t = clamp(abs(g.x - 0.5) / 0.36, 0.0, 1.0);
		float arch = sqrt(1.0 - t * t);   // a broad round arch, nearly armpit to armpit
		return vec2(over(g.y, 0.40 + 0.32 * arch), 0.0);
	} else if (d == 17) {  // twohoops (Western Bulldogs): a pattern-colour hoop over a second-colour hoop, below the chest
		return vec2(over(g.y, 0.38) * over(0.47, g.y), over(g.y, 0.25) * over(0.34, g.y));
	}
	return vec2(0.0);
}

// The designs clubs wore in earlier seasons (Legacy mode, each copied from the club's
// home guernsey that year; docs/research/era_guernseys). x, y = the pattern colours as
// design_core's, z = a third pattern colour. g.x runs from the wearer's right, so on
// the front it is left to right as you look at him, and on the back right to left.
vec3 design(int d, vec3 g) {
	if (d < 18) {
		return vec3(design_core(d, g), 0.0);
	}
	float front = g.z;
	float back = 1.0 - g.z;
	float ax = abs(g.x - 0.5);
	if (d == 18) {         // anchor (Fremantle 1995-2010): white anchor arms from the armpits to a point
		// at the stomach and a shank up to the collar; green above on the wearer's right,
		// red on his left. The back: green and red across the shoulders.
		float arm = 0.47 + 0.36 * pow(clamp(ax / 0.46, 0.0, 1.0), 1.4);
		float upper = over(g.y, arm + 0.075);
		float arms = over(g.y, arm) * (1.0 - upper);
		float shank = over(0.022 + 0.05 * clamp((0.66 - g.y) / 0.12, 0.0, 1.0), ax) * upper;
		float colour = upper * (1.0 - shank) * front + over(g.y, 0.84) * back;
		float right = over(0.5, g.x);
		return vec3((arms + shank) * front, colour * right, colour * (1.0 - right));
	} else if (d == 19) {  // power97 (Port Adelaide 1997-2009): teal top, black below; claw slashes
		// rising to the wearer's left shoulder, black through the teal and white through the black.
		// The back: teal across the shoulders, white to mid-back, black below.
		float v = 1.0 - g.y;
		float top = over(g.y, 0.63);
		float f = 1.18 * (g.x - 0.38) - (v - 0.55);
		float w = clamp(f / 0.35, 0.0, 1.0) * 0.55;
		float t = abs(fract((v + 1.7 * g.x) * 4.3) - 0.5) * 2.0;
		float claw = over(w, 1.0 - t) * mix(1.0, over(g.x, 0.45), top);
		vec2 f_cols = vec2(top * (1.0 - claw), (1.0 - top) * claw);
		vec2 b_cols = vec2(over(g.y, 0.86), over(g.y, 0.45) * over(0.86, g.y));
		return vec3(f_cols * front + b_cols * back, 0.0);
	} else if (d == 20) {  // eagles00 (West Coast 2000-15): navy on the wearer's right, a white strip,
		// gold on his left; the back navy, its lower third gold, white and navy.
		vec2 f_cols = vec2(over(g.x, 0.48), over(g.x, 0.38) * over(0.48, g.x));
		float low = over(0.38, g.y);
		vec2 b_cols = vec2(over(g.x, 0.60), over(g.x, 0.48) * over(0.60, g.x)) * low;
		return vec3(f_cols * front + b_cols * back, 0.0);
	} else if (d == 21) {  // swans90 (Sydney 1990-91): white, a red yoke on the front with the Opera
		// House sails hanging from it on the wearer's right, red down each side, a red back yoke.
		float sail = 0.0;
		for (int i = 0; i < 3; i++) {
			sail = max(sail, clamp(1.0 - abs(g.x - (0.20 + 0.10 * float(i))) / 0.05, 0.0, 1.0));
		}
		float yoke = over(g.y, 0.72 - 0.17 * sail) * front + over(g.y, 0.84) * back;
		return vec3(max(yoke, over(ax, 0.42)), 0.0, 0.0);
	} else if (d == 22) {  // giants12 (GWS 2012-20): orange top; charcoal below, cut on the wearer's
		// right by a white G with its bar. The back orange, charcoal down the sides.
		float v = 1.0 - g.y;
		float low = over(v, 0.38);
		float white = low * over(0.48 - 1.2 * (v - 0.38), g.x);
		white *= 1.0 - over(v, 0.50) * over(0.57, v) * over(g.x, 0.06);
		vec2 f_cols = vec2(low - white, white);
		vec2 b_cols = vec2(over(ax, 0.42) * over(0.65, g.y), 0.0);
		return vec3(f_cols * front + b_cols * back, 0.0);
	} else if (d == 23) {  // saints97 (St Kilda 1997-2001): a black cross on the front, a white panel
		// under its arms to a V; the back black above, red below.
		float bottom = 0.22 + 0.36 * ax;
		float bar = over(0.06, ax) * over(g.y, bottom);
		float black = max(bar, over(g.y, 0.52) * over(0.70, g.y));
		float white = over(g.y, bottom) * over(0.52, g.y) * (1.0 - bar);
		return vec3(black * front + over(g.y, 0.42) * back, white * front, 0.0);
	} else if (d == 24) {  // lions10 (Brisbane Lions 2010-13): the top in the pattern colour to mid-chest;
		// on the back only across the shoulders.
		return vec3(over(g.y, 0.42) * front + over(g.y, 0.86) * back, 0.0, 0.0);
	} else if (d == 25) {  // dogs90 (Footscray 1990-96): a wide pattern hoop round the middle, edged
		// in the second colour.
		float hoop = over(g.y, 0.392) * over(0.540, g.y);
		float edge = over(g.y, 0.349) * over(0.392, g.y) + over(g.y, 0.540) * over(0.578, g.y);
		return vec3(hoop, edge, 0.0);
	} else if (d == 26) {  // dogs97 (Western Bulldogs 1997-2011): a pattern hoop across the chest edged
		// in the second colour; the back in the pattern colour above it.
		float hoop = over(g.y, 0.590) * over(0.705, g.y) * front + over(g.y, 0.590) * back;
		float edge = over(g.y, 0.572) * over(0.590, g.y) + over(g.y, 0.705) * over(0.723, g.y) * front;
		return vec3(hoop, edge, 0.0);
	} else if (d == 27) {  // crows06 (Adelaide 2006-09): the low hoops, cut on the front by base-colour
		// panels down each side that sweep in towards the hem.
		float side = over(ax, 0.36 + 0.14 * clamp((g.y - 0.2) / 0.37, 0.0, 1.0));
		float k = 0.36 - 0.9 * (0.2 - g.y);
		float sweep = over(0.035, abs(ax - k));
		float cut = mix(sweep, side, over(g.y, 0.2)) * front;
		return vec3(design_core(14, g) * (1.0 - cut), 0.0);
	}
	return vec3(0.0);
}

// A picture kit's colour at guernsey coordinate g (see kit_atlas).
vec3 kit_image(int cell, vec3 g) {
	bool front = g.z > 0.5;
	vec2 at = vec2(front ? g.x : 1.0 - g.x, 1.0 - g.y);
	vec2 inset = vec2(0.5) / (vec2(textureSize(kit_atlas, 0)) / vec2(float(kit_grid.x) * 2.0, float(kit_grid.y)));
	at = clamp(at, inset, vec2(1.0) - inset);
	vec2 c = vec2(float(cell % kit_grid.x) * 2.0 + (front ? 0.0 : 1.0), float(cell / kit_grid.x));
	return texture(kit_atlas, (c + at) / vec2(float(kit_grid.x) * 2.0, float(kit_grid.y))).rgb;
}

// The number printed on the back: x = 1 where it's drawn (alpha), rgb its colour.
vec4 number_on_back(int n, vec3 g, vec3 base, bool mirrored) {
	float x = (NUMBER_ACROSS.y - g.x) / (NUMBER_ACROSS.y - NUMBER_ACROSS.x);   // from behind, left to right
	if (mirrored) {
		x = 1.0 - x;      // the frame is flipped on screen: flip the digits back
	}
	float y = (NUMBER_UP.y - g.y) / (NUMBER_UP.y - NUMBER_UP.x);             // top down
	int digit = n;
	float dx = (x - 0.25) * 2.0;
	if (n >= 10) {
		digit = x < 0.5 ? n / 10 : n % 10;
		dx = x < 0.5 ? x * 2.0 : x * 2.0 - 1.0;
	}
	if (dx < 0.0 || dx > 1.0 || y < 0.0 || y > 1.0) {
		return vec4(0.0);
	}
	vec4 d = texture(digits_tex, vec2((float(digit) + dx) / 10.0, y));
	float lum = dot(base, vec3(0.299, 0.587, 0.114));
	vec3 ink = lum > 0.58 ? vec3(0.06, 0.06, 0.07) : vec3(1.0);
	// Edged in the guernsey's own colour, so it reads across stripes and panels.
	return vec4(mix(base, ink, d.r), d.g * (1.0 - smoothstep(0.35, 0.6, g.z)));
}

void fragment() {
	// glTF stores a texture coordinate's V as 1 - v (Blender's exporter flips it): undo that.
	vec3 g = vec3(UV.x, 1.0 - UV.y, 1.0 - UV2.y);
	vec3 base = kit_base[0].rgb, pat = kit_pattern[0].rgb, pat2 = kit_pattern2[0].rgb;
	vec3 pat3 = kit_pattern3[0].rgb;
	int dn = int(round(kit_design[0]));
	vec3 jumper;
	if (dn >= 100) {
		jumper = kit_image(dn - 100, g);
	} else {
		vec3 p = design(dn, g);
		jumper = base + (pat - base) * p.x + (pat2 - base) * p.y + (pat3 - base) * p.z;
	}
	if (number >= 0) {
		vec3 under = dn >= 100 ? jumper : base;
		vec4 num = number_on_back(number, g, under, false);
		jumper = mix(jumper, num.rgb, num.a);
	}
	// The sock: base colour, the band in the pattern colour (the sprites' maskA).
	float band = over(g.y, 0.0) * over(1.0, g.y);
	vec3 sock = mix(base, pat, band);
	vec3 c = skin.rgb;
	c = mix(c, hair.rgb, region(UV2.x));
	// Where two kit regions meet, each field is about 0.5 and neither might pass it, which
	// leaves a hairline of skin between guernsey and shorts. So the lower garment is drawn
	// wherever the two together cover the body, and the upper one over it at its own edge.
	c = mix(c, boot.rgb, region(COLOR.a));
	c = mix(c, sock, region(COLOR.b + COLOR.a * step(0.02, COLOR.b)));
	c = mix(c, shorts.rgb, region(COLOR.g + COLOR.r));
	c = mix(c, jumper, region(COLOR.r));
	ALBEDO = c;
	ROUGHNESS = 0.82;
}
