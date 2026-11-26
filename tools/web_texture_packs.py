#!/usr/bin/env python3
"""Export the Web build with its textures in one pack per graphics family (bug bash M-12).

A browser draws compressed textures in one family only: PC graphics (S3TC and BPTC) or
phones (ETC2 and ASTC). The Web preset imports both, so a single index.pck carried every
3D and figure texture twice: 522 MB on 2026-11-26, past itch's 200 MB a file. This export
keeps the game in index.pck without those textures, puts them in index.textures_pc.pck
and index.textures_phone.pck, and patches index.html so the page fetches only the pack
its browser draws with, alongside index.pck. scripts/core/WebPacks.gd, the first autoload,
mounts it before anything else loads, so every texture loads exactly as before.

  python3 tools/web_texture_packs.py <godot> <out dir>     # e.g. build/web

Run it after `godot --import`: the Epic textures' .import files exist only then. It
rewrites export_presets.cfg for the three exports and always puts the file back. It checks
that each pack holds only its own family, then prints every file's size against itch's
HTML5 limits (itch.io/docs/creators/html5); --summary FILE appends that table there too.
"""
import fnmatch
import json
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRESETS = os.path.join(ROOT, "export_presets.cfg")
WEB = "Web"
# (preset, pack file, desktop formats, phone formats): a family preset exports only its own files.
PACKS = (
    ("Web textures PC", "index.textures_pc.pck", True, False),
    ("Web textures phone", "index.textures_phone.pck", False, True),
)
FAMILY = {"s3tc": 0, "bptc": 0, "etc2": 1, "astc": 1}  # format -> index in PACKS
MOUNT_AS = "textures.pck"  # scripts/core/WebPacks.gd PACK
ENGINE_LINE = "const engine = new Engine(GODOT_CONFIG);"
ITCH_FILE_MB, ITCH_TOTAL_MB, ITCH_FILES = 200, 500, 1000


def fail(msg):
    sys.exit("FAIL: " + msg)


# --- export_presets.cfg ---------------------------------------------------------------

def sections(lines):
    """[(header line index, end index)] for each [section]."""
    heads = [i for i, l in enumerate(lines) if l.startswith("[")]
    return [(h, heads[k + 1] if k + 1 < len(heads) else len(lines)) for k, h in enumerate(heads)]


def set_key(block, key, value):
    hits = [i for i, l in enumerate(block) if l.startswith(key + "=")]
    if len(hits) != 1:
        fail(f"export_presets.cfg: expected one {key}= line, found {len(hits)}")
    block[hits[0]] = f"{key}={value}"


def get_key(block, key):
    for l in block:
        if l.startswith(key + "="):
            return l[len(key) + 1:]
    fail(f"export_presets.cfg: no {key}= line")


def split_presets(text, textures):
    """The Web preset without the textures, plus one pack preset per family."""
    lines = text.split("\n")
    secs = sections(lines)
    web = [(h, e) for h, e in secs if f'name="{WEB}"' in lines[h:e]]
    if len(web) != 1:
        fail(f'export_presets.cfg: expected one preset named "{WEB}", found {len(web)}')
    h, e = web[0]
    head = lines[h]  # [preset.N]
    opt_head = head[:-1] + ".options]"
    opts = [(oh, oe) for oh, oe in secs if lines[oh] == opt_head]
    if len(opts) != 1:
        fail(f"export_presets.cfg: no {opt_head} section")
    oh, oe = opts[0]
    numbers = [int(m.group(1)) for l in lines for m in [re.match(r"^\[preset\.(\d+)\]$", l)] if m]
    nxt = max(numbers) + 1

    block = lines[h:e]
    excl = get_key(block, "exclude_filter")
    if not (excl.startswith('"') and excl.endswith('"')):
        fail("export_presets.cfg: Web exclude_filter is not one quoted line")
    joined = ", ".join([excl[1:-1]] + textures) if excl[1:-1] else ", ".join(textures)
    set_key(block, "exclude_filter", '"' + joined + '"')

    files = "PackedStringArray(" + ", ".join(json.dumps("res://" + t) for t in textures) + ")"
    extra = []
    for k, (name, _pack, desktop, mobile) in enumerate(PACKS):
        p = lines[h:e]
        p[0] = f"[preset.{nxt + k}]"
        set_key(p, "name", json.dumps(name))
        set_key(p, "runnable", "false")
        set_key(p, "export_filter", '"resources"')
        set_key(p, "include_filter", '""')
        set_key(p, "exclude_filter", '""')
        set_key(p, "export_path", '""')
        i = next(i for i, l in enumerate(p) if l.startswith("export_filter="))
        p.insert(i + 1, "export_files=" + files)
        o = lines[oh:oe]
        o[0] = f"[preset.{nxt + k}.options]"
        set_key(o, "vram_texture_compression/for_desktop", "true" if desktop else "false")
        set_key(o, "vram_texture_compression/for_mobile", "true" if mobile else "false")
        while p and p[-1] == "":
            p.pop()
        while o and o[-1] == "":
            o.pop()
        extra += p + [""] + o + [""]
    out = lines[:h] + block + lines[e:]
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out + [""] + extra)


