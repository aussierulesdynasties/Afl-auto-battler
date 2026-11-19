# Row 202 2b texture pass: hand-paints wear, joints and module detail onto the flat Traeger maps (stddev under 10).
# Runs after texgen.py, texclub.py and texsite.py; reads and rewrites tex3/*.png. No photo pixels: each map keeps its
# drawn pattern and mean colour, and gets marks at measured module sizes in metres (TILE from tex3/tex.json; PANEL maps
# at their drawing scale). Alpha (rails) is kept as drawn.
import json,os,numpy as np
from PIL import Image
from texpaint import Canvas,gstd
O='tex3';T=json.load(open(os.path.join(O,'tex.json')))['TILE']
PANEL_M={'soffit_box':60,'banner':120,'sign_white':100,'roof_blue_club':100}   # px per metre the panel was drawn at
def load(n,seed):
    im=Image.open(os.path.join(O,n+'.png'));A=np.asarray(im)
    CLUB={'club_render':(2,2),'bal_back_blue':(2,2)}   # texclub tile sizes (not in tex.json)
    tu,tv=T[n] if n in T else CLUB[n] if n in CLUB else (A.shape[1]/PANEL_M.get(n,200),A.shape[0]/PANEL_M.get(n,200))   # club maps: 200 px/m (texclub)
    c=Canvas(tu,tv,A,seed);c.alpha=A[...,3] if A.shape[-1]==4 else None;return c
def dust(c,amt,col=(0.42,0.41,0.39)):
    d=np.clip(0.5+0.5*c.noise(0.4,0.15),0,1)*((np.arange(c.h)/c.h)**1.3)[:,None];c.a=c.a*(1-amt*d[...,None])+np.array(col)*amt*d[...,None]
def out(n,c,mean=True):
    if mean:c.keep_mean()
    a=np.clip(c.a*255+0.5,0,255).astype(np.uint8)
    if c.alpha is not None:Image.fromarray(np.dstack([a,c.alpha]),'RGBA').save(os.path.join(O,n+'.png'))
    else:Image.fromarray(a).save(os.path.join(O,n+'.png'))
# ---- ribbed roof sheeting (trimdek 0.76 m cover sheets): per-sheet tone, dirt runs along the pans, lichen spots
for i,n in enumerate(('roof_top','canopy','roof_white','shed_wall')):
    c=load(n,100+i);c.mottle(0.06,(1.5,0.5,0.15));c.panels(0.76,1.9,joint=0.01,dark=0.8,tone=0.09 if n=='shed_wall' else 0.05)
    c.streaks([0.0],per_m=3.0,length=(0.5,1.8),width=(0.01,0.05),amt=0.35);c.speckle(6,(0.01,0.04),0.25);out(n,c)
# ---- sheeting underside: per-sheet tone, purlin shadow line every 1.9 m, dust
for i,n in enumerate(('roof_soffit','canopy_under')):
    c=load(n,110+i);c.mottle(0.07,(1.5,0.5,0.15));c.panels(0.76,1.9,joint=0.012,dark=0.75,tone=0.06)
    c.hline(0.05,0.08,c.col*0.55,0.8);c.speckle(4,(0.01,0.03),0.2);out(n,c)
# ---- clubroom blue roof (24.6 x 8.6 m panel): sun fade, per-sheet tone, dirt toward the eave (image bottom)
c=load('roof_blue_club',120);c.mottle(0.07,(4,1.2,0.3));c.panels(0.76,8.6,joint=0.012,dark=0.8,tone=0.05)
c.grime_bottom(2.0,0.22,col=(0.35,0.33,0.30));c.speckle(1.5,(0.02,0.06),0.2);out('roof_blue_club',c)
# ---- painted render and steel (2 x 2 m repeat): sheet/render joints, rain streaks from the top, grime at the foot
P={'fascia':(1.0,2.0,0.04),'steel_white':(1.0,2.0,0.04),'steel_grey':(1.0,2.0,0.10),'steel':(1.0,2.0,0.10),'cream':(1.0,1.0,0.05),
   'rear_dark':(1.0,2.0,0.18),'under_wall':(1.0,1.0,0.16),'render_grey':(1.0,1.0,0.05),'club_render':(1.0,1.0,0.05),
   'bal_back_blue':(1.0,2.0,0.16)}
