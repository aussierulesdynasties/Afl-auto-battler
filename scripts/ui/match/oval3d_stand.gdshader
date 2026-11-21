// A ground model's surfaces in a match (Oval3DTurf.light_stands): the model's own colour, roughness
// and metal, lit as before by the sun, the sky and its reflections, with one change (director,
// 2026-11-21: roof undersides "grey, a faint green tint"). The sky's light map has sunlit grass
// below the horizon, as the centre square sees it; a stand's face turned down sees seats and
// concrete. amb_* is the difference between the sky's light with that grass greyed and with it as
// it is, for a face turned straight down, half down, level, half up and straight up: added to the
// sky's own light it greys what a face took from the grass. A face turned up changes by nothing.
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 albedo_col : source_color = vec4(1.0);
uniform float roughness_v = 0.85;
uniform float metallic_v = 0.0;
uniform vec3 uv_scale = vec3(1.0);
uniform vec3 uv_offset = vec3(0.0);
uniform vec3 amb_down = vec3(0.0);
uniform vec3 amb_low = vec3(0.0);
uniform vec3 amb_level = vec3(0.0);
uniform vec3 amb_high = vec3(0.0);
uniform vec3 amb_up = vec3(0.0);

void fragment() {
	vec4 a = texture(albedo_tex, UV * uv_scale.xy + uv_offset.xy) * albedo_col;
	ALBEDO = a.rgb;
	ROUGHNESS = roughness_v;
	METALLIC = metallic_v;
	float y = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).y;
	vec3 amb;
	if (y < -0.5) {
		amb = mix(amb_low, amb_down, (-y - 0.5) * 2.0);
	} else if (y < 0.0) {
		amb = mix(amb_level, amb_low, -y * 2.0);
	} else if (y < 0.5) {
		amb = mix(amb_level, amb_high, y * 2.0);
	} else {
		amb = mix(amb_high, amb_up, (y - 0.5) * 2.0);
	}
	// The diffuse share of the sky's light, as the engine's own (metal reflects, it does not scatter).
	EMISSION = a.rgb * amb * (1.0 - metallic_v);
}
