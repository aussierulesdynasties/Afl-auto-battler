// A tower's lamp face switched on at night (Oval3DTowers): the model's own lamp pattern (pale
// frames round darker glass), its glass now glowing white and the frames dark against it.
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;

uniform sampler2D pattern : source_color, filter_linear_mipmap;
uniform bool has_pattern = false;
uniform float strength = 1.0;        // 0 off .. 1 a night game
uniform float glow = 2.6;            // the glass's brightness (over 1: the film blooms it)
uniform vec3 tint = vec3(0.96, 0.98, 1.0);

void fragment() {
	float l = 0.5;
	if (has_pattern) {
		vec3 c = texture(pattern, UV).rgb;
		l = dot(c, vec3(0.2126, 0.7152, 0.0722));
	}
	float lit = has_pattern ? 1.0 - smoothstep(0.45, 0.75, l) : 1.0;
	ALBEDO = mix(vec3(0.18), tint * glow, lit * strength);
}