SMOOTH={'cream':None,'render_grey':None,'steel_white':None,'fascia':None,'steel':None,'steel_grey':None}   # lead 2026-11-20: south wing is smooth render and panels in the photo (c08), no blotches
for i,(n,(pw,ph,tone)) in enumerate(P.items()):
    if n in SMOOTH:
        c=load(n,130+i);pp=SMOOTH[n]
        if pp:c.panels(pp[0],pp[1],joint=0.006,dark=0.88,tone=0.0)
        c.grime_bottom(0.3,0.05);c.grain(0.006);out(n,c);continue
    c=load(n,130+i);dark=c.col.mean()<0.4
    c.mottle(0.18 if dark else 0.06,(1.5,0.5,0.12));c.panels(pw,ph,joint=0.012,dark=0.6,tone=tone)
    c.streaks([0.0,1.0],per_m=1.5,length=(0.3,1.2),amt=0.45 if dark else 0.35,col=(0.8,0.78,0.74) if dark else (0.35,0.33,0.30))
    c.grime_bottom(0.4,0.15,band=1.0);(dust(c,0.45) if dark else c.speckle(3,(0.005,0.02),0.25));out(n,c,not dark)
# ---- concrete deck and risers (3 x 3 m): per-bay tone, stains and wear
for i,n in enumerate(('deck','riser')):
    c=load(n,150+i);c.mottle(0.06,(1.5,0.4,0.1));c.panels(1.5,1.5,joint=0.006,dark=0.85,tone=0.05)
    c.speckle(5,(0.02,0.08),0.12);c.speckle(10,(0.005,0.015),0.25);out(n,c)
# ---- seats (0.5 m): moulded back catching light on top, seat pan in shadow, gap between seats
for i,n in enumerate(('seat_navy','seat_white')):
    c=load(n,160+i);col=c.col.copy();c.mottle(0.03,(0.2,0.05))
    c.hline(0.06,0.06,np.minimum(col*1.30,1),0.9);c.hline(0.40,0.12,col*0.62,0.9);c.vline(0.0,0.04,col*0.45,0.9)
    c.keep_mean(col);out(n,c,False)
# ---- bench slats 0.1 m with gaps, black steel posts and louvres, tan blocks, trunks
c=load('bench_white',170);c.mottle(0.03,(0.3,0.1))
for k in range(10):c.hline(k*0.1,0.012,c.col*0.55,0.9)
c.streaks([0.0],per_m=2,length=(0.2,0.8),amt=0.2);out('bench_white',c)
for i,n in enumerate(('post','louvre_black')):
    c=load(n,175+i);c.mottle(0.25,(1.0,0.3,0.08));c.panels(1.0,2.0,joint=0.01,dark=0.6,tone=0.15);c.streaks([0.0],per_m=2,length=(0.4,1.5),amt=0.5,col=(0.9,0.88,0.84))
    dust(c,0.5);out(n,c,False)
c=load('block_tan',180);c.panels(0.4,0.2,joint=0.008,dark=0.7,tone=0.02,stagger=0.5);c.speckle(10,(0.004,0.012),0.2);out('block_tan',c)
c=load('trunk',181);c.mul(1+0.10*c.noise(0.03,0.4));c.speckle(12,(0.01,0.03),0.2);out('trunk',c)
# ---- rails (alpha kept): paint wear, chips and dirt on the bars
for i,n in enumerate(('rail_bars','rail_bow','rail_pal')):
    c=load(n,185+i);dark=c.col.mean()<0.4;c.mottle(0.35 if dark else 0.12,(0.6,0.2,0.05))
    c.speckle(40 if dark else 10,(0.004,0.012),1.5 if dark else 0.25,light=dark);c.grime_bottom(0.3,0.25,band=c.tv);out(n,c)
