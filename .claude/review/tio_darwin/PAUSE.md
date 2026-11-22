# TIO Stadium (Darwin) exterior: PAUSED, not ready for gate (usage limit, 2026-11-19)

No model built yet. Research and plan-source tools only (tools/grounds/tio_darwin/).

## Found
- Frame: origin = OSM pitch way 121389821 centroid (-12.3991417, 130.8872844), x east, y north (geo.py).
- Esri z19 (0.29 m/px) available; z20 is "map data not available". sat.py 19 5 rebuilds it.
- OSM pitch outline (osm_m.json 'pitch', 144 x 179 m) sits on the satellite boundary: use it for the fence ring.
- Reference photos: Commons "TIO Stadium, Darwin, September 2025 01-21" (CC BY-SA 4.0) + 2016 front elevation
  "Marrara Oval grandstand" (CC BY-SA 4.0). dl.py fetches them (needs sleeps, Commons rate-limits).
- Parts: Maurice Rioli Stand (west; centre grey roof x -110..-73, y -29..26; white-roof N and S wings, roofs step
  down to the ends; seats light blue/orange/purple mosaic, 2025), rear building with orange stair cylinder; Michael
  Long Centre (north, x -51..45, y 97..139, terrace in front); 5 lattice light towers with "TIO Stadium" panels;
  NE big screen on stilts (~76,49); east building (77..90, -34..5); gates "Ah Mat Gates" and "Bonson Gates"
  (probably roofs.json blobs at (-108.6,59.2) and (-130.8,-51.2): unconfirmed).
- Towers lean in the satellite (parallax): base at the narrow south end of each smear. E tower base ~ (108.7,-12.2),
  head drawn ~(104.6,0.4). NW/NE/SW/SE bases still to read.
- Outside the stadium (leave out): Wanderers FC (NE, ~104,63), St Marys FC (SE, ~93,-86), car parks.
- Ball-stop net poles behind the north goal: leave out (no nets).
## Open
- Outer palisade fence line not traced yet (west line near x -116; south under trees).
- Then: heights by camera fit, build (Blender 5.2, Traeger blend.py style), hand textures, full READY proof set.
