# 6. Limits, costs and fixes

## Cost

| Item | Cost |
|---|---|
| n8n self-hosted | Free |
| Claude | Covered by Claude Pro (no API key, nothing billed per call) |
| Gmail, RSS, Discord bot | Free |
| **Total** | **₹0/month on top of Pro** |

## Limits to know about

**Claude Pro usage is shared.** The 9 calls a day come out of the same allowance as your
normal Claude and Claude Code use. Each call is small: the 3-item test took about
4 seconds and its API-equivalent size was under a tenth of a US cent, and a 30-item
batch also went through in one call.

**A failed Claude call no longer loses items.** New items wait in a buffer
(`~/.n8n-files/radar/pending/`) and are only removed once scored. Whatever fails is
retried on the next run. If a whole run fails, the `Radar - failure alert` workflow mails
you "[Radar] Run failed: ..." with the step and the error.

**The laptop must be on, but you no longer have to be logged in or awake at the exact
time.** Two things cover the gaps:

- n8n now starts when the laptop boots, before you log in (`loginctl enable-linger`).
- A watchdog, `tools/catchup.py`, runs every 5 minutes (`radar-catchup.timer`). If the
  last 3-hour mark passed with no successful run, because the laptop was asleep, off, or
  not yet online, it waits for the internet and then starts the run. That run looks back
  to the previous run, up to 24 hours. It does the same for the 22:00 wrap until
  midnight, after the 3-hourly run so the wrap includes its results.

So after opening the lid or switching on, a missed run starts within about 5 minutes of
the network coming up. A run that failed is tried again after 30 minutes, not every 5.
Mail that arrived during a gap longer than 24 hours is not picked up. Wi-Fi usually
connects only after you log in, so "starts at boot" mostly helps on wired or saved
system-wide networks.

Check the watchdog with `systemctl --user list-timers radar-catchup.timer` and
`journalctl --user -u radar-catchup.service`.

**The daily wrap needs the laptop awake at 22:00.** If it is usually off then, change the
cron to a time you are reliably online.

**Free alternative if Pro quota becomes a problem:** swap **Ask Claude** for n8n's Google
Gemini node with a free-tier key. Note that Google may use free-tier inputs to improve
its models.

## Safety notes

- Mail and Discord text is written by strangers. The Claude call has no tools and the
  text is passed as a file, so a malicious message cannot make it run anything.
- Do not "simplify" **Ask Claude** by pasting `{{ $json.text }}` into the command. That would
  let message text become part of a shell command.
- The Execute Command node can run anything on your laptop. Keep n8n on `localhost` and
  do not expose port 5678 to the internet.
- Only messages that pass the Gmail search are ever shown to Claude. Using a
  `radar-src` label (see `05_sources.md`) narrows this further.

## When something breaks

| Symptom | Likely cause | Fix |
|---|---|---|
| Execute Command node is missing | It is disabled by default | Keep `NODES_EXCLUDE=[]` in the service file |
| `claude: command not found` in n8n | n8n does not have your PATH | Use the full path `/home/vzux/.local/bin/claude` |
| Claude step returns a login or auth error | Claude Code session expired | Run `claude` in a terminal and sign in again |
| Claude step fails with a usage limit message | Pro allowance used up for now | Wait; later runs work again, that batch is skipped |
| File node: access denied | n8n restricts where it can write | Write under `~/.n8n-files/`, or set `N8N_RESTRICT_FILE_ACCESS_TO` |
| **Gmail fetch** or a **Send ...** step fails with "could not sign in" or "Invalid credentials" | The app password was deleted, or your Google password changed | Create a new app password and put it in `~/.config/radar/gmail_app_password` (`07_gmail_login_fix.md`) |
| Same item mailed twice | Dedupe is keyed on the wrong field | **Skip already seen** must use `{{ $json.id }}` |
| Digest mails show up as new items | Search is missing the exclusion | Keep `-subject:"[Radar]"` in the Gmail search |
| Discord messages have empty text | Message Content Intent is off | Enable it on the bot page, re-invite the bot |
| Too much noise | Profile too loose | Tighten `prompts/score_prompt.md`, or raise the cut-off from 7 to 8 |
| Missing good items | Keyword filter or profile too strict | Add keywords in **Keyword filter**; lower the cut-off |
| An RSS branch shows an error item | The feed was down or rate-limited | Nothing; the run continues and the next one retries |
| n8n page does not open | Service is not running | `systemctl --user start n8n` |
| Runs fire at the wrong hour | Timezone not set | Workflow settings → `Asia/Kolkata` |

## Service commands

```bash
systemctl --user status n8n      # is it running?
systemctl --user restart n8n     # restart after changing the service file
journalctl --user -u n8n -n 50   # recent log lines
systemctl --user disable --now n8n   # stop it and keep it from starting again
```

To update n8n later: `npm install -g n8n@latest`, then restart the service.

## Tuning after the first week

1. Look at what the daily wrap contained and what you actually opened.
2. Add two or three "not interested in" lines to the profile for the noise you saw.
3. Add sources for anything you found by hand that the radar missed.
