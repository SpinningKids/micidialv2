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
- `v2/` — micidial v2 Scene Compiler (to be built)
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
- `v2/extract.py` reads `original/uncompressed.html` → scene model for the compiler.
- `v2` runtime (JS) expands fitted tracks back to the exact original `P`
  structure, then runs the v1-style payload path like
  `micidial/tools/minify.py`'s bootstrap (DecompressionStream).
- Verifiers in `micidial/tools/` (browser_test.js, verify_html.js) reuse for v2.

## Gotchas
- To parse `P` out of the script use `json.JSONDecoder().raw_decode` at
  `const P=`; brace-matching breaks (escaped quotes inside P's strings).
- Windows bash quoting: avoid inline `python -c` with quotes/backslashes —
  write to a script file under `tools/` instead.
- Playwright must run from `micidial/tools/node_modules` (copy scripts there).
