import json,cv2,numpy as np,math,sys
f=sys.argv[1];u0,u1,w0,w1=map(float,sys.argv[2:6]);dw=float(sys.argv[6]);out=sys.argv[7]
h=json.load(open('sat/her20.json'));c=h['c'];HS=h['HS'];m=h['mpp']
sat=cv2.imread('sat/her20.png')
ns={};exec(open('blds.py').read(),ns);FR=ns['FR'];BLD=ns['BLD']
(ox,oy),a=FR[f];a=math.radians(a);U=np.array([math.cos(a),math.sin(a)]);W=np.array([-U[1],U[0]])
K=10
uu,ww=np.meshgrid(np.arange(u0,u1,1/K),np.arange(w1,w0,-1/K))
X=ox+uu*U[0]+ww*W[0];Y=oy+uu*U[1]+ww*W[1]
mx=((X-c[0]+HS)/m).astype(np.float32);my=((HS-(Y-c[1]))/m).astype(np.float32)
im=cv2.remap(sat,mx,my,cv2.INTER_LINEAR)
def P(u,w):return (int((u-u0)*K),int((w1-w)*K))
for g in np.arange(math.ceil(u0/5)*5,u1,5):
    cv2.line(im,P(g,w0),P(g,w1),(0,255,255) if g%10==0 else (0,140,140),1);cv2.putText(im,'%d'%g,P(g,w1-1.5),0,0.4,(0,255,255),1)
for g in np.arange(math.ceil(w0/5)*5,w1,5):
    cv2.line(im,P(u0,g),P(u1,g),(0,255,255) if g%10==0 else (0,140,140),1);cv2.putText(im,'%d'%g,P(u0+0.3,g+0.3),0,0.4,(0,255,255),1)
if dw>-99:
  for b in BLD:
    if b[1]!=f:continue
    cv2.rectangle(im,P(b[2],b[5]+dw),P(b[3],b[4]+dw),(0,0,255),2);cv2.putText(im,b[0],P(b[2]+0.5,b[4]+dw+1),0,0.5,(0,0,255),2)
cv2.imwrite(out,im)
