s=open('clsfy.py',encoding='utf-8').read()
a=s.index('        # forecourt (aerial):'); b=s.index('        _col = np.where(_pv[..., None], _fc, _col)')+len('        _col = np.where(_pv[..., None], _fc, _col)')
new='''        # forecourt (aerial): broad flowing bands of salmon, cream and taupe paving. Each pixel of the unblurred aerial
        # votes for its nearest tone (trees and shadows, L < 0.32, don't vote); each tone's votes are Gaussian-smoothed
        # (sigma 3 px = 4.5 m) and the strongest wins: smooth band outlines instead of majority-filter blotches.
        _raw = np.asarray(Image.open(_sp).convert('RGB').resize((N, N), Image.LANCZOS)).astype(np.float32) / 255
        _ref = np.array([[0.70, 0.50, 0.46], [0.80, 0.73, 0.64], [0.58, 0.55, 0.53]], np.float32)
        _t = ((_raw[..., None, :] - _ref[None, None]) ** 2).sum(-1).argmin(-1); _ok = _raw.mean(2) >= 0.32
        _vs = np.stack([_ndi.gaussian_filter(((_t == k) & _ok).astype(np.float32), 3.0) for k in range(3)], -1)
        _tb = _vs.argmax(-1)
        _pal = np.array(spec['forecourt_tones'], np.float32)
        _col = np.where(_pv[..., None], _pal[_tb], _col)'''
open('clsfy.py','w',encoding='utf-8',newline='').write(s[:a]+new+s[b:])
import json;p='spec/optus.json';j=json.load(open(p));j['forecourt_tones']=[[184,122,104],[212,192,166],[164,152,140]];json.dump(j,open(p,'w'),indent=1)