def web_excludes(text):
    lines = text.split("\n")
    for h, e in sections(lines):
        if f'name="{WEB}"' in lines[h:e]:
            return [g.strip() for g in get_key(lines[h:e], "exclude_filter").strip('"').split(",") if g.strip()]
    fail(f'export_presets.cfg: no preset named "{WEB}"')


def vram_textures(excludes):
    """Source paths of every VRAM-compressed texture the Web preset exports."""
    found = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT).replace(os.sep, "/")
        rel = "" if rel == "." else rel + "/"
        # Godot's file system skips hidden folders and folders with a .gdignore.
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".")
                             and not os.path.exists(os.path.join(dirpath, d, ".gdignore")))
        for f in sorted(filenames):
            if not f.endswith(".import"):
                continue
            src = rel + f[:-len(".import")]
            if any(fnmatch.fnmatchcase(src.lower(), g.lower()) for g in excludes):
                continue
            with open(os.path.join(dirpath, f), encoding="utf-8", errors="replace") as fh:
                imp = fh.read()
            if '"vram_texture": true' not in imp:
                continue
            fams = {FAMILY[m] for m in re.findall(r"^path\.(\w+)=", imp, re.M) if m in FAMILY}
            if fams != {0, 1}:
                fail(f"{src}.import is VRAM-compressed but lacks a PC or a phone format")
            if "," in src or "*" in src or "?" in src:
                fail(f"{src}: a comma or wildcard in the name breaks Godot's export filter")
            found.append(src)
    return found


# --- packs ------------------------------------------------------------------------------

def pck_files(path):
    """[(name, size)] in a Godot 4 .pck."""
    with open(path, "rb") as f:
        if f.read(4) != b"GDPC":
            fail(f"{path} is not a Godot pack")
        ver = struct.unpack("<IIII", f.read(16))[0]
        dir_offset = 0
        if ver >= 2:
            f.read(12)  # flags, file base
        if ver >= 3:
            dir_offset = struct.unpack("<Q", f.read(8))[0]
        f.read(64)
        if dir_offset:
            f.seek(dir_offset)
        rows = []
        for _ in range(struct.unpack("<I", f.read(4))[0]):
            n = struct.unpack("<I", f.read(4))[0]
            name = f.read(n).rstrip(b"\0").decode("utf-8", "replace")
            _off, size = struct.unpack("<QQ", f.read(16))
            f.read(20 if ver >= 2 else 16)  # md5 (+ flags)
            rows.append((name, size))
    return rows


def formats_in(path):
    seen = {}
    for name, size in pck_files(path):
        m = re.search(r"\.(s3tc|bptc|etc2|astc)\.ctex$", name)
        if m:
            seen[m.group(1)] = seen.get(m.group(1), 0) + 1
    return seen


def check_packs(out_dir, n_textures):
    main = formats_in(os.path.join(out_dir, "index.pck"))
    if main:
        fail(f"index.pck still holds textures in {sorted(main)}")
    for k, (_name, pack, _d, _m) in enumerate(PACKS):
        seen = formats_in(os.path.join(out_dir, pack))
        wrong = sorted(f for f in seen if FAMILY[f] != k)
        if wrong or sum(seen.values()) != n_textures:
            fail(f"{pack}: {sum(seen.values())} textures of {n_textures}, wrong family {wrong}")
        print(f"{pack}: {sum(seen.values())} textures ({', '.join(f'{v} {f}' for f, v in sorted(seen.items()))})")


# --- index.html -------------------------------------------------------------------------

PAGE_JS = """
// The textures come in two packs, one per graphics family (tools/web_texture_packs.py):
// this browser fetches only the one it draws with, alongside the main pack, and
// scripts/core/WebPacks.gd mounts it. The test is the engine's own: PC graphics if
// WebGL 2 offers both S3TC and BPTC, otherwise the phone formats (ETC2 and ASTC).
const GODOT_TEXTURE_PACK = (function () {
	let exts = [];
	try {
		const gl = document.createElement('canvas').getContext('webgl2');
		exts = (gl && gl.getSupportedExtensions()) || [];
		const lose = gl && gl.getExtension('WEBGL_lose_context');
		if (lose) {
			lose.loseContext();
		}
	} catch (e) {
		exts = [];
	}
	const pc = exts.includes('WEBGL_compressed_texture_s3tc') && exts.includes('EXT_texture_compression_bptc');
	return pc ? '%PC%' : '%PHONE%';
}());
(function () {
	let texturePack = Promise.resolve();
	const startGame = engine.startGame;
	const start = engine.start;
	engine.startGame = function (override) {
		texturePack = this.preloadFile(GODOT_TEXTURE_PACK, '%MOUNT%');
		return startGame.call(this, override);
	};
	engine.start = function (override) {
		const me = this;
		return texturePack.then(function () {
			return start.call(me, override);
		});
	};
}());
"""


