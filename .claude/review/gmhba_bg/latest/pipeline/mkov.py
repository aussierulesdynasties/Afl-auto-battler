import json,sys
sun={"az":60,"el":25,"power":4.5}; sky=[[0.0,[0.77,0.84,0.89]],[0.45,[0.25,0.49,0.77]]]
# name: cam xy, look xyz(rel ground), fov_h, res
V=[("p_se",[43.9,-181.9],[-20,40,15],38,[640,908]),
   ("p_moorabool",[8.4,-279.1],[46,40,20],32,[640,855]),
   ("p_yarra",[261.0,-239.8],[262,600,1],62,[960,640]),
   ("p_fyans",[-29.8,-398.3],[-600,-330,1],62,[960,734])]
for n,c,l,f,r in V:
    json.dump({"out":"ov","res":r,"samples":16,"sun":sun,"sky":sky,"views":[{"name":n,"cam":c+[1.6],"look":l,"fov_h":f}]},open('out/gmhba/ov0_%s.json'%n,'w'))
