#!/usr/bin/env python3
"""Fetches matching mails from Gmail over IMAP. Run by the "Gmail fetch" node.

usage: gmail_fetch.py <address> <after-epoch-seconds> <output-file>

Searches all mail with Gmail's own search syntax: "after:<epoch>" plus the terms in
gmail_search.txt. Writes the mails to <output-file> as a JSON array, one object per mail
with id, from.text, subject, text, html and date, and prints how many it found. The id
is Gmail's own message id, the same one the mail's web address uses. The mailbox is
opened read-only, so nothing is marked as read or changed.

The raw mails are parsed by mail_parse.js (n8n's own mail parser). If that cannot run,
Python's parser is used instead: mails without a plain-text part then have empty text,
which only means such job mails are scored whole and not split.
"""
import base64, datetime, email, email.policy, email.utils, imaplib, json, os, re, subprocess, sys
from gmail_common import password

ADDRESS, AFTER, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
NODE = '/home/vzux/.nvm/versions/node/v24.12.0/bin/node'
QUERY = 'after:%d %s' % (AFTER, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gmail_search.txt')).read().strip())


def part(msg, kind):
    body = msg.get_body(preferencelist=(kind,))
    if body is None:
        return ''
    try:
        return body.get_content()
    except Exception:   # odd or mislabelled charset
        return (body.get_payload(decode=True) or b'').decode('utf-8', 'replace')


def when(msg):
    try:
        t = email.utils.parsedate_to_datetime(msg['Date'])
        if t.tzinfo is None:
            t = t.replace(tzinfo=datetime.timezone.utc)
        return t.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    except Exception:
        return ''


imap = imaplib.IMAP4_SSL('imap.gmail.com', timeout=60)
imap.login(ADDRESS, password())
# "All Mail" has a different name in other languages; find it by its \All flag.
box = '"[Gmail]/All Mail"'
for line in imap.list()[1]:
    line = line.decode('utf-8', 'replace')
    if '\\All' in line:
        box = '"%s"' % line.rsplit(' "', 1)[1].rstrip('"')
imap.select(box, readonly=True)
quoted = '"%s"' % QUERY.replace('\\', '\\\\').replace('"', '\\"')
uids = imap.uid('SEARCH', 'X-GM-RAW', quoted)[1][0].split()

mails, raws = [], []
for uid in uids:
    data = imap.uid('FETCH', uid, '(X-GM-MSGID BODY.PEEK[])')[1]
    head = b' '.join(p[0] if isinstance(p, tuple) else p for p in data if p)
    raw = next(p[1] for p in data if isinstance(p, tuple))
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    gid = '%x' % int(re.search(rb'X-GM-MSGID (\d+)', head).group(1))
    raws.append({'id': gid, 'raw': base64.b64encode(raw).decode()})
    mails.append({'id': gid,
                  'from': {'text': str(msg['From'] or '')}, 'subject': str(msg['Subject'] or ''),
                  'text': part(msg, 'plain'), 'html': part(msg, 'html'), 'date': when(msg)})
imap.logout()

tmp, rawfile = OUT + '.tmp', OUT + '.raw'
try:
    with open(rawfile, 'w') as f:
        json.dump(raws, f)
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([NODE, here + '/mail_parse.js', rawfile, tmp], check=True, timeout=300)
    assert len(json.load(open(tmp))) == len(mails)
except Exception as e:
    print('mail_parse.js did not run (%s); using the built-in parser' % e, file=sys.stderr)
    with open(tmp, 'w') as f:
        json.dump(mails, f)
finally:
    if os.path.exists(rawfile):
        os.remove(rawfile)
os.replace(tmp, OUT)
print(len(mails))
