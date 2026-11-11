# #0009 P1: Replace 4-tap tetrahedral gradient with analytical ∇SDF for all 7 primitives + 11 modifiers (chain rule) — 30-45% fragment time

- 2026-11-10T18:06:25Z `issue`: P1: Replace 4-tap tetrahedral gradient with analytical ∇SDF for all 7 primitives + 11 modifiers (chain rule) — 30-45% fragment time [shader_frag.glsl]
- 2026-11-10T18:20:36Z `attempt`: S4: Replaced boot.js hand-rolled varint decoder with DataView+LEB128 [v2/boot.js] (worked)
- 2026-11-10T18:20:36Z `attempt`: S5: Removed dead code from outer.js (WebWorker particle field builder, ScriptProcessor fallback, unused vars FC/FPROGRAMS) [v2/iface.py] (worked)
- 2026-11-10T18:20:36Z `fix`: S4+S5 implemented: boot.js varint decoder optimized (~0.8 KB savings), outer.js dead code removed (~5 KB savings). New artifact micidial_v2_v03.html at 65,161 bytes (under 65,536 cap).
- 2026-11-10T19:13:10Z `fix`: P1 complete: analytical gradients implemented for 7 primitives + chain rule through 11 modifiers
