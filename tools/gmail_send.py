#!/usr/bin/env python3
"""Sends every mail waiting in the outbox. Run by the "Send ..." nodes and by catchup.py.

usage: gmail_send.py <address> <outbox-dir>

Each file in the outbox is JSON holding one mail, or a list of mails, with "subject" and
"html". Every mail goes from <address> to <address> through Gmail's SMTP server. A file
is deleted only after its mails were accepted, so a mail that could not be sent stays in
the outbox and goes out the next time this runs. Exits with an error if anything is left.
"""
import email.message, email.utils, glob, json, os, re, smtplib, sys
from gmail_common import password

ADDRESS, OUTBOX = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(OUTBOX + '/*.json'))
if not files:
    print('outbox empty')
    sys.exit(0)

sent, left = 0, 0
try:
    smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=60)
    smtp.login(ADDRESS, password())
except Exception as e:
    sys.exit('could not sign in to Gmail to send (%s); %d mail file(s) stay in the outbox' % (e, len(files)))
for path in files:
    try:
        mails = json.load(open(path))
        for m in mails if isinstance(mails, list) else [mails]:
            if not isinstance(m, dict) or not m.get('html'):
                continue
            msg = email.message.EmailMessage()
            msg['From'] = msg['To'] = ADDRESS
            msg['Subject'] = str(m.get('subject') or '[Radar]')
            msg['Date'] = email.utils.formatdate(localtime=True)
            msg['Message-ID'] = email.utils.make_msgid(domain='radar.local')
            msg.set_content(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', m['html'])).strip())   # plain fallback
            msg.add_alternative(m['html'], subtype='html')
            smtp.send_message(msg)
            sent += 1
        os.remove(path)
    except Exception as e:
        left += 1
        print('not sent, left in the outbox: %s (%s)' % (os.path.basename(path), e), file=sys.stderr)
smtp.quit()
print('sent %d mail(s)' % sent)
if left:
    sys.exit(1)
