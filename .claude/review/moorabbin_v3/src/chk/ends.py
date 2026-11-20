import json,math,numpy as np
exec(open('chk/ringover.py').read().split("cam=np.array")[0])
w=lambda a:(a+math.pi)%(2*math.pi)-math.pi
print('lo',round(math.degrees(w(lo)),2),'hi',round(math.degrees(w(hi)),2),'PC',PC.round(2))
print('front ends',np.degrees([w(fa[0]),w(fa[-1])]).round(2),'rear ends',np.degrees([w(ra[0]),w(ra[-1])]).round(2))
for deg in (-117.9,-112,-110,-108,-105):
    a=math.radians(deg);print(deg,in_stand(a),round(d_out(a),1),np.round(pt(a,d_out(a))[:2],1))
