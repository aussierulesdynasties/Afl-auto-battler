// The far rows of a ground's seats (GroundModels._seat_far_mesh): one quad a seat, back top to tread
// front, painted as the shell looks from the field, its mipmaps averaging the gaps and rows away.
// Lit as the shell it stands for: the shell's back (leaning 12 degrees) and pan (flat) each take the
// sun by their own normal; the sky comes in by the mesh normal, the two faces' mix. Distance fades it in where
// the shells' own material fades them out (pixel dither, as Godot's PIXEL_DITHER).
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic;
uniform float fade_from = 40.0;
uniform float fade_to = 70.0;

varying vec3 nb;
varying vec3 np;

void vertex() {
	nb = normalize((MODELVIEW_MATRIX * vec4(0.0, 0.2085, 0.978, 0.0)).xyz);
	np = normalize((MODELVIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
}

void fragment() {
	ALBEDO = texture(tex, UV).rgb;
	ROUGHNESS = 1.0;
	AO = 0.85;
	AO_LIGHT_AFFECT = 0.0;
	float f = clamp((length(VERTEX) - fade_from) / (fade_to - fade_from), 0.0, 1.0);
	float t = fract(52.9829189 * fract(dot(FRAGCOORD.xy, vec2(0.06711056, 0.00583715))));
	if (f < t) {
		discard;
	}
}

void light() {
	// Each face's share of the shell's light, fitted to the shells' own render at Bellerive (2026-11-23,
	// cloud render, both stands within 6 of each channel): the back as seen from the field takes half,
	// the pan a little under a quarter (the rest of the shell is in its own shade).
	float lam = 0.5 * max(dot(nb, LIGHT), 0.0) + 0.22 * max(dot(np, LIGHT), 0.0);
	DIFFUSE_LIGHT += lam * ATTENUATION * LIGHT_COLOR / PI;
}
