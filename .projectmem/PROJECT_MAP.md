# Project Map - micidial_v2

Status: real content, refined by AI session.

## Project purpose
Build "micidial v2": a scene compiler that compresses the single-file WebGL
intro `original/uncompressed.html` (5.36 MB) below 64 KiB while remaining a
self-contained HTML that renders identically in a standard browser.

## Structure
- `original/` — reference artifacts
  - `original/uncompressed.html` — the compressed-source's ORIGINAL page, recovered in stage 1 (5,359,781 B). Compression target.
  - `original/PRESSURE_ATBS135_v13.html` — v1-engine-compressed page (657,106 B); navigation/reference only.
- `micidial/` — micidial v1 engine (documentation of how v1 compresses; DO NOT modify)
  - `micidial/REBUILD.md` — v1 rebuild procedure
  - `micidial/MINIFY_PLAN.md` — v1 plan: entropy packing (gzip payload ~450 B bootstrap)
  - `micidial/tools/minify.py` — v1 pipeline: sentinels → terser → gzip-9 → base64 payload
  - `micidial/tools/*.js` — v1 verifiers (diff_engine, verify_html, glsl_diff, browser_test, eval_literals)
  - `micidial/tools/node_modules/` — Playwright install (canonical; not scratch)
- `tools/` — stage-1/2 analysis tooling for the TARGET file
  - `tools/budget.py` — byte budget + gzip-9 entropy floor of uncompressed.html
  - `tools/scene_census.py` — P.s snapshot census (26,982 records, role histogram)
  - `tools/probe_inner.py`, `tools/snap_count.py` — P.a / P.s structure probes
  - `tools/analyze_scene.py` — rough segment anatomy
  - `tools/decompress.py` — stage-1 static decoder for PRESSURE_ATBS135_v13.html
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
  - `v2/boot.js` — runtime decoder/section 0: rebuilds P, writes shell, runs outer
  - `v2/assemble.py` — stage 5: container (10 sections, deflate-raw) +
    base85 (+v1 bootstrap splice) → micidial_v2.html
  - `v2/build/shell.html` — hand-written DOM shell input (only kept build file)
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
- `v2/assemble.py` packs boot.js + outer.js + synth.min.js + scene stream +
  statics + pv/meta/skeleton + audio.bin + shell.html into ONE deflate-raw
  container, splices v1's bootstrap head, writes `micidial_v2.html`.
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
- Playwright must run from `micidial/tools/node_modules` (copy scripts there).
