# Progress log

Last updated: 2026-10-09, 23:55 IST. Read this first when picking the project up again.

## Where things stand

| Part | State |
|---|---|
| n8n 2.42.4, background service on <http://localhost:5678> | Running |
| `Radar - 3 hourly` | Published. The 00:00 run on 9 Oct fired by itself and succeeded |
| `Radar - daily wrap` | Published. Ran once by hand on 8 Oct and mailed a wrap; its 22:00 timer has not fired yet |
| Gmail (read + send) | Connected as credential "Gmail account" |
| Resume-based rating and two-section mail | In place; tested on samples, no real two-section mail seen yet |
| Styled mail layout (cards, score chips, deadline chips) | In place in both workflows; previews in `previews/`, no real styled mail seen yet |
| Job mails (LinkedIn, Glassdoor, Indeed, Internshala, Unstop, SWE List) | Pulled in by the Gmail search and split into one item per job by **Split job mails**. SWE List roles get their own mail section |
| Buffer + chunked scoring | New items wait in `~/.n8n-files/radar/pending/`; `tools/score_batch.py` scores them 40 at a time and retries failures on the next run |
| Start at boot | On (`loginctl enable-linger vzux`) |
| Missed-run watchdog | `radar-catchup.timer` runs `tools/catchup.py` every 5 minutes; a forced catch-up through it succeeded on 9 Oct |
| `Radar - failure alert` | Published. Test alert mailed on 9 Oct; a real failure has not happened yet |
| Gmail login | App password in `~/.config/radar/gmail_app_password`; fetch over IMAP, send through an outbox. No weekly re-login any more |
| Discord branch | In the workflow, **switched off**. Setup is half done (see below) |
| Twitter/X | Deliberately not connected (reading tweets needs a paid API) |

## Discord: exactly where you stopped

Done:
- Created Discord server `myradar` with text channel `#text-radar`.

Not done yet, in this order (full steps in `02_setup.md`, section E):
1. In other servers, open announcement channels (megaphone icon) → **Follow** → send to
   `myradar` / `#text-radar`. Optional test: type a fake internship post in `#text-radar`.
2. Create a bot at <https://discord.com/developers/applications>: turn on
   **Message Content Intent**, copy the token, invite it to `myradar` with
   **View Channels** + **Read Message History**.
3. In n8n, open `Radar - 3 hourly` → **Discord fetch**: create a **Discord Bot API**
   credential, pick server `myradar` and channel `#text-radar`, **Execute step**.
4. Switch **Discord fetch** on (it is greyed out now), **Execute workflow**, **Publish**.

The Discord field mapping in **Shape Discord** has not been checked against real
messages. After step 3, look at the output and compare with `03_workflow_3hourly.md`.

## Other open items

- **LinkedIn alerts.** Create the job alerts on LinkedIn (search → **Set alert** → daily
  email). Job-recommendation mails already arrive; alert mails
  (`jobalerts-noreply@linkedin.com`) have not been seen yet, so check the first one is
  split. If it is not, it is still scored as one whole mail, nothing is lost.
- **Bigger Claude calls.** Splitting means roughly 100 or more new jobs a day reach
  Claude where about 20 mails did before. The first run after the change is the largest.
  If the Pro limit starts to bite, drop obviously senior titles in
  `tools/job_mail_split.js` before they are scored.
- **Old Gmail login can be removed.** Once the new setup has run for a few days: remove
  the app's access at <https://myaccount.google.com/permissions>, delete the Google
  Cloud project `n8ninternship` and the "Gmail account" credential in n8n.
- **Reddit feed** (r/developersIndia search) produced nothing useful in testing. Replace
  its URL if it stays empty for a week.
- **Leftover test workflow** `Radar - Claude step test` can be deleted in n8n.
  `Radar - self test (no Gmail)` is worth keeping.
- **A failed Claude call drops that batch**, because items are marked as seen before
  scoring. Not fixed; see `06_limits_and_fixes.md`.

