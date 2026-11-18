import cv2,sys,json
# mark.py strip.png a_start a0 a1 out  ; marks from marks.json: low (rows 0-175, green), up (rows 300-720, cyan), vom (magenta)
im=cv2.imread(sys.argv[1]);As=float(sys.argv[2]);a0,a1=float(sys.argv[3]),float(sys.argv[4]);M=json.load(open('marks.json'))
x0=int((a0-As)/0.05);x1=int((a1-As)/0.05);c=im[:,x0:x1].copy()
for k,(r0,r1,col) in {'low':(0,150,(0,255,0)),'up':(300,720,(255,255,0)),'vom':(260,330,(255,0,255))}.items():
    for a in M[k]:
        if a0<=a<a1:X=int((a-a0)/0.05);cv2.line(c,(X,r0),(X,r1),col,1)
for k in range(int(a0),int(a1)+1):
    X=int((k-a0)/0.05);cv2.putText(c,str(k),(X,12),0,0.35,(0,255,255),1)
c=cv2.resize(c,(c.shape[1]*2,c.shape[0]))
cv2.imwrite(sys.argv[5],c)
