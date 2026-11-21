// A ground's surroundings (GroundModels.backdrop): the walls and roofs of the houses, flats and
// towers, as the background scene painted them in Blender. Each building's own colour (its vertex
// colour) tints the texture's plain wall; where the texture's alpha marks glass or a window frame,
// the texture shows as it is and shines (roughness 0.8 on the wall to 0.13 on the glass).
shader_type spatial;
// No shadows: the surroundings lie past the shadow map's reach, where receiving reads blue-grey.
render_mode shadows_disabled;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;

void fragment() {
	vec4 t = texture(tex, UV);
	ALBEDO = mix(COLOR.rgb * t.rgb, t.rgb, t.a);
	ROUGHNESS = mix(0.8, 0.13, t.a);
}
