exec(open('fence.py',encoding='utf-8').read().split('#MAIN')[0])
import json
from PIL import Image,ImageDraw,ImageFont,ImageFilter
def bp2(u,v,z=0):
    Rm=R(*p[3:6]);x=(u-W/2-p[7])/p[6];y=-(v-H/2-p[8])/p[6];ray=Rm.T@np.array([x,y,1.0]);t=(z-p[2])/ray[2];return (p[:3]+t*ray)[:2]
co=np.load('bco.npy');K=5
def bd(s):
    a=2*np.pi*np.asarray(s,float)/PER;return np.column_stack([np.ones_like(a)]+[f(k*a) for k in range(1,K+1) for f in(np.cos,np.sin)])@co
# centre square from picked corners
sq=np.array([bp2(*q) for q in[(461,248.5),(574,248.5),(580,309),(458.5,309)]])
C0=sq.mean(0);ax=((sq[0]-sq[1])+(sq[3]-sq[2]))/2;ax/=np.linalg.norm(ax);ay=np.array([-ax[1],ax[0]])
print('square sides',[round(float(np.linalg.norm(sq[i]-sq[(i+1)%4])),1) for i in range(4)],'C0',C0,'axis',ax)
# goal centres: where the long axis meets the boundary line
SSf=np.arange(0,PER,0.05);BL=F(SSf)+N(SSf)*bd(SSf)[:,None]
goals=[]
for sg in(1,-1):
    t=np.arange(30,100,0.05);X=C0+np.outer(t*sg,ax)
    dist=np.min(np.linalg.norm(X[:,None,:]-BL[None,::20],axis=2),axis=1);i=np.argmin(dist);
    # refine
    goals.append(C0+ax*sg*t[i])
