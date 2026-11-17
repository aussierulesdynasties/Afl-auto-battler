# Real players' heads on the 3D oval (row 202, 2d)

Director, 2026-11-17: Tripo heads "for only the best 23 players on every 2026 list"; he generates
them himself and adds other players and Legacy players in later patches. Every other man is drawn
with recognisable features only (skin tone, size, hair, facial hair) on one plain face.

`best23_2026.csv` is the list: each 2026 club's top 23 by overall at a 2026 start (414 men, 18
clubs), with the game's player id.

## Making a head

- Tripo Studio, image to 3D, from a clear front photo of the player's head.
- **Smart Mesh** (low-poly, about 10k triangles). Never the HD model.
- Download the GLB and name it by the player id in the list: `ADE_12.glb` is Jordan Dawson.
- Put it in `Desktop/footy assets/heads/`.

The pipeline (fitting a head to the body at the neck, matching his skin below it, his own hair)
is proven on one head before the rest are made.
