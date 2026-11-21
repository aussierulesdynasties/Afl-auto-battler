import json,numpy as np,cv2
exec(open('fitgreen.py').read().split("for th0")[0])
st=json.load(open('stand.json'));O=np.array(st['O']);a=np.array(st['a']);b=np.array(st['b'])
for zc in (5.0,5.5,6.0,6.5):
    # corner on ray1 at height zc
    l=(zc-C[2])/r1[2];A=C+l*r1;dd=A[:2]-O
    for thd in (76.4,93.1):
        th=np.radians(thd);d=np.array([np.cos(th),np.sin(th),0.]);n=np.array([-d[1],d[0],0.]);n=-n if n[0]>0 else n
        out=[]
        for pitch in (13,18,22,26):
            B=A+8*n+np.array([0,0,8*np.tan(np.radians(pitch))]);out.append('%d:%.1f'%(pitch,line_res(A,B-A,[(970,316)])[0]))
        print('zc',zc,'s %.1f t %.1f'%(dd@a,dd@b),'th',thd,' '.join(out))
