#!/usr/bin/env python3
"""Prepares the 22:00 wrap. Run by the "Write the wrap" node.

usage: wrap_batch.py <radar-dir> <prompts-dir>

Reads every file in <radar-dir>/day/ (the items the 3-hourly runs kept today) and prints
the wrap as one JSON object: {"top_pick": ..., "items": [...]}. Prints nothing if the day
folder is empty, which stops the workflow before the mail step.

Claude is only asked for the two things that need judgement: which items are the same
opportunity, and which single item is the best of the day. Everything else (dropping
expired items, choosing the section, keeping titles, summaries and links exactly as they
were scored) is done here, so the call stays small.
"""
import datetime, glob, json, os, subprocess, sys

R, P = sys.argv[1], sys.argv[2]
ATTEMPTS = 2
TIMEOUT = 300
CLAUDE = [os.environ.get('RADAR_CLAUDE', '/home/vzux/.local/bin/claude'), '-p',  # RADAR_CLAUDE: tests only
          '--model', 'haiku', '--tools', '', '--strict-mcp-config', '--no-session-persistence', '--output-format', 'json',
          '--system-prompt-file', P + '/daily_prompt.md', '--json-schema', open(P + '/daily_schema.json').read()]


def log(*a):
    print(*a, file=sys.stderr)


def day(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


today = datetime.date.today()
items, seen = [], {}
for path in sorted(glob.glob(R + '/day/*.json')):
    try:
        batch = json.load(open(path))
    except Exception as e:
        log('unreadable day file skipped:', path, e)
        continue
    for i in batch if isinstance(batch, list) else []:
        if not isinstance(i, dict) or not i.get('title'):
            continue
        d = day(i.get('deadline'))
        if d and d < today:            # deadline already past
            continue
        if i.get('id') in seen:        # same id saved twice: keep the first
            continue
        seen[i.get('id')] = True
        items.append(i)
if not items:
    sys.exit(0)

# Ask Claude about duplicates and the best item, by number, so the answer is tiny.
numbered = [{'n': n, 'title': i.get('title', ''), 'summary': i.get('summary', ''), 'score': i.get('score', 0),
             'deadline': i.get('deadline', '')} for n, i in enumerate(items, 1)]
answer, tokens = None, 0
for attempt in range(ATTEMPTS):
    try:
        out = subprocess.run(CLAUDE, input='Today is %s.\n%s' % (today.isoformat(), json.dumps(numbered)),
                             capture_output=True, text=True, timeout=TIMEOUT, cwd=R)
        raw = json.loads(out.stdout)
        if raw.get('is_error'):
            raise ValueError('claude reported an error')
        answer = raw['structured_output']
        tokens = (raw.get('usage') or {}).get('output_tokens', 0)
        break
    except Exception as e:
        log('wrap call failed (attempt %d): %s' % (attempt + 1, str(e)[:200]))

# Merge each group of duplicates into its highest-scoring member.
gone = set()
for group in (answer or {}).get('duplicates') or []:
    group = sorted({n for n in group if isinstance(n, int) and 1 <= n <= len(items) and n not in gone})
    if len(group) < 2:
        continue
    parts = [items[n - 1] for n in group]
    best = max(parts, key=lambda i: i.get('score') or 0)
    direct = [i.get('link') for i in parts if i.get('link') and 'mail.google.com' not in i['link']]
    if 'mail.google.com' in (best.get('link') or '') and direct:
        best['link'] = direct[0]       # prefer a link to the posting over a link to the mail
    times = sorted(i['mailed_at'] for i in parts if i.get('mailed_at'))
    best['mailed_at'] = times[0] if times else ''
    gone.update(n for n in group if items[n - 1] is not best)

result = []
for n, i in enumerate(items, 1):
    if n in gone:
        continue
    d = day(i.get('deadline'))
    if i.get('source') == 'swelist':
        section = 'swelist'
    elif d and (d - today).days <= 7:
        section = 'deadline'
    else:
        section = 'related' if i.get('match') == 'related' else 'direct'
    result.append({'section': section, 'category': i.get('category', 'internship'), 'score': i.get('score', 0),
                   'title': i.get('title', ''), 'summary': i.get('summary', ''), 'fit': i.get('fit', ''),
                   'deadline': i.get('deadline', ''), 'link': i.get('link', ''), 'sent_at': i.get('mailed_at', '')})

top = str((answer or {}).get('top_pick') or '').strip()
if not top:                            # Claude unavailable: the wrap still goes out
    best = max(result, key=lambda i: i['score'])
    top = '%s is the highest-scoring item today (%s/10).' % (best['title'], best['score'])
log(json.dumps({'day_items': len(items), 'merged_away': len(gone), 'in_wrap': len(result),
                'claude_answered': answer is not None, 'output_tokens': tokens}))
print(json.dumps({'top_pick': top, 'items': result}))
