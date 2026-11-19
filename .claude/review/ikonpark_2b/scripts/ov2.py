import cv2,json,sys,numpy as np
G=json.load(open(sys.argv[1]));out=sys.argv[2];x0,y0,x1,y1=map(float,sys.argv[3:7]);K=float(sys.argv[7]) if len(sys.argv)>7 else 0
DX,DY=map(float,__import__('os').environ.get('DIR','0.46,0.89').split(','));S=int(__import__('os').environ.get('S','3'))
s=cv2.imread(__import__('os').environ.get('SAT','sat/esri_025.png'))
r0,r1,c0,c1=int((230-y1)/0.25),int((230-y0)/0.25),int((x0+150)/0.25),int((x1+150)/0.25)
c=cv2.resize(s[r0:r1,c0:c1],None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
def px(x,y,z=0):
  x+=K*DX*z;y+=K*DY*z
  return int(((x+150)/0.25-c0)*S),int(((230-y)/0.25-r0)*S)
col={'pratt':(0,0,255),'heroes':(0,255,0),'gardiner':(255,0,0),'fosters':(255,0,255),'eaststep':(0,255,255),'legends':(255,255,0)}
for n in G['stands']:
  if n not in G: continue
  st=G[n]
  for key,th in (('front',1),('back',2)):
    p=[px(*q) for q in st[key]];cv2.polylines(c,[np.array(p)],False,col.get(n,(255,255,255)),th)
  for i in st.get('mastidx',[]):
    q=st['back'][i];cv2.drawMarker(c,px(q[0],q[1],q[2]+st.get('masth',4)),(0,0,255),cv2.MARKER_TILTED_CROSS,14,2)
for xx in range(int(x0)//10*10,int(x1)+1,10):
  u=px(xx,0)[0];cv2.line(c,(u,0),(u,8),(0,200,255),2);cv2.putText(c,str(xx),(u+2,22),0,0.45,(0,200,255),1)
for yy in range(int(y0)//10*10,int(y1)+1,10):
  v=px(0,yy)[1];cv2.line(c,(0,v),(8,v),(0,200,255),2);cv2.putText(c,str(yy),(10,v+4),0,0.45,(0,200,255),1)
[cv2.drawMarker(c,px(*m),(255,255,255),cv2.MARKER_DIAMOND,16,2) for m in [[-32.08,104.16],[-22.23,-39.47],[117.50,78.77],[132.35,-69.24]]];cv2.imwrite(out,c);print(c.shape)
