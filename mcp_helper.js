const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const args = process.argv.slice(2);
const command = args[0];
const method = args[1];
const jsonFile = args[2];

if (!command || !method) {
  console.error('用法: node mcp_helper.js <command> <method> [jsonFile]');
  process.exit(1);
}

const bridgePath = path.join(
  process.env.APPDATA,
  'reasonix', 'skills', 'mcp-streamable-connect', 'mcp-bridge.js'
);

let cmd;
if (jsonFile) {
  const json = fs.readFileSync(jsonFile, 'utf8');
  cmd = `node "${bridgePath}" ${command} ${method} "${json.replace(/"/g, '\\"')}"`;
} else {
  cmd = `node "${bridgePath}" ${command} ${method}`;
}

try {
  const result = execSync(cmd, { encoding: 'utf8', stdio: 'pipe' });
  console.log(result);
} catch (e) {
  console.log(e.stdout || e.message);
}
