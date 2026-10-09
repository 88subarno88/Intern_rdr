import json, sys, os, datetime
OUT = sys.argv[1]
P = '/home/vzux/Desktop/Internship_Radar_n8n/prompts'
R = os.environ.get('RADAR_DIR', '/home/vzux/.n8n-files/radar')  # tests point this at ~/.n8n-files/radar-test
T = os.path.dirname(os.path.abspath(__file__))
sample = json.load(open(P + '/sample_items.json'))
for _i in sample:
    _i['id'] += os.environ.get('SAMPLE_TAG', '')
    _i['timestamp'] = datetime.datetime.now().astimezone().isoformat(timespec='seconds')  # inside the fetch window

def node(name, typ, ver, params, pos, **extra):
    n = {"parameters": params, "name": name, "type": "n8n-nodes-base." + typ, "typeVersion": ver,
         "position": pos, "id": name.lower().replace(' ', '-').replace('.', '')}
    n.update(extra)
    return n

def cond(left, op_type, op, right="", single=False):
    o = {"type": op_type, "operation": op}
    if single: o["singleValue"] = True
    return {"id": "c-" + op + str(abs(hash(left)) % 9999), "leftValue": left, "rightValue": right, "operator": o}

def filt(name, conds, pos):
    return node(name, "filter", 2.2, {"conditions": {"options": {"caseSensitive": True, "leftValue": "",
                "typeValidation": "loose", "version": 2}, "conditions": conds, "combinator": "and"},
                "looseTypeValidation": True, "options": {}}, pos)

def norm(name, fields, pos):
    a = [{"id": "f%d" % i, "name": k, "type": "string", "value": v} for i, (k, v) in enumerate(fields.items())]
    return node(name, "set", 3.4, {"mode": "manual", "assignments": {"assignments": a},
                "includeOtherFields": False, "options": {}}, pos)

def link(conn, a, b, idx=0):
    conn.setdefault(a, {"main": [[]]})["main"][0].append({"node": b, "type": "main", "index": idx})

KEYWORDS = "={{ ['linkedin', 'glassdoor', 'indeed', 'internshala', 'unstop', 'swelist'].includes($json.source) || ($json.source === 'discord' && ($json.text || '').trim().length > 20) || /intern|hiring|stipend|hackathon|fellowship|open.?source|apply|launch|released|show hn/i.test($json.text || '') }}"
DISCORD_FIELDS = {"id": "=discord-{{ $json.id }}", "source": "discord",
                  "author": "={{ $json.author?.username || 'discord' }}",
                  "text": "={{ (($json.content || '') + ' ' + ($json.embeds || []).map(e => (e.title || '') + ' ' + (e.description || '') + ' ' + (e.url || '')).join(' ')).replace(/\\s+/g, ' ').trim().slice(0, 1500) }}",
                  "link": "={{ $json.message_reference?.guild_id ? 'https://discord.com/channels/' + $json.message_reference.guild_id + '/' + $json.message_reference.channel_id + '/' + $json.message_reference.message_id : 'https://discord.com/channels/@me' }}",
                  "timestamp": "={{ $json.timestamp }}"}
# Gmail is reached with an app password (see tools/gmail_common.py), not through n8n's Gmail node.
# The search terms live in tools/gmail_search.txt.
ADDRESS = 'ssubarno547@gmail.com'
FETCH_CMD = ("=/usr/bin/python3 %s/gmail_fetch.py %s {{ $('Fetch window').first().json.after }} %s/inbox.json" % (T, ADDRESS, R))
SEND_CMD = '/usr/bin/python3 %s/gmail_send.py %s %s/outbox' % (T, ADDRESS, R)
RSS_FIELDS = {"id": "=rss-{{ $json.guid || $json.link }}", "source": "rss",
              "author": "={{ $json.creator || 'rss' }}",
              "text": "={{ (($json.title || '') + ' - ' + ($json.contentSnippet || '')).slice(0, 1500) }}",
              "link": "={{ $json.link }}", "timestamp": "={{ $json.isoDate }}"}
# Items made by "Split job mails" carry jobSource/jobId/jobLink; ordinary mails do not.
GMAIL_FIELDS = {"id": "={{ $json.jobKey ? 'job-' + $json.jobKey : 'gmail-' + $json.id }}",
                "source": "={{ $json.jobSource || 'gmail' }}",
                "author": "={{ $json.from?.text || '' }}",
                "text": "={{ (($json.subject || '') + ' - ' + ($json.text || ($json.html || '').replace(/<[^>]+>/g, ' '))).replace(/\\s+/g, ' ').slice(0, 1500) }}",
                "link": "={{ $json.jobLink || 'https://mail.google.com/mail/u/0/#all/' + $json.id }}", "timestamp": "={{ $json.date }}"}