def patch_html(out_dir):
    path = os.path.join(out_dir, "index.html")
    with open(path, encoding="utf-8", newline="") as f:
        html = f.read()
    if html.count(ENGINE_LINE) != 1:
        fail(f"index.html: expected one '{ENGINE_LINE}'")
    m = re.search(r"^const GODOT_CONFIG = (\{.*\});$", html, re.M)
    if not m:
        fail("index.html: no one-line GODOT_CONFIG")
    config = json.loads(m.group(1))
    for _name, pack, _d, _m in PACKS:
        config["fileSizes"][pack] = os.path.getsize(os.path.join(out_dir, pack))
    html = html[:m.start(1)] + json.dumps(config, separators=(",", ":")) + html[m.end(1):]
    js = PAGE_JS.replace("%PC%", PACKS[0][1]).replace("%PHONE%", PACKS[1][1]).replace("%MOUNT%", MOUNT_AS)
    html = html.replace(ENGINE_LINE, ENGINE_LINE + "\n" + js.strip("\n"))
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(html)


# --- report -----------------------------------------------------------------------------

def report(out_dir, summary):
    rows = []
    for dirpath, _dirs, files in os.walk(out_dir):
        for f in files:
            p = os.path.join(dirpath, f)
            rows.append((os.path.getsize(p), os.path.relpath(p, out_dir).replace(os.sep, "/")))
    rows.sort(reverse=True)
    total = sum(s for s, _ in rows)
    lines = ["| File | MB | itch limit |", "|---|---|---|"]
    for s, n in rows:
        lines.append(f"| {n} | {s / 1e6:.1f} | {'OVER ' if s > ITCH_FILE_MB * 1e6 else ''}{ITCH_FILE_MB} MB a file |")
    lines.append(f"| all {len(rows)} files | {total / 1e6:.1f} | {'OVER ' if total > ITCH_TOTAL_MB * 1e6 else ''}"
                 f"{ITCH_TOTAL_MB} MB, {ITCH_FILES} files |")
    per = [total - os.path.getsize(os.path.join(out_dir, p)) for _n, p, _d, _m in PACKS]
    lines.append(f"\nOne player downloads {per[1] / 1e6:.1f} MB on a PC, {per[0] / 1e6:.1f} MB on a phone.")
    text = "\n".join(lines)
    print(text)
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("### Web build against itch's limits\n\n" + text + "\n\n")
    over = [n for s, n in rows if s > ITCH_FILE_MB * 1e6]
    if over or total > ITCH_TOTAL_MB * 1e6 or len(rows) > ITCH_FILES:
        print(f"WARNING: over itch's HTML5 limits ({', '.join(over) or 'total'}); itch can raise them on request.")


def main():
    args = sys.argv[1:]
    summary = None
    if "--summary" in args:
        i = args.index("--summary")
        summary = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        sys.exit(__doc__)
    godot, out_dir = args[0], os.path.abspath(args[1])
    os.makedirs(out_dir, exist_ok=True)

    with open(PRESETS, "rb") as f:
        original = f.read()
    text = original.decode("utf-8")
    crlf = "\r\n" in text
    text = text.replace("\r\n", "\n")
    textures = vram_textures(web_excludes(text))
    if not textures:
        fail("no VRAM-compressed textures found: run godot --import first")
    print(f"{len(textures)} VRAM-compressed textures move to the family packs")
    split = split_presets(text, textures)
    try:
        with open(PRESETS, "wb") as f:
            f.write((split.replace("\n", "\r\n") if crlf else split).encode("utf-8"))
        runs = [("--export-release", WEB, "index.html")] + [("--export-pack", n, p) for n, p, _d, _m in PACKS]
        for flag, preset, name in runs:
            target = os.path.join(out_dir, name)
            if os.path.exists(target):
                os.remove(target)
            print(f"== {flag} {preset} -> {target}", flush=True)
            code = subprocess.run([godot, "--headless", "--path", ROOT, flag, preset, target]).returncode
            if code != 0 or not os.path.isfile(target) or os.path.getsize(target) == 0:
                fail(f"{flag} {preset} did not write {target} (exit {code})")
    finally:
        with open(PRESETS, "wb") as f:
            f.write(original)
    check_packs(out_dir, len(textures))
    patch_html(out_dir)
    report(out_dir, summary)


if __name__ == "__main__":
    main()
