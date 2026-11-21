# Move an OpenCV camera (r,t) with the stand: the stand plan moved onto the satellite by a rigid turn+shift T
# (old O (-72.4,-15.0) along (-1.6,29.9) -> new O (-68.6,-7.5) along (-0.36,29.94)); a camera fitted to the stand moves with it.
# python camxf.py in.json out.json
import json,sys,math,numpy as np,cv2
O0=np.array([-72.4,-15.0]);a0=np.array([-1.6,29.9]);O1=np.array([-68.6,-7.5]);a1=np.array([-68.96,22.44])-O1
th=math.atan2(a1[1],a1[0])-math.atan2(a0[1],a0[0]);c,s=math.cos(th),math.sin(th)
RT=np.array([[c,-s,0],[s,c,0],[0,0,1.]]);d=np.r_[O1-RT[:2,:2]@O0,0]
J=json.load(open(sys.argv[1]));R,_=cv2.Rodrigues(np.array(J['r'],float));t=np.array(J['t'],float)
R2=R@RT.T;t2=t-R2@d;J['r']=cv2.Rodrigues(R2)[0].ravel().tolist();J['t']=t2.tolist()
json.dump(J,open(sys.argv[2],'w'));print('moved',sys.argv[1],'->',sys.argv[2],'centre',(-R2.T@t2).round(2))
