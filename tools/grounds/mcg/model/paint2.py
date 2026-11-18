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
        s.a+=R.normal(0,2.0,(s.h,s.w,1))
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
def glasspane(t,u0,u1,z0,z1,col,frame=(226,228,226),fw=0.08,nx=2,ny=1):
    t.rect(u0,u1,z0,z1,col)
    y0,y1=t.Y(z1),t.Y(z0);g=np.linspace(1.12,0.9,y1-y0)[:,None,None];t.a[y0:y1,t.X(u0):t.X(u1)]*=g  # sky reflection fade
    for k in range(nx+1):t.vline(u0+(u1-u0)*k/nx,fw,z0,z1,frame)
    for k in range(ny+1):t.rect(u0,u1,z0+(z1-z0)*k/ny-fw/2,z0+(z1-z0)*k/ny+fw/2,frame)
# Olympic/Ponsford stand bays 128-150 and 170-180: light blue-grey square metal panels (3 m), dark window bands
# at z 4.0, 8.2, 12.3 (0.8 m), parapet at the top.
t=T(6.0,(176,190,198))
for u in (0,3):t.vline(u,0.05)
for z in np.arange(0,24,3):t.hline(z,0.05)
for z in (4.0,8.2,12.3):t.rect(0,6,z-0.4,z+0.4,(48,58,70));t.hline(z-0.42,0.06,(230,232,232))
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
t=T(6.0,(46,64,86))
for u in np.arange(0,6,1.5):t.vline(u,0.07,col=(170,176,182))
for z in (1.6,5.8,9.8,14.4,18.3):t.rect(0,6,z-0.3,z+0.3,(226,228,226))

t.save('fac_glasstower')
# Blue-grey curtain wall 190-235 with thin white horizontal bands (z 6.0, 14.0, 18.5 at 195-210; 5.2, 11.2, 15.2 at 215-235).
for nm,zs in (('fac_bluewall_a',(6.0,10.2,14.0,18.5)),('fac_bluewall_b',(5.2,11.2,15.2,19.2))):
    t=T(6.0,(64,88,116))
    for u in np.arange(0,6,1.5):t.vline(u,0.06,col=(120,138,156))
    for z in np.arange(0,24,1.2):t.hline(z,0.04,col=(98,118,138))
    for z in zs:t.rect(0,6,z-0.25,z+0.25,(222,226,228))
    t.save(nm)
# Northern Stand office blocks (19-26, 36-45): light grey cladding, large dark-green four-pane windows in rows at
# z 4.4-8.8, 11.9-15.6, 16.9-20.6; window 4.2 m wide per 6.5 m bay.
t=T(6.7,(204,208,208))
for z in np.arange(0,24,1.2):t.hline(z,0.03,mul=0.9)
for z0,z1 in ((4.4,8.7),(10.0,13.8),(15.6,19.4)):
    glasspane(t,1.8,5.6,z0,z1,(38,74,66),frame=(236,238,236),fw=0.1,nx=2,ny=2);t.rect(1.7,5.7,z0-0.25,z0,(176,180,182))
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
for z0,z1 in ((4.6,8.2),(9.8,13.4),(15.0,18.6)):glasspane(t,0.8,8.2,z0,z1,(54,70,86),fw=0.1,nx=4,ny=2);t.rect(0.7,8.3,z0-0.2,z0,(170,172,172))
t.save('fac_mcc_win')
t=T(5.8,(198,200,198))
t.rect(0,5.8,7.0,21.0,(70,88,108));t.a[t.Y(21):t.Y(7)]*=np.linspace(1.15,0.9,t.Y(7)-t.Y(21))[:,None,None]
for u in (0.3,3.2):t.vline(u,0.45,7.0,21.0,(220,224,226));t.vline(u+1.45,0.12,7.0,21.0,(150,154,158));t.vline(u+0.3,0.08,7.0,21.0,(150,154,158))
for z in (7.0,21.0):t.hline(z,0.25,col=(226,228,226))
t.save('fac_louvre')
# Plaza concrete: light broom-finished slabs with saw joints on a 3 m grid and a darker diagonal band every 12 m;
# park gravel: tan crushed rock.
N=1024;a=np.ones((N,N,3))*np.array((200,198,192),float)+R.normal(0,4,(N,N,1));p=N/12.0
for k in range(4):a[int(k*3*p):int(k*3*p)+3]*=0.8;a[:,int(k*3*p):int(k*3*p)+3]*=0.8
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(OUT+'paving.png');TILE['paving']=(12.0,12.0)
a=np.ones((N,N,3))*np.array((196,160,118),float)+R.normal(0,9,(N,N,1))*np.array((1,0.9,0.8))
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(OUT+'gravel.png');TILE['gravel']=(4.0,4.0)
json.dump(TILE,open(OUT+'tiles.json','w',newline=''),indent=0);print('ok')