## What was done, in order

8 Oct 2026
1. Planned the system: n8n for timing/fetching/mailing, `claude -p` for scoring so the
   Claude Pro login is used and no API key is bought. Cost ₹0.
2. Wrote this guide folder and the prompts. Tested the Claude command on samples.
3. Installed n8n 2.42.4 under Node v24.12.0 (nvm). The newest release failed to install
   because of an upstream dependency published out of order; installed the previous one
   with `--before=2026-10-07T12:00:00Z`.
4. Set it up as a systemd user service, local-only, Execute Command node enabled.
   The old n8n data from May was upgraded; backup at `~/.n8n.backup-2026-10-08`.
5. Built both workflows with `tools/build_workflows.py`, imported them, and tested the
   whole chain with live RSS through `Radar - self test (no Gmail)`.
6. You created the Google OAuth client, connected Gmail, ran both workflows by hand
   (digest and wrap mails arrived) and published both.
7. Loaded the resume (`~/Downloads/RESUME (1).pdf`) into `prompts/score_prompt.md`.
   Items now get `match` (direct / related / none), `score` and `fit`; mails have the
   sections "Matches your resume" and "Not on your resume, but related and worth a look".

9 Oct 2026
8. Confirmed the 00:00 scheduled run fired and succeeded.
9. Added the Discord branch (**Discord fetch**, **Shape Discord**, 4th Merge input;
   Discord items bypass the keyword filter). Left **Discord fetch** switched off because
   an enabled Discord node without a credential fails the entire run.
10. You created the `myradar` server and `#text-radar` channel.
11. Added the mail formatter: `tools/mail_template.js` is pasted into the **Build mail**
    node of both workflows by `tools/build_workflows.py`. The daily wrap changed with it:
    Claude now returns structured data (`prompts/daily_schema.json`) and n8n does the
    layout, where before Claude wrote the HTML itself. Old prompt kept as
    `prompts/daily_prompt.before-formatter.md`.

