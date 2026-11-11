// Evaluate a micidial v1 document.write bootstrap payload and emit the real page.
// shortcut: no browser tag auto-insertion (<html>/<head>/<body>), so output is
// ~27 B shorter than a browser-decoded page; upgrade if a byte-exact regen is ever needed.
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const chunks = [];
global.document = { open(){}, write(s){ chunks.push(String(s)); }, close(){} };
eval(src);
fs.writeFileSync(process.argv[3], chunks.join(''));
console.log('page bytes:', chunks.join('').length);
