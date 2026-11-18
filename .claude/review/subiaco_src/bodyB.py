# ================= 1997 (version B) parts, all from layoutB.json (measured on refs/c/17.jpg through camB.json)
JB=json.load(open(SP+'/layoutB.json'))
def fD(S,ref):return fn(S,1,ref)
def fZ(S,ref):return fn(S,2,ref)
def tube(b,h,r0,r1,m='steel',n=10):
    for j in range(n):
        t0=2*math.pi*j/n;t1=2*math.pi*(j+1)/n;c0=Vector((math.cos(t0),math.sin(t0),0));c1=Vector((math.cos(t1),math.sin(t1),0))
        face([b+c0*r0,b+c1*r0,b+c1*r1+Vector((0,0,h)),b+c0*r1+Vector((0,0,h))],m)
# ---- near bowl (south and near side, under one long roof): front rows from the fence, roof measured on both edges
SF=[[a,max(d,0.5),z] for a,d,z in JB['SF']];SB=JB['SB']
sfd,sfz,sbd,sbz=fD(SF,-70),fZ(SF,-70),fD(SB,-70),fZ(SB,-70)
def nb_prof(a):
    dF,zF,dB,zB=sfd(a),sfz(a),sbd(a),sbz(a)
    return [(0,0),(0,1.2),(0.8,1.2),(dB-1.0,zB-4.0),(dB,zB),(dF,zF),(dF,zF-1.0)]
NBM=['wall','fascia','seatsb','wall',None,'fascia']
sweep(-141.4,-4.3,nb_prof,NBM,tile=4)
sweep(-141.4,-95,lambda a:nb_prof(a)[4:6],['roof'],tile=4);sweep(-95,-4.3,lambda a:nb_prof(a)[4:6],['roofd'],tile=4)
sweep(-141.4,-4.3,lambda a:[(sbd(a),0),(sbd(a),sbz(a))],['facade'],tile=16)
endcap(-141.4,lambda a:[(0,0),(sbd(a),0),(sbd(a),sbz(a)),(sfd(a),sfz(a)),(0,1.2)],'wall')
# ---- near-right stand: concrete multi-storey block with a dark flat roof
NRF,NRB=JB['NRF'],JB['NRB'];nfd,nfz,nbd=fD(NRF,10),fZ(NRF,10),fD(NRB,10)
def nr_prof(a):dF,z=nfd(a),nfz(a);dB=max(nbd(a),dF+8);return [(0,0),(0,1.2),(0.8,1.2),(dB-1,z-4),(dB,z),(dF,z),(dF,z-1.0)]
sweep(-4.3,33.2,nr_prof,['wall','fascia','seatsb','wall','roofd','fascia'],tile=4)
sweep(-4.3,33.2,lambda a:[(nr_prof(a)[4][0],0),nr_prof(a)[4]],['facade'],tile=16)
endcap(33.2,lambda a:[(0,0),(nr_prof(a)[4][0],0),nr_prof(a)[4],nr_prof(a)[5],(0,1.2)],'wall')
# ---- north stand: blue seats raked from the fence up under a white roof (east end under the grey corner roof)
BF=JB['BF'];BB=JB['BB'];bfd,bfz,bbd,bbz=fD(BF,100),fZ(BF,100),fD(BB,100),fZ(BB,100)
def bs_prof(a):dF,zF,dB,zB=bfd(a),bfz(a),bbd(a),bbz(a);return [(0,0),(0,1.2),(0.8,1.2),(dF,zF-1.2),(dB-0.5,zF-1.2),(dB,zB),(dF,zF),(dF,zF-1.0)]
sweep(33.2,136.0,bs_prof,['wall','fascia','seatsb','under','wall',None,'fascia'],tile=4)
sweep(62.3,136.0,lambda a:bs_prof(a)[5:7],['roof'],tile=4)
sweep(33.2,136.0,lambda a:[(bbd(a),0),(bbd(a),bbz(a))],['wall'],tile=4)
endcap(136.0,lambda a:[(0,0),(bbd(a),0),(bbd(a),bbz(a)),(bfd(a),bfz(a)),(0,1.2)],'wall')
block([p for p in JB['CR']],18.0,'wall','steel')                                              # grey corner roof block
# ---- west end under construction: bare lit pad, grass bank, perimeter boards
W1,W2=JB['W1'],JB['W2'];w1d,w2d=fD(W1,170),fD(W2,170)
sweep(136.0,196.0,lambda a:[(0.1,0.05),(w1d(a),0.3)],['pad'],tile=12)
sweep(136.0,196.0,lambda a:[(w1d(a),0.3),(w2d(a),3.0)],['bank'],tile=8)
sweep(142.0,192.0,lambda a:[(w2d(a),3.0),(w2d(a),5.4)],['ads'],tile=24)
sweep(196.0,218.6,lambda a:[(0.1,0.05),(w1d(a)*0.9,0.3)],['pad'],tile=12)                 # SW corner pad to the near roof
block(JB['LW'],8.0,'wall','roof');block(JB['FL1'],8.0,'brick','roofd');block(JB['FL2'],5.0,'wall','roofd')
block(JB['GB'],10.0,'wall','steel')
# ---- four light towers: tapered (thicker at the base), lamp head facing the centre
for x,y,h in JB['TOW']:
    b=Vector((x,y,0));tube(b,h-3.0,0.9,0.45,'steel',12)
    c=Vector((x,y,h-3.0));t=(Cc-c);t.z=0;t.normalize();s=Vector((-t.y,t.x,0))*3.2;up=Vector((0,0,3.0))+t*0.6
    face([c-s,c+s,c+s+up*2,c-s+up*2],'lamps',[(0,0),(1,0),(1,1),(0,1)]);face([c-s-t*0.4,c-s-t*0.4+up*2,c+s-t*0.4+up*2,c+s-t*0.4],'steel')
