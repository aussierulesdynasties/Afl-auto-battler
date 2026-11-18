p='build5.py';s=open(p,encoding='utf-8',newline='').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a[:60];s=s.replace(a,b)
# --- roof: navy strip 5.25 m inside the old inner edge (measured), flatter membrane
rep("SR=[0,0.04,0.08,0.13,0.18,0.24,0.32,0.45,0.6,0.72,0.82,0.88,0.92,0.95,0.975,0.99,1.0]",
    "SR=[0,0.03,0.06,0.09,0.12,0.15,0.18,0.21,0.24,0.28,0.34,0.45,0.6,0.72,0.82,0.88,0.92,0.95,0.975,0.99,1.0]\nNAVYW=5.25  # navy glazed strip inside the white membrane, measured on the photo (near side 5.75, far side 4.5 m)")
rep("LOBE_IN=float(os.environ.get('LOBE_IN',1.2));LOBE_OUT=float(os.environ.get('LOBE_OUT',3.5));CAP0=float(os.environ.get('CAP0',0.86))",
    "LOBE_IN=float(os.environ.get('LOBE_IN',0.35));LOBE_OUT=float(os.environ.get('LOBE_OUT',1.1));CAP0=float(os.environ.get('CAP0',0.94))")
rep("ph=phase(a);ri=rin(a)+0.8-1.6*math.sin(math.pi*ph);ro=rout(a)",
    "ph=phase(a);ri=rin(a)-NAVYW+0.8-1.6*math.sin(math.pi*ph);ro=rout(a)")
rep("face([top[a][b] for a,b in q],NAVY if sc<0.13 else ROOF,",
    "am=(ra[i]+ra[i+1])/2;nf=NAVYW/max(1.0,rout(am)-rin(am)+NAVYW)\n        face([top[a][b] for a,b in q],NAVY if sc<nf else ROOF,")
open(p,'w',encoding='utf-8',newline='').write(s)
