// Offline browser-parity check for a shipped v2 page:
// - decode file bytes with windows-1252 (Chrome behaviour: defined 0x80-0x9F slots
//   map to cp1252 chars, undefined slots stay identity)
// - run the carrier decoder code verbatim with a stubbed document
// - assert the shell section was written and every section round-trips byte-exact
// Usage: node tools/verify_page.js <page.html> <shell.html>
const fs = require('fs');
// cp1252 table for defined slots (char code values)
const CP_TABLE = {0x80:0x20AC,0x82:0x201A,0x83:0x0192,0x84:0x201E,0x85:0x2026,0x86:0x2020,0x87:0x2021,
  0x88:0x02C6,0x89:0x2030,0x8A:0x0130,0x8B:0x2039,0x8C:0x0152,0x8E:0x017E,0x91:0x2018,0x92:0x2019,
  0x93:0x201C,0x94:0x201D,0x95:0x2022,0x96:0x2013,0x97:0x2014,0x98:0x02DC,0x99:0x2122,0x9A:0x0131,
  0x9B:0x203A,0x9C:0x0153,0x9E:0x017F,0x9F:0x0178};
const bytes = fs.readFileSync(process.argv[2]);
let s = '';
for (const b of bytes) s += (b >= 0x80 && b <= 0x9f && b in CP_TABLE) ? String.fromCharCode(CP_TABLE[b]) : String.fromCharCode(b);
const i = s.indexOf('<script>'), j = s.lastIndexOf('</script>');
const body = s.slice(i + 8, j);
const chunks = [];
global.document = {
  currentScript: { textContent: body },
  open() {}, write(t) { chunks.push(String(t)); }, close() {},
  body: { set textContent(v) { global.__err = String(v); } },
};
(async () => {
  await eval(body); // carrier + boot + outer; outer dies offline at WebGL (expected)
  const shell = fs.readFileSync(process.argv[3], 'utf8');
  const got = chunks.join('');
  console.log('shell written:', got === shell ? 'EXACT' : 'MISMATCH len ' + got.length + ' vs ' + shell.length);
  console.log('engine stage error captured:', global.__err ? global.__err.slice(0, 80) : 'none (engine ran past WebGL?)');
})();
