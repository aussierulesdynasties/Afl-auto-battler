// PROTOTYPE (row 202, 2a lighting): the sky over a stadium, as the light sees it. Blue above;
// from the horizon up to the stands' rim (about 12 degrees from the centre square) the stands
// themselves, dark with crowd; below the horizon the grass. The ambient light and reflections
// are taken from this, so a white fence or a player's side faces the stands, not open sky,
// and only the top of a head sees the blue. Computed once into the radiance map; on screen
// only above the stands' rim in the wide views.
shader_type sky;

uniform vec4 zenith : source_color = vec4(0.22, 0.43, 0.78, 1.0);
uniform vec4 horizon : source_color = vec4(0.68, 0.78, 0.88, 1.0);
uniform vec4 bowl : source_color = vec4(0.22, 0.21, 0.23, 1.0);
uniform vec4 grass : source_color = vec4(0.22, 0.38, 0.14, 1.0);
uniform float bowl_top = 0.21;      // sin of the stands' rim elevation
uniform float energy = 1.0;
uniform float grass_energy = 1.0;   // the sunlit grass's bounce, relative to the sky

void sky() {
	float y = EYEDIR.y;
	vec3 up = mix(horizon.rgb, zenith.rgb, smoothstep(bowl_top, 0.75, y));
	vec3 c = mix(bowl.rgb, up, smoothstep(bowl_top - 0.02, bowl_top + 0.02, y));
	c = mix(grass.rgb * grass_energy, c, smoothstep(-0.02, 0.02, y));
	if (!AT_CUBEMAP_PASS && LIGHT0_ENABLED) {
		float d = dot(EYEDIR, LIGHT0_DIRECTION);
		c += LIGHT0_COLOR * smoothstep(0.99985, 0.99995, d) * 20.0;
	}
	COLOR = c * energy;
}
