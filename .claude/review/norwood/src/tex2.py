# Second pass (lead's review): crowd banks, field, WBCC sides, signage, clubroom front.
# Run inside tex.py (exec) so it shares save/canvas/noise/flat/corrugated/font. Everything is painted from numbers.
import geo
def ss_save(name,im,tw,th,mode='wall',k=2):   # painted at k x size, reduced once: crisp edges, no blur filter
    im=im.resize((im.width//k,im.height//k),Image.LANCZOS);save(name,np.array(im,float),tw,th,mode)
# ---------- standing crowd on a terrace step (main photo: packed, navy/white/black/red shirts, flags) ----------
SHIRT=[(30,36,72),(24,24,28),(232,232,228),(188,38,46),(118,120,126),(58,88,156),(190,172,140),(70,40,110),(40,60,48),(214,120,40)]
SW=np.array([16,14,12,8,8,8,6,4,3,2],float);SW/=SW.sum()
HAIR=[(38,28,22),(70,50,32),(150,118,78),(22,22,22),(200,180,150),(120,120,120),(214,170,140)]
def crowd(name,seed,tw=6.0,th=0.9,ppm=160,k=2):   # packed standing crowd: two staggered ranks per step, shadow between bodies
    r=np.random.default_rng(seed);P_=ppm*k;W,H=int(tw*P_),int(th*P_)
    a=canvas(W,H,(74,70,68))+noise(H,W,3)[...,None];im=Image.fromarray(a.clip(0,255).astype(np.uint8));d=ImageDraw.Draw(im)
    d.rectangle([0,H-int(0.05*P_),W,H],fill=(120,118,114))                   # concrete step nosing at the front edge (v=0 = image bottom)
    for rank,(yl,yh) in enumerate(((0.58,0.74),(0.18,0.34))):                 # back rank first, the front rank overlaps it
        x=r.uniform(0,0.4)
        while x<tw:
            if r.random()<0.03: x+=r.uniform(0.3,0.6);continue
            y=r.uniform(yl,yh);w=r.uniform(0.44,0.54);dp=r.uniform(0.28,0.36)
            sc_=SHIRT[r.choice(len(SHIRT),p=SW)];sc_=tuple(int(min(255,c*r.uniform(0.9,1.08))) for c in sc_)
            hr=r.uniform(0.10,0.12)*P_;hc=HAIR[r.integers(len(HAIR))]
            if r.random()<0.15: hc=SHIRT[r.integers(4)]                       # caps and beanies
            face=r.random()<0.55;flag=r.random()<0.03;fc=(96,62,150) if r.random()<0.6 else (236,236,236)
            for xo in (0,-tw,tw):                                               # wrap across the tile edge
                cx=(x+xo)*P_;cy=H-y*P_
                d.ellipse([cx-w/2*P_,cy-dp/2*P_+0.04*P_,cx+w/2*P_,cy+dp/2*P_+0.04*P_],fill=tuple(max(c-40,0) for c in sc_))   # shaded front of the body
                d.ellipse([cx-w/2*P_,cy-dp/2*P_,cx+w/2*P_,cy+dp/2*P_],fill=sc_)                                    # shoulders
                hy=cy-0.04*P_
                d.ellipse([cx-hr,hy-hr,cx+hr,hy+hr],fill=hc)
                if face: d.chord([cx-hr*0.8,hy-hr*0.2,cx+hr*0.8,hy+hr*1.0],0,180,fill=(214,168,136))  # face turned to the play
                if flag:
                    d.rectangle([cx+0.1*P_,hy-0.5*P_,cx+0.12*P_,hy],fill=(60,60,60));d.rectangle([cx+0.12*P_,hy-0.5*P_,cx+0.45*P_,hy-0.3*P_],fill=fc)
            x+=r.uniform(0.40,0.50)
    ss_save(name,im,tw,th,k=k)
crowd('crowd_a',11);crowd('crowd_b',12);crowd('crowd_c',13)
def riser_legs(name,tw=6.0,th=0.28,ppm=160):   # the step face is hidden by the standing row in front: packed shirts and arms, seen side-on
    r=np.random.default_rng(21);W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(60,56,54))+noise(H,W,2)[...,None]
    x=0.0
    while x<tw:
        w=r.uniform(0.36,0.48);c=np.array(SHIRT[r.choice(len(SHIRT),p=SW)],float)*r.uniform(0.85,1.0)
        x0,x1=int(x*ppm),int(min(x+w,tw)*ppm);a[:,x0+2:x1-2]=c
        a[:,x0+2:x0+int(0.05*ppm)]=c*0.7                                                # shaded side of the body
        if r.random()<0.4: a[:int(0.06*ppm),x0+int(w*0.3*ppm):x0+int(w*0.7*ppm)]=(212,166,134)   # hands on the barrier / forearms
        x+=w
    save(name,a,tw,th)
# ---------- playing surface (render only): mowing stripes and the markings measured off the main photo ----------
def turf(name,ppm=30):
    X0,X1,Y0,Y1=geo.FIELD_BB;W,H=int((X1-X0)*ppm),int((Y1-Y0)*ppm)
    x=((np.arange(W)+0.5)/ppm+X0).astype(np.float32);y=(Y1-(np.arange(H)+0.5)/ppm).astype(np.float32)
    q=x[None,:]*geo.PX[0]+y[:,None]*geo.PX[1]-float(geo.CEN@geo.PX)
    band=(np.floor(q/10.0+0.5)%2).astype(np.float32)                                # 10 m stripes along the long axis
    L=np.array((118,170,60),np.float32);D=np.array((88,140,44),np.float32)
    a=L[None,None,:]*band[...,None]+D[None,None,:]*(1-band[...,None])
    a+=rng.normal(0,3.5,(H,W,1)).astype(np.float32)
    im=Image.fromarray(a.clip(0,255).astype(np.uint8));d=ImageDraw.Draw(im)
    def px(p): return (float((p[0]-X0)*ppm),float((Y1-p[1])*ppm))
    WH=(240,242,236);BL=(104,168,240);lw=max(int(0.2*ppm),2)
    def poly(pts,c,closed=False):
        P_=[px(p) for p in pts]+([px(pts[0])] if closed else [])
        if len(P_)>1: d.line(P_,fill=c,width=lw,joint='curve')
    th=np.radians(np.arange(0,360,0.5));rb=geo.rfence(th)+0.2-4.7
    poly([(r_*np.sin(t),r_*np.cos(t)) for t,r_ in zip(th,rb)],WH,True)                # boundary, 4.7 m inside the fence
    AX,PX=geo.AX,geo.PX
    for G,D_ in ((geo.GN,-AX),(geo.GS,AX)):
        poly([G-PX*3.2,G+PX*3.2,G+PX*3.2+D_*9,G-PX*3.2+D_*9],WH,True)                 # goal square 6.4 x 9
        arc=[]
        for f in np.radians(np.arange(-90,90.01,0.5)):
            p_=G+50*(np.cos(f)*D_+np.sin(f)*PX);t=np.arctan2(p_[0],p_[1])
            if np.hypot(*p_)<float(geo.rfence(t)[0])+0.2-4.7: arc.append(p_)
        poly(arc,BL)                                                                    # 50 m arc (blue)
    C=geo.CEN;h=25
    poly([C-AX*h-PX*h,C-AX*h+PX*h,C+AX*h+PX*h,C+AX*h-PX*h],WH,True)                    # centre square 50 m
    for rr in (5.0,1.5): poly([C+rr*(np.cos(f)*AX+np.sin(f)*PX) for f in np.linspace(0,2*np.pi,90)],WH,True)
    poly([C-PX*5,C+PX*5],WH)                                                            # centre line across the circle
    for dg in np.arange(296,322,2.0):                                                   # white dashes 2.2 m inside the fence (north-west)
        t0,t1=np.radians(dg),np.radians(dg+1.0);r0_=float(geo.rfence(t0)[0])+0.2-2.2
        poly([(r0_*np.sin(t0),r0_*np.cos(t0)),(r0_*np.sin(t1),r0_*np.cos(t1))],WH)
    save(name,np.array(im,float),X1-X0,Y1-Y0,mode='fit')
turf('turf')
flat('goal_pad',(34,78,172),tw=1,th=1,n=2,joints=(0.5,3),jc=0.85)
# ---------- WBCC street sides (woods2_ws west face, woods1_wb south face) ----------
def mesh(W,H,ppm,seed=5):   # red/navy diagonal bands behind white expanded-metal mesh with white light dots; bands rise to the right
    r=np.random.default_rng(seed);yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    u=xx/ppm;v=(H-yy)/ppm;ph=(u-v*1.1229)/1.6                                          # 1.6 m bands at 41.7 degrees: tiles in 12.8 x 5.7 m
    red=np.array((192,40,52),np.float32);nav=np.array((38,40,94),np.float32)
    b=(np.floor(ph)%2)[...,None];a=red*b+nav*(1-b)
    m=(((u+v)/0.13)%1<0.12)|(((u-v)/0.13)%1<0.12)                                       # diamond wire
    a[m]=a[m]*0.45+np.array((235,235,235),np.float32)*0.55
    a+=rng.normal(0,3,(H,W,1)).astype(np.float32)
    im=Image.fromarray(a.clip(0,255).astype(np.uint8));d=ImageDraw.Draw(im)
    for _ in range(int(W*H/ppm/ppm/0.5)):
        x_,y_=r.uniform(0,W),r.uniform(0,H);rr=0.035*ppm;d.ellipse([x_-rr,y_-rr,x_+rr,y_+rr],fill=(246,246,240))
    return im
def wbcc_mesh(name,tw=12.8,th=5.7,ppm=80):
    a=np.array(mesh(int(tw*ppm),int(th*ppm),ppm),float);a[-int(0.12*ppm):]=(214,206,190);save(name,a,tw,th)   # pale frame edge at the foot
wbcc_mesh('wbcc_mesh')
def wbcc_west_lo(name,tw=8.0,th=3.3,ppm=100):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(198,190,174))+noise(H,W,2.5)[...,None]
    for gx in np.arange(0,4.4,2.2): a[:,int(gx*ppm):int(gx*ppm)+2]*=0.8                # precast panel joints
    a[:,int(4.4*ppm):int(5.3*ppm)]=(46,44,42);a[int(0.3*ppm):int(1.2*ppm),int(4.5*ppm):int(5.2*ppm)]=(30,28,26)   # recessed doorway
    sh=a[:,int(5.5*ppm):]                                                               # black louvred roller shutters
    sh[:]=(34,34,36);sh[::6]=(62,62,64);a[:,int(5.5*ppm)-6:int(5.5*ppm)]=(150,144,132)
    a[:int(0.3*ppm)]*=0.62                                                              # shade under the soffit
    save(name,a,tw,th)
