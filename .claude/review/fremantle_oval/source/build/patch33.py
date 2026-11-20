import shutil
p = 'build/build.py'
shutil.copy(p, 'build/build_v12pre33.py')
s = open(p, encoding='utf-8', newline='').read()
def rep(a, b):
    global s
    assert a in s, a[:80]; s = s.replace(a, b, 1)

# heights and widths from the camera fits (g18 eye height known; g34 rms 3.0 px, a02 rms 10.5 px with the HQ fixed):
# nine sawtooth gables (four tall, not three, after the 8.1 m one), then a 7 m section whose ridge runs along the
# front with its gable end facing west (g34: apex 1058, eaves 1030 / 1092; a02: the ridge behind the last apex)
rep("HQ_ZE = HQ_ZB + 7.1    # two-storey eaves (g18 fit: 7.2-7.5 m above the column bases)",
    "HQ_ZE = HQ_ZB + 7.24   # two-storey eaves (g18 fit)")
rep("HQ_RISE = 2.15         # gable rise above the eaves (g18 fit 2.1-2.2)",
    "HQ_RISE = 2.35         # gable rise above the eaves (g34 and a02 fits: apex picks sit on the outer barge edge)")
rep("HQ_ZE_LOW = HQ_ZB + 5.3   # glass-hall gables 1-4: eaves (g18 fit 5.4-5.8 m above the column bases)",
    "HQ_ZE_LOW = HQ_ZB + 5.38  # glass-hall gables 1-4: eaves (g18 fit)")
rep("HQ_RISE_LOW = 2.0", "HQ_RISE_LOW = 1.96")
rep("HQ_WIDTHS = [5.8] * 4 + [8.1] + [5.75] * 3   # g18 fit: hall 5.8, first two-storey 8.1, others 5.75",
    "HQ_WIDTHS = [5.79] * 4 + [8.09] + [5.73] * 4   # g18/g34 fit: hall 5.79, first two-storey 8.09, four more at 5.73")
rep("HQ_WBIG = 12.5   # wide gable: from the end of gable 8 to the porch notch of the OSM outline",
    "HQ_WBIG = 7.0    # entrance section past gable 9: ridge along the front, west-facing gable end (g34 pW fit)\n"
    "HQ_DBIG = 10.0   # its depth front to back (ridge at half depth)")
rep("    spans = [(acc_[k], acc_[k + 1]) for k in range(8)] + [(acc_[8], acc_[8] + HQ_WBIG)]",
    "    spans = [(acc_[k], acc_[k + 1]) for k in range(9)] + [(acc_[9], acc_[9] + HQ_WBIG)]")
rep("""        if k == 8:   # past the OSM front's end: carry on along the last chord
            a_, b_ = Vector(HQ_FRONT[-2]), Vector(HQ_FRONT[-1]); t_ = (b_ - a_).normalized()
            B = A + t_ * HQ_WBIG
""", "")
rep("        big = k == 8\n", "        big = k == 9\n")
rep("        depth = 10.0 if big else (13.0 if low else 8.0)", "        depth = HQ_DBIG if big else (13.0 if low else 8.0)")
# the entrance section's roof: two slopes falling to the front and back eaves, gable end on the west
rep("""        # roof slopes (white corrugated) and white soffit just under them
        roof += [""", """        if big:
            zr_ = ze + rise; dm = depth / 2
            roof += [[P(0, -oh, ze), P(w + oh * 0.6, -oh, ze), P(w + oh * 0.6, dm, zr_), P(0, dm, zr_)],
                     [P(0, dm, zr_), P(w + oh * 0.6, dm, zr_), P(w + oh * 0.6, depth, ze), P(0, depth, ze)]]
            sof += [[P(0, -oh, ze - 0.12), P(0, dm, zr_ - 0.12), P(w + oh * 0.6, dm, zr_ - 0.12), P(w + oh * 0.6, -oh, ze - 0.12)],
                    [P(0, dm, zr_ - 0.12), P(0, depth, ze - 0.12), P(w + oh * 0.6, depth, ze - 0.12), P(w + oh * 0.6, dm, zr_ - 0.12)],
                    [P(w, -oh, ze - 0.12), P(w, depth, ze - 0.12), P(w, dm, zr_ - 0.2)],      # white gable infill, west end
                    [P(0, -oh, ze - 0.12), P(0, dm, zr_ - 0.2), P(0, depth, ze - 0.12)]]      # east end, above gable 9's slope
            wb = w + oh * 0.6
            barge += [[P(wb, -oh, ze - 0.3), P(wb, dm, zr_ - 0.3), P(wb, dm, zr_ + 0.02), P(wb, -oh, ze + 0.02)],
                      [P(wb, dm, zr_ - 0.3), P(wb, depth, ze - 0.3), P(wb, depth, ze + 0.02), P(wb, dm, zr_ + 0.02)],
                      [P(0, -oh - 0.02, ze - 0.3), P(wb, -oh - 0.02, ze - 0.3), P(wb, -oh - 0.02, ze + 0.02), P(0, -oh - 0.02, ze + 0.02)]]
        else:
          # roof slopes (white corrugated) and white soffit just under them
          roof += [""")
s = s.replace("""                 [P(h, -oh, zr_), P(w, -oh, ze), P(w, depth, ze), P(h, depth, zr_)]]
        sof += [[P(0, -oh, zl - 0.12)""", """                 [P(h, -oh, zr_), P(w, -oh, ze), P(w, depth, ze), P(h, depth, zr_)]]
          sof += [[P(0, -oh, zl - 0.12)""", 1)
rep("""        # white gable infill set back under the open front rake (g18, g34: white triangles, not glass)
        dvi = 0.6 if not big else 1.0
        sof.append(""", """          # white gable infill set back under the open front rake (g18, g34: white triangles, not glass)
          dvi = 0.6
          sof.append(""")
rep("""        if low: sof.append([P(0, depth - 0.05, zl - 0.12), P(h, depth - 0.05, zr_ - 0.2), P(w, depth - 0.05, ze - 0.12)])
        # green bargeboards on the front rake and the back rake
        for dd in (-oh, depth):
            barge += [""", """          if low: sof.append([P(0, depth - 0.05, zl - 0.12), P(h, depth - 0.05, zr_ - 0.2), P(w, depth - 0.05, ze - 0.12)])
          # green bargeboards on the front rake and the back rake
          for dd in (-oh, depth):
            barge += [""")
rep("        for a in ((0.0, w) if k in (0, 8) else (0.0,)):", "        for a in ((0.0, w) if k in (0, 9) else (0.0,)):")
# the entrance hall: glass on the west face too, between the front and the back wall
rep("""            plinth.append([P(0, -0.3, zb), P(w, -0.3, zb), P(w, dv, zb), P(0, dv, zb)])
        else:""", """            plinth.append([P(0, -0.3, zb), P(w, -0.3, zb), P(w, dv, zb), P(0, dv, zb)])
            if big:
                glassq.append([P(w, dv, zb), P(w, depth, zb), P(w, depth, ze - 0.12), P(w, dv, ze - 0.12)])
        else:""")
rep("        rise = HQ_RISE_LOW if low else (3.3 if big else HQ_RISE)", "        rise = HQ_RISE_LOW if low else HQ_RISE")
open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
