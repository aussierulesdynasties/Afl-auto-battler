# Writes views_tex.json for views.py: a game-distance view (gc_) and a close view (cl_) of every repainted surface.
# Points come from geom.json (drum, podium, roof rings, fence oval, stair corners); eyes sit outside along the bowl normal.
import json,math,os
import numpy as np
H=os.path.dirname(os.path.abspath(__file__));J=json.load(open(os.path.join(H,'geom.json')))
D=np.array(J['drum']);RF=np.array(J['roof']);IN=np.array(J['inner']);PD=np.array(J['pod']);OC=np.array(J['oc']);FE=J['fence']
def u(i):d=D[i]-OC;return d/np.linalg.norm(d)
def ell(i):
    c=np.array(FE['c']);a=FE['ang'];U=np.array((math.cos(a),math.sin(a)));Vv=np.array((-math.sin(a),math.cos(a)));d=(RF[i]-c)/np.linalg.norm(RF[i]-c)
    k=1/math.sqrt((d@U/FE['a'])**2+(d@Vv/FE['b'])**2);return c+d*k
P=lambda xy,z:[float(xy[0]),float(xy[1]),float(z)]
def out(tgt,i,d,h):return P(np.array(tgt[:2])+u(i)*d,tgt[2]+h)
V={}
def add(n,tgt,gce,cle,lc=35,lg=35):V['gc_'+n]={'eye':gce,'tgt':tgt,'lens':lg};V['cl_'+n]={'eye':cle,'tgt':tgt,'lens':lc}
i=330;t=P(RF[i]+(IN[i]-RF[i])*0.4,45.6);add('roof',t,out(t,i,160,90),out(t,i,14,16))
t=P(RF[i]+(IN[i]-RF[i])*0.5,43.0);fc=P(OC,25);add('under',t,fc,out(t,i,-16,-9))
s=ell(i)+(RF[i]-ell(i))*0.3;t=P(s,13);add('seats',t,fc,out(t,i,-13,3))
i=300;t=P(D[i],26);add('bronze',t,out(t,i,200,60),out(t,i,22,1))
i=150;t=P(D[i]+u(i)*-3,30);add('glass',t,out(t,i,200,60),out(t,i,26,2))
i=20;t=P(PD[i],3);add('podwall',t,out(t,i,200,60),out(t,i,12,1.5))
t=P((PD[i]+D[i])/2,6.4);add('terrace',t,out(t,i,200,60),out(t,i,8,9))
i=250;t=P(PD[i]+(D[i]-PD[i])*0.5,0);add('plaza',t,out(t,i,200,60),out(P(PD[i],0),i,3,4.5))   # plaza lies inside the podium line, under the bronze
S=J['stair'];c=np.mean([S[k] for k in S],0);dv=np.mean([S['B1'],S['B2']],0)-np.mean([S['T1'],S['T2']],0);dv/=np.linalg.norm(dv)
t=P(c,3.2);add('stair',t,P(c+dv*200,60),P(c+dv*16,10))
i=277;t=P(D[i],28);add('sign_a',t,out(t,i,250,60),out(t,i,55,3))
i=17;t=P(D[i],26);add('sign_b',t,out(t,i,250,60),out(t,i,45,3))
json.dump(V,open(os.path.join(H,'views_tex.json'),'w'),indent=0);print(len(V))
