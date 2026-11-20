# Far-rib proof: photo | render strip of the far roof, and the satellite with the built ribs (inner->outer) drawn in red.
import json,sys,math,numpy as np
from PIL import Image,ImageDraw
rp,fj,tag=sys.argv[1:4]
ph=Image.open('photo_clean.png').convert('RGB');r=Image.open(rp).convert('RGBA')
bg=Image.new('RGB',r.size,(60,60,60));bg.paste(r,mask=r.split()[3]);r=bg
box=(660,330,1120,480);s=3
def lab(im,t):
    d=ImageDraw.Draw(im);d.rectangle((0,0,9*len(t)+16,26),fill=(0,0,0));d.text((8,7),t,fill=(255,255,255));return im
cp=lab(ph.crop(box).resize(((box[2]-box[0])*s,(box[3]-box[1])*s),Image.LANCZOS),'photo');cr=lab(r.crop(box).resize(cp.size,Image.LANCZOS),'render '+tag)
st=Image.new('RGB',(cp.width,cp.height*2+8),(30,30,30));st.paste(cp,(0,0));st.paste(cr,(0,cp.height+8));st.save(f'z_ribstrip_{tag}.png')
S=json.load(open('sat.json'));D=json.load(open('geo_j.json'));SH=D['roofshift']
def ip(arr,a):arr=np.array(arr);n=len(arr);return float(np.interp((a%360)/360*n,np.arange(n+1),np.r_[arr,arr[0]]))
def uv(a,rr):t=math.radians(a);return (S['px']+(rr*math.cos(t)+SH[0])/S['mpp'],S['py']-(rr*math.sin(t)+SH[1])/S['mpp'])
im=Image.open('sat.png').convert('RGB');d=ImageDraw.Draw(im)
for ai,ao in json.load(open(fj)):d.line([uv(ai,ip(D['rin'],ai)),uv(ao,ip(D['rout'],ao))],fill=(255,0,0),width=2)
pts=[uv(x,rr) for x in (348,399) for rr in (70,130)];xs=[p[0] for p in pts];ys=[p[1] for p in pts]
c=im.crop((int(min(xs))-20,int(min(ys))-20,int(max(xs))+20,int(max(ys))+20));c=c.resize((c.width*3,c.height*3),Image.LANCZOS)
lab(c,'satellite + built ribs (red) '+tag).save(f'z_ribsat_{tag}.png')
