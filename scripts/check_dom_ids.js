const fs = require('fs');
const content = fs.readFileSync('backend/app/modules/dashboard/web.py', 'utf8');

const regex = /document\.getElementById\(['"]([^'"]+)['"]\)/g;
let match;
const ids = new Set();
while ((match = regex.exec(content)) !== null) {
  ids.add(match[1]);
}

console.log('Total unique getElementById IDs:', ids.size);

const missing = [];
for (const id of ids) {
  const hasId = content.includes('id="' + id + '"') || content.includes("id='" + id + "'");
  if (!hasId) {
    missing.push(id);
  }
}

console.log('Missing IDs:', missing);
