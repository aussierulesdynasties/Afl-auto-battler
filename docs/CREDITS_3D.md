# 3D view credits

One line per source and ground (rule: docs/MCG_STANDARD.md, "Where shipped data may come from").
These lines go on the game's credits screen before 1.0.

## Bellerive Oval

- Streets, beach, buildings and mapped trees: © OpenStreetMap contributors (ODbL).
- Buildings OpenStreetMap lacks: Microsoft Global ML Building Footprints (ODbL).
- Tree positions and heights within 700 m: "Canopy height: Meta and World Resources Institute, CC BY 4.0".
- Hills out to kunanyi: AWS Terrain Tiles (Terrarium); sources: SRTM (NASA), GMTED2010 (USGS),
  ETOPO1 (NOAA) and the other sources listed in the tiles' attribution.

## People First Stadium

- Streets, buildings, the river and mapped trees; the Gold Coast skyline in the background scene:
  © OpenStreetMap contributors (ODbL).
- The precinct's sheds and halls OpenStreetMap lacks: Microsoft Global ML Building Footprints (ODbL).

## Marvel Stadium

- Streets, harbour, rail yards, building footprints, mapped trees and the bridges:
  © OpenStreetMap contributors (ODbL).
- The landmark buildings next to the ground (tools/grounds/marvel/landmarks.py) are modelled by eye
  from Google Earth on OpenStreetMap footprints; no imagery is shipped.
- Buildings out to 950 m: City of Melbourne, 2023 Building Footprints (3D massing),
  data.melbourne.vic.gov.au, CC BY.

## Adelaide Oval

- Streets, parklands, the Torrens, building footprints and mapped trees: © OpenStreetMap contributors (ODbL).
- The stadium, the landmark buildings (tools/grounds/adelaide/landmarks.py), tree positions (ge_trees.py) and nearby
  roof colours (roof_colours.py) are measured or modelled by eye from Google Earth and Esri World Imagery on
  OpenStreetMap footprints; no imagery is shipped. Reference photos are listed in .claude/review/adelaide/SOURCES.md
  and used for shape and colour only.
