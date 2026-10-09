# 3. Workflow A: `Radar - 3 hourly`

Already imported into n8n. This file explains each node so you can change it with
confidence. Timezone is set to `Asia/Kolkata` in the workflow settings.

## Fetch (three branches run side by side)

| Node | What it does |
|---|---|
| **Every 3 hours** | Timer, cron `0 */3 * * *` (00:00, 03:00, 06:00 ... IST) |
| **Catch-up call** | A second way in: a local-only address that `tools/catchup.py` calls when a timed run was missed (see `06_limits_and_fixes.md`) |
| **Fetch window** | Works out how far back this run looks (see below). Code in `tools/fetch_window.js` |
| **Gmail fetch** | Runs `tools/gmail_fetch.py`: every mail from inside the fetch window matching the search below (no cap), saved to `~/.n8n-files/radar/inbox.json`. Signs in with the Gmail app password |
| **Read fetched mail** + **Mail file to list** + **One item per mail** | Turn that file into one item per mail |
| **RSS Reddit internships** | r/developersIndia posts mentioning "internship" |
| **RSS Show HN** | The newest "Show HN" project launches on Hacker News |

Gmail search used (the terms after `after:` are in `tools/gmail_search.txt`):

```
after:<start of the fetch window> -subject:"[Radar]" (intern OR internship OR hiring OR stipend OR hackathon OR fellowship OR "open source" OR "apply by" OR from:jobalerts-noreply@linkedin.com OR from:jobs-noreply@linkedin.com OR from:jobs-listings@linkedin.com OR from:noreply@glassdoor.com OR from:jobalert.indeed.com OR from:student@internshala.com OR from:unstop.news OR from:swelist.com)
```

The `from:` terms pull in every job mail from LinkedIn, Glassdoor, Indeed, Internshala,
Unstop and SWE List even when it contains none of the keywords.
`-subject:"[Radar]"` stops the robot reading its own digests. If an RSS feed is down, that
branch is skipped and the rest of the run carries on.

## The fetch window

Each run only picks up what arrived in the last **3 hours 5 minutes**: the timer period
plus a 5-minute overlap so nothing falls between two runs. Gmail is asked for mails after
that moment, and **Only recent** (after **Merge**) drops RSS and Discord items older than
it. Everything a run keeps is saved to the day folder, and the 22:00 wrap collects the
whole folder.

Catch-up: if the previous timed run was longer ago than that, because the laptop was off
or asleep, the run looks back to 5 minutes before that previous run, at most 24 hours.
Without this, anything arriving while the laptop is off would never be seen. For a
strict 3 h 5 min window every time, set `CATCH_UP = false` in `tools/fetch_window.js`.
Only timed runs move the "previous run" marker. A run started by hand or by the catch-up
watchdog does not, so the next timed run looks back a little further than needed; the
repeat check drops what was already handled.

## Split job mails into single jobs

**Split job mails** sits between **Gmail fetch** and **Shape Gmail**. A job mail lists
several jobs; this node turns it into one item per job, so each job gets its own score
and its own card in the mail. Its code lives in `tools/job_mail_split.js`.

| Board | Read from | Link in the item |
|---|---|---|
| LinkedIn | Plain text, "View job:" lines | `linkedin.com/jobs/view/<n>/` |
| Glassdoor | Plain text, job links in square brackets | `glassdoor.co.in/job-listing/?jl=<n>` |
| Indeed | Plain text, one paragraph per job | `in.indeed.com/viewjob?jk=<key>` |
| Internshala | HTML cards (the mail has no usable plain text) | `internshala.com/internship/detail/...` |
| Unstop | HTML cards: title, organiser, pay | Unstop's own tracking link from the mail |
| SWE List | Plain text, "Company: Role" lines | `simplify.jobs/p/<id>` |

SWE List is treated as its own kind of source. Its roles get the source `swelist`, are
graded against your resume from the role title, and appear in a separate **From SWE
List** section in both the 3-hourly mail and the 22:00 wrap. Its mail usually arrives
between midnight and 3 am, so its roles show up in the 03:00 or 06:00 run.

Every job gets the id `job-<company>--<title>`, built from the company and title in
lower case without punctuation or suffixes such as "Pvt Ltd". The id does not contain
the board, so the same job arriving from two boards, or twice from one, has the same id.

- Every other mail passes through unchanged.
- A job mail it cannot read cleanly (the sender changed the layout, or it is not a job list at all) also passes through whole and is scored as
  one item, as before.
- A job repeated in several mails or on several boards is handled once: inside one run
  the node keeps the first copy, and in later runs **Skip already seen** drops it.
- These items have the board name as `source` and skip the keyword filter.

Limits of the repeat check: it needs the same company and the same title wording.
"Full Stack Developer Intern" and "Full Stack Development internship" count as two jobs,
and one company posting the same title for two cities counts as one. The 22:00 wrap
gives a second chance: its prompt tells Claude to merge items that are the same
opportunity.

## Make every item the same shape

