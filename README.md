# Micidial v2

A **lossy semantic compression engine** that shrinks a single-file WebGL demo
page into a self-contained HTML file small enough to run in any standard
browser — with visually and audibly identical output.

## The problem

The input is a monolithic `original/uncompressed.html` (~5.36 MB) containing a
large scene graph, GLSL shaders, an audio worklet, and a 308 KB editor project
file (the file is not committed — it functionally regenerates from
`original/PRESSURE_ATBS135_v13.html` via `tools/decompress_any.py` +
`tools/unwrite_page.js`; byte-exact copy stays in git history).
A pure lossless codec cannot reach the target: its gzip-9 entropy floor is
~508 KB — far above the **64 KiB (65,536 byte)** cap we aim for.

## The approach

Instead of packing bytes, Micidial v2 **re-models the content** so it can be
reconstructed cheaply at load time:

- **Animation** — the 26,982 per-frame snapshot records in `P.s` are replaced
  by parametric *fitted tracks* (const / linear / quadratic / run-length /
  delta-chain / spline-knot / piecewise-polynomial), re-expanded at runtime by a
  small JS decoder. RDP keyframe reduction with an explicit vertical-error bound
  keeps the render error within tolerance.
- **Audio** — the 96 KB audio worklet + 308 KB editor JSON are replaced by a
  compact *procedural synth remake* (`v2/synth.js`) plus a quantized pattern
  blob extracted from the source (`v2/audio_extract.py` → `audio.pkl`, then
  `v2/audio.py` → `audio.bin`).
- **Everything else** — outer engine JS, GLSL shaders, and static scene config
  are kept byte-identical and pooled into one deflate-raw container.

All lossy choices carry explicit, bounded error tolerances (see
[`MICIDIAL_V2.md`](MICIDIAL_V2.md)).

## Result