# ---- panel maps: box underside (ceiling sheets, dust round the downlights), banner, blank pole sign
c=load('soffit_box',190);c.mottle(0.05,(2,0.6,0.15));c.panels(1.2,1.2,joint=0.012,dark=0.6,tone=0.025);c.speckle(2,(0.02,0.06),0.15);out('soffit_box',c)
c=load('banner',191);c.mottle(0.10,(2,0.5,0.1));c.panels(1.5,1.0,joint=0.01,dark=0.6,tone=0.07)
c.streaks([0.0],per_m=1.5,length=(0.2,0.7),amt=0.35,col=(0.8,0.78,0.74));out('banner',c)
c=load('sign_white',192);c.mottle(0.03,(1,0.3,0.1));c.panels(1.2,2.5,joint=0.01,dark=0.7,tone=0.04);c.streaks([0.06],per_m=3,length=(0.5,2.5),amt=0.45)
c.grime_bottom(0.8,0.2);c.speckle(3,(0.01,0.03),0.2);out('sign_white',c)
# dark painted steel (posts, rear walls, bow-top fence): primer-grey chips and scuffs where the black paint is worn
for i,n in enumerate(('post','rear_dark','under_wall','rail_bow','rail_pal')):
    c=load(n,195+i)
    if n=='rail_bow':c.speckle(30,(0.006,0.02),1.6,light=True)
    elif n=='rail_pal':c.mottle(0.10,(0.6,0.2))
    else:c.streaks([0.0,1.0],per_m=3,length=(0.3,1.5),amt=0.6,col=(0.9,0.88,0.84));dust(c,0.35)
    if c.alpha is not None and n=='rail_bow':   # round bars: sky highlight along the top/left edge of every bar
        m=c.alpha>128;e=m&(~np.roll(m,3,1)|~np.roll(m,3,0));c.a[e]=np.minimum(c.a[e]*2.6+0.06,1)
    out(n,c)
# ---- the ground's own lettering (director 2026-11-19: ground's own signs allowed; sponsor logos stay out, so no TIO box)
# spans measured off w04 (stand metres s from the south front corner): banner name s 15.8..19.0, white on navy;
# cream band "Bowden McAdam Grandstand" s 14.6..19.0, dark grey; Segoe UI as the nearest humanist sans to the photo.
from PIL import ImageDraw,ImageFont
SP=json.load(open('stand.json'))['P'];S0,S1=SP['box_s0'],SP['box_s1']
def letter(n,txt,s0,s1,hfrac,col,fnt='segoeui.ttf'):
    im=Image.open(os.path.join(O,n+'.png')).convert('RGB');W,H=im.size;x0,x1=(s0-S0)/(S1-S0)*W,(s1-S0)/(S1-S0)*W
    f=ImageFont.truetype('C:/Windows/Fonts/'+fnt,int(H*hfrac));d=ImageDraw.Draw(im);bw=d.textlength(txt,font=f)
    sz=int(H*hfrac*min(1.0,(x1-x0)/bw));f=ImageFont.truetype('C:/Windows/Fonts/'+fnt,sz)
    d.text(((x0+x1)/2,H*0.5),txt,font=f,fill=col,anchor='mm');im.save(os.path.join(O,n+'.png'))
letter('banner','Traeger Park Oval',15.8,19.0,0.62,(236,238,240))
letter('cream_band','Bowden McAdam Grandstand',14.6,19.0,0.62,(52,52,54))
# light-pole signs (c05 zoom): white bold "Traeger / Park Oval" in the lower half, as texsite drew it; the TIO box above is a sponsor, left off
im=Image.open(os.path.join(O,'sign_tio.png')).convert('RGB');W,H=im.size;d=ImageDraw.Draw(im);f=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',int(H*0.13))
for t,y in (('Traeger',0.56),('Park Oval',0.73)):d.text((W//2,int(H*y)),t,font=f,fill=(250,250,250),anchor='mm')
im.save(os.path.join(O,'sign_tio.png'))
# scoreboard header (c05 zoom): "Traeger Park Oval" in white bold on the blue header; TIO box left off
im=Image.open(os.path.join(O,'screen.png')).convert('RGB');W,H=im.size;d=ImageDraw.Draw(im);hh=int(H*0.17)
d.text((W//2,hh//2),'Traeger Park Oval',font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',int(hh*0.55)),fill=(248,248,248),anchor='mm')
im.save(os.path.join(O,'screen.png'))
c=load('grass',193);c.mul(1+0.06*c.noise(0.3)+0.05*c.noise(0.05));out('grass',c)   # unused (field left out)
for n in sorted(f[:-4] for f in os.listdir(O) if f.endswith('.png')):
    g=gstd(os.path.join(O,n+'.png'))
    if g<10:print('UNDER 10',n,round(g,1))
print('paint_tex done')
