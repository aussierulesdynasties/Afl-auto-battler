# Texture pass (row 202 2b; director: "texture it by fucking hand to look the same but not like a fucking BLURRY PHOTO").
# Runs after mktex4.py. Repaints every plain map by hand with texpaint.py (no photo pixels): formwork joints, rain
# streaks, blotching, roof sheet ribs and laps, soffit purlins, paving slabs, painted-steel seams and wear.
# Each map keeps the mean colour mktex4 matched to the photo (keep_mean), so only the detail changes.
# Module sizes are in metres; one canvas = one texture repeat (gen.py TILE).
import json,numpy as np
from PIL import Image
from texpaint import Canvas,save,gstd
N=512
def mean_of(name):return np.asarray(Image.open('tex2/%s.png'%name).convert('RGB'),float).reshape(-1,3).mean(0)/255
def lift(c,target):
    # dark shade variants: raise the painted contrast around the mean until grey stddev >= 10.5 (lead's rule: >= 10)
    for _ in range(40):
        c.keep_mean(target);g=(c.img()*255)@np.array([0.299,0.587,0.114])
        if g.std()>=10.5:break
        m=c.a.reshape(-1,3).mean(0);c.a=m+(c.a-m)*1.3
    c.keep_mean(target)
def out(name,c,target):
    lift(c,target);save(c.img(),'tex2/%s.png'%name)
def concrete(name,tile,seed,pw=2.4,ph=1.2,streak=0.30,ties=True):
    t=mean_of(name);c=Canvas(*tile,t,seed,N);c.mottle(0.06,(1.6,0.5,0.12));c.panels(pw,ph,joint=0.012,dark=0.6,tone=0.06,stagger=0.5)
    if ties:
        for u in np.arange(0.3,tile[0],0.6):
            for v in np.arange(0.3,tile[1],0.6):
                y,x=int(v*c.pv),int(u*c.pu);c.a[y-2:y+2,x-2:x+2]*=0.7
    c.streaks([0.0],per_m=2.0,length=(0.6,min(3.2,tile[1]*0.8)),width=(0.03,0.2),amt=streak)
    c.streaks([k*ph for k in range(1,int(tile[1]/ph))],per_m=0.8,length=(0.2,0.8),amt=streak*0.5)
    c.grime_bottom(0.4,0.16);c.speckle(2,(0.006,0.02),0.18);c.grain(0.02);out(name,c,t)
def paving(name,seed):
    # the photo's concourse is asphalt and gravel, no slab joints: aggregate, patch repairs, tyre-worn darker bands
    t=mean_of(name);c=Canvas(4,4,t,seed,N);c.mottle(0.08,(2.0,0.6,0.1));c.mul(1-0.06*np.clip(c.noise(1.2,0.3),0,3))
    c.speckle(1.5,(0.02,0.08),0.30);c.speckle(10,(0.004,0.012),0.35);c.speckle(10,(0.004,0.010),0.30,light=True);c.speckle(3,(0.005,0.015),0.25,light=True);c.tint(0.25,0.8,(0.45,0.42,0.36));c.grain(0.025);out(name,c,t)
def roof(name,tile,seed,pitch=0.4):
    # ribbed steel deck: crests every 0.4 m running down the slope (v), an end lap every 4 m, dirt beside each rib
    t=mean_of(name);c=Canvas(*tile,t,seed,N);c.mottle(0.05,(3,1.0,0.3))
    d=np.abs(((np.arange(c.n)/c.pu+pitch/2)%pitch)-pitch/2);dirt=np.exp(-(d/0.06)**2)
    c.mul(1-0.12*dirt[None,:]*np.clip(1+0.8*c.noise(0.05,1.5),0,2))
    for u in np.arange(0,tile[0],pitch):c.vline(u,0.03,np.minimum(t*1.18,1));c.vline(u+0.035,0.03,t*0.62,0.85)
    c.hline(0.0,0.05,t*0.6);c.hline(0.06,0.025,np.minimum(t*1.15,1),0.6)
    c.mul(1-0.06*np.clip(c.noise(0.4,3.0),0,3));c.speckle(0.8,(0.01,0.04),0.15);c.grain(0.015);out(name,c,t)
def soffit(name,tile,seed):
    t=mean_of(name);c=Canvas(*tile,t,seed,N);c.mottle(0.06,(3,1,0.3))
    for u in np.arange(0,tile[0],0.2):c.vline(u,0.03,np.minimum(t*1.3,1),0.8);c.vline(u+0.04,0.03,t*0.6,0.6)
    for v in np.arange(0,tile[1],1.5):c.hline(v,0.12,t*0.45);c.hline(v+0.08,0.03,np.minimum(t*1.35,1),0.7)
    c.streaks([v+0.08 for v in np.arange(0,tile[1],1.5)],per_m=0.6,length=(0.3,1.0),amt=0.22);c.grain(0.015);out(name,c,t)
def painted(name,tile,seed,pw,ph,streak=0.18,grime=0.18):
    t=mean_of(name);c=Canvas(*tile,t,seed,N);c.mottle(0.04);c.panels(pw,ph,joint=0.012,dark=0.6,tone=0.04,bevel=False)
    c.streaks([0.0],per_m=1.4,length=(0.3,1.4),amt=streak);c.grime_bottom(min(0.5,tile[1]*0.3),grime)
    c.speckle(1.5,(0.005,0.015),0.25);c.mul(1-0.05*np.clip(c.noise(0.3,1.0),0,3));c.grain(0.012);out(name,c,t)
