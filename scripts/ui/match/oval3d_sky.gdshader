// The sky over a stadium (rules 2.80 and 2.84, copied from the approved prototype
// tools/visual/look3d_sky.gdshader). Two jobs. (1) The light: computed once into the radiance map,
// it lights the ground and the men. Blue above; from the horizon up to the stands' rim (about 12
// degrees from the centre square) the stands themselves, dark with crowd; below the horizon the
// grass. So a white fence or a player's side faces the stands, not open sky, and only the top of a
// head sees the blue. (2) The sky you see: the same colours run down to the horizon, with clouds,
// the sun's halo and stars. Those are drawn on screen only, never into the radiance map.
shader_type sky;

uniform vec4 zenith : source_color = vec4(0.22, 0.43, 0.78, 1.0);
uniform vec4 horizon : source_color = vec4(0.68, 0.78, 0.88, 1.0);
uniform vec4 bowl : source_color = vec4(0.22, 0.21, 0.23, 1.0);
uniform vec4 grass : source_color = vec4(0.22, 0.38, 0.14, 1.0);
uniform float bowl_top = 0.21;      // sin of the stands' rim elevation
uniform float energy = 1.0;
uniform float grass_energy = 1.0;   // the sunlit grass's bounce, relative to the sky
uniform vec4 glow : source_color = vec4(1.0, 0.45, 0.25, 1.0);  // a sunset's glow round the sun
uniform float glow_energy = 0.0;
// The sky you see.
uniform float cover = 0.0;          // cloud cover, 0 clear to 1 a full deck
uniform float cloud_size = 1.0;     // larger = bigger, softer clouds
uniform vec4 cloud_lit : source_color = vec4(1.0, 1.0, 1.0, 1.0);    // tops and sun side
uniform vec4 cloud_dark : source_color = vec4(0.6, 0.63, 0.7, 1.0);  // thick bellies
uniform float cloud_sun = 0.5;      // how much brighter the clouds round the sun are
uniform float sun_halo = 0.0;
uniform float stars = 0.0;
uniform vec4 rim : source_color = vec4(0.0, 0.0, 0.0, 1.0);  // light thrown up over the rim
uniform float rim_energy = 0.0;
uniform float view = 1.0;
uniform vec4 seen_zenith : source_color = vec4(0.0);   // the seen sky's own colours, when
uniform vec4 seen_horizon : source_color = vec4(0.0);  // set (alpha 1); else the light's
uniform float sky_curve = 0.7;      // how high the horizon colour reaches (sin of elevation)
uniform float disc = 20.0;          // the sun's disc brightness
uniform sampler2D clouds_tex : filter_linear_mipmap, repeat_enable;  // seamless cloud noise           // the seen sky's brightness, set for the camera's exposure

float hash2(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
float hash3(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }

void sky() {
	float y = EYEDIR.y;
	float sd = LIGHT0_ENABLED ? max(dot(EYEDIR, LIGHT0_DIRECTION), 0.0) : 0.0;
	vec3 c;
	if (AT_CUBEMAP_PASS) {
		vec3 up = mix(horizon.rgb, zenith.rgb, smoothstep(bowl_top, 0.75, y));
		up += glow.rgb * glow_energy * (pow(sd, 24.0) * 0.5 + pow(sd, 128.0));
		c = mix(bowl.rgb, up, smoothstep(bowl_top - 0.02, bowl_top + 0.02, y));
		c = mix(grass.rgb * grass_energy, c, smoothstep(-0.02, 0.02, y));
	} else {
		float h = max(y, 0.0);
		vec3 zc = seen_zenith.a > 0.0 ? seen_zenith.rgb : zenith.rgb;
		vec3 hc = seen_horizon.a > 0.0 ? seen_horizon.rgb : horizon.rgb;
		c = mix(hc, zc, smoothstep(0.0, sky_curve, h));
		c += glow.rgb * glow_energy * (pow(sd, 24.0) * 0.5 + pow(sd, 128.0));
		if (LIGHT0_ENABLED) {
			c += LIGHT0_COLOR * sun_halo * (pow(sd, 48.0) + 0.25 * pow(sd, 8.0));
		}
		// Stars: fewer near the horizon, none behind cloud.
		if (stars > 0.0) {
			vec3 d = EYEDIR * 220.0;
			vec3 cell = floor(d);
			float r = hash3(cell);
			float s = step(0.988, r) * smoothstep(0.38, 0.0, length(fract(d) - 0.5));
			c += vec3(0.9, 0.92, 1.0) * s * stars * (0.4 + 0.6 * fract(r * 37.0))
					* smoothstep(0.05, 0.35, h) * (1.0 - cover);
		}
		// The towers' light thrown up over the stands' rim.
		c += rim.rgb * rim_energy * exp(-max(h - 0.08, 0.0) / 0.12);
		// Clouds on a flat layer overhead: thick bellies darker, edges and the sun side bright.
		if (cover > 0.0) {
			vec2 uv = EYEDIR.xz / (h + 0.12) * (0.9 / cloud_size);
			float n = 0.7 * texture(clouds_tex, uv * 0.22 + vec2(0.37, 0.13)).r
					+ 0.3 * texture(clouds_tex, uv * 0.7 + vec2(0.61, 0.29)).r;
			float lo = mix(0.75, 0.05, cover);
			float amt = smoothstep(lo, lo + 0.25, n) * smoothstep(0.0, 0.1, h);
			float thick = smoothstep(lo + 0.05, lo + 0.45, n);
			vec3 cc = mix(cloud_lit.rgb, cloud_dark.rgb, thick);
			cc *= 1.0 + cloud_sun * (pow(sd, 6.0) + 0.5 * pow(sd, 2.0));
			cc += rim.rgb * rim_energy * 0.8 * (1.0 - smoothstep(0.05, 0.5, h));
			c = mix(c, cc, amt * 0.85);
		}
		if (LIGHT0_ENABLED) {
			c += LIGHT0_COLOR * smoothstep(0.99985, 0.99995, sd) * disc;
		}
		c *= view;
	}
	COLOR = c * energy;
	// A dither of about one step of the Mobile renderer's 10-bit scene buffer, per colour, so a
	// dark night sky does not store in bands that the night exposure then shows (green and
	// purple stripes without it).
	if (!AT_CUBEMAP_PASS) {
		vec2 q = SCREEN_UV * vec2(1931.0, 1733.0);
		COLOR += (vec3(hash2(q), hash2(q + 17.0), hash2(q + 41.0)) - 0.5) * 0.004;
		COLOR = max(COLOR, vec3(0.0));
	}
}