FETCH_WINDOW = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fetch_window.js')).read()
RECENT = "={{ isNaN(new Date($json.timestamp).getTime()) || new Date($json.timestamp).getTime() >= $('Fetch window').first().json.sinceMs }}"
JOB_MAIL_SPLIT = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'job_mail_split.js')).read()
# Scores everything in the buffer (pending/) in chunks and prints the kept items as JSON.
SCORE_CMD = '/usr/bin/python3 %s/score_batch.py %s %s' % (T, R, P)
# Builds the wrap from the day folder; prints nothing when the folder is empty.
WRAP_CMD = '/usr/bin/python3 %s/wrap_batch.py %s %s' % (T, R, P)
ARCHIVE_CMD = 'cd %s && mkdir -p sent && mv day/*.json sent/' % R
_TEMPLATE = ' '.join(l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mail_template.js')).read().splitlines()
                     if l.strip() and not l.strip().startswith('//'))
assert '{{' not in _TEMPLATE and '}}' not in _TEMPLATE, 'mail_template.js: adjacent curly braces break n8n expressions'
def _expr(body): return "={{ (() => { " + _TEMPLATE + " " + body + " })() }}"
SWE_NOTE = 'Roles from the SWE List daily mail, graded against your resume.'
MAIL_HTML = _expr("const sw = byScore($json.top.filter(i => i.source === 'swelist')); const rest = $json.top.filter(i => i.source !== 'swelist'); "
                  "const d = byScore(rest.filter(i => i.match !== 'related')); const r = byScore(rest.filter(i => i.match === 'related')); "
                  "return page('Internship Radar', $now.toFormat('ccc d LLL, HH:mm') + ' \u00b7 ' + $json.top.length + ' new', "
                  "section('Matches your resume', 'Overlaps what you have already built or worked with.', d) + "
                  "section('Related and worth a look', 'Not on your resume, but a strong next step.', r) + "
                  "section('From SWE List', '" + SWE_NOTE + "', sw));")
MAIL_SUBJECT = "={{ '[Radar] ' + $json.top.length + ' new: ' + ($json.top.slice().sort((a, b) => b.score - a.score)[0].title || '').slice(0, 70) }}"
DAILY_HTML = _expr("const o = JSON.parse($json.stdout); const it = o.items || []; const pick = s => byScore(it.filter(i => i.section === s)); "
                   "return page('Daily wrap', $now.toFormat('cccc d LLLL') + ' \u00b7 ' + it.length + ' kept today', "
                   "callout('If you only do one thing today:', o.top_pick) + "
                   "section('Deadlines in the next 7 days', 'Closing soon, act on these first.', pick('deadline')) + "
                   "section('Matches your resume', 'Overlaps what you have already built or worked with.', pick('direct')) + "
                   "section('Related and worth a look', 'Not on your resume, but a strong next step.', pick('related')) + "
                   "section('From SWE List', '" + SWE_NOTE + "', pick('swelist')));")

def mail_out(N, C, source, kind, send_name, x, y):
    """Three nodes that mail what `source` built: write it to the outbox, then send the outbox.
    A mail that cannot be sent stays in the outbox and goes out with the next send."""
    to_json, save = kind + " to JSON", "Save to outbox"
    N += [node(to_json, "convertToFile", 1.1, {"operation": "toJson", "mode": "once", "binaryPropertyName": "data", "options": {}}, [x, y]),
          node(save, "readWriteFile", 1, {"operation": "write",
               "fileName": "=" + R + "/outbox/{{ $now.toFormat('yyyyLLdd-HHmmss') }}-" + kind.lower() + ".json", "dataPropertyName": "data", "options": {}}, [x + 220, y]),
          node(send_name, "executeCommand", 1, {"command": SEND_CMD}, [x + 440, y], retryOnFail=True, maxTries=2, waitBetweenTries=5000)]
    link(C, source, to_json); link(C, to_json, save); link(C, save, send_name)

def catchup_hook(path, pos):
    return node("Catch-up call", "webhook", 2, {"httpMethod": "POST", "path": path, "options": {}}, pos, webhookId=path)

