# Hand-made textures for the clubrooms (no photo pixels). Layout read off w09 (front, x pixels south->north),
# colours read off w09 and scaled to daylight albedo. Run after texgen.py: adds to tex3/tex.json.
import numpy as np,json,os
from PIL import Image,ImageDraw,ImageFont
exec(open('texgen.py').read().split('TILE={};PANEL={}')[0])   # helpers: noise, rgb, base, save
J=json.load(open(os.path.join(OUT,'tex.json')));TILE={k:tuple(v) for k,v in J['TILE'].items()};PANEL={k:True for k in J['PANEL']}
PX=200
def u8(a):return Image.fromarray(np.clip(a,0,255).astype(np.uint8))
NAVY=(29,41,50);DOOR=(34,46,54)
# ---- painted blockwork (blue building and ground floor walls): 0.40 x 0.20 m blocks, faint joints ----
def blocks(col,w_m,h_m,seed,K=PX):
    w,h=int(w_m*K),int(h_m*K);img=base(h,w,col,4,6,seed)
    y=np.arange(h)/K;x=np.arange(w)/K
    img[(y%0.2)<0.008]-=10
    row=(y//0.2).astype(int)
    for r in np.unique(row):
        m=row==r;xo=(x+0.2*(r%2))%0.4;img[np.ix_(m,xo<0.008)]-=8
    return img
save('club_render',blocks('#c4a585',2,2,101));TILE['club_render']=(2,2)
# ---- face brick (green building upper walls, gable): 230 x 76 mm bricks, 10 mm joints, stretcher bond ----
def brick(col,seed):
    w,h=int(1.84*PX),int(0.86*PX);img=np.zeros((h,w,3))+rgb('#d2c3a6')+noise(h,w,40,4,seed)[...,None]
    r=np.random.default_rng(seed);x=np.arange(w)/PX;y=np.arange(h)/PX
    for c in range(10):
        y0,y1=c*0.086,c*0.086+0.076;ys=(y>=y0)&(y<y1);off=0.115*(c%2)
        for k in range(-1,9):
            x0=k*0.23+off;xs=((x-x0)%1.84<0.22)
            img[np.ix_(ys,xs)]=rgb(col)*(1+r.normal(0,0.06))+r.normal(0,3,3)
    img+=noise(h,w,30,5,seed+1)[...,None]
    return img
save('club_brick',brick('#b18a66',111));TILE['club_brick']=(1.84,0.86)
# ---- weatherboard (green building gable ends, w04): 0.15 m boards, shadow under each lap ----
w,h=int(2*PX),int(1.2*PX);img=base(h,w,'#c3a57c',3,5,121);y=(np.arange(h)/PX)%0.15
img+=np.where(y<0.012,-38,np.where(y<0.03,-12,(y-0.03)/0.12*10))[:,None,None]
save('club_weather',img);TILE['club_weather']=(2,1.2)
# ---- corrugated roofing: 76 mm pitch sine ribs running down the slope ----
def corr(col,tile,seed,amp=16):
    w,h=int(tile[0]*PX),int(tile[1]*PX);img=base(h,w,col,3,4,seed);x=np.arange(w)/PX
    img+=(np.sin(2*np.pi*x/0.0762)*amp)[None,:,None];return img
# w04 (2025): the clubroom's corrugated roof reads mid teal-green in daylight (median 96,125,121); paint darkened by the render/photo ratio so the sunlit render lands on that tone
save('roof_green',corr('#446e67',(1.83,1.83),131));TILE['roof_green']=(1.83,1.83)
# ---- AC units (w04): dark grey casing with a fine louvre grille ----
w,h=int(1*PX),int(1*PX);img=base(h,w,'#4a4c4e',3,4,141);y=(np.arange(h)/PX)%0.03
img+=np.where(y<0.012,-22,10)[:,None,None];img[:8]+=30;img[-8:]+=30;img[:,:8]+=30;img[:,-8:]+=30
save('ac_unit',img);TILE['ac_unit']=(1,1)
# ---- blue wall seen behind the glass balcony ----
save('bal_back_blue',base(200,200,'#5aa6e6',3,4,151));TILE['bal_back_blue']=(2,2)
# ======== front panels (PANEL: image left = south end, top = wall top) ========
K=100
def front(name,length_m,height_m,x_s,x_n,feats,seed,wall='#c4a585'):
    """feats: (kind, x0, x1, y0, y1) in w09 pixels; x maps x_s..x_n -> 0..length, y maps 240(top)..300(ground)."""
    W,H=int(length_m*K),int(height_m*K);img=blocks(wall,length_m,height_m,seed,K)
    im=u8(img);d=ImageDraw.Draw(im)
    X=lambda x:int((x-x_s)/(x_n-x_s)*W);Y=lambda y:int((y-240)/60*H)
    for kind,x0,x1,y0,y1 in feats:
        if kind=='door':
            d.rectangle([X(x0),Y(y0),X(x1),H],fill=DOOR);d.rectangle([X(x0)+3,Y(y0)+3,X(x1)-3,H],outline=(46,60,70),width=2)
            d.rectangle([X(x1)-int(0.12*K),Y(y0)+int(0.95*K),X(x1)-int(0.07*K),Y(y0)+int(1.0*K)],fill=(170,170,165))
        elif kind=='post':d.rectangle([X(x0),0,X(x1),H],fill=NAVY)
        elif kind=='win':
            d.rectangle([X(x0),Y(y0),X(x1),Y(y1)],fill=(22,30,36));d.rectangle([X(x0),Y(y0),X(x1),Y(y1)],outline=(60,72,80),width=3)
            d.line([((X(x0)+X(x1))//2,Y(y0)),((X(x0)+X(x1))//2,Y(y1))],fill=(60,72,80),width=3)
        elif kind=='servery':
            d.rectangle([X(x0),Y(y0),X(x1),Y(y1)],fill=(18,24,28));d.rectangle([X(x0)-4,Y(y1),X(x1)+4,Y(y1)+8],fill=(214,212,204))
        elif kind=='band':d.rectangle([X(x0),Y(y0),X(x1),Y(y1)],fill=(30,36,40))
        elif kind=='light':d.rectangle([X(x0),Y(y0),X(x1),Y(y1)],fill=(224,222,214))
    d.rectangle([0,H-int(0.10*K),W,H],fill=(150,132,112))   # plinth course at the ground
    im.save(os.path.join(OUT,name+'.png'));PANEL[name]=True
# blue building front: w09 x 578 (south, u 24) .. 885 (north, u 0); 3 doors, clerestory windows under the fascia
cl=[('win',a,b,247,255) for a,b in ((597,617),(635,660),(690,710),(727,753),(770,793),(810,833),(853,875))]
front('blue_front',24.0,2.6,578,885,cl+[('door',660,670,251,300),('door',750,760,251,300),('door',836,846,251,300),
      ('light',603,607,258,262),('light',705,709,258,262),('light',795,799,258,262)],161)
# green building ground floor: w09 x 200 (south) .. 447 (north); doors, servery window, navy posts
front('green_front_lo',13.4,3.2,200,447,[('post',228,232,0,0),('door',239,256,248,300),('door',287,300,248,300),('post',310,315,0,0),
      ('servery',318,354,248,277),('door',359,376,248,300),('post',394,397,0,0),('door',420,432,248,300),('post',443,447,0,0),
      ('band',380,447,244,252)],171)
# glass balcony block ground floor: w09 x 447 (south) .. 577 (north)
front('bal_front_lo',8.6,3.2,447,577,[('post',447,451,0,0),('door',470,486,248,300),('post',494,497,0,0),('post',521,525,0,0),
      ('post',544,547,0,0),('post',572,577,0,0),('band',451,572,244,252)],181)
# glass balustrade: navy frame, vertical balusters over tinted glass (w09 x 447..577, y 213..233)
W,H=860,110;img=np.zeros((H,W,3))+rgb('#7fa6c8')+noise(H,W,6,6,191)[...,None];im=u8(img);d=ImageDraw.Draw(im)
for x in range(0,W,9):d.rectangle([x,0,x+2,H],fill=NAVY)
for x in np.linspace(0,W-8,5).astype(int):d.rectangle([x,0,x+8,H],fill=NAVY)
d.rectangle([0,0,W,7],fill=NAVY);d.rectangle([0,H-7,W,H],fill=NAVY);im.save(os.path.join(OUT,'glass_bal.png'));PANEL['glass_bal']=True
# ---- blue roof (aerial + w09): sky-blue corrugated, white "Territorians" script, TIO logo box (white, blue letters, red bar) ----
L,D=24.6,8.6;W,H=int(L*K),int(D*K)
img=np.zeros((H,W,3))+rgb('#3b9be2')+noise(H,W,8,3,201)[...,None];x=np.arange(W)/K
im=u8(img);d=ImageDraw.Draw(im)
# panel u runs 0 (south) .. 1 (north); v 0 at the eave (front, bottom of the image) .. 1 at the ridge (top)
# no lettering (director 2026-11-18): plain blue roof
img=np.asarray(im).astype(float)
# corrugation at 100 px/m cannot hold a 76 mm sine cleanly: use soft ribs every 0.19 m (trimdek profile)
xr=(np.arange(W)/K)%0.19;img+=np.where(xr<0.03,-14,np.where(xr<0.045,8,0))[None,:,None]
save('roof_blue_club',img);PANEL['roof_blue_club']=True
# ---- back slope (aerial): green roofing with a yellow band along the ridge over the south part ----
W,H=int(L*K),int(7.6*K);img=np.zeros((H,W,3))+rgb('#59745a')+noise(H,W,8,4,211)[...,None]
im=u8(img);d=ImageDraw.Draw(im)
d.polygon([(0,0),(int(16/L*W),0),(0,int(0.75*H))],fill=(222,186,74))
img=np.asarray(im).astype(float);xr=(np.arange(W)/K)%0.19;img+=np.where(xr<0.03,-14,np.where(xr<0.045,8,0))[None,:,None]
save('roof_back_club',img);PANEL['roof_back_club']=True
json.dump(dict(TILE=TILE,PANEL=list(PANEL)),open(os.path.join(OUT,'tex.json'),'w'))
print('club textures:',[k for k in ('club_render','club_brick','club_weather','roof_green','ac_unit','bal_back_blue','blue_front','green_front_lo','bal_front_lo','glass_bal','roof_blue_club','roof_back_club') if os.path.exists(os.path.join(OUT,k+'.png'))])
