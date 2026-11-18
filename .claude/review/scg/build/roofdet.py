# --- Trumper roof details (reference photo, back-projected onto the roof): a thin grey safety rail ~3.6 m behind the
# front edge along the whole roof, and small white boxes on it every ~3.4 deg (about 6.5 m) from -99 to -69 deg
_rda0,_rda1,_rdf,_rdzf,_rdo,_rdzo=STANDS['trumper']
def _rdz(d,r):lo,hi=_rdf(d),_rdo(d);return _rdzf(d)+(_rdzo(d)-_rdzf(d))*(r-lo)/(hi-lo)
def _rail(d):
    lo,hi=_rdf(d),_rdo(d)
    if np.isnan(lo) or np.isnan(hi) or hi-lo<6:return None
    r=lo+3.6;return [(r-0.15,_rdz(d,r-0.15)+0.12),(r+0.15,_rdz(d,r+0.15)+0.12)]
band(_rail,_rda0+0.5,_rda1-0.5,'rail')
for _d in np.arange(-99.0,-68.0,3.4):
    lo=_rdf(_d);r0,r1=lo+3.2,lo+4.4;h=math.degrees(0.6/lo)
    A0,A1=math.radians(_d-h),math.radians(_d+h);zb_=min(_rdz(_d,r0),_rdz(_d,r1))-0.1
    c=[P(r_,a_,zb_+(0.7 if top else 0)) for top in (0,1) for a_ in (A0,A1) for r_ in (r0,r1)]
    for f in ((0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5),(4,5,7,6)):quad(*[c[i] for i in f],'slab')
