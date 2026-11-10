# Micidial v2

A **lossy semantic compression engine** that shrinks a single-file WebGL demo
page into a self-contained HTML file small enough to run in any standard
browser — with visually and audibly identical output.

## The problem

The input is a monolithic `original/uncompressed.html` (~5.36 MB) containing a
large scene graph, GLSL shaders, an audio worklet, and a 308 KB editor project
file. A pure lossless codec cannot reach the target: its gzip-9 entropy floor is
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
  blob (`v2/audio.py` → `audio.bin`).
- **Everything else** — outer engine JS, GLSL shaders, and static scene config
  are kept byte-identical and pooled into one deflate-raw container.

All lossy choices carry explicit, bounded error tolerances (see
[`MICIDIAL_V2.md`](MICIDIAL_V2.md)).

## Result

| Artifact | Size | Method |
|---|---|---|
| Input (`original/uncompressed.html`) | ~5.36 MB | — |
| v1 ([SpinningKids/micidial](https://github.com/SpinningKids/micidial)) `original/PRESSURE_ATBS135_v13.html` | 657 KB | lossless entropy packing |
| **v2** `micidial_v2.html` | **~67 KB** | semantic re-modeling + runtime decode |

> Current status: the clean-tree build is byte-for-byte reproducible, but sits
> ~1.5 KB over the 64 KiB cap. See [`MICIDIAL_V2.md`](MICIDIAL_V2.md) §1 / §12 for
> the exact numbers and the remaining improvement levers (§13).

## Repository layout

| Path | Purpose |
|---|---|
| `original/` | Reference artifacts: the uncompressed input (5.36 MB) and the v1-compressed page (657 KB, navigation/reference only — do **not** modify). |
| `original/PRESSURE_ATBS135_v13.html` | The **v1**-compressed page (657 KB), from the upstream repo [SpinningKids/micidial](https://github.com/SpinningKids/micidial). Kept here as navigation/reference only. |
| `tools/` | Stage-1 / stage-2 analysis tooling for the target file (budget, scene census, decompression probes). |
| `v2/` | The Micidial **v2** compiler pipeline (`compile.py`, `iface.py`, `audio_extract.py`, `audio.py`, `assemble.py`, `boot.js`, `synth.js`). |
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

# 5. Assemble container + bootstrap splice -> micidial_v2.html (repo root)
python v2/assemble.py
```

See [`MICIDIAL_V2.md`](MICIDIAL_V2.md) §3 for full flag documentation and §7 for
the byte-exact wire formats.

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
