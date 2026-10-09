# 1. How it works

## The idea in one paragraph

n8n is a visual automation tool: you drag boxes ("nodes") onto a canvas and join them
with lines. Each node does one job, such as "read my Gmail" or "send a mail". A group of
joined nodes is a "workflow". A Schedule node at the start makes the workflow run by
itself on a timer. That timer is the cron job.

## Who does what

| Part | Job | Cost |
|---|---|---|
| **n8n** (on your laptop) | Timer, fetching, filtering, remembering what it has seen, sending mail | Free |
| **Claude Code** (`claude -p`) | Reads the candidate messages, scores and summarises them | Your Pro plan |
| **Gmail** | A source of opportunities, and the place the digest is delivered | Free |
| **RSS feeds** | Sources that need no login at all | Free |
| **Discord bot** | Reads channels in your own server | Free |

## The flow

```
          every 3 hours (00:00, 03:00, 06:00 ... IST)
                           |
        +------------------+------------------+
        |                  |                  |
   Gmail: last 24h    RSS feeds      Discord (added later)
        |                  |                  |
        +------------------+------------------+
                           |
              make every item the same shape
          (id, source, author, text, link, timestamp)
                           |
         keyword filter  (intern, hiring, hackathon ...)
                           |
         drop anything already seen in an earlier run
                           |
              save the batch to items.json
                           |
        claude -p  ->  category, score 1-10, title,
                       2-line summary, deadline, link
                           |
               drop "skip" and scores below 5
                           |
             save the keepers in the day folder  ----------+
                           |                               |
                  any score 7 or higher?                   |
                     |            |                        |
                    yes           no                       |
                     |            |                        |
           mail "[Radar] New"   stay silent                |
                                                           |
          every day at 22:00                               |
                 |                                         |
        read today's saved batches  <----------------------+
                 |
        claude -p ranks them, closest deadline first
                 |
        mail "[Radar] Daily wrap", archive the batches
```

## Four design choices that matter

**1. Fetch 24 hours, not 3.** Each run looks back a full day and relies on the
"already seen" step to avoid repeats. If your laptop was asleep for a run, the next run
picks up everything that was missed.

**2. Cheap filter first, Claude second.** A plain keyword check removes most mail before
Claude sees it. This keeps each Claude call tiny, so it barely touches your Pro limit,
and it keeps unrelated private mail away from the model.

**3. Claude gets no tools.** The command runs with `--tools ""`, so Claude can only read
the text and answer. Mails and Discord posts are written by strangers and may contain
text like "ignore your instructions". With no tools, the worst such text can do is get
one item mis-scored.

**4. Text travels in a file, never in the command line.** n8n writes the items to
`items.json` and Claude reads that file. If message text were pasted into the shell
command directly, a crafted mail could run commands on your laptop.

## What "score" means

| Score | Meaning | What happens |
|---|---|---|
| 7-10 | Fits you well | In the 3-hourly mail and the daily wrap |
| 5-6 | Maybe | Daily wrap only |
| 1-4 or "skip" | Noise, expired, fee-charging | Dropped |

Your profile lives in `prompts/score_prompt.md`. Editing that one section is how you
tune what counts as relevant.