wbcc_west_lo('wbcc_west_lo')
WB_S=float(np.hypot(geo.wb[3][0]-geo.wb[4][0],geo.wb[3][1]-geo.wb[4][1]))
def wbcc_south_lo(name,tw=WB_S,th=3.3,ppm=100):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(58,58,62))+noise(H,W,2)[...,None]       # dark open undercroft (woods1_wb)
    for gx in np.arange(1.0,tw,3.0): a[:,int(gx*ppm):int(gx*ppm)+int(0.18*ppm)]=(26,26,28)
    a[int(1.0*ppm):,int(0.4*ppm):int(3.2*ppm)]=(40,40,42);a[int(1.0*ppm)::6,int(0.4*ppm):int(3.2*ppm)]=(66,66,68)
    a[:int(0.3*ppm)]*=0.7;save(name,a,tw,th,mode='fit')
wbcc_south_lo('wbcc_south_lo')
def wbcc_south_up(name,tw=WB_S,th=5.7,ppm=80):
    W,H=int(tw*ppm),int(th*ppm);m=np.array(mesh(W,H,ppm,seed=6),float)
    a=canvas(W,H,(208,210,214))+noise(H,W,2)[...,None]                                 # pale cladding panels on the west part (q_wbw)
    for gx in np.arange(0,tw,1.2): a[:,int(gx*ppm):int(gx*ppm)+2]*=0.9
    cut=int(0.45*W);a[:,cut:]=m[:,cut:];a[:,cut:cut+4]=(150,150,154)
    save(name,a,tw,th,mode='fit')