12. Machine was off for the 12:00 and 18:00 runs. A manual run at 19:51 succeeded but
    sent no mail: nothing scored 7 or more (all of today's runs topped out at 6).
13. LinkedIn: widened the Gmail search with three `from:` terms for LinkedIn job mails,
    added the **Split LinkedIn jobs** Code node (`tools/linkedin_split.js`) between
    **Gmail fetch** and **Shape Gmail**, let `linkedin` items past the keyword filter,
    and told the scoring prompt how to read them. Checked inside n8n on the 21 mails of
    the 19:51 run (one LinkedIn mail became 4 jobs) and with one Claude call. Export of
    the live workflow from before the change (credentials attached):
    `workflows/live_backup_2026-10-09_before_linkedin.json`.

14. Extended the splitter to Glassdoor, Indeed and Internshala and renamed the node to
    **Split job mails** (`tools/job_mail_split.js`, which replaces `linkedin_split.js`).
    On the 21 mails of the 19:51 run: 12 job mails became 114 separate jobs, 9 other
    mails passed through whole. One Claude call scored all 124 items in 139 seconds
    (about 39,000 output tokens): 45 kept, 5 scored 7 or more.

15. Repeats across boards: job ids are now `job-<company>--<title>` with no board in
    them, so one job from two boards is scored and mailed once. Checked with a LinkedIn
    and a Glassdoor copy of the same job (one survived). Today's 114 real jobs contained
    no such repeat.
16. Fetch window: new **Fetch window** node and **Only recent** filter. A run looks back
    3 h 5 min, or to the previous timed run if that was longer ago (max 24 h). Gmail
    search changed from `newer_than:1d` to `after:<window start>`. Self-test run in n8n:
    window correct, 35 fetched items cut to 7 recent ones, rest of the pipeline fine.
    Not yet seen: a timed run of the live workflow with these changes.

17. Built the nine improvements in one go:
    - Buffer (`pending/`) and `tools/score_batch.py`: scoring in chunks of 40, items
      removed from the buffer only once scored, failed chunks retried next run.
    - Leaner answers from Claude: only kept items come back, links are re-attached by
      the script. About 125 output tokens per item, against about 310 before.
    - Gmail fetch has no 50-mail cap any more.
    - Unstop and SWE List mails are split. SWE List roles have source `swelist` and a
      **From SWE List** section in both mails.
    - **When n8n starts** trigger: a catch-up run one minute after n8n starts.
    - `Radar - failure alert` workflow, set as the error workflow of both others.
    - The wrap tags entries already mailed in a 3-hourly digest ("Already sent HH:MM").
    - `oauth_pages/` and `07_gmail_login_fix.md` for the permanent Gmail login.
    Tested in a sandbox folder (`~/.n8n-files/radar-test/`): full pipeline, a run with
    nothing new, a forced Claude failure (items stayed in the buffer), 185 real items in
    5 chunks (146 s, 85 kept), and a wrap of those 85 (124 s, about 28,000 output tokens).
    The live workflows are now generated wholesale from `tools/build_workflows.py`
    (credentials copied over by node name); backups of the previous live versions are
    `workflows/live_backup_2026-10-09_2040_*.json`.
    Note: you ran the daily wrap by hand at 19:54, which mailed and archived the day's
    items up to then.

18. Slimmed the daily wrap: **Write the wrap** now runs `tools/wrap_batch.py`. Claude
    only returns duplicate groups and the top pick; the script does expiry, sections and
    merging and keeps the scored text as it is. Sandbox test on 86 items: 7 seconds and
    about 1,000 output tokens, against 124 seconds and about 28,000 before. Old prompt
    and schema kept as `prompts/daily_prompt.before-slim.md` and
    `daily_schema.before-slim.json`. First live run: the 22:00 wrap on 9 Oct.

19. The 21:00 run and the wrap (at 22:25, late after sleep) both succeeded on the new
    setup.
20. Start at boot and catch-up after sleep: enabled linger; added `tools/catchup.py`
    with `~/.config/systemd/user/radar-catchup.{service,timer}`; both workflows got a
    **Catch-up call** webhook (`/webhook/radar-catchup`, `/webhook/radar-wrap-catchup`,
    reachable from this machine only). The **When n8n starts** trigger was removed: the
    watchdog replaces it, waits for the internet, and does not fire on every restart.
    Not yet seen: a real catch-up after an actual sleep or reboot.

21. Gmail moved from the Google OAuth app to an app password, so nothing has to be
    published and the login no longer expires. New: `tools/gmail_fetch.py` (IMAP, same
    search, same ids; parsed by `tools/mail_parse.js` with n8n's own mail parser, so the
    output matched the old login exactly on 21 saved mails), `tools/gmail_send.py` and
    the outbox folder. All three workflows switched; no n8n Gmail node is left. The first
    app password was exposed in a screenshot and replaced. Old OAuth versions:
    `workflows/live_backup_2026-10-09_2345_oauth_*.json`.

22. Glassdoor: the shortened link (`/job-listing/?jl=<n>`) opened Glassdoor's security
    block page on the phone, so items now keep the exact link from the mail. Items scored
    before 00:10 on 10 Oct still carry the short link.

## Technical notes for whoever edits this next

Paths
- Buffer of unscored items: `~/.n8n-files/radar/pending/`; given-up items: `failed/`
- Sandbox for tests: `~/.n8n-files/radar-test/` (build with `RADAR_DIR=$HOME/.n8n-files/radar-test`)
- Guide, prompts, tools: `~/Desktop/Internship_Radar_n8n/`
- n8n data: `~/.n8n/` (SQLite). Working files: `~/.n8n-files/radar/` (`items.json`,
  `day/` = batches waiting for the wrap, `sent/` = archived batches)
- Service file: `~/.config/systemd/user/n8n.service`; watchdog: `radar-catchup.service` and `.timer` next to it
- Claude binary used by n8n: `/home/vzux/.local/bin/claude`

Workflow ids
- `radarFailAlert001` = Radar - failure alert (its **Test alert** trigger mails a sample)
- `radar3Hourly00001` = Radar - 3 hourly
- `radarDailyWrap001` = Radar - daily wrap
- `radarSelfTest0001` = Radar - self test (no Gmail)

Shell setup for any n8n CLI command (non-interactive shells do not load nvm):

```bash
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 24.12.0
export NODES_EXCLUDE="[]" GENERIC_TIMEZONE=Asia/Kolkata N8N_RUNNERS_BROKER_PORT=5691
```

Changing a prompt: edit the file in `prompts/`. It is read on every run; nothing to
restart. `score_schema.json` must list every field the prompt asks for.

Changing a live workflow from the command line (keeps the Gmail credential):

```bash
n8n export:workflow --id=radar3Hourly00001 --output=live.json   # then edit live.json
n8n import:workflow --input=live.json        # this unpublishes the workflow
n8n publish:workflow --id=radar3Hourly00001  # may not exit by itself; see below
systemctl --user restart n8n
```

- `n8n publish:workflow` does its work but often does not exit, and ignores a normal
  `kill`. Check the database or wait a minute, then stop it with `kill -9 <pid>`.
  Do not use `pkill -f "n8n publish"`: it also kills the shell that typed it.
- Do not import the files in `workflows/` over the live workflows. Those copies have no
  credentials attached; they are for reference or a fresh install.
- After any command-line change, refresh the n8n browser tab before touching the editor,
  or saving from the stale tab will undo the change.

`n8n execute --id=radar3Hourly00001` does not work: the command line only starts
workflows that have a manual trigger, and the live one has just the timer. To run it by
hand use **Execute workflow** in the editor.

Changing the job-mail splitter or the fetch window: edit `tools/job_mail_split.js` or
`tools/fetch_window.js`, rebuild, and copy the `parameters` of **Split job mails** or
**Fetch window** from the built JSON into the exported live
workflow, as for **Build mail** below.

Replacing a live workflow with a fresh build: export it, replace its `nodes` and
`connections` with the built ones, copy `credentials` and `webhookId` across by node
name (none are needed since the Gmail nodes went; only a connected Discord node would have one), keep the live **Discord fetch** node, keep `staticData`,
then import and publish as above. `items.json` is no longer used.

Testing without sending mail: build with `RADAR_DIR=$HOME/.n8n-files/radar-test` so the
test never touches the real buffer or day folder. `tools/build_workflows.py <out-dir>` writes `test_a.json`
(3-hourly pipeline with sample items in place of Gmail, no send step). Import it and run
`n8n execute --id=radarSelfTest0001 > run.txt`, then
`python3 tools/summarise_run.py run.txt "Build mail"`. Set `SAMPLE_TAG=-x123` when
building so the sample ids are new and get past the dedupe step. Delete the file the
test leaves in `~/.n8n-files/radar/day/`, or sample items land in the real wrap.

Changing how mails look: edit `tools/mail_template.js`, run
`python3 tools/build_workflows.py <out-dir>`, then copy the `parameters` of the
**Build mail** node from the built JSON into the exported live workflow and re-import as
above. To preview, run the self-test, write the `html` field of **Build mail** to a file
and open it in a browser.

Things learnt the hard way
- `hnrss.org` answers n8n with 429/502; use `https://news.ycombinator.com/showrss`.
- Google will not let an OAuth app leave Testing without homepage + privacy URLs.
- The generic "Google OAuth2 API" credential fails with "Missing required parameter:
  scope"; the Gmail nodes need the "Gmail OAuth2 API" type.
- A node that is switched off passes one empty item through. **Shape Discord** turns it
  into an item with empty text, which the keyword filter drops.
