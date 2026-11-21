# Hand-painted full-height facade textures for the MCG (no photo pixels). One tile = W m along the wall x 24 m up
# (v = z / 24, so every band sits at its measured height above the plaza). Heights read off the photo elevations
# (work/zprof.py profiles of the f-views); colours are the real daylight materials.
import numpy as np,json,os
from PIL import Image
R=np.random.default_rng(7);OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'tex')+'/'
TILE=json.load(open(OUT+'tiles.json'));H=24.0;PPM=128  # pixels per metre
class T:
    def __init__(s,W,col):
        s.W=W;s.w=int(W*PPM);s.h=int(H*PPM);s.a=np.ones((s.h,s.w,3))*np.array(col,float)
        s.a+=R.normal(0,2.0,(s.h,s.w,1));s.wins=[]  # u spans of the windows drawn (tex/winspans.json)
    def Y(s,z):return int(round((H-z)*PPM))
    def X(s,u):return int(round(u*PPM))
    def rect(s,u0,u1,z0,z1,col,mul=None):
        y0,y1=max(0,s.Y(z1)),min(s.h,s.Y(z0));x0,x1=max(0,s.X(u0)),min(s.w,s.X(u1))
        if y1<=y0 or x1<=x0:return
        if mul is not None:s.a[y0:y1,x0:x1]*=mul
        else:s.a[y0:y1,x0:x1]=np.array(col,float)+R.normal(0,1.5,(max(0,y1-y0),max(0,x1-x0),1))
    def hline(s,z,t,col=None,mul=0.7):s.rect(0,s.W,z-t/2,z+t/2,col,None if col else mul)
    def vline(s,u,t,z0=0,z1=H,col=None,mul=0.75):s.rect(u-t/2,u+t/2,z0,z1,col,None if col else mul)
    def save(s,name):
        Image.fromarray(np.clip(s.a,0,255).astype(np.uint8)).save(OUT+name+'.png');TILE[name]=(s.W,H)
        p=OUT+'winspans.json';J=json.load(open(p)) if os.path.exists(p) else {}  # ribbons (>=95% of the tile) left out
        J[name]=[[max(0.0,a),min(s.W,b)] for a,b in s.wins if b-a<0.95*s.W];json.dump(J,open(p,'w',newline=''))
def glasspane(t,u0,u1,z0,z1,col,frame=(226,228,226),fw=0.08,nx=2,ny=1):
    t.rect(u0,u1,z0,z1,col);t.wins.append((u0-fw,u1+fw))
    y0,y1=t.Y(z1),t.Y(z0);g=np.linspace(1.12,0.9,y1-y0)[:,None,None];t.a[y0:y1,t.X(u0):t.X(u1)]*=g  # sky reflection fade
    for k in range(nx+1):t.vline(u0+(u1-u0)*k/nx,fw,z0,z1,frame)
    for k in range(ny+1):t.rect(u0,u1,z0+(z1-z0)*k/ny-fw/2,z0+(z1-z0)*k/ny+fw/2,frame)
# Olympic/Ponsford stand bays 128-150 and 170-180: light blue-grey square metal panels (3 m), dark window bands
# at z 4.0, 8.2, 12.3 (0.8 m), parapet at the top.
t=T(6.0,(196,200,200))
for u in (0,3):t.vline(u,0.05)
for z in np.arange(0,24,3):t.hline(z,0.05)
for z in (4.0,8.2,12.3):t.rect(0,6,z-0.4,z+0.4,(44,54,66));t.hline(z-0.42,0.06,(230,232,232))
t.save('fac_panel')
# Southern stand bays 87-110: white precast, four dark window slots at z 1.8, 6.8, 11.8, 16.8 (0.9 m), joints 1.5 m.
t=T(6.0,(232,232,226))
for u in np.arange(0,6,1.5):t.vline(u,0.04,mul=0.86)
for z in (1.8,6.8,11.8,16.8):
    t.rect(0,6,z-0.45,z+0.45,(44,50,58))
    for u in np.arange(0,6,1.5):t.vline(u+0.75,0.06,z-0.45,z+0.45,(150,156,160))
    t.rect(0,6,z+0.45,z+0.55,None,0.8)
t.save('fac_white5')
# Glass tower 155-165: dark blue glass, white floor slabs at z 1.6, 5.8, 9.8, 14.4, 18.3, mullions 1.5 m.
t=T(6.0,(44,56,70))
for u in np.arange(0,6,1.5):t.vline(u,0.07,col=(190,194,196))
for z in (1.6,5.8,9.8,14.4,18.3):t.rect(0,6,z-0.3,z+0.3,(226,228,226))

