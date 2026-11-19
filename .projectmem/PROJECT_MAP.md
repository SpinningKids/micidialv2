# Project Map - micidial_v2

Status: real content, refined by AI session.

## Project purpose
Build "micidial v2": a scene compiler that compresses the single-file WebGL
intro `original/uncompressed.html` (5.36 MB) below 64 KiB while remaining a
self-contained HTML that renders identically in a standard browser.

## Structure
- `original/` — reference artifacts (uncompressed input is NOT committed; regenerate via `tools/decompress_any.py` + `tools/unwrite_page.js`)
  - `original/PRESSURE_ATBS135_v13.html` — v1 page, baseline input for the v2 pipeline (657,106 B)
  - `original/PRESSURE_ATBS135_v21.html` — v21 variant page (735,341 B); uses `--src=` profile Q11 (`--rdp=1.8`)
- `tools/` — permanent variant tooling (all committed)
  - `tools/decompress.py`, `tools/decompress_any.py` — v1 container → payload decoder (any `PRESSURE_ATBS135_vN.html`)
  - `tools/unwrite_page.js` — `document.write` payload → real uncompressed page (Node)
  - `tools/diff_pages.py` — generic P-key scoping diff between two pages (argv A B)
  - `tools/extract_shipped.py` — decode a shipped micidial_v2 page's embed into its 10 sections
  - `tools/verify_page.js` — Chrome-faithful windows-1252 offline boot check
- `tmp/` — untracked scratch from the v21 variant experiments (`uncompressed_v21.html`, `v21_r*.html` sweep, `v21_sections/`, `shipped/`)
- `v2/` — micidial v2 Scene Compiler + procedural audio engine
  - `v2/compile.py` — stage 1: loads P from uncompressed.html, RDP keyframe
    reduction, track fitting, writes v2/build/{stream.bin,statics.txt,
    pv.json,meta.json,skeleton.json,model32.pkl}
  - `v2/iface.py` — stage 1b: extracts outer engine JS → v2/build/outer.js
  - `v2/audio_extract.py` — stage 2: P.a → v2/build/audio.pkl (worklet src + song)
  - `v2/audio.py` — stage 3: song → v2/build/audio.bin quantized blob
    (layout documented in file header)
  - `v2/synth.js` — procedural atbs-v04 worklet remake (class D synth +
    class Lt processor)
  - `v2/min_synth.js` — stage 4: terser-minifies synth.js → build/synth.min.js
  - `v2/min_boot.js` — stage 4b: terser (compress:false) minifies boot.js → build/boot.min.js (2,948 B, byte-exact reproducer)
  - `v2/boot.js` — runtime decoder/section 0: rebuilds P, writes shell, runs outer
  - `v2/assemble.py` — stage 5 (committed v0.2-layout producer since v0.3): per-section deflate + windows-1252 cp1252 comment embedding + carrier harvested from the shipped page; options `--src/--out/--shell/--carrier`. Baseline output = `micidial_v2.html` (65,288 B on disk; not byte-identical to the shipped file — current zlib compresses better than the old build)
  - `v2/build/shell.html` — hand-written DOM shell input; the ONLY committed build file (others are gitignored regenerables; `boot.min.js`, `engine.js`, `outer.js` were not covered by .gitignore and showed up as untracked in the working tree)
- Root artifacts (tracked): `micidial_v2_v01.html` (67,041 B, over cap), `micidial_v2_v02.html` (65,288 B, under cap), `micidial_v2_v21.html` (65,299 B variant build). Working `micidial_v2.html` (65,288 B, md5 b16e6195… = byte-identical copy of v02) is gitignored build output.
- Docs (all tracked): `MICIDIAL_V2.md` (operating spec; §12 = current state), `README.md`, `CHANGELOG.md`, `MICIDIAL_V2_USER_GUIDE.md` (run guide + variant flow §10b), `ABTS_OPTIMIZATION_GUIDE.md` (generator-side invariants), `V02_PIPELINE.md` (older v0.2-era writeup), `AGENTS.md` / `CLAUDE.md` (agent rules). README claims a LICENSE file that does not exist.
- `package.json` — root Node deps: terser ^5.51.2 only (`node_modules/` gitignored; drives min_synth.js / min_boot.js).
- `.projectmem/` — project memory (summary.md derived; never hand-edit it)

## Key facts about the target (`original/uncompressed.html`)
- Shell (head + one `<style>` + mid + tail): ~1.8 KB. Single `<script>` holds
  `const P = {...}` (5,295,109 chars) + engine code (~34 KB) + shader
  literals (~29 KB).
- `P` keys: x(64×13), t, d, s(=SCENES), q, b, n, a(['json',[engineSrc 96,684
  chars, projectJSON 308,452]]), v(62 layer defs).
- `P.s` = list of 62 scenes: `[duration, int, objectDefs(7), lights(2),
  camera(4), background(20), SNAPSHOTS(list of records), [1,0.5,0.8,0.6]]`.
- Snapshot record = `[name, role, time, 0, payload]`; 26,982 total; roles &
  counts: object:9 5985, camera 5609, light:1 2714, light:2 2709, object:3
  2362, object:5 1752, object:1 1586, object:4 1441, object:2 1436,
  background 1255, object:10 133.
- gzip-9 floor with raw P = ~508 KB → naive packing CANNOT reach 64 KiB;
  parametric reconstruction is mandatory.

## Relationships
- `v2/compile.py` reads `original/uncompressed.html` → scene model, writes
  the binary/JSON sections consumed by `v2/boot.js` (stream.bin format is
  byte-exact in MICIDIAL_V2.md §7.1).
- `v2/assemble.py` packs boot.min.js + outer.js + synth.min.js + scene stream +
  statics + pv/meta/skeleton + audio.bin + shell.html into per-section deflate
  streams embedded page-safely (cp1252 inverse table + `*` escapes for NUL/CR),
  reusing the carrier code from a shipped page; writes `micidial_v2.html` /
  variant output via `--out`.
- `v2/boot.js` (section 0) inflates + reconstructs `P`, injects shell.html
  (section 9), then runs outer.js as `new Function('P', …)`; audio runs as
  `P.a = ['json', [synthSrc, audioBin]]` honoring the atbs-v04 message
  protocol `{state, play, stop}`.
- `v2/synth.js` (class D) consumes `v2/build/audio.bin` verbatim
  (producer = `v2/audio.py`); `class Lt` is the AudioWorkletProcessor.
- `v2/audio_extract.py` reads `original/uncompressed.html` `P.a` →
  `v2/build/audio.pkl`; `v2/audio.py` reads that pickle.

## Gotchas
- To parse `P` out of the script use `json.JSONDecoder().raw_decode` at
  `const P=`; brace-matching breaks (escaped quotes inside P's strings).
- Windows bash quoting: avoid inline `python -c` with quotes/backslashes —
  write to a script file under `tools/` instead.
- Offline parity checks run through plain Node (`tools/verify_page.js`, `tools/unwrite_page.js`) — no Playwright/browser harness is needed (the `micidial/tools/node_modules` Playwright install was removed in ac4c1b9; root `node_modules/` holds only terser).

