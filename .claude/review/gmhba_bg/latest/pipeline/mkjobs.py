import json, math
C=math.cos(math.radians(38.158219))
def xy(lat,lon): return [round((lon-144.354577)*111320*C,1), round((lat+38.158219)*110540,1)]
sun={"az":110,"el":55,"power":4.5}; sky=[[0.0,[0.77,0.84,0.89]],[0.45,[0.25,0.49,0.77]]]
json.dump({"out":"map","res":[2000,2000],"samples":16,"sun":sun,"views":[{"name":"whole_3km","ortho":3000,"centre":[0,0]},{"name":"ortho_1400","ortho":1400,"centre":[0,0]}]},open('out/gmhba/job_map.json','w'))
V=[]
for b in range(0,360,45):
    a=math.radians(b); V.append({"name":"fence_%03d"%b,"cam":[round(175*math.cos(a),1),round(175*math.sin(a),1),25],"look":[round(260*math.cos(a+0.6),1),round(260*math.sin(a+0.6),1),0],"fov_h":60})
json.dump({"out":"fence","res":[960,540],"samples":16,"sun":sun,"sky":sky,"views":V},open('out/gmhba/job_fence0.json','w'))
P={"p_se":(-38.159865,144.355078,[0,0],1280/1816),"p_moorabool":(-38.160744,144.354673,None,1280/1710),"p_fyans":(-38.161822,144.354236,None,1280/979),"p_yarra":(-38.160388,144.357559,None,1280/853),"p_aco2":(-38.156750,144.352433,[-226,124],1280/960)}
print({k:xy(v[0],v[1]) for k,v in P.items()})
