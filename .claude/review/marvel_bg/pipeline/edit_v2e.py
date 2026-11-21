"""v2d crops: station roof = isolated domes (polka dots); glass reflects pale sky (rough 0.13) so towers read grey.
Wave rows instead of domes; glass roughness 0.32."""
def sub(path, pairs):
    s = open(path, newline='').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:60]); s = s.replace(a, b)
    open(path, 'w', newline='').write(s)
sub('facade_mix.py', [
 ("3.5 * (0.5 - 0.5 * np.cos(2 * np.pi * (UU - u0) / HUMP_U)) * (0.5 - 0.5 * np.cos(2 * np.pi * (VV - v0) / HUMP_V))",
  "3.5 * (0.5 - 0.5 * np.cos(2 * np.pi * (UU - u0) / HUMP_U)) * (0.8 + 0.2 * np.cos(2 * np.pi * (VV - v0) / (3 * HUMP_V)))"),
 ("sh = 0.9 + 0.1 * (ZZ[r_, c_] - z0 - 15.0) / 3.5", "sh = 0.97"),
])
sub('scene.py', [("rm.inputs['To Max'].default_value = 0.13", "rm.inputs['To Max'].default_value = 0.32")])
print('ok')
