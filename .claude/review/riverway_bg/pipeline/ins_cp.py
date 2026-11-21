# ---- carport / shade-sail canopy: 1 m cells measured from the aerial (carports.py); hand-made panel colours
_cpf = os.path.join(D, 'carports.json')
if os.path.exists(_cpf):
    CP = np.array(json.load(open(_cpf)), float)
    if len(CP):
        _occ = set(zip(np.floor(CP[:, 0]).astype(int), np.floor(CP[:, 1]).astype(int)))
        _uc = np.array([(int(np.floor(x)), int(np.floor(y))) in _occ for x, y in TR[:, :2]])
        TR = TR[~_uc]; print('trees under carports removed', int(_uc.sum()))
        cx, cy, cl = CP[:, 0], CP[:, 1], CP[:, 2]
        cz = height(cx, cy) + cl + 3.5
        o = np.array([[-.5, -.5], [.5, -.5], [.5, .5], [-.5, .5]])
        V = np.zeros((len(CP) * 4, 3)); V[:, 0] = (cx[:, None] + o[:, 0]).ravel(); V[:, 1] = (cy[:, None] + o[:, 1]).ravel()
        V[:, 2] = np.repeat(cz, 4)
        F = np.arange(len(CP) * 4).reshape(-1, 4).tolist()
        ob = mk_obj('bg_carports', V, F, mat_vcol('m_carport', 0.55))
        rng_c = np.random.default_rng(11)
        base = np.array([62, 66, 78]) / 255.0           # hand-made dark blue-grey panel; lighter seam every 2nd metre
        seam = ((np.floor(cx) + np.floor(cy)) % 2 == 0)[:, None] * 0.035
        col = np.clip(base[None, :] + seam + rng_c.normal(0, 0.008, (len(CP), 1)), 0, 1) ** 2.2
        col = np.concatenate([col, np.ones((len(CP), 1))], 1)
        set_corner_col(ob.data, np.repeat(col, 4, 0))
        print('carport canopy cells', len(CP))
