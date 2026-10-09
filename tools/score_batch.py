#!/usr/bin/env python3
"""Scores everything waiting in the buffer. Run by the "Ask Claude" node.

usage: score_batch.py <radar-dir> <prompts-dir>

<radar-dir>/pending/ is the buffer: each run of the 3-hourly workflow drops one JSON file
of new items there. This script scores all of it in chunks, prints the kept items as one
JSON object on stdout, and only then removes what it scored. Anything Claude could not
score stays in the buffer for the next run, so a failed call no longer loses items.
"""
import datetime, fcntl, glob, json, os, subprocess, sys, time

R, P = sys.argv[1], sys.argv[2]
CHUNK = 40          # items per Claude call
ATTEMPTS = 2        # tries per chunk inside one run
GIVE_UP_AFTER = 5   # runs an item may fail in before it is parked in failed/
TIMEOUT = 420       # seconds for one Claude call
CLAUDE = [os.environ.get('RADAR_CLAUDE', '/home/vzux/.local/bin/claude'), '-p',  # RADAR_CLAUDE: tests only
          '--model', 'haiku', '--tools', '', '--strict-mcp-config',
          '--no-session-persistence', '--output-format', 'json',
          '--system-prompt-file', P + '/score_prompt.md', '--json-schema', open(P + '/score_schema.json').read()]
PENDING, FAILED = R + '/pending', R + '/failed'


def log(*a):
    print(*a, file=sys.stderr)


def write_json(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f)
    os.replace(tmp, path)


def ask(chunk):
    """Returns the list of kept items for one chunk, or None if the call failed."""
    payload = json.dumps([{k: i.get(k, '') for k in ('id', 'source', 'author', 'text', 'timestamp')} for i in chunk])
    for attempt in range(ATTEMPTS):
        try:
            out = subprocess.run(CLAUDE, input=payload, capture_output=True, text=True, timeout=TIMEOUT, cwd=R)
            answer = json.loads(out.stdout)
            items = answer['structured_output']['items']
            if answer.get('is_error') or not isinstance(items, list):
                raise ValueError('claude reported an error')
            global tokens
            tokens += (answer.get('usage') or {}).get('output_tokens', 0)
            return items
        except Exception as e:  # timeout, usage limit, bad JSON: all mean "try again"
            log('chunk failed (attempt %d): %s' % (attempt + 1, str(e)[:200]))
            time.sleep(5)
    return None


os.makedirs(PENDING, exist_ok=True)
lock = open(R + '/.score.lock', 'w')
fcntl.flock(lock, fcntl.LOCK_EX)   # two runs at once must not score the same buffer

files = sorted(glob.glob(PENDING + '/*.json'))
items, seen, loaded = [], set(), []
for path in files:
    try:
        batch = json.load(open(path))
    except Exception as e:
        log('unreadable buffer file left in place:', path, e)
        continue
    loaded.append(path)
    for i in batch if isinstance(batch, list) else []:
        if isinstance(i, dict) and i.get('id') and (i.get('text') or '').strip() and i['id'] not in seen:
            seen.add(i['id'])
            items.append(i)

kept, retry, parked, failed_chunks, tokens = [], [], [], 0, 0
chunks = [items[n:n + CHUNK] for n in range(0, len(items), CHUNK)]
stamp = datetime.datetime.now()
for chunk in chunks:
    scored = ask(chunk)
    if scored is None:
        failed_chunks += 1
        for i in chunk:
            i['_tries'] = i.get('_tries', 0) + 1
            (parked if i['_tries'] >= GIVE_UP_AFTER else retry).append(i)
        continue
    by_id = {i['id']: i for i in chunk}
    for s in scored:
        src = by_id.get(s.get('id'))
        if not src or s.get('category') == 'skip':
            continue
        s['source'] = src.get('source', '')
        if not str(s.get('link') or '').lower().startswith('http'):
            s['link'] = src.get('link', '')
        # Items scoring 7 or more go out in this run's digest; the 22:00 wrap shows that.
        s['mailed_at'] = stamp.strftime('%H:%M') if isinstance(s.get('score'), int) and s['score'] >= 7 else ''
        kept.append(s)

# Only now touch the buffer: first save what must be retried, then drop what was read.
name = stamp.strftime('%Y%m%d-%H%M%S')
if retry:
    write_json(PENDING + '/retry-' + name + '.json', retry)
if parked:
    os.makedirs(FAILED, exist_ok=True)
    write_json(FAILED + '/' + name + '.json', parked)
for path in loaded:
    os.remove(path)

stats = {'buffered': len(items), 'kept': len(kept), 'chunks': len(chunks), 'failed_chunks': failed_chunks,
         'waiting_for_retry': len(retry), 'parked_in_failed': len(parked), 'output_tokens': tokens}
log(json.dumps(stats))
print(json.dumps({'items': kept, 'stats': stats}))
if chunks and failed_chunks == len(chunks):
    log('every Claude call failed; the items stay in the buffer for the next run')
    sys.exit(1)
