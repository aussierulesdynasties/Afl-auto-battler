Football Park exterior (row 202 step 2b). A = 1991-2000 (Getty 1997 aerial), B = 2001-2013 (Alamy A1K6CR).
Blender 5.2. From build/:
  python tex.py tex_A A ; python tex.py tex_B B ; python nwtex.py tex_B     (hand-made procedural textures)
  FAST=0 TEXDIR=tex_A bash run.sh spec_A.py AT ../a/camA.json 407 612       (model fpAT.glb + render rAT.png)
  FAST=0 TEXDIR=tex_B bash run.sh spec_B.py BT ../b/camB.json 1300 956
World: x west, y south, z up, metres; fence ellipse 72.5 x 88.5. Rulings applied: stadium only, field out,
posts out, bare fence (no boards), no lettering, no nets.
Textures are embedded in both GLBs (glTF bufferViews); a clean checkout loads fully textured in Godot 4.7.2 (A 24/24, B 26/26 surfaces).
Join audit: python joins.py A|B -> shotsJ<A|B>.json; FAST=1 TEXDIR=$PWD/tex_X bash run.sh spec_X.py JX shotsJX.json 1200 750;
python sheet.py "joins/X_*.png" X_joins -> review X_joins_0..2.png (aisles, walkways, roof ends, section edges).
proofs.sh rebuilds both models and every proof.
