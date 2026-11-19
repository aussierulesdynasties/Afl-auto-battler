# Geelong crest traced on the p1 grid (photo pixels, canvas origin 478,486), drawn by hand at 20x.
# The photo sees the crest at an angle, so each half is traced on its own (no mirroring).
import math,os,json
from PIL import Image,ImageDraw,ImageFont
def cats_p1(w,h,NAVY,WHITE,font,raw=False):
    K=20;OX,OY=478,486;DK=(22,24,32)
    def P(pts):return [((x-OX)*K,(y-OY)*K) for x,y in pts]
    W,H=66*K,66*K;im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    # outer dark edge, clockwise from the top-left flare (p1 grid)
    rim=[(488.6,494.6),(491.0,495.2),(500,494.6),(511,494.4),(520,495.2),(527,496.7),(530.8,497.8),(532.6,497.0),   # top edge; both corners flare up and out
         (531.6,500.2),(532.8,504.2),(533.6,509),(532.2,513.6),(529,518.6),(525,523.4),(520,527.6),(515,530.6),(511,532.2),
         (507.4,530.4),(503,527.6),(498,523.6),(494,519),(490.6,514),(488.4,509),(488.0,505),(488.6,501.0),(489.6,497.6)]
    cx,cy=510.6,512
    def shield(off):
        out=[]
        for x,y in rim:
            dx,dy=x-cx,y-cy;L=math.hypot(dx,dy) or 1;out.append((x+dx/L*off,y+dy/L*off))
        return P(out)
    d.polygon(shield(0.7),fill=DK);d.polygon(shield(-0.8),fill=WHITE)
    m=Image.new('L',(W,H),0);ImageDraw.Draw(m).polygon(shield(-1.6),fill=255)
    f=Image.new('RGBA',(W,H),WHITE);g=ImageDraw.Draw(f)
    # navy top band under GEELONG; it drops between the eyes into the brow
    g.polygon(P([(482,488),(540,488),(540,504.6),(525.6,505.0),(524,508.6),(514.6,509.0),(512.8,511.8),(508.8,511.8),
                 (507.2,507.4),(499.6,507.2),(497.6,502.2),(482,502.0)]),fill=NAVY)
    # the cat's face: navy from the band down to the first hoop, which runs out to each side short of the rim
    g.polygon(P([(499,506),(524.6,506),(524.2,510.2),(528.6,511.2),(529.8,516.0),(523,516.0),(517,515.6),(513.6,516.2),(511.6,517.2),
                 (509.0,517.2),(507.4,516.0),(503,515.6),(497,515.2),(491.6,515.0),(492.2,510.6),(498.6,510.0)]),fill=NAVY)
    # eyes: slanted white almonds with navy pupils, holes in the navy face
    g.polygon(P([(500.8,509.0),(503.4,507.7),(506.6,508.8),(507.6,510.8),(504.8,511.8),(502.0,511.0)]),fill=WHITE)
    g.ellipse(P([(503.6,509.0),(505.6,511.0)]),fill=NAVY)
    g.polygon(P([(513.0,511.2),(514.2,509.4),(517.2,508.8),(520.4,509.8),(518.6,512.3),(515.6,512.8)]),fill=WHITE)
    g.ellipse(P([(515.6,509.8),(517.6,511.8)]),fill=NAVY)
    # white star between the eyes
    st=[];sx,sy,R,r=509.8,513.0,2.0,0.8
    for i in range(10):
        a=-math.pi/2+i*math.pi/5;rr=R if i%2==0 else r;st.append((sx+rr*math.cos(a),sy+rr*math.sin(a)))
    g.polygon(P(st),fill=WHITE)
    # white whiskers waving through the first hoop
    for pts in([(493.4,512.8),(496.6,513.8),(500.2,513.2),(503.4,514.2),(506.2,514.8)],[(513.8,514.8),(516.8,514.0),(520.2,514.6),(523.6,513.6),(527.6,514.0)]):
        g.line(P(pts),fill=WHITE,width=int(0.8*K),joint='curve')
    # nose and the V of the mouth in the white band
    g.polygon(P([(508.4,516.4),(511.8,516.4),(511.2,519.0),(510.4,520.6),(509.4,520.6),(508.8,519.0)]),fill=NAVY)
    g.polygon(P([(504.6,517.0),(506.2,516.4),(509.8,520.0),(509.0,521.2)]),fill=NAVY)
    g.polygon(P([(511.0,521.2),(510.2,520.0),(514.6,517.6),(515.8,518.6)]),fill=NAVY)
    # second hoop, a smile with the white chin at its centre
    g.polygon(P([(498.4,521.0),(503,521.2),(507,522.2),(510,522.6),(513,522.2),(517,521.4),(521.6,521.0),
                 (521.2,523.6),(517,527.0),(512.4,529.4),(510,529.6),(505.4,528.0),(500.6,524.6)]),fill=NAVY)
    g.polygon(P([(508.2,522.0),(511.8,522.0),(510.0,524.6)]),fill=WHITE)
    im.paste(f,(0,0),m);d=ImageDraw.Draw(im)
    # GEELONG in white across the band (letters x 493-527, y 497-502), following the crest's tilt
    gf=font('BarlowCondensed-Bold.ttf',int(6.6*K));txt='GEELONG';sp=0.6*K
    tw=sum(d.textlength(c,font=gf) for c in txt)+sp*6;sc=(527-493)*K/tw;x=(493-OX)*K
    for c in txt:
        cw=d.textlength(c,font=gf)*sc;ccx=x+cw/2;px=ccx/K+OX;u=(px-510)/17
        ccy=(499.4-OY)*K+0.8*K*u*u+0.03*K*(px-493)
        L=Image.new('RGBA',(int(10*K),int(10*K)),(0,0,0,0));ImageDraw.Draw(L).text((5*K-d.textlength(c,font=gf)/2,1.2*K),c,font=gf,fill=WHITE)
        L=L.resize((max(1,int(L.width*sc)),L.height),Image.LANCZOS).rotate(-u*12,resample=Image.BICUBIC)
        im.alpha_composite(L,(int(ccx-L.width/2),int(ccy-5*K)));x+=cw+sp*sc
    # CATS: navy with a dark edge, x 497-525, y 530-542
    cf=font('BarlowCondensed-Bold.ttf',int(17*K));T=Image.new('RGBA',(int(60*K),int(30*K)),(0,0,0,0))
    ImageDraw.Draw(T).text((K,K),'CATS',font=cf,fill=NAVY,stroke_width=int(0.7*K),stroke_fill=DK);T=T.crop(T.getbbox())
    T=T.resize((int(28*K),int(12*K)),Image.LANCZOS);im.alpha_composite(T,(int((497-OX)*K),int((530-OY)*K)))
    if os.environ.get('CREST_CAL'):   # calibration: four coloured dots at known photo pixels
        im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
        for (x,y),cl in zip(CAL,((255,0,0),(0,200,0),(0,0,255),(255,200,0))):d.ellipse(P([(x-1.6,y-1.6),(x+1.6,y+1.6)]),fill=cl+(255,))
    elif os.path.exists(WARP) and not raw:   # undo the facade's slant in the p1 view (affine measured from the dots)
        A=json.load(open(WARP));im=im.transform(im.size,Image.AFFINE,tuple(A),resample=Image.BICUBIC)
    if raw:return im
    x0,y0,x1,y1=P([BOX[:2],BOX[2:]])[0]+P([BOX[:2],BOX[2:]])[1]
    return im.crop((int(x0),int(y0),int(x1),int(y1))).resize((w,h),Image.LANCZOS)
BOX=(481.45,488.53,541.64,545.68)   # fixed texture box in p1 pixels (tex.py places it on the facade)
CAL=[(491,498),(530,498),(491,538),(530,538)]
WARP=os.path.join(os.path.dirname(os.path.abspath(__file__)),'crest_warp.json')