| Artifact | Size | Method |
|---|---|---|
| Input (`original/uncompressed.html`) | ~5.36 MB | — |
| v1 ([SpinningKids/micidial](https://github.com/SpinningKids/micidial)) `original/PRESSURE_ATBS135_v13.html` | 657 KB | lossless entropy packing |
| v2 v0.1 `micidial_v2_v01.html` | 67,041 B | semantic re-modeling + runtime decode (over cap) |
| **v2 v0.2 `micidial_v2_v02.html`** | **65,288 B** | semantic re-modeling + runtime decode (**under cap**) |
| **v2 v0.3 `micidial_v2_v21.html`** | **65,299 B** | same engine applied to the **v21 variant** page (RDP eps 1.8, Q11) — (**under cap**) |

> v0.3 is the current release: it adds **variant processing** — any v1-compressed
> ABTS demo page can be recompressed under the cap end-to-end (see
> [`MICIDIAL_V2_USER_GUIDE.md`](MICIDIAL_V2_USER_GUIDE.md) §10b). The baseline v13
> build stays **65,288 bytes — 248 B under cap**; the v21 variant ships at
> **65,299 B — 237 B under cap**. See [`MICIDIAL_V2.md`](MICIDIAL_V2.md) §12 for
> exact numbers and [`CHANGELOG.md`](CHANGELOG.md) for what changed.

## Repository layout

| Path | Purpose |
|---|---|
| `original/` | Reference artifacts: the two v1-compressed pages (`PRESSURE_ATBS135_v13.html` 657 KB, `PRESSURE_ATBS135_v21.html` 735 KB — navigation/reference only, do **not** modify). The uncompressed input is **not committed** (storage); functionally regenerate with `tools/decompress_any.py` + `tools/unwrite_page.js`, byte-exact via git history. |
| `tools/` | Variant tooling: `decompress.py` / `decompress_any.py` (v1 container → payload), `unwrite_page.js` (`document.write` payload → real page), `diff_pages.py` (P-key scoping diff), `extract_shipped.py` (decode a shipped page's embed into its 10 sections), `verify_page.js` (offline cp1252 boot check). |
| `v2/` | The Micidial **v2** compiler pipeline (`compile.py`, `iface.py`, `audio_extract.py`, `audio.py`, `min_synth.js`, `min_boot.js`, `assemble.py`, `boot.js`, `synth.js`). |
| `v2/build/shell.html` | The only build artifact committed by hand — the DOM shell injected at runtime. Every other file in `v2/build/` is regeneratable from the pipeline and not kept. |
| `.projectmem/` | Persistent project memory + workflow rules (managed by [`pjm`](https://www.google.com)); never hand-edit. |

## Running the v2 pipeline

There is no single runner; run the stages in order (all idempotent, paths
relative to repo root):

```text
# 1. Scene compiler -> v2/build/{stream.bin,statics.txt,pv.json,meta.json, skeleton.json,model32.pkl}
python v2/compile.py --rdp=1 --quant=100 --tol=0.011

# 1b. Outer-JS extractor (byte-exact js[vend:] slice) -> v2/build/outer.js
python v2/iface.py

# 2. Audio model extraction (original page P.a -> v2/build/audio.pkl)
python v2/audio_extract.py

# 3. Audio blob encoder (v2/build/audio.pkl -> v2/build/audio.bin)
python v2/audio.py

# 4. Synth minification (v2/synth.js -> v2/build/synth.min.js; needs root node_modules)
node v2/min_synth.js

# 4b. Boot minification (v2/boot.js -> v2/build/boot.min.js; byte-exact)
node v2/min_boot.js

# 5. Assemble container + bootstrap splice -> micidial_v2.html (repo root)
python v2/assemble.py
```

> For a variant input page (any `PRESSURE_ATBS135_vN.html`), the three input
> stages take `--src=<page>` and `assemble.py` takes `--out`/`--shell` — see
> [`MICIDIAL_V2_USER_GUIDE.md`](MICIDIAL_V2_USER_GUIDE.md) §10b for the full flow.

> Every file produced in `v2/build/` except `shell.html` is a regeneratable
> build artifact — the tree above reproduces them all from `original/`. Only
> `shell.html` is authored by hand and committed; keep the working tree clean of
> the rest (see [`AGENTS.md`](AGENTS.md)).

See [`MICIDIAL_V2.md`](MICIDIAL_V2.md) §3 for full flag documentation and §7 for
the byte-exact wire formats.

## Version history

| Version | Artifact | Size | Key changes |
|---------|----------|------|-------------|
| **v0.3** (current) | `micidial_v2_v21.html` (variant) + `micidial_v2.html` (baseline, 65,288 B) | 65,299 B | **Variant processing**: `--src=` input override on compile/iface/audio_extract, generic v1 unpacking tools (`tools/decompress_any.py`, `unwrite_page.js`, `diff_pages.py`, `extract_shipped.py`, `verify_page.js`), restored `v2/min_boot.js`, committed v0.2-layout `assemble.py`. `original/uncompressed.html` removed from repo (regeneratable). |
| v0.2 | `micidial_v2_v02.html` | 65,288 B | Per-section deflate-raw container + `windows-1252` cp1252 page-safe encoding (replaces base85 + single-stream deflate); minified boot.js (2,948 B); entirely new hand-written procedural synth (50,521 B raw, achieving parity with the original atbs-v04 audio). Sections 3–9 unchanged from v0.1. |
| v0.1 | `micidial_v2_v01.html` | 67,041 B | Single whole-container deflate-raw + base85 (1.25x expansion); unminified boot.js (3,798 B); legacy synth.js (7,939 B). 1,505 B over the 64 KiB cap. |

See [`CHANGELOG.md`](CHANGELOG.md) for the full v0.1 → v0.2 changelog.

## Documentation

The complete operating specification — pipeline, wire formats, container layout,
runtime decoder, and the verified quality-degradation table — lives in
[`MICIDIAL_V2.md`](MICIDIAL_V2.md).

## Notes for contributors / AI agents

This project uses **projectmem** for persistent memory and workflow rules. Read
`.projectmem/AI_INSTRUCTIONS.md`, `.projectmem/summary.md`, and
`.projectmem/PROJECT_MAP.md` before working, and log decisions/notes via the
provided `pjm` tools (see [`AGENTS.md`](AGENTS.md)).

## License

See [LICENSE](LICENSE).
