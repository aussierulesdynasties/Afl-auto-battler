import sys,numpy as np,gecam as G
def pick(v,px,py,z=0.0):
    p=np.array([0.0,0.0])
    for _ in range(30):
        f=G.P(v,[p[0],p[1],z])[0][:2]-[px,py]
        J=np.zeros((2,2))
        for i in range(2):
            d=np.zeros(2);d[i]=0.5
            J[:,i]=(G.P(v,[p[0]+d[0],p[1]+d[1],z])[0][:2]-G.P(v,[p[0],p[1],z])[0][:2])/0.5
        p=p-np.linalg.solve(J,f)
    return p
if __name__=='__main__':
    v=sys.argv[1];a=sys.argv[2:]
    for i in range(0,len(a),3):
        x,y=pick(v,float(a[i]),float(a[i+1]),float(a[i+2]));print(a[i:i+3],round(x,1),round(y,1))
