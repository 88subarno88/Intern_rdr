// Code of the "Split job mails" node (Run Once for All Items). tools/build_workflows.py
// pastes this file into the node, so edit it here and rebuild rather than editing in n8n.
// A job mail from LinkedIn, Glassdoor, Indeed, Internshala, Unstop or SWE List lists several jobs; this turns
// it into one item per job so each job gets its own score. Every other mail passes through
// untouched. If a job mail cannot be read cleanly (the layout changed, or the count of
// jobs found does not match the count of job links) it also passes through whole, so
// nothing is lost.
// Board-independent name of a job: company + title, lower-cased, without punctuation or
// company suffixes. The same job seen on two boards, or twice on one, gets the same key.
const slug = s => String(s || '').toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim();
const jobKey = (board, job) => {
  const company = slug(job.company).replace(/\b(pvt|private|ltd|limited|llp|llc|inc|corp|co)\b/g, ' ').replace(/\s+/g, '-').replace(/^-+|-+$/g, '');
  const title = slug(job.title).replace(/\binternship\b/g, 'intern').replace(/\s+/g, '-');
  return company && title ? (company + '--' + title).slice(0, 150) : board + '-' + job.id;
};
const clean = s => String(s || '').replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();

// LinkedIn (plain text): title, company, location, optional notes, then "View job: <link>".
function linkedin(mail) {
  const lines = (mail.text || '').split(/\r?\n/).map(l => l.trim());
  const jobs = [];
  const seen = new Set();
  let links = 0;
  lines.forEach((line, n) => {
    const hit = line.match(/^View job:?\s*(https?:\S+)?$/i);
    if (!hit) return;
    const id = ((hit[1] || lines[n + 1] || '').match(/\/jobs\/view\/(\d+)/) || [])[1];
    if (!id || seen.has(id)) return;
    links++;
    const block = [];
    for (let k = n - 1; k >= 0 && lines[k] && !/^-{5,}$/.test(lines[k]) && !/https?:\/\//i.test(lines[k]); k--) block.unshift(lines[k]);
    if (!block.length) return;
    seen.add(id);
    jobs.push({ id, title: block[0], company: block[1] || '', location: block[2] || '', notes: block.slice(3), link: 'https://www.linkedin.com/jobs/view/' + id + '/' });
  });
  return jobs.length === links ? jobs : [];
}

// Indeed (plain text): one paragraph per job. Title, "Company - Location", optional pay,
// description, age, and the link (carrying jk=<id>) on the last line.
function indeed(mail) {
  const jobs = [];
  const seen = new Set();
  let links = 0;
  for (const para of (mail.text || '').split(/\r?\n\s*\r?\n/)) {
    const lines = para.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    const hit = (lines[lines.length - 1] || '').match(/^(https?:\/\/[^\/\s]+)\/\S*[?&]jk=([0-9a-f]{6,})/i);
    if (!hit || seen.has(hit[2])) continue;
    links++;
    if (lines.length < 3) continue;
    seen.add(hit[2]);
    const cut = lines[1].lastIndexOf(' - ');
    jobs.push({ id: hit[2], title: lines[0], company: cut > 0 ? lines[1].slice(0, cut) : lines[1], location: cut > 0 ? lines[1].slice(cut + 3) : '',
      notes: lines.slice(2, -1).filter(l => !/^easily apply$/i.test(l)), link: hit[1] + '/viewjob?jk=' + hit[2] });
  }
  return jobs.length === links ? jobs : [];
}

// Glassdoor (plain text): one field per line. Company, title, location, optional pay,
// optional "Easy Apply", age, then the job link in square brackets (jobListingId=<id>).
function glassdoor(mail) {
  const marked = (mail.text || '').replace(/\[(https?:\/\/[^\]]*)\]/g, (all, u) => /\/partner\/jobListing\.htm/i.test(u) ? '\n@@JOB ' + u.replace(/\s+/g, '') + '\n' : '\n');
  const jobs = [];
  const seen = new Set();
  let links = 0;
  let buf = [];
  for (const line of marked.split(/\r?\n/).map(l => l.trim()).filter(Boolean)) {
    if (!line.startsWith('@@JOB ')) { if (!/^(avatar|easy apply)$/i.test(line)) buf.push(line); continue; }
    const fields = buf;
    buf = [];
    const id = (line.match(/[?&]jobListingId=(\d+)/) || [])[1];
    if (!id || seen.has(id)) continue;
    links++;
    const notes = [];
    if (/^\d+\s*[hdm]\+?$/i.test(fields[fields.length - 1] || '')) notes.unshift('Posted ' + fields.pop() + ' ago');
    if (/[₹$€£]|Est\.\)/.test(fields[fields.length - 1] || '')) notes.unshift('Pay: ' + fields.pop());
    if (fields.length < 3) continue;
    seen.add(id);
    const host = (line.match(/^@@JOB (https?:\/\/[^\/]+)/) || [])[1];
    jobs.push({ id, title: fields[fields.length - 2], company: fields[fields.length - 3].replace(/\s*\d(\.\d)?\s*★$/, ''), location: fields[fields.length - 1],
      notes, link: host + '/job-listing/?jl=' + id });
  }
  return jobs.length === links ? jobs : [];
}