wbcc_south_up('wbcc_south_up')
flat('wbcc_soffit',(206,196,176),tw=2,th=2,n=2,joints=(2.4,4),jc=0.85)
# ---------- signage: club words in place of the sponsors' names (painted, not copied) ----------
def signboard(name,txt,bg,fg,tw,th,mode,ppm=120,hfrac=0.58):
    W,H=int(tw*ppm),int(th*ppm);im=Image.new('RGB',(W,H),bg);d=ImageDraw.Draw(im)
    segs=txt if isinstance(txt,list) else [txt];n=len(segs)
    for j,t in enumerate(segs):
        f=font(int(th*hfrac*ppm));tb=d.textbbox((0,0),t,font=f)
        while tb[2]-tb[0]>0.9*W/n: f=font(int(f.size*0.9));tb=d.textbbox((0,0),t,font=f)
        x0=j*W//n+(W//n-(tb[2]-tb[0]))//2-tb[0];y0=(H-(tb[3]-tb[1]))//2-tb[1]
        d.text((x0,y0),t,font=f,fill=fg)
        if j: d.rectangle([j*W//n-2,0,j*W//n+2,H],fill=(30,30,30))
    d.rectangle([0,0,W-1,H-1],outline=tuple(int(c*0.7) for c in bg),width=3)
    save(name,np.array(im,float)+noise(H,W,1.5)[...,None],tw,th,mode)
signboard('sign_red',['NORWOOD','REDLEGS'],(200,32,44),(250,250,250),6.0,0.9,'wall')
signboard('sign_blue','NORWOOD FOOTBALL CLUB',(28,64,150),(250,250,250),7.0,1.1,'fit')
signboard('sign_white','REDLEGS  EST. 1878',(240,240,236),(28,64,150),7.0,1.1,'fit')
signboard('sign_kiosk','NORWOOD MEMBERS',(30,70,170),(250,250,250),7.0,0.7,'fit')
def led_board(name,tw=5.0,th=1.0,cell=0.04,ppm=125):
    gw,gh=int(tw/cell),int(th/cell);g=Image.new('L',(gw,gh),0);d=ImageDraw.Draw(g)
    f=font(int(gh*0.62));t='NOR  12.8.80';tb=d.textbbox((0,0),t,font=f);d.text(((gw-(tb[2]-tb[0]))//2-tb[0],(gh-(tb[3]-tb[1]))//2-tb[1]),t,font=f,fill=255)
    G=np.array(g)>100;ys,xs=np.nonzero(G)
    if ys.size: G=np.roll(np.roll(G,(gh-1-ys.max()-ys.min())//2,0),(gw-1-xs.max()-xs.min())//2,1)
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(16,16,18));c=int(cell*ppm)
    for j in range(gh):
        for i in range(gw):
            a[j*c+1:j*c+c-1,i*c+1:i*c+c-1]=(255,176,40) if G[j,i] else (34,30,26)
    a[:3]=a[-3:]=(60,60,64);a[:,:3]=a[:,-3:]=(60,60,64)
    save(name,a,tw,th,mode='fit')
led_board('led_board')
# ---------- clubrooms' north-east face (main photo): bluestone 0-6.4 m from the corner, red brick beyond, plaque, doorway, window ----------
def tile_to(img,tw,th,ppm,W,H):
    t=Image.open(os.path.join(OUT,img+'.png')).convert('RGB').resize((int(tw*ppm),int(th*ppm)),Image.LANCZOS)
    t=np.array(t,float);return np.tile(t,(H//t.shape[0]+2,W//t.shape[1]+2,1))[:H,:W]
def nw_front(name,tw=14.76,th=4.2,ppm=100):
    W,H=int(tw*ppm),int(th*ppm);P_=lambda m:int(m*ppm);Y=lambda z:H-int(z*ppm)
    a=tile_to('brick_red',1.2,0.86,ppm,W,H);a[:,:P_(6.4)]=tile_to('bluestone',2.0,1.2,ppm,P_(6.4),H)
    for z in np.arange(0,4.0,0.6):                                                      # dressed quoins at the corner and the bluestone/brick join
        q=0.45 if int(round(z/0.6))%2 else 0.25
        for x0 in (0.0,6.4-q): a[Y(z+0.55):Y(z),P_(x0):P_(x0+q)]=(196,186,164)
    a[Y(2.4):Y(0),P_(0.7):P_(2.4)]=tile_to('brick_dark',1.2,0.86,ppm,P_(2.4)-P_(0.7),Y(0)-Y(2.4))   # bricked-up doorway
    a[Y(2.5):Y(2.4),P_(0.6):P_(2.5)]=(190,180,160)                                    # lintel
    a[Y(2.9):Y(2.5),P_(0.6):P_(2.5)]=(238,236,228)                                    # white plaque
    a[Y(4.2):Y(3.95)]=(222,210,176)                                                    # cream top band under the eave
    a[Y(2.4):Y(1.0),P_(7.1):P_(8.1)]=(236,236,232);a[Y(2.32):Y(1.08),P_(7.18):P_(8.02)]=(46,56,64)   # white-framed window
    a[Y(1.72):Y(1.66),P_(7.18):P_(8.02)]=(236,236,232);a[Y(1.0):Y(0.9),P_(7.0):P_(8.2)]=(200,192,176)
    save(name,a+noise(H,W,1.5)[...,None],tw,th,mode='fit')
nw_front('nw_wing_front')
flat('hut_green',(44,76,52),tw=2,th=2,n=2,joints=(0.9,3),jc=0.8)
flat('roof_beige',(200,190,162),tw=3,th=3,n=2.5,grain=2,joints=(3,1.2),jc=0.9)
corrugated('corr_beige',(196,186,160))   # hall roof (satellite and main photo)
signboard('hoard_red','REDLEGS',(204,30,42),(250,250,250),5.0,3.7,'fit',ppm=80,hfrac=0.3)
signboard('hoard_blue','NFC',(26,96,186),(250,250,250),5.0,4.6,'fit',ppm=80,hfrac=0.45)
signboard('hoard_teal','NORWOOD',(26,150,168),(250,250,250),5.0,2.1,'fit',ppm=80,hfrac=0.35)
# ---------- standing supporters on each terrace step, seen from the field (cut-out card, hand-painted figures) ----------
SKIN=[(236,196,164),(222,176,140),(198,150,112),(160,112,80),(112,76,52),(244,210,184)]
PANTS=[(52,70,110),(30,30,34),(70,84,120),(150,136,108),(46,46,52),(96,100,108)]
def people(name,seed,tw=6.0,th=2.1,ppm=110,k=3):
    r=np.random.default_rng(seed);P_=ppm*k;W,H=int(tw*P_),int(th*P_)
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    X=lambda m:int(m*P_);Y=lambda m:H-int(m*P_)
    def dark(c,f): return tuple(int(v*f) for v in c[:3])+(255,)
    def person(cx,h,shade):
        s=h/1.75;sk=SKIN[r.integers(len(SKIN))];sc_=SHIRT[r.choice(len(SHIRT),p=SW)];pc=PANTS[r.integers(len(PANTS))]
        sc_=dark(sc_,shade*r.uniform(0.92,1.06));pc=dark(pc,shade);skc=dark(sk,shade)
        shorts=r.random()<0.3;lw=0.13*s;gap=0.025*s;hip=0.47*h;sh=0.81*h
        for sx in (-1,1):                                                    # legs and shoes
            x0=cx+sx*gap/2+(0 if sx>0 else -lw);x1=x0+lw
            d.rectangle([X(x0),Y(hip),X(x1),Y(0.05*s)],fill=pc)
            if shorts: d.rectangle([X(x0+0.01*s),Y(0.30*h),X(x1-0.01*s),Y(0.05*s)],fill=skc)
            d.rectangle([X(x0-0.01*s),Y(0.05*s),X(x1+0.02*s),Y(0)],fill=dark((30,28,28),shade))
        tw_,ww=0.21*s,0.17*s                                                 # torso: shoulders wider than the waist
        d.polygon([(X(cx-ww),Y(hip-0.02*s)),(X(cx+ww),Y(hip-0.02*s)),(X(cx+tw_),Y(sh-0.04*s)),(X(cx+tw_-0.05*s),Y(sh)),(X(cx-tw_+0.05*s),Y(sh)),(X(cx-tw_),Y(sh-0.04*s))],fill=sc_)
        d.polygon([(X(cx-ww),Y(hip-0.02*s)),(X(cx-ww+0.05*s),Y(hip-0.02*s)),(X(cx-tw_+0.06*s),Y(sh-0.04*s)),(X(cx-tw_),Y(sh-0.04*s))],fill=dark(sc_,0.78))
        if r.random()<0.25:                                                  # club scarf: navy and red bars
            for j in range(4): d.rectangle([X(cx-0.07*s),Y(sh-0.02*s-j*0.06*s),X(cx-0.02*s),Y(sh-0.02*s-(j+1)*0.06*s)],fill=dark((30,40,90) if j%2 else (196,34,44),shade))
        up=r.random()<0.04
        for sx in (-1,1):                                                    # arms: sleeve then forearm; now and then one arm up
            ax=cx+sx*(tw_+0.005*s);a0,a1=(ax,ax+sx*0.085*s) if sx>0 else (ax+sx*0.085*s,ax)
            if up and sx>0:
                d.rectangle([X(a0),Y(h+0.18*s),X(a1),Y(sh-0.04*s)],fill=skc);d.rectangle([X(a0),Y(sh+0.05*s),X(a1),Y(sh-0.04*s)],fill=sc_)
                d.ellipse([X(a0-0.01*s),Y(h+0.24*s),X(a1+0.01*s),Y(h+0.15*s)],fill=skc)
            else:
                d.rectangle([X(a0),Y(sh-0.02*s),X(a1),Y(0.50*h)],fill=skc);d.rectangle([X(a0),Y(sh-0.02*s),X(a1),Y(0.68*h)],fill=sc_)
        d.rectangle([X(cx-0.045*s),Y(0.87*h),X(cx+0.045*s),Y(sh-0.01*s)],fill=skc)   # neck
        hx,hy,rx,ry=cx,0.935*h,0.085*s,0.105*s
        d.ellipse([X(hx-rx),Y(hy+ry),X(hx+rx),Y(hy-ry)],fill=skc)
        hc=HAIR[r.integers(len(HAIR))];cap=r.random()<0.15
        if cap: hc=SHIRT[r.integers(4)]
        d.chord([X(hx-rx-0.005*s),Y(hy+ry+0.01*s),X(hx+rx+0.005*s),Y(hy-ry*(0.6 if cap else 0.2))],180,360,fill=dark(hc,shade))
        if cap: d.rectangle([X(hx-rx),Y(hy+0.01*s),X(hx+rx+0.06*s),Y(hy-0.01*s)],fill=dark(hc,shade*0.8))
        for ex in (-0.035,0.035): d.ellipse([X(hx+ex*s-0.012*s),Y(hy-0.005*s+0.012*s),X(hx+ex*s+0.012*s),Y(hy-0.005*s-0.012*s)],fill=(40,30,28,255))
        d.rectangle([X(hx-0.025*s),Y(hy-0.055*s),X(hx+0.025*s),Y(hy-0.065*s)],fill=dark(skc,0.75))
    for rank,(off,shade) in enumerate(((0.26,0.80),(0.0,1.0))):              # back rank peeks between the front rank's shoulders
        x=r.uniform(0,0.3)+off
        while x<tw+0.3:
            if r.random()<0.04: x+=r.uniform(0.3,0.5);continue
            h=r.uniform(1.55,1.86)+(0.05 if rank==0 else 0);cx=x%tw
            for wx in (cx,cx-tw,cx+tw): person(wx,h,shade)                   # wrap so the tile repeats without a seam
            x+=r.uniform(0.46,0.58)
    im=im.convert('RGBa').resize((W//k,H//k),Image.LANCZOS).convert('RGBA')
    save(name,np.array(im,float),tw,th,alpha=True)
# ---------- open terrace concrete (director 2026-11-18: grey concrete, hand-made joints) ----------
# u runs along the step (6 m tile): a saw-cut joint every 1.5 m, a sealed expansion joint at 0 and 3 m (black sealant
# with a chipped edge); the tread's front edge is a worn, lighter nosing; the back edge a shadow line where the next riser rises.
def concrete(name,tw,th,base,ppm=160,tread=True,seed=41):
    r=np.random.default_rng(seed);W,H=int(tw*ppm),int(th*ppm)
    a=canvas(W,H,base)+noise(H,W,4.5)[...,None]+noise(H,W,6,blur=6)[...,None]*1.6   # aggregate speckle and a soft mottle
    for _ in range(int(tw*th*30)):                                                    # dark aggregate stones
        x,y=r.integers(W),r.integers(H);a[y:y+2,x:x+2]*=r.uniform(0.7,0.85)
    a+=noise(H,W,7,blur=18)[...,None]*1.2                                              # broad, soft weathering (no hard edges)
    for xm in np.arange(0,tw,1.5):                                                    # joints
        x=int(xm*ppm)
        if abs(xm%3.0)<1e-6:
            a[:,max(0,x-3):x+3]=(28,28,30);a[:,max(0,x-5):max(0,x-3)]*=0.8;a[:,x+3:x+5]*=0.8
        else:
            a[:,max(0,x-1):x+1]*=0.55;a[:,x+1:x+2]*=0.85
    if tread:
        nz=int(0.07*ppm);a[H-nz:,:]=a[H-nz:,:]*1.12+6;a[H-nz:H-nz+2,:]*=0.85          # worn nosing at the front (v=0 is the image bottom)
        a[:3,:]*=0.6;a[3:8,:]*=0.85                                                    # shadow line at the back
    else:
        for xm in np.arange(0.375,tw,0.75): a[H//2-2:H//2+2,int(xm*ppm)-2:int(xm*ppm)+2]*=0.6   # formwork tie holes
        a[:2,:]*=0.8
    save(name,a,tw,th)
concrete('terrace_tread',6.0,0.9,(158,156,150))
concrete('terrace_riser',6.0,0.28,(136,134,129),tread=False,seed=42)
flat('paint_yellow',(236,196,40),tw=1,th=1,n=2)
