// Shared mail renderer. tools/build_workflows.py pastes this file into the "Build mail"
// node of both workflows, so edit it here and rebuild rather than editing in n8n.
// Rules: inline styles only (mail clients drop <style>), every function is a one-line
// arrow expression, and no two curly braces may sit next to each other (n8n would read
// them as the end of the expression).
const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const url = u => /^https?:\/\//i.test(u || '') ? esc(u) : '#';
const scoreBg = n => n >= 9 ? '#0f7b4f' : n >= 7 ? '#1d4ed8' : '#6b7280';
const chip = (t, bg, fg) => '<span style="display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;line-height:18px;font-weight:600;background:' + bg + ';color:' + fg + ';margin:0 6px 4px 0;">' + esc(t) + '</span>';
const card = i => '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 12px 0;border:1px solid #e5e7eb;border-radius:10px;background:#ffffff;"><tr><td style="padding:14px 16px;">'
  + '<div style="font-size:16px;line-height:22px;font-weight:700;margin-bottom:8px;"><a href="' + url(i.link) + '" style="color:#111827;text-decoration:none;">' + esc(i.title) + '</a></div>'
  + '<div style="margin-bottom:6px;">' + chip(i.score + '/10', scoreBg(i.score), '#ffffff') + chip(i.category === 'internship' ? 'Internship' : 'Project', '#eef2ff', '#3730a3') + (i.deadline ? chip('Deadline ' + i.deadline, '#fef2f2', '#b91c1c') : '') + (i.sent_at ? chip('Already sent ' + i.sent_at, '#f3f4f6', '#4b5563') : '') + '</div>'
  + '<div style="font-size:14px;line-height:21px;color:#374151;">' + esc(i.summary) + '</div>'
  + (i.fit ? '<div style="font-size:13px;line-height:19px;color:#4b5563;margin-top:10px;padding:2px 0 2px 10px;border-left:3px solid #c7d2fe;"><b style="color:#3730a3;">Why you:</b> ' + esc(i.fit) + '</div>' : '')
  + '<div style="margin-top:12px;"><a href="' + url(i.link) + '" style="display:inline-block;padding:6px 14px;border-radius:6px;background:#4338ca;color:#ffffff;font-size:13px;font-weight:600;text-decoration:none;">Open &rarr;</a></div>'
  + '</td></tr></table>';
const byScore = list => (list || []).slice().sort((a, b) => (b.score || 0) - (a.score || 0));
const section = (title, note, items) => items.length ? '<div style="font-size:12px;letter-spacing:.06em;text-transform:uppercase;font-weight:700;color:#4338ca;margin:24px 0 2px 0;">' + esc(title) + ' &middot; ' + items.length + '</div><div style="font-size:13px;line-height:19px;color:#6b7280;margin-bottom:10px;">' + esc(note) + '</div>' + items.map(card).join('') : '';
const callout = (label, text) => text ? '<div style="margin:16px 0 0 0;padding:12px 14px;background:#ecfdf5;border:1px solid #a7f3d0;border-radius:10px;font-size:14px;line-height:21px;color:#065f46;"><b>' + esc(label) + '</b> ' + esc(text) + '</div>' : '';
const page = (heading, sub, body) => '<div style="margin:0;padding:24px 12px;background:#f3f4f6;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"><table role="presentation" align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:620px;margin:0 auto;"><tr><td style="padding:18px 20px;background:#312e81;border-radius:12px;"><div style="font-size:20px;line-height:26px;font-weight:700;color:#ffffff;">' + esc(heading) + '</div><div style="font-size:13px;line-height:19px;color:#c7d2fe;margin-top:2px;">' + esc(sub) + '</div></td></tr><tr><td style="padding:0 2px;">' + body + '<div style="font-size:12px;line-height:18px;color:#9ca3af;margin-top:18px;text-align:center;">Internship Radar &middot; rated against your resume &middot; runs on your laptop</div></td></tr></table></div>';
