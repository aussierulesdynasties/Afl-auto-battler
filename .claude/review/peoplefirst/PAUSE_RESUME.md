# Resume notes 2026-11-19 ~15:40 Melbourne (usage limit), NOT ready for gate

Done this round (scripts in build/scripts, build in build/):
- rin re-solved from satellite (newrin.py); roof inner/outer within ~1.5 m of satellite.
- Fault 1: lower fence own white 'fencelow' material; fascia is a 2.9 m parapet (white cap, pale blue, navy).
- North end (37-124 deg, no roof): seats now run to satellite depth north_db (8.8-11.8 m) in geo_sat.json; build5 low_pf/nc_pf.
- Camera: jointcam.py fits camera + roof hin/hout to field edge and roof edges: field 0.96 px, roof inner 0.61, outer 3.1
  (was 5.7/5.0/4.6). Result cam_j.json + geo_j.json (roof ~2.5 m higher). NOT yet adopted as cam.json; check stands/fascia.

Open:
- North seats rake: photo suggests rake ~0.2-0.3 (back ~3 m), model uses 0.6 (RAKE in build5). Measure robustly, set, rebuild.
- Lead questions unanswered: scoreboard satellite vs photo position (~9 m); sign name era. Current satellite has a grass
  gap behind the goals at 88-95 deg; photo (Metricon era) has continuous seats; model follows photo.
- PAUSE.md faults 2-4, gate faults, signs, texture pass, proofs, push.
Rebuild: GEO=geo_j.json SATRIBS=1 blender -b -P build5.py -- out.glb render.png (cam.json = cam_j.json to adopt).
