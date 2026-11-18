# python prj.py cam.json s,t,z ... -> u,v
import sys,json,numpy as np,cv2,stand
c=json.load(open(sys.argv[1]));K=np.array([[c['f'],0,c['w']/2],[0,c['f'],c['h']/2],[0,0,1]])
for q in sys.argv[2:]:
    s,t,z=map(float,q.split(','));X=np.array([stand.W(s,t,z)])
    p,_=cv2.projectPoints(X,np.array(c['r']),np.array(c['t']),K,None);print(q,'-> %.0f,%.0f'%tuple(p[0,0]))
