# 5. Sources: where the opportunities come from

The robot is only as good as what you feed it. The cheapest strong setup is to make
**Gmail the hub**: switch on email alerts everywhere, and one connector covers them all.

## Gmail

Turn on email alerts or subscribe at:

| Source | What to switch on |
|---|---|
| LinkedIn | Job alerts for "software intern", "ML intern", "research intern" (search, then **Set alert**, daily email). Each job in the mail is scored separately |
| Internshala | Daily internship alerts for your categories. Each internship is scored separately |
| Glassdoor, Indeed | Job alerts for your searches. Each job is scored separately |
| Unstop | Hackathon and competition notifications. Each opportunity is scored separately |
| SWE List | The daily internship mail (<https://swelist.com>). Each role is scored separately and shown in its own mail section |
| Devfolio | Hackathon announcements |
| Wellfound | Startup internship alerts |
| Google Alerts | e.g. `"summer internship 2027" software`, delivered to email |
| College | Placement cell and department mailing lists |
| Programmes | GSoC, MLH Fellowship, LFX Mentorship, Outreachy newsletters |

Tip: create a Gmail filter that labels all of these `radar-src`. You can then tighten the
n8n search to `label:radar-src newer_than:1d`, which makes the keyword list unnecessary
and keeps the robot away from personal mail.

## RSS

No login needed. One **RSS Read** node per feed. Two are already in the workflow:
r/developersIndia posts mentioning "internship", and Hacker News "Show HN".

The Reddit feed is mostly discussion: in the first test all 25 of its posts were
correctly scored as "skip". If it stays empty for a week, swap its URL for a better feed.

| Feed | URL pattern |
|---|---|
| Commits of any GitHub repo (e.g. a community internship list) | `https://github.com/OWNER/REPO/commits/main.atom` |
| Releases of a project you follow | `https://github.com/OWNER/REPO/releases.atom` |
| Hacker News "Show HN" (cool projects) | `https://news.ycombinator.com/showrss` |
| Hacker News front page | `https://news.ycombinator.com/rss` |
| A search inside one subreddit | `https://www.reddit.com/r/SUBREDDIT/search.rss?q=WORD&restrict_sr=1&sort=new` |
| A subreddit | `https://www.reddit.com/r/SUBREDDIT/new/.rss` |
| Company engineering or careers blogs | Look for the RSS icon or try `/feed` or `/rss.xml` |

`hnrss.org` offers filtered Hacker News feeds, but it refused n8n's requests during
testing (errors 429 and 502), so the official feeds above are used instead.

GitHub commit feeds of the big internship-list repos carry only generic commit titles
such as "update listings", so they tell Claude little. Release feeds of projects you
follow are more useful.

## Discord (not connected yet)

Follow announcement channels into your own server (see `02_setup.md`, section E). Good
candidates are the `#announcements`, `#jobs` or `#opportunities` channels of hackathon
organisers, open-source projects and college tech clubs.

Limit: only channels marked as announcement channels can be followed. Ordinary chat
channels in servers you do not manage cannot be read by a bot.

## Twitter / X (left out for now)

Reading tweets automatically is the one piece that is neither free nor simple:

| Option | Cost | Verdict |
|---|---|---|
| Official X API through n8n's X node | Paid; the free tier cannot read tweets. Check current pricing | Works, costs money |
| RSS bridge service (e.g. RSS.app) | Small free tier, paid above it | Fine for 1-2 accounts or a list |
| Self-hosted RSSHub | Free but needs your X login cookies and breaks often | Fiddly |
| Scraping your logged-in timeline | - | Against X's terms; avoid |

Recommendation: run without X for two weeks. Most internship tweets point to a posting
that also reaches you through LinkedIn alerts, GitHub lists or Hacker News. If you still
miss specific accounts, add an RSS bridge for just those and plug it into an RSS Read
node. Nothing else in the workflow changes.

## Adding any new source later

1. Add its fetch node and connect it to **Every 3 hours**.
2. Add an Edit Fields node producing the six standard fields (copy **Shape RSS 1**).
3. Raise "Number of inputs" on **Merge** by one and connect the new branch to it.

Everything after the Merge node stays the same.
