shader_type canvas_item;
// Club marker A as the Tripo guernsey (GuernseyCrest): a lit white guernsey (TEXTURE, the
// light over white, x1.08, alpha = coverage) tinted by the club's colours. Made by
// ard-asset-pipeline tools/guernsey_badges.py from the Tripo mesh's render.
//   parts_tex: R trim (collar, armholes, edge), G the inside of the back through the neck,
//              B the ARD patch on the chest, A coverage.
//   designs_tex: one cell per GuernseyCrest.BADGE_DESIGNS entry, 4 a row: R the pattern
//              colour's shapes, G the second colour's (drawn in the trim colour, as the crest),
//              B a third colour's (only the anchor's).
// Every colour is a uniform, so created clubs work too.
//   kit_atlas: Legacy seasons' real guernseys (tools/kits/kit_atlas.py); kit_cell >= 0 colours
//              the guernsey from that cell's front instead of the design.

uniform sampler2D parts_tex : filter_linear_mipmap;
uniform sampler2D designs_tex : filter_linear_mipmap;
uniform vec4 primary : source_color = vec4(1.0);
uniform vec4 secondary : source_color = vec4(0.4, 0.4, 0.4, 1.0);
uniform vec4 accent : source_color = vec4(1.0, 0.84, 0.0, 1.0);
uniform vec4 third : source_color = vec4(1.0, 0.84, 0.0, 1.0);
uniform int design_cell = 0;
uniform int design_rows = 5;
uniform sampler2D kit_atlas : filter_linear, repeat_disable;
uniform ivec2 kit_grid = ivec2(12, 1);
uniform int kit_cell = -1;
// The guernsey's left and right edge in the badge (badge_light's coverage, of its width).
const float KIT_X0 = 0.184;
const float KIT_X1 = 0.816;
// Club Forge outlines the part under the pointer: 0 none, 1 body, 2 pattern, 3 trim.
uniform int highlight = 0;

float lum(vec3 c) {
	return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

void fragment() {
	vec4 lit = texture(TEXTURE, UV);
	vec4 parts = texture(parts_tex, UV);
	vec2 cell = vec2(float(design_cell % 4), float(design_cell / 4));
	vec3 d = texture(designs_tex, (cell + UV) / vec2(4.0, float(design_rows))).rgb;
	vec3 col = primary.rgb;
	col = mix(col, secondary.rgb, d.r);
	col = mix(col, accent.rgb, d.g);
	col = mix(col, third.rgb, d.b);
	if (kit_cell >= 0) {
		// The picture's front: its own collar and trim, so no trim tint over it.
		vec2 g = vec2(clamp((UV.x - KIT_X0) / (KIT_X1 - KIT_X0), 0.0, 1.0), clamp(UV.y, 0.0, 1.0));
		vec2 px = vec2(textureSize(kit_atlas, 0));
		vec2 cell_px = px / vec2(float(kit_grid.x) * 2.0, float(kit_grid.y));
		vec2 at = vec2(float(kit_cell % kit_grid.x) * 2.0, float(kit_cell / kit_grid.x)) * cell_px;
		vec2 uv = (at + clamp(g * cell_px, vec2(0.5), cell_px - 0.5)) / px;
		col = texture(kit_atlas, uv).rgb;
		col = mix(col, col * 0.45, parts.g);
	} else {
		col = mix(col, accent.rgb, parts.r);
		col = mix(col, primary.rgb * 0.45, parts.g);
	}
	vec3 patch = lum(primary.rgb) > 0.5 ? vec3(0.09, 0.07, 0.05) : vec3(0.95);
	col = mix(col, patch, parts.b);
	col *= lit.r * 1.08;
	if (highlight > 0) {
		float part = highlight == 1 ? (1.0 - max(max(d.r, d.g), parts.r))
				: (highlight == 2 ? d.r : max(d.g, parts.r));
		col = mix(col, vec3(1.0), 0.35 * part);
	}
	COLOR = vec4(clamp(col, 0.0, 1.0), lit.a);
}