t.save('fac_glasstower')
# Great Southern Stand 190-235 (GE f180, director's gate note): pale grey precast with 1.5 m joints, the white ledges
# kept (z 6.0, 10.2, 14.0, 18.5 at 195-210; 5.2, 11.2, 15.2, 19.2 at 215-235), a dark glass window row above each ledge.
for nm,zs in (('fac_bluewall_a',(6.0,10.2,14.0,18.5)),('fac_bluewall_b',(5.2,11.2,15.2,19.2))):
    t=T(6.0,(198,200,198))
    for u in np.arange(0,6,1.5):t.vline(u,0.04,mul=0.86)
    for z in zs:
        t.rect(0,6,z+0.25,z+1.6,(44,54,66))
        for u in np.arange(0,6,1.5):t.vline(u+0.75,0.08,z+0.25,z+1.6,(176,180,182))
        t.rect(0,6,z-0.25,z+0.25,(226,228,228))
    t.save(nm)
# Northern Stand office blocks (19-26, 36-45): light grey cladding, large dark-green four-pane windows in rows at
# z 4.4-8.8, 11.9-15.6, 16.9-20.6; window 4.2 m wide per 6.5 m bay.
t=T(6.7,(204,208,208))
for z in np.arange(0,24,1.2):t.hline(z,0.03,mul=0.9)
for z0,z1 in ((4.4,8.7),(10.0,13.8),(15.6,19.4)):
    glasspane(t,1.8,5.6,z0,z1,(34,56,54),frame=(236,238,236),fw=0.1,nx=2,ny=2);t.rect(1.7,5.7,z0-0.25,z0,(176,180,182))
t.save('fac_north_win')
# Northern Stand open concourse 27-35: grey frame with dark recessed floors at z 4.8-5.6, 9.0-12.5, 14.5-16.2, 18.0-19.6.
t=T(6.0,(186,190,192))
for z0,z1 in ((4.8,5.6),(9.0,12.5),(14.5,16.2),(18.0,19.6)):t.rect(0,6,z0,z1,(40,46,54));t.rect(0,6,z1,z1+0.12,None,0.75)
for u in (0,6):t.vline(u,0.5,col=(196,200,200))
t.save('fac_open')
# MCC (261-295): light grey precast panels; window groups (three rows of four-pane windows) and the central
# vertical-fin glass wall at z 7-21.
t=T(6.0,(198,200,198))
for u in np.arange(0,6,1.5):t.vline(u,0.04,mul=0.86)
for z in np.arange(0,24,3.0):t.hline(z,0.04,mul=0.86)
t.save('fac_mcc')
t=T(8.8,(198,200,198))
for z0,z1 in ((4.6,8.2),(9.8,13.4),(15.0,18.6)):glasspane(t,0.8,8.2,z0,z1,(46,56,68),fw=0.1,nx=4,ny=2);t.rect(0.7,8.3,z0-0.2,z0,(170,172,172))
t.save('fac_mcc_win')
t=T(5.8,(198,200,198))
t.rect(0,5.8,7.0,21.0,(48,58,70));t.a[t.Y(21):t.Y(7)]*=np.linspace(1.15,0.9,t.Y(7)-t.Y(21))[:,None,None]
for u in (0.3,3.2):t.vline(u,0.45,7.0,21.0,(220,224,226));t.vline(u+1.45,0.12,7.0,21.0,(150,154,158));t.vline(u+0.3,0.08,7.0,21.0,(150,154,158))
for z in (7.0,21.0):t.hline(z,0.25,col=(226,228,226))
t.save('fac_louvre')
# North-west (Olympic stand) 326.4-342: dark full-height glazing, fine transoms every 0.7 m, light main transoms at
# z 6.0, 9.4, 13.0, 17.5, 20.0, white marker dashes on the z 20 transom every 9 m, faint mullions every 1.5 m.
t=T(9.0,(40,50,62))
for z in np.arange(0.7,23.4,0.7):t.hline(z,0.04,(54,70,92))
for u in np.arange(0,9,1.5):t.vline(u,0.05,0,23.4,(60,74,94))
for z in (6.0,9.4,13.0,17.5,20.0):t.hline(z,0.14,(150,160,170))
t.rect(4.2,4.8,19.7,20.4,(236,238,236))
t.rect(0,9,23.4,24,(150,156,160))
t.save('fac_nwglass')
# Grey blocks either side 308.5-326.4: blue-grey panels (3 m), white sills at z 4.5, 10.2, 15.5, small teal windows
# at z 20-22.
t=T(6.0,(192,196,196))
for u in (0,3):t.vline(u,0.05)
for z in np.arange(0,24,3):t.hline(z,0.05)
for z in (4.5,10.2,15.5):t.rect(0,6,z-0.12,z+0.12,(228,230,228))
for u in (0.6,4.2):glasspane(t,u,u+1.2,20.0,22.0,(44,62,66))
t.save('fac_nwgrey')
# 342-350.5: the same grey with full-height teal window columns (1.1 m) at u 0.3 and 3.3, split at the sills.
t=T(6.0,(192,196,196))
for u in (0,3):t.vline(u,0.05)
for z in (4.5,10.2,15.5):t.rect(0,6,z-0.12,z+0.12,(228,230,228))
for u in (0.3,3.3):
    for z0,z1 in ((4.7,10.0),(10.4,15.3),(15.7,22.0)):glasspane(t,u,u+1.1,z0,z1,(44,62,66),ny=2,nx=1)
