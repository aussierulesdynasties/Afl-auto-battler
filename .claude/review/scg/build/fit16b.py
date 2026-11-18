exec(open('fitx.py').read())
import io,contextlib
pitch=dens(G['4000006'],3);pitch=np.c_[pitch,np.zeros(len(pitch))]
HEAD={'F':(197,334),'A':(337,97),'B':(1205,74),'C':(1372,139),'D':(1263,553),'E':(550,561)}
SHAFT={'F':[(212.5,437),(222,531)],'A':[(347,187),(355,269)],'B':[(1195,156),(1189,237)],'C':[(1361,219),(1349,312)],
'D':[(1256,687),(1242,825)],'E':[(556,687),(564,812)]}
GR=np.load('grass16.npy');GR=GR[GR[:,1]<570][::3]
print(len(GR),len(pitch))
p0=cj['p'][:6]+[cj['p'][6]*4/3,800,533]
for drop in [None]+order:
    Hd={k:v for k,v in HEAD.items() if k!=drop};Sd={k:v for k,v in SHAFT.items() if k!=drop}
    with contextlib.redirect_stdout(io.StringIO()) as o:p=fit(Hd,Sd,1600,1067,p0,GR)
    print('drop',drop,o.getvalue().replace('\n',' | ')[:220],'f',round(p[6]))
