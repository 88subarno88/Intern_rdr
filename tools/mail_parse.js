// Turns raw mails into the fields the workflow uses. Called by gmail_fetch.py.
// usage: node mail_parse.js <raw.json> <out.json>
// It uses the same mail parser, in the same way, as n8n's own Gmail node, so the result
// is identical to what the workflow received before the switch to an app password. That
// matters because many job mails have no plain-text part: the parser makes one from the
// HTML, and tools/job_mail_split.js reads that text.
const fs = require('fs');
const path = require('path');
const { simpleParser } = require(path.join(path.dirname(process.execPath), '../lib/node_modules/n8n/node_modules/mailparser'));

(async () => {
  const out = [];
  for (const m of JSON.parse(fs.readFileSync(process.argv[2], 'utf8'))) {
    const p = await simpleParser(Buffer.from(m.raw, 'base64').toString('utf8'));
    out.push({ id: m.id, from: { text: (p.from && p.from.text) || '' }, subject: p.subject || '', text: p.text || '', html: p.html || '', date: p.date || '' });
  }
  fs.writeFileSync(process.argv[3], JSON.stringify(out));
})().catch(e => { console.error(String(e)); process.exit(1); });