t.save('fac_nwgrey2')
# North entrance 350.5-10 (f000 zoom): dark open undercroft to z 6.1 with columns every 10 m, light grey-blue cladding
# 6.1-11.3, a dark window band 11.3-13.7 (1.2 m mullions), white ledge, light glass balustrade 14.3-16.5.
def nentry(side):
    t=T(10.0,(192,196,198))
    t.rect(0,10,0,6.1,(34,44,60));t.rect(4.7,5.3,0,6.1,(170,176,180))
    for u in np.arange(0,10,1.2):t.vline(u,0.04,6.1,11.3,mul=0.9)
    if side:
        for u in np.arange(0.2,10,2.4):glasspane(t,u,u+2.2,7.2,9.6,(46,56,68),nx=2)
    glasspane(t,0,10,11.3,13.7,(46,56,68),nx=8)
    t.rect(0,10,13.7,14.3,(232,234,232))
    glasspane(t,0,10,14.3,16.5,(70,84,96),nx=8,frame=(200,206,210))
    t.save('fac_nentry2' if side else 'fac_nentry')
nentry(False);nentry(True)
# NE 53-64 (pzc60/pzc0): light blue-grey glazed cladding, horizontal rows every 1.5 m, mullions every 1.5 m.
t=T(6.0,(190,196,200))
for z in np.arange(0,24,1.5):t.hline(z,0.06,(150,156,160))
for u in np.arange(0,6,1.5):t.vline(u,0.04,mul=0.85)
for z in (6.0,12.0,18.0):t.hline(z,0.18,(220,224,226))
t.save('fac_nelight')
# 64-73 (pzc60): light grey cladding with three dark window bands at z 7-9, 12-14.5, 17-19.5 and white ledges.
t=T(6.0,(190,196,200))
for u in (0,3):t.vline(u,0.05)
for z0,z1 in ((7.0,9.0),(12.0,14.5),(17.0,19.5)):glasspane(t,0,6,z0,z1,(46,56,68),nx=4);t.hline(z0-0.1,0.16,(232,234,232))
t.save('fac_neband')
# West 250-261 (pzc240, in shade like the NW greys): blue-grey panels (3 m), dark window strip at z 14.5-17.5.
t=T(6.0,(192,196,198))
for u in (0,3):t.vline(u,0.05)
for z in np.arange(0,24,3):t.hline(z,0.05)
glasspane(t,0,6,14.5,17.5,(46,56,68),nx=4)
t.save('fac_wgrey')
# Plaza concrete: light broom-finished slabs with saw joints on a 3 m grid and a darker diagonal band every 12 m;
# park gravel: tan crushed rock.
N=1024;a=np.ones((N,N,3))*np.array((186,178,165),float)+R.normal(0,4,(N,N,1));p=N/12.0
for k in range(4):a[int(k*3*p):int(k*3*p)+3]*=0.8;a[:,int(k*3*p):int(k*3*p)+3]*=0.8
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(OUT+'paving.png');TILE['paving']=(12.0,12.0)
a=np.ones((N,N,3))*np.array((214,188,160),float)+R.normal(0,9,(N,N,1))*np.array((1,0.9,0.8))
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(OUT+'gravel.png');TILE['gravel']=(4.0,4.0)
json.dump(TILE,open(OUT+'tiles.json','w',newline=''),indent=0);print('ok')
