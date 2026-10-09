#!/usr/bin/env python3
"""Starts a Radar run that was missed. Run every 5 minutes by radar-catchup.timer.

n8n only fires its timers while the laptop is awake, so a run whose time passed during
sleep, shutdown or before the network was up never happens by itself. This script looks
at n8n's run history and, when a run is overdue and the internet is reachable, starts it
through the workflow's local "Catch-up call" address.

  3-hourly run: overdue when no successful run has started since the last 3-hour mark.
  Daily wrap:   overdue when it is past 22:00 and no successful wrap has started since.

It waits 3 minutes after a mark (to let the normal timer go first), never starts a
workflow that is running or was tried in the last 30 minutes, and does the 3-hourly run
before the wrap so the wrap includes its results.

usage: catchup.py [--dry-run] [--force 3hourly|wrap]
"""
import datetime, glob, os, sqlite3, subprocess, sys, time, urllib.request

DB = '/home/vzux/.n8n/database.sqlite'
N8N = 'http://127.0.0.1:5678'
GRACE = datetime.timedelta(minutes=3)
BACKOFF = datetime.timedelta(minutes=30)
DRY = '--dry-run' in sys.argv
FORCE = sys.argv[sys.argv.index('--force') + 1] if '--force' in sys.argv else ''

now = datetime.datetime.now().astimezone()
JOBS = [('3hourly', 'radar3Hourly00001', 'radar-catchup', now.replace(hour=now.hour // 3 * 3, minute=0, second=0, microsecond=0)),
        ('wrap', 'radarDailyWrap001', 'radar-wrap-catchup', now.replace(hour=22, minute=0, second=0, microsecond=0))]


def utc(t):  # n8n stores run times as UTC text
    return t.astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def reachable(url):
    try:
        urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=8)
    except urllib.error.HTTPError:
        return True   # any answer from the server means the network is up
    except Exception:
        return False
    return True


db = sqlite3.connect('file:%s?mode=ro' % DB, uri=True, timeout=10)
started = False
for name, wf, path, mark in JOBS:
    if FORCE:
        due = FORCE == name
    else:
        ok = db.execute("select count(*) from execution_entity where workflowId=? and status='success' and startedAt>=?", (wf, utc(mark))).fetchone()[0]
        busy = db.execute("select count(*) from execution_entity where workflowId=? and (status in ('running','new','waiting') or startedAt>=?)",
                          (wf, utc(now - BACKOFF))).fetchone()[0]
        due = now >= mark + GRACE and not ok and not busy
        if busy:
            started = started or name == '3hourly'   # hold the wrap back while a 3-hourly run is going
    if not due:
        continue
    if name == 'wrap' and started:
        print('wrap is overdue; waiting for the 3-hourly run to finish first')
        continue
    if not reachable(N8N + '/healthz'):
        print('n8n is not answering; nothing started')
        break
    if not reachable('https://gmail.googleapis.com/'):
        print('no internet yet; will try again in 5 minutes')
        break
    print('%s run is overdue (mark %s): starting it' % (name, mark.strftime('%H:%M')))
    if not DRY:
        try:
            urllib.request.urlopen(urllib.request.Request(N8N + '/webhook/' + path, data=b'{}', method='POST',
                                                          headers={'Content-Type': 'application/json'}), timeout=20)
        except Exception as e:   # n8n still starting, or the workflow is unpublished: try again next time
            print('could not start it (%s); will try again in 5 minutes' % e)
            break
    started = True

# Mails that could not be sent earlier wait in the outbox; send them once the net is back.
OUTBOX = '/home/vzux/.n8n-files/radar/outbox'
waiting = [f for f in glob.glob(OUTBOX + '/*.json') if time.time() - os.path.getmtime(f) > 120]
if waiting and not DRY and reachable('https://gmail.googleapis.com/'):
    print('%d mail file(s) waiting in the outbox: sending' % len(waiting))
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run(['/usr/bin/python3', here + '/gmail_send.py', 'ssubarno547@gmail.com', OUTBOX])
