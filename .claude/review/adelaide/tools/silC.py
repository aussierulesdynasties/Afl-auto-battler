"""model roof_east silhouette top in photo C vs the traced photo top line"""
import sys; sys.path.insert(0,'tools')
import numpy as np
from projC import proj
from plyread import readply
V,F=readply('model/roof_east.ply',True)
# densify: sample triangle points
T=V[F]; w=np.random.default_rng(0).dirichlet([1,1,1],size=(len(F),12))
P=(w[...,None]*T[:,None]).sum(2).reshape(-1,3); P=np.vstack([P,V])
U=proj(P)
photo={900:757,1000:760,1100:775,1150:780,1250:750,1300:725,1400:700,1500:683,1625:675,1750:685,1850:710,1940:742,2000:725,2100:695,2250:672,2325:670,2450:685,2550:720,2650:770,2700:800,2800:790,2900:785,3000:800,3100:840,3200:895}
for x,yp in photo.items():
    m=np.abs(U[:,0]-x)<8
    print(x, yp, round(U[m,1].min()) if m.any() else None, round(U[m,1].min()-yp) if m.any() else '')
