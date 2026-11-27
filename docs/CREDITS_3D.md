# 3D view credits

One line per source and ground (rule: docs/MCG_STANDARD.md, "Where shipped data may come from").
These lines go on the game's credits screen before 1.0.

## Norwood Oval

- Streets, buildings, the city's towers (footprints and heights) and mapped trees: © OpenStreetMap contributors (ODbL).
- Buildings OpenStreetMap lacks: Microsoft Global ML Building Footprints (ODbL).
- Tree heights within 700 m: "Canopy height: Meta and World Resources Institute, CC BY 4.0".
- The Adelaide Hills and the plains: AWS Terrain Tiles (Terrarium); sources: SRTM (NASA), GMTED2010 (USGS),
  ETOPO1 (NOAA) and the other sources listed in the tiles' attribution.
- Tree positions the canopy map misses, and each roof's colour, were measured from aerial imagery; no imagery
  is shipped or baked into a texture.

## Bellerive Oval

- Streets, beach, buildings and mapped trees: © OpenStreetMap contributors (ODbL).
- Buildings OpenStreetMap lacks: Microsoft Global ML Building Footprints (ODbL).
- Tree positions: traced from Google Earth (positions only; no imagery is shipped).
- Tree heights where measured: "Canopy height: Meta and World Resources Institute, CC BY 4.0".
- Hills out to kunanyi: AWS Terrain Tiles (Terrarium); sources: SRTM (NASA), GMTED2010 (USGS),
  ETOPO1 (NOAA) and the other sources listed in the tiles' attribution.

## York Park (UTAS Stadium)

- Streets, the river, building footprints and mapped trees: © OpenStreetMap contributors (ODbL).
- Land cover out to 25 km: ESA WorldCover 2021 v200 (CC BY 4.0; contains modified Copernicus Sentinel data).
- Hills: AWS Terrain Tiles (Terrarium); sources: SRTM (NASA), GMTED2010 (USGS), ETOPO1 (NOAA).
- Stand and neighbour outlines and heights are measured from Google Earth (no imagery is shipped).

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

## TIO Traeger Park

- The stadium is modelled from measurements (tools/grounds/traeger); its textures are generated in code.
- Streets, buildings and mapped trees: © OpenStreetMap contributors (ODbL).
- Buildings OpenStreetMap lacks: Microsoft Global ML Building Footprints (ODbL).
- Land colour out to 24 km: Contains modified Copernicus Sentinel data 2025 (scene S2B_53KLP_20251029).
- Tree heights: "Canopy height: Meta and World Resources Institute, CC BY 4.0".
- The MacDonnell Ranges: AWS Terrain Tiles (Terrarium); sources: SRTM (NASA) and the other sources listed
  in the tiles' attribution.

## The land round every ground (tools/grounds/terrain)

- Mainland Australia: "Digital Elevation Model (DEM) of Australia derived from LiDAR 5 Metre Grid",
  © Commonwealth of Australia (Geoscience Australia), CC BY 4.0.
- Tasmania (Bellerive, York Park, North Hobart, Macquarie Point): Tasmanian 2 metre DEM, the LIST
  © State of Tasmania, CC BY 3.0.
- Wellington (Sky Stadium): New Zealand LiDAR 1m DEM, Toitū Te Whenua Land Information New Zealand,
  CC BY 4.0.
- Mars Stadium, Traeger Park, Jiangwan: FABDEM V1-2, University of Bristol and Fathom, CC BY-NC-SA 4.0,
  from Copernicus GLO-30 (© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018,
  provided under COPERNICUS by the European Union and ESA).
- Delivered through Mapterhorn terrain tiles (mapterhorn.com, Copernicus GLO-30 past the LiDAR).

## The surroundings beyond each ground (tools/grounds/backdrop/scene)

Covers the grounds whose surroundings come from this tool: Subiaco, Football Park, WACA, Optus, Ikon Park,
Whitten, Windy Hill, Moorabbin, Hands, North Hobart, Bruce, Summit, Sky, Macquarie Point, Jiangwan, Blacktown.

- Streets, buildings, water, parks and mapped trees: © OpenStreetMap contributors (ODbL).
- Buildings OpenStreetMap lacks, and building heights: Overture Maps Foundation buildings (ODbL), including
  Microsoft and Google footprints.
- Land and tree colours: Contains modified Copernicus Sentinel-2 data 2025 (via Digital Earth Australia and
  Element 84 Earth Search).
- Building heights at Sky Stadium: New Zealand LiDAR 1m DSM and DEM, Toitū Te Whenua Land Information New
  Zealand, CC BY 4.0.
- Building heights at Jiangwan: CNBH-10m (Wu et al., 2023, CC BY 4.0).
- Roof heights of big buildings and towers elsewhere, and the era checks at the closed grounds (Google Earth
  historical imagery, 2000-2013): read or compared by eye in Google Earth; only heights, outlines and
  verdicts are kept, no imagery is shipped.
- The land: see "The land round every ground" above.

## Player movement

- Walking, walking and running backwards, and side-stepping (the slow gaits): "The 100STYLE Dataset - Ian Mason"
  (Ian Mason, Sebastian Starke, Taku Komura), Creative Commons Attribution 4.0,
  https://www.ianxmason.com/100style/ . Retargeted onto our footballer (tools/oval3d/gaits/retarget_bvh.py);
  the capture files are not shipped.
