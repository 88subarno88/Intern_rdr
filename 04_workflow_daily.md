# 4. Workflow B: `Radar - daily wrap`

Already imported into n8n. It reads what Workflow A saved during the day and mails one
ranked summary.

| Node | What it does |
|---|---|
| **Every day 22.00** | Timer, cron `0 22 * * *` |
| **Catch-up call** | A local-only address that `tools/catchup.py` calls if the 22:00 wrap was missed and the laptop comes back before midnight |
| **Write the wrap** | Runs `tools/wrap_batch.py`, which builds the wrap from every file in `~/.n8n-files/radar/day/` (see below) |
| **Anything to send** | Stops here if the day folder was empty |
| **Build mail** | Subject `[Radar] Daily wrap - 08 Oct`, body laid out by the shared mail template. Preview: `previews/daily_wrap_mail.png` |
| **Wrap to JSON** + **Save to outbox** + **Send wrap** | Writes the mail to the outbox and sends it, as in the 3-hourly workflow |
| **Archive today** | Moves the day's files into `~/.n8n-files/radar/sent/` |

The archive step runs after the mail step, so files are only moved once the mail has
actually gone out. If sending fails, tomorrow's wrap includes today's items.

What `tools/wrap_batch.py` does:

1. Reads the day's files and drops items whose deadline has passed.
2. Asks Claude two things only, by item number: which items are the same opportunity,
   and which one is the best of the day. Claude does not rewrite the items, so the
   answer is tiny (about 1,000 to 2,000 output tokens for 86 items, against about
   28,000 when Claude wrote every entry out again).
3. Merges each group of duplicates into its highest-scoring entry, keeping a link to the
   posting over a link to the mail.
4. Puts every entry in its section. Titles, summaries, "Why you" lines and links are
   exactly the ones written when the item was scored.
5. If Claude cannot be reached, the wrap still goes out: nothing is merged, and the top
   line names the highest-scoring item.

## What the wrap contains

The mail is laid out as:

- a green box at the top: "If you only do one thing today: ...",
- **Deadlines in the next 7 days**,
- **Matches your resume**,
- **Related and worth a look**,
- **From SWE List** (every SWE List role kept that day),

each sorted by score, with a "Why you:" line per entry. An entry that already went out in
a 3-hourly mail carries a grey **Already sent HH:MM** tag, so you can skip what you have
seen.

## What was tested

On 2026-10-08 the first three nodes plus **Build mail** ran on a saved batch and produced
a correct mail body. Not yet run: the timer, **Send wrap** and **Archive today**.

## Changing the time

If the laptop is usually off at 22:00, open **Every day 22.00** and change the cron.
`30 20 * * *` means 20:30. Avoid the exact 3-hour marks (21:00, 00:00) so the wrap does
not start while a 3-hourly run is still writing its file.

## Tidy-up

`~/.n8n-files/radar/sent/` grows by a few small files a day. Delete old ones whenever
you like; nothing reads them.
