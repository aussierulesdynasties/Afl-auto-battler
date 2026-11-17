// Supporter knitwear (scarf, beanie) in any club's colours, set at run time, so Forge clubs get theirs too.
// The texture holds no colour: R = knit light and shade, G = which stripe this is, A = cut-out (scarf fringe).
// Scarf: G = stripe number x 16 (stripes counted from each end); stripe n takes colour n mod count.
// Beanie: G = 0..1, dark band to light band (mixes the first two colours).
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D knit : filter_linear_mipmap, repeat_enable;   // the beanie wraps round (u past 1 at its seam)
uniform sampler2D stripe_id : filter_nearest, repeat_disable;   // same texture, unfiltered so stripes stay crisp
uniform sampler2D knit_normal : hint_normal, filter_linear_mipmap;
uniform bool use_normal = false;
uniform bool beanie = false;
uniform vec3 colour_0 : source_color = vec3(0.0, 0.17, 0.36);
uniform vec3 colour_1 : source_color = vec3(1.0);
uniform vec3 colour_2 : source_color = vec3(0.0);
uniform vec3 colour_3 : source_color = vec3(0.0);
uniform int colour_count : hint_range(1, 4) = 2;

vec3 pick(int i) {
	return i == 0 ? colour_0 : (i == 1 ? colour_1 : (i == 2 ? colour_2 : colour_3));
}

void fragment() {
	vec4 k = texture(knit, UV);
	float shade = pow(k.r, 2.2);   // stored as sRGB brightness
	vec3 c;
	if (beanie) {
		c = mix(colour_0, colour_1, k.g) * pow(k.r * 1.25, 2.2);   // R stored at 1/1.25 so the knit's highlights fit
	} else {
		int n = int(round(texture(stripe_id, UV).g * 255.0 / 16.0));
		c = pick(n % max(colour_count, 1)) * shade;
	}
	ALBEDO = c;
	ALPHA = k.a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	if (use_normal) { NORMAL_MAP = texture(knit_normal, UV).rgb; }
	ROUGHNESS = 0.95;
	SPECULAR = 0.2;
}
