s=open('clsfy.py',encoding='utf-8').read()
a=s.index('        # forecourt bands:'); b=s.index('        _col = np.where(_pv[..., None], _pal[_tb], _col)')
b=b+len('        _col = np.where(_pv[..., None], _pal[_tb], _col)')
new='''        # forecourt (aerial): a terracotta field crossed by thin winding cream lines. Lines = white top-hat of the
        # unblurred aerial luminance (bright ridges narrower than ~6 m); field = flat hand-picked terracotta.
        _raw = np.asarray(Image.open(_sp).convert('RGB').resize((N, N), Image.LANCZOS)).astype(np.float32) / 255
        _L = _raw.mean(2); _th = _L - _ndi.grey_opening(_L, size=(5, 5))
        _ln = _ndi.gaussian_filter((_th > 0.07).astype(np.float32), 0.6) > 0.45
        _pal = np.array(spec['forecourt_tones'], np.float32)
        _fc = np.where(_ln[..., None], _pal[1], _pal[0])
        _col = np.where(_pv[..., None], _fc, _col)'''
open('clsfy.py','w',encoding='utf-8',newline='').write(s[:a]+new+s[b:])
import json;p='spec/optus.json';j=json.load(open(p));j['forecourt_tones']=[[178,112,94],[214,196,170],[160,150,140]];json.dump(j,open(p,'w'),indent=1)