def workflow_a(test):
    N, C = [], {}
    if test:
        N += [node("Start", "manualTrigger", 1, {}, [0, 200]),
              node("Empty branch", "set", 3.4, {"mode": "raw", "jsonOutput": json.dumps({"text": "nothing"})}, [220, 0]),
              filt("Drop everything", [cond("={{ false }}", "boolean", "true", single=True)], [440, 0]),
              node("Sample items", "set", 3.4, {"mode": "raw", "jsonOutput": json.dumps({"items": sample})}, [220, 200]),
              node("Split samples", "splitOut", 1, {"fieldToSplitOut": "items", "options": {}}, [440, 200])]
        link(C, "Start", "Empty branch"); link(C, "Empty branch", "Drop everything"); link(C, "Drop everything", "Merge", 0)
        link(C, "Start", "Sample items"); link(C, "Sample items", "Split samples"); link(C, "Split samples", "Merge", 1)
        trig = "Start"
    else:
        N.append(node("Every 3 hours", "scheduleTrigger", 1.2, {"rule": {"interval": [{"field": "cronExpression", "expression": "0 */3 * * *"}]}}, [-220, 200]))
        trig = "Every 3 hours"
        # Second way in: tools/catchup.py (radar-catchup.timer) calls this local address when a timed run was missed.
        N.append(catchup_hook("radar-catchup", [-220, 400]))
        link(C, "Catch-up call", "Fetch window")
    N.append(node("Fetch window", "code", 2, {"mode": "runOnceForAllItems", "jsCode": FETCH_WINDOW}, [0, 200]))
    link(C, trig, "Fetch window")
    if test:
        for k in ("Empty branch", "Sample items"): C["Start"]["main"][0] = [c for c in C["Start"]["main"][0] if c["node"] != k]; link(C, "Fetch window", k)
    trig = "Fetch window"
    if not test:
        N += [node("Gmail fetch", "executeCommand", 1, {"command": FETCH_CMD}, [220, -360], retryOnFail=True, maxTries=2, waitBetweenTries=5000),
              node("Read fetched mail", "readWriteFile", 1, {"operation": "read", "fileSelector": R + "/inbox.json", "options": {}}, [440, -360]),
              node("Mail file to list", "extractFromFile", 1, {"operation": "fromJson", "binaryPropertyName": "data", "destinationKey": "mails", "options": {}}, [660, -360]),
              node("One item per mail", "splitOut", 1, {"fieldToSplitOut": "mails", "options": {}}, [880, -360]),
              node("Split job mails", "code", 2, {"mode": "runOnceForAllItems", "jsCode": JOB_MAIL_SPLIT}, [330, -150]),
              norm("Shape Gmail", GMAIL_FIELDS, [440, 0]),
              node("RSS Reddit internships", "rssFeedRead", 1.1, {"url": "https://www.reddit.com/r/developersIndia/search.rss?q=internship&restrict_sr=1&sort=new", "options": {}}, [220, 200], onError="continueRegularOutput"),
              norm("Shape RSS 1", RSS_FIELDS, [440, 200])]
        link(C, trig, "Gmail fetch"); link(C, "Gmail fetch", "Read fetched mail"); link(C, "Read fetched mail", "Mail file to list")
        link(C, "Mail file to list", "One item per mail"); link(C, "One item per mail", "Split job mails"); link(C, "Split job mails", "Shape Gmail"); link(C, "Shape Gmail", "Merge", 0)
        link(C, trig, "RSS Reddit internships"); link(C, "RSS Reddit internships", "Shape RSS 1"); link(C, "Shape RSS 1", "Merge", 1)
    N += [node("RSS Show HN", "rssFeedRead", 1.1, {"url": os.environ.get("RSS2", "https://news.ycombinator.com/showrss"), "options": {}}, [220, 400], onError="continueRegularOutput"),
          norm("Shape RSS 2", RSS_FIELDS, [440, 400])]
    link(C, trig, "RSS Show HN"); link(C, "RSS Show HN", "Shape RSS 2"); link(C, "Shape RSS 2", "Merge", 2)
    dn = node("Discord fetch", "discord", 2, {"authentication": "botToken", "resource": "message", "operation": "getAll",
              "guildId": {"__rl": True, "mode": "list", "value": ""}, "channelId": {"__rl": True, "mode": "list", "value": ""},
              "returnAll": False, "limit": 50, "options": {"simplify": False}}, [220, 600], onError="continueRegularOutput")
    if os.environ.get("DISCORD_MODE", "disabled") == "disabled": dn["disabled"] = True
    N += [dn, norm("Shape Discord", DISCORD_FIELDS, [440, 600])]
    link(C, trig, "Discord fetch"); link(C, "Discord fetch", "Shape Discord"); link(C, "Shape Discord", "Merge", 3)
    N += [node("Merge", "merge", 3.2, {"mode": "append", "numberInputs": 4}, [660, 200]),
          # alwaysOutputData: with nothing new these three pass one empty item on, so "Ask Claude"
          # still runs and retries whatever is waiting in the buffer. The script ignores the empty item.
          dict(filt("Only recent", [cond(RECENT, "boolean", "true", single=True)], [770, 40]), alwaysOutputData=True),
          dict(filt("Keyword filter", [cond(KEYWORDS, "boolean", "true", single=True)], [880, 200]), alwaysOutputData=True),
          node("Skip already seen", "removeDuplicates", 2, {"operation": "removeItemsSeenInPreviousExecutions",
               "logic": "removeItemsWithAlreadySeenKeyValues", "dedupeValue": "={{ $json.id || 'nothing-new' }}", "options": {}}, [1100, 200], alwaysOutputData=True),
          node("Items to JSON", "convertToFile", 1.1, {"operation": "toJson", "mode": "once", "binaryPropertyName": "data", "options": {}}, [1320, 200]),
          node("Save to buffer", "readWriteFile", 1, {"operation": "write",
               "fileName": "=" + R + "/pending/{{ $now.toFormat('yyyyLLdd-HHmmss') }}.json", "dataPropertyName": "data", "options": {}}, [1540, 200]),
          node("Ask Claude", "executeCommand", 1, {"command": SCORE_CMD}, [1760, 200], retryOnFail=True, maxTries=2, waitBetweenTries=5000),
          node("Parse answer", "set", 3.4, {"mode": "manual", "assignments": {"assignments": [{"id": "a1", "name": "scored", "type": "array",
               "value": "={{ JSON.parse($json.stdout).items }}"}]}, "options": {}}, [1980, 200]),
          node("Split scored", "splitOut", 1, {"fieldToSplitOut": "scored", "options": {}}, [2200, 200]),
          filt("Keep relevant", [cond("={{ $json.category }}", "string", "notEquals", "skip"), cond("={{ $json.score }}", "number", "gte", 5)], [2420, 200]),
          node("Day batch to JSON", "convertToFile", 1.1, {"operation": "toJson", "mode": "once", "binaryPropertyName": "data", "options": {}}, [2640, 400]),
          node("Save for daily wrap", "readWriteFile", 1, {"operation": "write",
               "fileName": "=" + R + "/day/{{ $now.toFormat('yyyyLLdd-HHmmss') }}.json", "dataPropertyName": "data", "options": {}}, [2860, 400]),
          filt("Score 7 or more", [cond("={{ $json.score }}", "number", "gte", 7)], [2640, 100]),
          node("Collect top", "aggregate", 1, {"aggregate": "aggregateAllItemData", "destinationFieldName": "top", "options": {}}, [2860, 100]),
          node("Build mail", "set", 3.4, {"mode": "manual", "assignments": {"assignments": [
               {"id": "m1", "name": "subject", "type": "string", "value": MAIL_SUBJECT},
               {"id": "m2", "name": "html", "type": "string", "value": MAIL_HTML}]}, "includeOtherFields": False, "options": {}}, [3080, 100])]
    chain = ["Merge", "Only recent", "Keyword filter", "Skip already seen", "Items to JSON", "Save to buffer", "Ask Claude", "Parse answer", "Split scored", "Keep relevant"]
    for a, b in zip(chain, chain[1:]): link(C, a, b)
    link(C, "Keep relevant", "Day batch to JSON"); link(C, "Day batch to JSON", "Save for daily wrap")
    link(C, "Keep relevant", "Score 7 or more"); link(C, "Score 7 or more", "Collect top"); link(C, "Collect top", "Build mail")
    if not test:
        mail_out(N, C, "Build mail", "Digest", "Send digest", 3300, 100)
    return N, C

