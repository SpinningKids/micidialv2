# Micidial v2 Changelog

## [v0.3] — variant processing + storage trim (2026-11-11)

### Added
- `MICIDIAL_V2_USER_GUIDE.md` — AI agent reference for running the micidial v2 pipeline: 5-stage build commands, tuning parameters (`--rdp`, `--quant`, `--tol`), size budget breakdown, quick + structural levers when output exceeds 64 KiB, validation rules, cleanup, and steps to adapt for a new input HTML (§10b now covers the **full flow from a compressed ABTS demo page**: container unpack → payload un-bootstrap → P-key diff → `--src=` stages → shipped-section reuse → variant assemble → offline verification).
- `ABTS_OPTIMIZATION_GUIDE.md` — AI agent reference for the ABTS demo system (generator of uncompressed HTML): 5 structural invariants micidial v2 exploits, tiered optimizations (animation curve compressibility, audio pattern schema, outer JS minification, P.v folding), exact audio blob schema with field requirements, anti-patterns table, validation checklist, and `compile.py`/`audio_extract.py` locations to update if ABTS output structure changes.
- **Variant pipeline**: `--src=<page>` input override on `compile.py`, `iface.py`, `audio_extract.py`; `assemble.py` gained `--out`/`--shell`/`--carrier`.
- `tools/` variant tooling (permanent): `decompress_any.py` (any v1 container → payload), `unwrite_page.js` (`document.write` payload → real page, needed for v21+), `diff_pages.py` (generic P-key scoping diff), `extract_shipped.py` (decode a shipped page's embed into its 10 sections), `verify_page.js` (Chrome-faithful windows-1252 offline boot check).
- `v2/min_boot.js` restored — stage 4b (`terser compress:false`) reproduces `boot.min.js` byte-exact (2,948 B, sha `067fa093`).
- `micidial_v2_v21.html` — variant build of the **v21** ABTS page: **65,299 B, 237 B under the 64 KiB cap**, profile `--rdp=1.8 --quant=100 --tol=0.011` (quality row Q11: kept 3,726/30,839 records, 0 hard mismatches, worst float deviation 0.01). Baseline v13 build unchanged at 65,288 B.

### Changes
- `v2/assemble.py` rewritten as the committed v0.2-layout producer (carrier pre/post + decoder code harvested from the shipped page; per-section deflate + cp1252 comment embedding). Rebuilds decode byte-exact through the shipped path but are not byte-identical to `micidial_v2.html`: current zlib finds better matches than the older build that shipped it (63,115 vs 63,484 deflated B).

### Removed
- `original/uncompressed.html` (5.36 MB) — deleted to save storage; functionally regeneratable with `tools/decompress_any.py` + `tools/unwrite_page.js` from `original/PRESSURE_ATBS135_v13.html` (output is 27 B shorter than the browser-decoded page — Node lacks `document.write` tag auto-insertion; pipeline anchors unaffected). Byte-exact copy remains in git history. Notarized in project memory and `MICIDIAL_V2.md` §3/§14.

## [v0.2] — `micidial_v2_v02.html` (65,288 B — 248 B under the 64 KiB cap)

### Changes from v0.1

#### 1. Container + bootstrap encoding (primary size win)

v0.1 packed the entire container as **one deflate-raw stream** then **base85-encoded** it (1.25x byte expansion, 65,990 chars for a 52,792 B payload).

v0.2 instead:
- Deflates **each section independently** (`zlib.compress(b, 9, wbits=-15)`), no 4-byte padding, no base85.
- Embeds the binary container **page-safe** using a `windows-1252` charset and a cp1252 inverse-table lookup (27 chars, embedded as a 54-char hex table `H`).
- Escapes three tokenizer-corrupting bytes with `*` pairs: NUL (0x00), CR (0x0D), and `*` (0x2A) itself — each costs exactly 1 extra byte (+712 B total on the real payload).
- Reads the payload from between `/*` and `*/` in the single `<script>` via `document.currentScript.textContent`.

Result: container sum of per-section deflates is 63,484 B (+42 B header = 63,526 B), vs 65,110 B for the old single stream. The bootstrap is ~630 B (no v1 base85 decoder splice).

#### 2. Boot code minified (section 0)

`v2/boot.js` source (3,798 B) is shipped minified as `v2/build/boot.min.js` (2,948 B source, 1,317 B deflated). Functionally identical to v0.1: same varint (uvb/svb) readers, same regen kinds 0–5 (const/lin/quad/runs/knots/cha), same banker's rounding `R()`, same section mapping (sections 1–9), same `document.write` shell injection before running outer.js. Kind 6 (`segs`) remains unimplemented in the runtime — latent gap, never selected by the current fit profile.

#### 3. Audio engine entirely rewritten (section 2)

v0.1 shipped `v2/synth.js` (7,939 B raw). v0.2 replaces it with a **new hand-written procedural synth** (50,521 B raw, 15,478 B deflated) that:
- Reproduces the original atbs-v04 audio with parity (verified by ear; Q7 loss budget accepted).
- Speaks the identical AudioWorklet message protocol (`{type:'state'|'play'|'stop'}`, `registerProcessor("atbs-v04", …)`), so `outer.js` needs no changes.
- Uses `Math.imul`-based xorshift RNG, a biquad filter class, and expanded voice architecture.

The audio blob (`audio.bin`, section 7, 3,724 B raw / 1,929 B deflated) format is unchanged from v0.1: quantized pattern grids, RDP-reduced automation anchors, sparse probability encoding.

#### 4. Sections 3–9 unchanged

`stream.bin`, `statics.txt`, `pv.json`, `meta.json`, `audio.bin`, `skeleton.json`, `shell.html` are byte-identical between v0.1 and v0.2.

#### 5. `outer.js` line endings

v0.2's section 1 has 6 CRLF line endings where v0.1 has LF — a build-environment artifact; content is otherwise byte-identical.

### What did NOT change

- Pipeline stages (`compile.py`, `iface.py`, `audio_extract.py`, `audio.py`, `assemble.py`) and their flags (`--rdp=1 --quant=100 --tol=0.011`) are unchanged from v0.1.
- Wire formats (§7 of MICIDIAL_V2.md): varint coding, track kinds 0–5, statics pool, skeleton templates, audio blob layout — all unchanged.
- Quality degradation bounds (Q1–Q10) unchanged; Q10 updated to reflect the new container.

## [v0.1] — `micidial_v2_v01.html` (67,041 B — 1,505 B over cap)

Initial release of Micidial v2. Semantic re-modeling of `P.s` snapshot records into fitted tracks, procedural synth replacing the 96 KB atbs-v04 worklet, single deflate-raw container + base85 packing, unminified boot.js.
