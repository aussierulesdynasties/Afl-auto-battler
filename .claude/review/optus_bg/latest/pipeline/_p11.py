import json;p='spec/optus.json';j=json.load(open(p));j['forecourt_tones']=[[190,136,118],[206,186,162],[168,154,142]];json.dump(j,open(p,'w'),indent=1)