def steel(name,tile,seed):
    t=mean_of(name);c=Canvas(*tile,t,seed,N);c.mottle(0.06,(1.0,0.3));c.vline(0,0.015,t*0.6);c.hline(0,0.015,t*0.6)
    c.mul(1-0.08*np.clip(c.noise(0.2,1.0),0,3));c.speckle(3,(0.005,0.02),0.3);c.grime_bottom(0.3,0.15);c.grain(0.02);out(name,c,t)
def void(name,seed):
    # the dark undercroft behind the column line: block back wall with joints, doorways and pipes
    t=mean_of(name);c=Canvas(2,2,t,seed,N);c.mottle(0.10,(0.8,0.3));c.panels(0.4,0.2,joint=0.01,dark=0.55,tone=0.10,stagger=0.5,bevel=False)
    c.hline(0.35,0.06,np.minimum(t*1.8,1),0.8);c.vline(1.3,0.05,np.minimum(t*1.6,1),0.7)
    c.grime_bottom(0.4,0.2);c.grain(0.03);out(name,c,t)
def grass(name,seed):
    t=mean_of(name);c=Canvas(4,4,t,seed,N);c.mottle(0.10,(1.5,0.4,0.08))
    y,x=np.mgrid[0:c.n,0:c.n];blade=c.noise(0.01,0.04);c.mul(1+0.10*blade)
    c.speckle(4,(0.02,0.06),0.25);c.speckle(6,(0.005,0.02),0.25,light=True);c.tint(0.25,1.2,(0.75,0.7,0.45));c.grain(0.03);out(name,c,t)
def dirt(name,seed):
    t=mean_of(name);c=Canvas(4,4,t,seed,N);c.mottle(0.12,(1.5,0.5,0.1));c.mul(1+0.08*c.noise(0.6,0.05))
    c.speckle(8,(0.005,0.02),0.35,light=True);c.speckle(4,(0.01,0.05),0.3);c.grain(0.04);out(name,c,t)
def seat_lift(name):
    # seat maps are painted by seattex.py (rows, gaps, aisles); the dark navy block only needs its contrast lifted
    t=mean_of(name);a=np.asarray(Image.open('tex2/%s.png'%name).convert('RGB'),float)/255
    c=Canvas(2,1,t,1,a.shape[0]);c.a=a;c.n=a.shape[0];out(name,c,t)
J=[]
concrete('concrete',(4,4),11);concrete('aislec',(4,4),12);concrete('aislec_n',(4,4),13)
concrete('bowlconc',(4,4),14,ph=0.8);concrete('bowllight',(4,4),15,ph=0.8);concrete('bowlgap',(4,4),16,ph=0.8)
concrete('fcol',(1,1),17,pw=1.0,ph=1.0,ties=False);concrete('fcol_n',(1,1),18,pw=1.0,ph=1.0,ties=False)
concrete('fslab',(1,1),19,pw=1.0,ph=0.23,ties=False);concrete('fslab_n',(1,1),20,pw=1.0,ph=0.23,ties=False)
concrete('facade_n',(4,4),21);concrete('black',(2,2),22,pw=1.2,ph=0.6,ties=False)
void('fvoid',23);void('fvoid_n',24)
for k,n in enumerate(('pave','pave_n','pave_nl','pave_b0','pave_b1','pave_b2','pave_b3','pave_b4')):paving(n,30+k)
roof('roof',(4,4),40);roof('roofn',(4,4),41);roof('roofm',(2,4),42)
soffit('underside',(4,4),43);soffit('underside_n',(4,4),44)
painted('white',(2,2),50,2.0,1.0,streak=0.25,grime=0.22);painted('redpaint',(2,2),51,1.0,2.0);painted('navywall',(3,3),52,1.0,3.0)
steel('steel',(2,2),53);steel('rib',(1,1),54)
grass('grass',60);dirt('dirt',61);seat_lift('seat_N')
# kiosk fronts: painted sheet fascia, a light capping along the top, grime at the foot. Photo shades (scan along
# d 35.3): kiosk red reads duller than the end building's red box, navy reads near black in the roof's shade.
def kiosk_tex(name,col,seed):
    c=Canvas(2,2,col,seed,N);c.mottle(0.05);c.panels(1.0,2.0,joint=0.012,dark=0.6,tone=0.05,bevel=False)
    c.hline(0.03,0.06,np.minimum(np.array(col)*1.6+0.15,1),0.9);c.grime_bottom(0.6,0.25);c.streaks([0.06],per_m=1.5,length=(0.2,1.0),amt=0.2)
    c.speckle(2,(0.005,0.015),0.25);c.grain(0.015);out(name,c,np.array(col))
kiosk_tex('kioskr',np.array((195,35,39))/255*np.array((0.60,1.35,1.20)),55)
kiosk_tex('kioskb',np.array((44,84,112))/255*0.40,56)
kiosk_tex('kiosko',np.array((226,128,44))/255,57)
painted('greenpaint',(2,2.6),58,1.0,2.6)