print('goals',goals,[np.linalg.norm(g-C0) for g in goals])
x0,y0=Q.min(0)-2;x1,y1=Q.max(0)+2;N_=4096;sc=N_/max(x1-x0,y1-y0)
def px(X):X=np.atleast_2d(X);return [((a-x0)*sc,(y1-b)*sc) for a,b in X]
rng=np.random.default_rng(3)
def noise(h,w,s,amp):
    n=rng.normal(0,1,(h//s+2,w//s+2));im=Image.fromarray(((n-n.min())/(n.max()-n.min())*255).astype(np.uint8)).resize((w+s,h+s),Image.BICUBIC);return (np.asarray(im)[:h,:w]/255.0-0.5)*amp
g=np.ones((N_,N_,3))*np.array([48,66,32.0])
g+=(noise(N_,N_,256,22)+noise(N_,N_,32,10)+rng.normal(0,5,(N_,N_)))[...,None]*np.array([0.6,1.0,0.5])
img=Image.fromarray(np.clip(g,0,255).astype(np.uint8))
# worn patches (soil showing through) at centre and goal squares
wear=Image.new('L',(N_,N_),0);dw=ImageDraw.Draw(wear)
def ell(c,r,val):
    (u,v),=px(c);dw.ellipse([u-r*sc,v-r*sc*0.6,u+r*sc,v+r*sc*0.6],fill=val)
ell(C0,9,200);ell(C0,15,110)
for gc in goals:ell(gc-ax*np.sign((gc-C0)@ax)*4,6,170)
wear=wear.filter(ImageFilter.GaussianBlur(40));wa=np.asarray(wear)/255.0*(0.6+noise(N_,N_,16,0.8))
soil=np.array([150,120,88.0])+rng.normal(0,8,(N_,N_,1))
g=np.asarray(img).astype(float);g=g*(1-wa[...,None])+soil*wa[...,None];img=Image.fromarray(np.clip(g,0,255).astype(np.uint8))
d=ImageDraw.Draw(img);LW=max(2,int(0.12*sc));WH=(236,238,232)
d.line(px(np.r_[BL[::10],BL[:1]]),fill=WH,width=LW)
d.line(px(np.r_[sq,sq[:1]]),fill=WH,width=LW)
def circ(c,r,arc=None):
    t=np.linspace(0,2*np.pi,400) if arc is None else np.linspace(*arc,200);pts=c+np.outer(r*np.cos(t),ax)+np.outer(r*np.sin(t),ay);d.line(px(pts),fill=WH,width=LW)
circ(C0,1.5);circ(C0,5.0)
for gc in goals:
    sg=np.sign((gc-C0)@ax)
    # 50 m arc: points of circle radius 50 about goal centre lying inside boundary
    t=np.linspace(0,2*np.pi,2000);pts=gc+np.outer(50*np.cos(t),ax)+np.outer(50*np.sin(t),ay)
    inside=((pts-C0)@ax)*sg<((gc-C0)@ax)*sg
    # keep points inside the boundary oval
    a=np.arctan2(pts[:,1]-PC[1],pts[:,0]-PC[0])
    dd=np.array([np.min(np.linalg.norm(BL[::20]-q,axis=1)) for q in pts])
    rr=np.linalg.norm(pts-PC,axis=1);rb=np.interp(a,np.arctan2(BL[:,1]-PC[1],BL[:,0]-PC[0])[np.argsort(np.arctan2(BL[:,1]-PC[1],BL[:,0]-PC[0]))],np.linalg.norm(BL-PC,axis=1)[np.argsort(np.arctan2(BL[:,1]-PC[1],BL[:,0]-PC[0]))])
    ok=inside&(rr<rb)
    seg=[];
    for q,k in zip(pts,ok):
        if k:seg.append(q)
        elif len(seg)>1:d.line(px(np.array(seg)),fill=WH,width=LW);seg=[]
        else:seg=[]
    if len(seg)>1:d.line(px(np.array(seg)),fill=WH,width=LW)
    # goal square 6.4 wide x 9 deep
    gs=[gc+ay*3.2,gc+ay*3.2-ax*sg*9,gc-ay*3.2-ax*sg*9,gc-ay*3.2];d.line(px(np.array(gs)),fill=WH,width=LW)
    d.line(px(np.array([gc+ay*9.6,gc-ay*9.6])),fill=WH,width=LW)   # goal line between behind posts
# banners: quads from picked corners [teal | logo | red]
def ban(c4,split1,split2,flip):
    q=np.array([bp2(*c) for c in c4])  # tl,tr,br,bl in image
    def lerp(a,b,t):return a+(b-a)*t
    tl,tr,br,bl=q
    def quad(t0,t1):return [lerp(tl,tr,t0),lerp(tl,tr,t1),lerp(bl,br,t1),lerp(bl,br,t0)]
    d.polygon(px(np.array(quad(0,split1))),fill=(26,54,56));d.polygon(px(np.array(quad(split1,split2))),fill=(18,30,42));d.polygon(px(np.array(quad(split2,1))),fill=(92,38,30))
    # emblem ring
    cc=np.mean(quad(split1,split2),axis=0);(u,v),=px(cc);r=0.33*np.linalg.norm(tl-bl)*sc;d.ellipse([u-r,v-r,u+r,v+r],outline=WH,width=LW+2)
    # lettering in a separate layer, rotated to the banner
    Lx=np.linalg.norm(lerp(tl,tr,split1)-tl);Hy=np.linalg.norm(bl-tl)
    lay=Image.new('RGBA',(int(Lx*sc),int(Hy*sc)),(0,0,0,0));dl=ImageDraw.Draw(lay)
    try:fnt=ImageFont.truetype('arialbd.ttf',int(Hy*sc*0.36))
    except Exception:fnt=ImageFont.load_default()
    for k,txt in enumerate(('CENTENARY','SEASON')):
        bb=dl.textbbox((0,0),txt,font=fnt);dl.text(((lay.size[0]-bb[2])/2,Hy*sc*(0.08+0.46*k)),txt,font=fnt,fill=WH)
    if flip:lay=lay.rotate(180)
    ang=np.degrees(np.arctan2(*(np.array(px(tr))[0]-np.array(px(tl))[0])[::-1]))
    lay=lay.rotate(-ang,expand=True,resample=Image.BICUBIC)
    c_=np.mean(quad(0,split1),axis=0);(u,v),=px(c_);img.paste(lay,(int(u-lay.size[0]/2),int(v-lay.size[1]/2)),lay)
    # red panel: plain white wave stripe (no brand lettering)
    t=np.linspace(split2+0.04,0.96,60);mid=[lerp(lerp(tl,tr,tt),lerp(bl,br,tt),0.5+0.18*np.sin((tt-split2)*18)) for tt in t]
    d.line(px(np.array(mid)),fill=WH,width=LW+1)
# director 2026-11-18 (sponsor boards, option C 'no boards'): bare fence, the ground banners go
img.save('tex2/turf.png')
json.dump({'bbox':[float(x0),float(y0),float(x1),float(y1)],'C0':C0.tolist(),'ax':ax.tolist(),'goals':[g_.tolist() for g_ in goals]},open('turf.json','w'))
