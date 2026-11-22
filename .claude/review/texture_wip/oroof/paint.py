# Optus roof textures, hand-drawn. roof_bay: one bay (u, rib to rib) x one cell (v, transverse arch to arch).
import numpy as np
from PIL import Image
D='D:/Temp/claude/2117a0e07442304a/b457f311-065b-4525-9ffd-7c62765dd586/scratchpad/oroof/'
W,H=2048,1024                       # ~18 m x 8 m at the outer edge -> ~110 px/m
a=np.zeros((H,W,3),np.float32);a[:]=(236,237,236)          # PTFE: even white
# welded fabric seams across the panel every ~1.6 m (5 per cell), faint
for k in range(1,5):
    y=int(k*H/5);a[y-1:y+2]=(222,223,223)
# panel seams along the bay every ~3 m (6 per bay), faint
for k in range(1,6):
    x=int(k*W/6);a[:,x-1:x+2]=(226,227,227)
# transverse steel arch at the cell edge: 0.35 m, light grey with a shadow line on the inner side
t=40;a[:t]=(196,200,204);a[H-t:]=(196,200,204);a[t:t+6]=(170,174,178)
# radial rib at the bay edge: 0.7 m truss top chord, steel grey with crisp dark edges
r=38
a[:,:r]=(182,187,192);a[:,W-r:]=(182,187,192)
a[:,r:r+5]=(140,146,152);a[:,W-r-5:W-r]=(140,146,152)
a[:,0:4]=(160,166,172);a[:,W-4:]=(160,166,172)
Image.fromarray(a.clip(0,255).astype(np.uint8)).save(D+'roof_bay.png')
# inner roof edge (gutter + lighting rail), 1.2 m tall x 24 m wide, 64 px/m
W2,H2=1536,96
b=np.zeros((H2,W2,3),np.float32);b[:]=(214,217,220)        # silver-grey gutter face
b[:10]=(240,240,238);b[10:13]=(170,174,178)                 # white capping, shadow line
b[H2-14:]=(196,200,204);b[H2-14:H2-12]=(150,154,158)        # lower lip
for x in range(0,W2,192):                                    # light fittings every 3 m on the rail
    b[40:62,x+80:x+112]=(120,126,132);b[42:60,x+82:x+110]=(238,240,236)
Image.fromarray(b.clip(0,255).astype(np.uint8)).save(D+'roof_edge.png')
