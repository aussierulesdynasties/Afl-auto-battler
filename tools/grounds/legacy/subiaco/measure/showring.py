import sys,cv2,json,numpy as np
sys.path.insert(0,'/home/user/work/subi/photo'); from camsolve import fr
a=cv2.imread(sys.argv[1]); d=json.load(open(sys.argv[2])); S=0.2945
for ang,f,b in d:
    if f is None: continue
    t=np.radians(ang); r0=fr(np.array([ang]))[0]
    for dd,col in ((f,(0,0,255)),(b,(255,0,255))):
        r=r0+dd; cv2.circle(a,(int(941+r*np.cos(t)/S),int(1021-r*np.sin(t)/S)),2,col,-1)
    if int(ang*2)%30==0: r=r0+b+8; cv2.putText(a,str(int(ang)),(int(941+r*np.cos(t)/S)-10,int(1021-r*np.sin(t)/S)),0,0.6,(0,255,255),2)
cv2.imwrite(sys.argv[3],a[520:1540,350:1530])
