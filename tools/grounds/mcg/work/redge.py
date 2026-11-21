import sys,json,numpy as np;sys.path.insert(0,'work');import tri,earthcam as E
from PIL import Image,ImageDraw
v,z=sys.argv[1],float(sys.argv[2])
c=tri.camv(v);im=np.asarray(Image.open(f'ge/{v}.png').convert('RGB')).astype(float)
R=np.arange(60,170,0.25);B=np.arange(0,360,1.0);res=[]
S=np.zeros((len(B)*3,len(R),3),np.uint8)
for i,b in enumerate(B):
    a=np.radians(b);X=np.stack([R*np.sin(a),R*np.cos(a),np.full_like(R,z)],1)
    P=np.array([E.proj(c,x) for x in X]);u=np.clip(P[:,0].round().astype(int),0,1919);w=np.clip(P[:,1].round().astype(int),0,1079)
    px=im[w,u];S[i*3:i*3+3]=px;L=px.mean(1);L=np.convolve(L,np.ones(5)/5,'same')
    k=np.where((R>78)&(L<85))[0];edge=None
    if len(k):
        for j in range(k[0],len(R)-12):
            if L[j:j+12].min()>120: edge=R[j];break
    res.append([float(b),None if edge is None else float(edge)])
json.dump(res,open(f'work/redge_{v}.json','w'))
I=Image.fromarray(S).resize((len(R)*2,len(B)*3));d=ImageDraw.Draw(I)
for r in range(60,170,10):
    x=(r-60)*8;d.line([x,0,x,I.height],fill=(255,0,255));d.text((x+2,2),str(r),fill=(255,0,255))
for b in range(0,360,10):
    y=b*3;d.line([0,y,40,y],fill=(255,255,0));d.text((2,y+1),str(b),fill=(255,255,0))
for b,e in res:
    if e: x=(e-60)*8;y=b*3+1;d.line([x-3,y,x+3,y],fill=(255,0,0),width=2)
I.save(f'work/redge_{v}.png');I.crop((0,0,880,540)).save('work/re1.png');I.crop((0,540,880,1080)).save('work/re2.png')
