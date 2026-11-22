c = open('clsfy.py', encoding='utf-8').read()
old = "    # clean speckle"
assert c.count(old) == 1
c = c.replace(old, """    # the stadium roof (white in the aerial) hides the concourse under it: paint that as the forecourt paving
    _yy, _xx = np.mgrid[0:N, 0:N]; _rr = np.hypot((_xx + 0.5) * PX - NEAR, NEAR - (_yy + 0.5) * PX)
    _roof = (_rr < R0 + 40) & (V_ > 0.72) & (S_ < 0.14)
    _roof = _ndi.binary_dilation(_roof, iterations=4) & (_rr < R0 + 45)
    cls[_roof] = names.index('brick_dark')
    # clean speckle""")
c = c.replace("uniform_filter((cls == k).astype(np.float32), 9)", "uniform_filter((cls == k).astype(np.float32), 15)")
c = c.replace("    img = Image.fromarray(_o.astype(np.uint8))", "    img = Image.fromarray(_o.astype(np.uint8))   # (hard class edges kept: the mask below matches palette colours exactly)")
open('clsfy.py', 'w', encoding='utf-8', newline='').write(c); print('ok')