// Internshala (HTML only): each internship is a link wrapping a card whose <div id> is
// the internship number, with the title in <h5> and company, place, duration and stipend
// in <span>s after it.
function internshala(mail) {
  const html = mail.html || '';
  const jobs = [];
  const seen = new Set();
  const cards = /<a\b[^>]*\bhref="([^"]+)"[^>]*>\s*<div[^>]*\bid="(\d+)"[^>]*>([\s\S]*?)<\/a>/gi;
  let links = 0;
  for (const card of html.matchAll(cards)) {
    if (seen.has(card[2])) continue;
    links++;
    const head = card[3].match(/<h5[^>]*>([\s\S]*?)<\/h5>([\s\S]*)/i);
    if (!head) continue;
    const spans = Array.from(head[2].matchAll(/<span[^>]*>([^<]*)/gi)).map(s => clean(s[1])).filter(Boolean);
    if (!spans.length) continue;
    seen.add(card[2]);
    let link = card[1].replace(/&amp;/g, '&');
    const wrapped = link.match(/\/CL0\/(https?:[^?]*)/i);
    if (wrapped) { try { link = decodeURIComponent(wrapped[1]).split('?')[0]; } catch (e) { link = card[1]; } }
    jobs.push({ id: card[2], title: clean(head[1]) + (/>\s*Internship\s*</i.test(card[3]) ? ' internship' : ''), company: spans[0], location: spans[1] || '', notes: spans.slice(2), link });
  }
  return jobs.length === links ? jobs : [];
}

// Unstop (HTML only): each opportunity is a link holding two <div>s, title then company,
// followed by a second link holding the pay (or "Apply Now"). Links are tracking links.
function unstop(mail) {
  const html = mail.html || '';
  const jobs = [];
  const cards = /<a\b[^>]*\bhref="([^"]+)"[^>]*>\s*<div[^>]*>([^<]+)<\/div>\s*<div[^>]*>([^<]+)<\/div>\s*<\/a>(?:\s*<\/td>(?:\s|<!--[\s\S]*?-->)*<td[^>]*>\s*<a\b[^>]*>\s*<span[^>]*>([^<]*)<\/span>)?/gi;
  for (const card of html.matchAll(cards)) {
    const title = clean(card[2]);
    const company = clean(card[3]);
    if (!title || !company) return [];
    const pay = clean(card[4]);
    jobs.push({ id: slug(company + ' ' + title).replace(/ /g, '-'), title, company, location: '', notes: pay && !/^apply now$/i.test(pay) ? ['Pay: ' + pay] : [], link: card[1].replace(/&amp;/g, '&') });
  }
  return jobs;
}

// SWE List (plain text): "Company: Role", possibly wrapped over two lines, followed by
// its simplify.jobs link in square brackets.
function swelist(mail) {
  const marked = (mail.text || '').replace(/\[(https?:\/\/[^\]]*)\]/g, (all, u) => /simplify\.jobs\/p\/[0-9a-f-]{8,}/i.test(u) ? '\n@@JOB ' + u.replace(/\s+/g, '') + '\n' : '\n\n');
  const jobs = [];
  let links = 0;
  let buf = [];
  let gap = false;
  for (const line of marked.split(/\r?\n/).map(l => l.trim())) {
    if (!line) { gap = true; continue; }
    if (!line.startsWith('@@JOB ')) { if (gap) buf = []; gap = false; buf.push(line); continue; }
    const role = buf.join(' ');
    buf = [];
    gap = false;
    const id = (line.match(/simplify\.jobs\/p\/([0-9a-f-]{8,})/i) || [])[1];
    links++;
    const cut = role.indexOf(': ');
    if (cut < 1) continue;
    jobs.push({ id, title: role.slice(cut + 2), company: role.slice(0, cut), location: '', notes: [], link: 'https://simplify.jobs/p/' + id });
  }
  return jobs.length === links ? jobs : [];
}

const BOARDS = [
  { source: 'linkedin', from: /linkedin\.com/i, parse: linkedin },
  { source: 'glassdoor', from: /glassdoor\./i, parse: glassdoor },
  { source: 'indeed', from: /indeed\.com/i, parse: indeed },
  { source: 'internshala', from: /internshala\.com/i, parse: internshala },
  { source: 'unstop', from: /unstop\./i, parse: unstop },
  { source: 'swelist', from: /swelist\.com/i, parse: swelist },
];

const out = [];
const taken = new Set();
for (const item of $input.all()) {
  const mail = item.json;
  const sender = (mail.from && mail.from.text) || '';
  const board = BOARDS.find(b => b.from.test(sender));
  let jobs = [];
  if (board) { try { jobs = board.parse(mail); } catch (e) { jobs = []; } }
  if (!jobs.length) { out.push(item); continue; }
  for (const job of jobs) {
    // The same job often sits in several mails of one run, also from different boards;
    // keep the first. Later runs drop it in "Skip already seen", which uses the same key.
    const key = jobKey(board.source, job);
    if (taken.has(key)) continue;
    taken.add(key);
    const details = [job.location && 'Location: ' + job.location].concat(job.notes);
    out.push({ json: {
      id: mail.id,
      jobSource: board.source,
      jobId: job.id,
      jobKey: key,
      jobLink: job.link,
      subject: job.title + (job.company ? ' at ' + job.company : ''),
      text: details.filter(Boolean).join('. '),
      from: { text: board.source },
      date: mail.date,
    } });
  }
}
return out;
