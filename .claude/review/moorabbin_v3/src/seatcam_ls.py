import bpy,json,sys,numpy as np
a=sys.argv[sys.argv.index('--')+1:];D=a[0]
o=bpy.data.objects['longstand_benches'];V=np.array([o.matrix_world@v.co for v in o.data.vertices])
zs=np.round(V[:,2],2);top=V[V[:,2]>V[:,2].max()-1.2]          # upper rows (back slats of the top 2 rows)
# end of the stand: the top-row point farthest from the stand's centroid; look 30 m along the row toward the middle
c=top.mean(0);A=top[np.argmax(np.linalg.norm(top[:,:2]-c[:2],axis=1))]
d=np.linalg.norm(top[:,:2]-A[:2],axis=1);B=top[np.argmin(np.abs(d-30))]
eye=A+(B-A)*0.2;eye[2]=A[2]+0.6
L=json.load(open(D+'/seatshots.json'))
L.append(dict(eye=eye.tolist(),at=[float(B[0]),float(B[1]),float(B[2]-4.0)],lens=24,out=D+'/proof/seat_longstand.png'))
mid=V[np.argmin(np.abs(V[:,2]-np.median(V[:,2]))+np.linalg.norm(V[:,:2]-B[:2],axis=1)*0.01)]
L.append(dict(eye=[float(mid[0]),float(mid[1]),float(mid[2]+0.9)],at=[float(B[0]+(B[0]-A[0])*0.2),float(B[1]+(B[1]-A[1])*0.2),float(mid[2]+0.3)],lens=35,out=D+'/proof/seat_longstand_close.png'))
json.dump(L,open(D+'/seatshots.json','w'),indent=1);print('LS',eye,B)
