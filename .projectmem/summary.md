# projectmem - micidial_v2

_Last updated: 2026-11-10_

## Project purpose
Build "micidial v2": a scene compiler that compresses the single-file WebGL
intro `original/uncompressed.html` (5.36 MB) below 64 KiB while remaining a
self-contained HTML that renders identically in a standard browser.

## Recent issues
- [OPEN] #0005 latent runtime gap: boot.js regen() implements track kinds 0-5 only; choose_fit can emit kind 6 (segs) in other profiles -> shipped page would break. Current default profile emits 0 segs (histogram: const 197/runs 134/cha 6/knots 1). [v2/boot.js] (open)
- [OPEN] #0001 built v2/extract+fit prototype (v2/compiler.py): per-(scene,role,slot) tracks, const/lin/quad/poly/RDP fits, varint cost estimator. Scene 0 alone = 55.6KB projected (under 64k); ALL 62 scenes = 157.9KB projected - OVER. Per-scene track splitting fragments smooth global curves (12,334 tracks... (open)
  - Partial attempt: built v2/extract+fit prototype (v2/compiler.py): per-(scene,role,slot) tracks, const/lin/quad/poly/RDP fits, varint cost estimator. Scene 0 alone = 55.6KB projected (under 64k); ALL 62 scenes = 157.9KB projected - OVER. Per-scene track splitting fragments smooth global curves (12,334 tracks...
  - Partial attempt: v2/floor.py fixed-cost measurement (everything except the 26,982 records): outer JS 34,194 -> deflate 13.8k; shaders 28,649 -> 9.4k; engine JS 96,684 (pure code, ZERO base64 samples, already minified; terser saves only 300 chars) -> 27.3k; project JSON 308,452 -> 10.8k; statics 93,890 -> 10.2k...
  - Partial attempt: compile.py v3.3: RDP reduction (reduce_records+rdp_local) + segs finite-difference token codec (fd_pick exact-seed + float LSQ binomial-basis solve, expand_segs verify) wired into choose_fit. Segs never wins: kept keys are jagged polylines (no index-polynomial after RDP); codec harmless but...
- [DONE] #0004 v2/iface.py (active outer.js producer) crashed after writing outputs: probe regex 'on("ci|on(\'ci' has unbalanced parens -> re.PatternError breaks &&-chained pipeline runs [v2/iface.py] (fixed)
- [DONE] #0003 #0002 boot.js never injects DOM shell (#start/#setup/#gpu/canvas); outer JS queries them and throws 'Cannot set properties of null (onclick)' (fixed)
- [DONE] #0002 micidial_v2.html fails to load: BDE PACK ERROR · TypeError: Failed to fetch. Root cause appears in assemble.py container/runtime wiring. [C:\Users\Luca\Dev\micidial_v2\micidial_v2.html] (fixed)

## Decisions
- micidial v2 goal: new compression engine to replace micidial v1; compress target HTML (original/PRESSURE_ATBS135_v13.html) below 64 KiB using the v2 engine once built
- Stage-2 scope CONFIRMED by user: visual parity + procedural audio remake. Drop inner engine (96.7KB) + project JSON (308KB) as-is data; replace with tiny procedural drum synth (~2-4KB) + compact quantized pattern data extracted from project JSON/pattern schedule. Full lossless-audio path would...
- RETIRE the expand-at-load + original-engine-untouched half of the architecture. Kept: de-flipbook 26,982 records -> parametric fitted tracks. Changed: v2 ships its own compact path (outer JS kept) + a procedural synth replacing the 96.7 KB atbs-v04 engine, because shipping original...
- User directive: eliminate the v2 verifier stage (pixel/audio comparison); the user will verify the produced file themselves. Plan updated accordingly
- Keyframe reduction SUPERSEDES uniform x4 subsampling: per-(scene,role,leafpath) RDP (rdp_local vertical metric = engine K() linear-blend error). v3.3 default profile --rdp=1 --quant=100 --tol=0.004 keeps 4,078/26,982 records; blend deviation <=1.0 raw unit vs x4-tier worst 5.6-10 -> strictly...
- Statics (P.s non-record slots) normalized: per (scene, object-def-id) with record coverage, def value replaced by scene-0 canonical (record payloads are full def arrays and K() always overrides base when a target exists; 196/439 object defs have no record in that scene and keep their real...
- Payload container + runtime layout: ONE deflate-raw stream over [u16 section count][u32 LE lens][concatenated section bodies]; sections: 0=boot decoder JS text, 1=outer JS verbatim (js[vend:]), 2=synth worklet source, 3=P.s binary stream (existing S12/S3end codec), 4=statics component-pool text...
- Fix #0003: add dedicated shell section to container; boot.js writes it via document.write() (canvas+#setup+#gpu+#start+#fs+styles) BEFORE running outer engine. Preserves original v13 DOM-injection behavior.
- Loss budget accepted for scene stream (default profile --rdp=1 --quant=100 --tol=0.011): RDP keyframe reduction 26,982->4,078 records (vertical metric = engine K() linear-blend error bound <=1.0 raw unit); float requant grid=100; validator measured worst deviation 0.01, 0 hard mismatches. Full... [v2/compile.py]
- Audio blob loss accepted: automation anchors RDP-reduced at eps 1.0 on round(v*100) (0.01 units); vel/prob *100 clamped 0..127 (caps at 1.27); ratchet>=2 boolean collapse; gate steps 2-bit {0,.5,1}; prob==1 implicit (lossless over asserted universe). Sound itself is a procedural atbs-v04 remake... [v2/audio.py]
- Cleanup 2026-11-10: deleted superseded scratch (compiler.py, compiler2.py, dead build.py, floor.py, iface2.py, interp_err.py, protocol.py, shapes.py, ties.py-7, synth_draft*.js.txt, test_synth.js, boot.min.js, unpack_orig.py, __pycache__, root nul) + tools one-shot probes; added audio_extract.py... [v2/]
- FINAL cleanup policy 2026-11-10 (strictens prior Cleanup decision): keep ONLY rerun inputs. v2/: compile.py, iface.py, audio_extract.py, audio.py, assemble.py, min_synth.js, synth.js, boot.js + build/shell.html. v2/build/ holds ONLY shell.html (hand-written input); all other build files are...

## Notes
- P.a structure: P.a=['gzip', base64(gzip(JSON [w, song]))]. w = the ENTIRE audio worklet source (96,684 B, the 'engine' — NOT a separate const in the HTML). song = full editor project JSON (308,452 B, schemaVersion 1.6.0, keys...
- Wire format invariants for runtime boot decoder (compile.py v3.3): stream = [roles: uvb n + (len+utf8)*][per scene: uvb vocabN, per vocab: uvb lenN + uvb rid*][per cluster: svb dt, uvb sid][tracks until EOF: per track: uvb rid, uvb grid-or-uniqN, KIND byte (0 const,1 lin,2 quad,3 runs,4 knots,5...
- High churn detected: v2\synth.js (4 edits in 10 min) [v2\synth.js]
- High churn detected: v2\min_synth.js (4 edits in 10 min) [v2\min_synth.js]
- High churn detected: v2\compile.py (4 edits in 10 min) [v2\compile.py]
- High churn detected: v2\assemble.py (4 edits in 10 min) [v2\assemble.py]
- Final HTML generated: micidial_v2.html 65,361 B (<65,536). Container sections 9, deflated 51.6KB, base85 encoded. Boot decoder with varint/regen implemented.
- Record names collapsed to constant id 0 in the P.s stream: probe verified names are never parsed/looked up by the engine (zero violations). Lossless vs runtime behavior, but any future feature that reads record names would break. Logged as Q5 in MICIDIAL_V2.md §11. [v2/compile.py]
- Reference doc: MICIDIAL_V2.md (repo root) = complete v2 operating spec - pipeline commands (compile.py, iface.py, audio_extract.py, audio.py, min_synth.js, assemble.py), byte-exact wire formats, container/base85 layout, boot.js runtime, and quality-degradation table with verified error bounds... [MICIDIAL_V2.md]
- lesson: a file literally named 'nul' (Windows reserved device name, created by a shell redirect slip) cannot be deleted via cmd/PowerShell rm; os.remove(r'\\?\C:\abs\path\nul') with the \?\ prefix works — it bypasses device-name resolution. Used during 2026-11-10 cleanup. [.]

## Key files
- `original/PRESSURE_ATBS135_v13.html`
- `tools\decompress.py`
- `decompress.py`
- `tools\dbg.py`
- `dbg.py`
- `micidial\tools\verify_reconstruct.js`
- `verify_reconstruct.js`
- `tools\parse_probe.js`
- `parse_probe.js`
- `tools\finalize_reconstruct.js`
- `finalize_reconstruct.js`
- `P.s`
- `uncompressed.html`
- `1.8KB`
- `P.a`
- `P.v`
- `P.x`
- `tools/analyze_scene.py`
- `budget.py`
- `probe_inner.py`

## Open questions
- None logged yet.
