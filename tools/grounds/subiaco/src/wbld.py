exec(open('wsolve.py').read().split("for x,y,h in JB")[0])
import json
def W(px,z):X=onz(np.array(px,float),z);return [round(float(X[0]),2),round(float(X[1]),2),z]
# B1: mono-pitch roof (west edge 3.4 m, east edge 2.6 m), east face down to ground
B1={'roof':[W((177,238),3.4),W((219,217),2.6),W((198,266),2.6),W((174,265),3.4)]}
# B2: gable, eaves 2.6 m, ridge 3.6 m, ridge parallel to the stand
B2={'we':[W((233,242),2.6),W((217,276),2.6)],'rg':[W((240,243),3.6),W((224,283),3.6)],'ee':[W((260,239),2.6),W((262,291),2.6)]}
json.dump({'B1':B1,'B2':B2},open('wbld.json','w'),indent=1);print(json.dumps({'B1':B1,'B2':B2}))
