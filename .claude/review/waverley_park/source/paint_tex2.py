# Gate fix 2026-11-19 (lead's fault board, faults 1-3): hand-painted maps for the near-side apron, the dark steel
# deck along the near-left wall and the grey Members roof masts. No photo pixels. Target mean colours are the photo's
# colour at traced points (apchk.py) divided by the render's lighting response on that surface (render/texture).
# Ground maps use only fine detail (aggregate, crumbs, tufts) on an 8 m repeat: no large blotches, no patch tones.
import numpy as np
from texpaint import Canvas,save
def lift(c,target):
    # same as paint_tex.lift: raise painted contrast around the mean until grey stddev >= 10.5
    for _ in range(40):
        c.keep_mean(target);g=(c.img()*255)@np.array([0.299,0.587,0.114])
        if g.std()>=10.5:break
        m=c.a.reshape(-1,3).mean(0);c.a=m+(c.a-m)*1.3
    c.keep_mean(target)
N=1024
def out(name,c,t):lift(c,np.array(t));save(c.img(),'tex2/%s.png'%name)
def c255(*v):return np.array(v,float)/255
def dirt(name,t,seed,tufts=0.0):
    c=Canvas(8,8,t,seed,N);c.mul(1+0.10*c.noise(0.012))          # crumb-sized texture only: no blotches
    c.speckle(10,(0.01,0.04),0.35);c.speckle(10,(0.008,0.03),0.30,light=True);c.grain(0.10)
    if tufts:c.tint(tufts,0.10,(0.55,0.62,0.30))                 # small grass tufts in the dirt (photo: patches)
    out(name,c,t)
def asph(name,t,seed):
    c=Canvas(8,8,t,seed,N);c.mul(1+0.08*c.noise(0.008))          # aggregate only: no blotches
    c.speckle(40,(0.004,0.012),0.40);c.speckle(30,(0.004,0.010),0.35,light=True);c.grain(0.10);out(name,c,t)
def grass(name,t,seed):
    c=Canvas(8,8,t,seed,N);c.mul(1+0.15*c.noise(0.01,0.03))
    c.speckle(8,(0.01,0.03),0.25);c.speckle(8,(0.005,0.02),0.25,light=True);c.grain(0.05);out(name,c,t)
def steeldk(name,t,seed):
    # open steel deck and frame: grating bars every 0.05 m, a joist every 1 m, rust and wear
    c=Canvas(2,2,t,seed,N)
    for u in np.arange(0,2,0.05):c.vline(u,0.012,t*0.55,0.9)
    for v in np.arange(0,2,1.0):c.hline(v,0.06,t*1.5,0.9)
    c.mul(1+0.05*c.noise(0.2));c.speckle(4,(0.01,0.04),0.3);c.grain(0.05);out(name,c,t)
def mastg(name,t,seed):
    c=Canvas(1,1,t,seed,N);c.mul(1+0.04*c.noise(0.1,0.4));c.speckle(4,(0.005,0.02),0.25);c.grain(0.03);out(name,c,t)
dirt('dirtA',c255(65,45,42),71)                 # concourse ring s 118-178: plain red-brown dirt (photo 62,43,40)
dirt('dirtS',c255(92,64,34),72,tufts=0.18)      # dirt slope s 118-182 with grass patches (photo mean s 168-181: 103,79,54)
dirt('dirtP',c255(150,103,80),79)               # light pink dirt in front of the green building, s 182-187 (photo ~160,115,95)
asph('asph',c255(62,52,48),73)                  # ring s 178-252 asphalt (photo 70,61,60)
asph('asphp',c255(115,88,77),74)                # plaza and road down the slope, s 187-200 (photo 132,106,100)
grass('grass_nl',c255(75,78,34),75)             # slope grass s 118-160 (photo 87,90,45)
grass('grass_n',c255(66,52,23),76)              # slope grass s 200-252, dry (photo 80,67,42)
steeldk('steeldk',c255(38,30,30),77)            # near-left deck, frame and rails (photo 32,25,26)
mastg('mastg',c255(140,135,132),78)             # Members roof masts and stays: grey (photo posts ~150,145,140)