**Shape Gmail**, **Shape RSS 1** and **Shape RSS 2** each turn their source into the same
six fields: `id, source, author, text, link, timestamp`. Text is cut to 1,500 characters
so Claude calls stay small.

**Merge** joins the three branches into one list.

## Filter and dedupe

| Node | What it does |
|---|---|
| **Only recent** | Drops items older than the fetch window. Items with no readable date are kept |
| **Keyword filter** | Lets every split job and Discord post through. For the rest, keeps items whose text mentions intern, hiring, stipend, hackathon, fellowship, open source, apply, launch, released or "Show HN" |
| **Skip already seen** | Drops any `id` handled in an earlier run |

If nothing new is left, the three nodes still pass one empty item on, so that **Ask
Claude** runs and can retry anything left in the buffer from an earlier failed run. With
an empty buffer that step finishes at once without calling Claude, and no mail is sent.

## Buffer and scoring

| Node | What it does |
|---|---|
| **Items to JSON** + **Save to buffer** | Saves this run's new items as one file in `~/.n8n-files/radar/pending/`. That folder is the buffer |
| **Ask Claude** | Runs `tools/score_batch.py`, which scores everything in the buffer |
| **Parse answer** + **Split scored** | Turns the result back into one item per opportunity |
| **Keep relevant** | Safety check: drops anything scoring below 5 |

What `tools/score_batch.py` does:

1. Reads every file in the buffer and drops repeated ids.
2. Sends the items to Claude in chunks of 40, each chunk tried twice.
3. Claude returns only the items worth keeping (score 5 or more), without the link. The
   script puts each item's own link and source back. This is what keeps the answers
   short: about 125 output tokens per item, against about 310 before.
4. Only after scoring does it empty the buffer. Items from a chunk that failed stay in
   the buffer and are retried on the next run. After 5 failed runs an item is moved to
   `~/.n8n-files/radar/failed/` so it stops being retried; it is not deleted.
5. If every chunk fails, the step fails, and the failure alert mails you.

The Claude call it makes for each chunk:

```bash
/home/vzux/.local/bin/claude -p --model haiku --tools "" --strict-mcp-config --no-session-persistence --output-format json --system-prompt-file prompts/score_prompt.md --json-schema "$(cat prompts/score_schema.json)"
```

| Part | Why it is there |
|---|---|
| `-p` | Run once, print the answer, exit |
| `--model haiku` | Smallest model, uses the least of your Pro limit |
| `--tools ""` | Claude can read and answer only, nothing else |
| `--strict-mcp-config` | Do not load your personal connectors for this call |
| `--json-schema` | Forces the answer into the exact fields n8n expects |

The items are fed to Claude as data on its input, never as part of the command.

## Remember and send

After **Keep relevant** the flow splits in two.

| Node | What it does |
|---|---|
| **Day batch to JSON** + **Save for daily wrap** | Saves this run's keepers (each marked with the time if it also goes out in this run's mail) to `~/.n8n-files/radar/day/<date-time>.json` for the 10 pm wrap |
| **Score 7 or more** | Only strong matches go in the 3-hourly mail |
| **Collect top** + **Build mail** | Builds the subject `[Radar] N new: <best title>` and a styled HTML body: the two sections below plus **From SWE List**. Preview: `previews/3_hourly_mail.png` |
| **Digest to JSON** + **Save to outbox** + **Send digest** | Writes the mail to `~/.n8n-files/radar/outbox/` and runs `tools/gmail_send.py`, which sends everything in the outbox. A mail that cannot be sent stays there and goes out with the next send |

If nothing scores 7 or more, no mail is sent.

## How items are rated against your resume

Claude gives every item a `match`, a `score` and a one-line `fit` reason.

| `match` | Meaning | Mail section |
|---|---|---|
| `direct` | The role, stack or topic overlaps your resume | **Matches your resume** |
| `related` | Not on your resume, but a credible next step and clearly high quality | **Not on your resume, but related and worth a look** |
| `none` | Neither; always dropped | - |

For `direct` items the score says how closely your resume meets the stated requirements.
For `related` items it says how exceptional the opportunity is, with 7 or more reserved
for the clearly great ones. Each entry in the mail shows a "Why you:" line with the reason.

## What was tested

Run on 2026-10-08 through the `Radar - self test (no Gmail)` workflow, which is the same
pipeline with sample items in place of Gmail and no send step:

- 30 live Show HN items went in, 13 were kept, 4 scored 7 or more.
- A second run dropped everything already seen.
- An empty branch and a feed outage (the feed returned an error) did not break the run.

Not yet run: the timer, **Gmail fetch** and **Send digest**.

## The Discord branch

**Discord fetch** reads the latest 50 messages of one channel in your own server, and
**Shape Discord** turns them into the six standard fields (message text plus any embed
titles and descriptions; the link points at the original announcement). It feeds input 4
of **Merge**.

**Discord fetch** stays switched off until you connect a bot: see `02_setup.md`,
section E. While it is off, the branch contributes nothing and the rest runs normally.
Not yet tested with real Discord messages.
