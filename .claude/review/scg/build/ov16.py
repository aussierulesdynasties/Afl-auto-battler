import io,contextlib,cv2,sys
with contextlib.redirect_stdout(io.StringIO()):exec(open('geo.py').read())
cj16=json.load(open(sys.argv[1]));p16=cj16['p'];im=cv2.imread(cj16['img'])
x0,y0,x1,y1,k=map(float,sys.argv[3:8])
for d,(lo,hi,zf,zo,s) in sorted(OUT.items()):
    a=math.radians(d);u=np.array([math.cos(a),math.sin(a)])
    top=proj(p16,[(*(PC+hi*u),zo)])[0];bot=proj(p16,[(*(PC+hi*u),0)])[0]
    c=(0,255,255) if s=='bottom' else (255,0,255)
    cv2.circle(im,tuple(int(t) for t in top),1,c,-1);cv2.circle(im,tuple(int(t) for t in bot),1,c,-1)
    if d%2==0:
        cv2.line(im,tuple(int(t) for t in top),tuple(int(t) for t in bot),c,1)
        if d%4==0:cv2.putText(im,str(int(d)),(int(bot[0])-8,int(bot[1])+12),0,0.35,c,1)
for t in TW:
    a,b=proj(p16,[(*t,0),(*t,68.09)]);cv2.line(im,tuple(a.astype(int)),tuple(b.astype(int)),(0,0,255),1)
c=im[int(y0):int(y1),int(x0):int(x1)];c=cv2.resize(c,None,fx=k,fy=k,interpolation=cv2.INTER_CUBIC);cv2.imwrite(sys.argv[2],c)
