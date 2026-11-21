import fit_fence as ring, json, glob, numpy as np
from PIL import Image, ImageDraw
fit=json.load(open('fit.json'))
tiles=[]
for s,f in sorted(fit.items()):
    T=ring.load(f'faces/{s}.bin')
    S=ring.segments(T,f['floor']+0.5)
    S2=ring.segments(T,f['floor']+3.0)
    W=400; sc=W/300.0; c=np.array(f['centre'])
    im=Image.new('RGB',(W,W),(20,20,24)); d=ImageDraw.Draw(im)
    def P(p): return ((p[0]-c[0])*sc+W/2,(p[1]-c[1])*sc+W/2)
    for a,b in S2: d.line([P(a),P(b)],fill=(70,70,110))
    for a,b in S: d.line([P(a),P(b)],fill=(200,200,200))
    th=np.radians(f['long_deg']); u=np.array([np.cos(th),np.sin(th)]); v=np.array([-u[1],u[0]])
    A,B=f['half']
    pts=[P(c+u*A*np.cos(t)+v*B*np.sin(t)) for t in np.linspace(0,2*np.pi,200)]
    d.line(pts+[pts[0]],fill=(255,80,80),width=2)
    d.line([P(c-u*A),P(c+u*A)],fill=(255,80,80))
    d.text((5,5),f"{s} {A:.0f}x{B:.0f} {f['long_deg']:.0f}deg rms{f['fit_rms']}",fill=(255,255,0))
    tiles.append(im)
cols=5; rows=(len(tiles)+cols-1)//cols
out=Image.new('RGB',(cols*400,rows*400))
for i,t in enumerate(tiles): out.paste(t,((i%cols)*400,(i//cols)*400))
out.save('sheet.png'); print('ok')