def workflow_b(test):
    N, C = [], {}
    trig = "Start" if test else "Every day 22.00"
    N.append(node("Start", "manualTrigger", 1, {}, [0, 0]) if test else
             node(trig, "scheduleTrigger", 1.2, {"rule": {"interval": [{"field": "cronExpression", "expression": "0 22 * * *"}]}}, [0, 0]))
    N += [node("Write the wrap", "executeCommand", 1, {"command": WRAP_CMD}, [220, 0], retryOnFail=True, maxTries=3, waitBetweenTries=5000),
          filt("Anything to send", [cond("={{ ($json.stdout || '').trim().length }}", "number", "gt", 0)], [440, 0]),
          node("Build mail", "set", 3.4, {"mode": "manual", "assignments": {"assignments": [
               {"id": "m1", "name": "subject", "type": "string", "value": "=[Radar] Daily wrap - {{ $now.toFormat('dd LLL') }}"},
               {"id": "m2", "name": "html", "type": "string", "value": DAILY_HTML}]}, "includeOtherFields": False, "options": {}}, [660, 0])]
    chain = [trig, "Write the wrap", "Anything to send", "Build mail"]
    for a, b in zip(chain, chain[1:]): link(C, a, b)
    if not test:
        mail_out(N, C, "Build mail", "Wrap", "Send wrap", 880, 0)
        N.append(node("Archive today", "executeCommand", 1, {"command": ARCHIVE_CMD}, [1540, 0])); link(C, "Send wrap", "Archive today")
    if not test:
        N.append(catchup_hook("radar-wrap-catchup", [0, 200])); link(C, "Catch-up call", "Write the wrap")
    return N, C

