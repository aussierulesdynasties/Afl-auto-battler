s = open('scene.py', newline='').read()
R = [("_ribbon(Q[r], 0, w, 0.08, RV, RF_)", "_ribbon(Q[r], 0, w, 0.04, RV, RF_)"),
     ("0.10, 0.10, LV, LF)", "0.10, 0.06, LV, LF)"),
     ("Z = height(GX, GY) + 0.05", "Z = height(GX, GY) + 0.03"),
     ("ob = mk_obj('bg_roads', RV, RF_, m_road); co = np.array(RV)", "ob = mk_obj('bg_roads', RV, RF_, m_road); co = np.array(RV); ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))"),
     ("m_park); co = np.array(PV, float)", "m_park); co = np.array(PV, float); ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))")]
for a, b in R:
    n = s.count(a); assert n >= 1, a; s = s.replace(a, b)
open('scene.py', 'w', newline='').write(s); print('ok')