def workflow_alert():
    """Mails a short note when a published Radar workflow fails. "Test alert" sends a sample."""
    html = ("={{ (() => { const e = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); "
            "const x = $json.execution || 0; const err = x.error || 0; const w = $json.workflow || 0; "
            "return '<div style=\"font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:14px;line-height:21px;color:#111827;\">' "
            "+ '<p><b>' + e(w.name || 'Test alert') + '</b> did not finish.</p>' "
            "+ '<p>Step that failed: ' + e(x.lastNodeExecuted || 'none, this is a test') + '<br>Error: ' + e(err.message || 'none, this is a test') + '</p>' "
            "+ '<p>Items waiting to be scored stay in the buffer and are retried on the next run, so nothing is lost. "
            "If the same alert keeps coming, open the run and look at the red step.</p>' "
            "+ (x.url ? '<p><a href=\"' + e(x.url) + '\">Open the failed run in n8n</a></p>' : '') + '</div>'; })() }}")
    N = [node("On failure", "errorTrigger", 1, {}, [0, 0]),
         node("Test alert", "manualTrigger", 1, {}, [0, 200]),
         node("Build alert", "set", 3.4, {"mode": "manual", "assignments": {"assignments": [
              {"id": "m1", "name": "subject", "type": "string", "value": "=[Radar] Run failed: {{ $json.workflow?.name || 'test alert' }}"},
              {"id": "m2", "name": "html", "type": "string", "value": html}]}, "includeOtherFields": False, "options": {}}, [220, 100])]
    C = {}
    link(C, "On failure", "Build alert"); link(C, "Test alert", "Build alert")
    mail_out(N, C, "Build alert", "Alert", "Send alert", 440, 100)
    return N, C

ALERT_ID = "radarFailAlert001"
def wf(id_, name, nc, alert=False):
    settings = {"executionOrder": "v1", "timezone": "Asia/Kolkata"}
    if alert: settings["errorWorkflow"] = ALERT_ID
    return {"id": id_, "name": name, "nodes": nc[0], "connections": nc[1], "active": False, "settings": settings}

json.dump(wf("radarSelfTest0001", "Radar - self test (no Gmail)", workflow_a(True)), open(OUT + '/test_a.json', 'w'), indent=1)
json.dump(wf("radarSelfTest0001", "Radar - self test (no Gmail)", workflow_b(True)), open(OUT + '/test_b.json', 'w'), indent=1)
json.dump(wf("radar3Hourly00001", "Radar - 3 hourly", workflow_a(False), alert=True), open(OUT + '/radar_3_hourly.json', 'w'), indent=1)
json.dump(wf("radarDailyWrap001", "Radar - daily wrap", workflow_b(False), alert=True), open(OUT + '/radar_daily_wrap.json', 'w'), indent=1)
json.dump(wf(ALERT_ID, "Radar - failure alert", workflow_alert()), open(OUT + '/radar_failure_alert.json', 'w'), indent=1)
print("built")
