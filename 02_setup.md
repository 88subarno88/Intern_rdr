# 2. Setup

## A. What is already installed

| Thing | Detail |
|---|---|
| Node.js | v24.12.0, already on this laptop through nvm |
| n8n | 2.42.4, installed with `npm install -g n8n@2.42.4` |
| Background service | `~/.config/systemd/user/n8n.service`, starts when you log in to the laptop |
| Address | <http://localhost:5678>, reachable only from this laptop |
| Working folder | `~/.n8n-files/radar/` (n8n's batch files live here) |
| Old n8n data from May | Kept and upgraded; a backup is at `~/.n8n.backup-2026-10-08` |

Settings the service runs with, and why:

| Setting | Why |
|---|---|
| `NODES_EXCLUDE=[]` | Switches on the Execute Command node, which is how n8n calls Claude |
| `N8N_LISTEN_ADDRESS=127.0.0.1` | Nobody else on the Wi-Fi can open your n8n |
| `GENERIC_TIMEZONE=Asia/Kolkata` | "22:00" means 22:00 IST |
| `N8N_DIAGNOSTICS_ENABLED=false` | No usage telemetry sent to n8n |

n8n 2.42.4 is one release behind the newest. The newest one could not be installed on
2026-10-08 because one of its dependencies pointed at a package version that had not been
published yet. Nothing here needs the newer release.

**Logging in:** an owner account already exists from when you tried n8n in May, under
your Gmail address. If you have forgotten the password:

```bash
systemctl --user stop n8n
n8n user-management:reset
systemctl --user start n8n
```

Then open <http://localhost:5678> and create the owner account again. Your workflows stay.

## B. Connect Gmail (your turn, free, about 15 minutes)

**No longer used.** Since 2026-10-09 Gmail is reached with an app password and no Google
Cloud app; see `07_gmail_login_fix.md`. The steps below describe the old login and are
kept only for reference.

Self-hosted n8n needs your own Google "OAuth client". It is a login permission slip, not
a paid API.

1. Go to <https://console.cloud.google.com> and create a project, e.g. `n8n-radar`.
2. **APIs & Services → Library →** search **Gmail API → Enable**.
3. **OAuth consent screen:** user type **External**, fill in an app name and your email.
4. Add yourself under **Test users**.
5. **Credentials → Create credentials → OAuth client ID → Web application.**
   Authorised redirect URI:
   `http://localhost:5678/rest/oauth2-credential/callback`
6. Copy the Client ID and Client Secret.
7. In n8n: **Credentials → Add credential → Gmail OAuth2 API**, paste both, click
   **Sign in with Google** and approve.

**Important:** while the consent screen is in "Testing" mode, Google expires the login
every 7 days and the workflows stop. To avoid that, press **Publish app** on the consent
screen. You will then see an "unverified app" warning when signing in; that is expected
for a personal app only you use.

## C. Switch the workflows on (your turn, 5 minutes)

1. Open **Radar - 3 hourly**. Click the **Gmail fetch** node and pick your Gmail
   credential. Do the same for **Send digest**.
2. Press **Execute workflow** once and click through the nodes to see what each produced.
   The first run scores about 30 Show HN items, so expect a `[Radar]` mail.
3. Switch the workflow on (the **Publish** / **Active** control at the top right).
4. Open **Radar - daily wrap**, pick the credential on **Send wrap**, and switch it on.

## D. Tell Claude who you are

`prompts/score_prompt.md` contains your resume (taken from `~/Downloads/RESUME (1).pdf`
on 2026-10-08, without phone number or email). Claude rates every item against it.
When your resume changes, update that section; the "Not wanted" list below it is the
place to block noise. Changes apply from the next run; nothing needs restarting.
The earlier generic version is kept as `prompts/score_prompt.before-resume.md`.

## E. Discord (your turn, about 15 minutes)

The workflow already contains a **Discord fetch** node and a **Shape Discord** node.
**Discord fetch** is switched off (greyed out) until you give it a bot, because a Discord
node without a login would make every run fail.

### 1. One channel that collects everything

1. In Discord, create your own server (the **+** in the server list), e.g. "My Radar".
2. Create a text channel in it, e.g. `#radar-feed`.
3. In each server you care about, open an **announcement channel** (megaphone icon),
   click **Follow**, and choose your server and `#radar-feed` as the destination.
   Follow as many as you like into the same channel.

Only announcement channels have a Follow button. Ordinary chat channels in servers you do
not manage cannot be read by a bot, and automating your personal account is against
Discord's rules.

### 2. Create the bot

1. Open <https://discord.com/developers/applications> and click **New Application**.
2. Open **Bot** in the left menu. Turn on **Message Content Intent** and save.
3. Click **Reset Token** and copy the token. Treat it like a password.
4. Open **OAuth2 → URL Generator**. Tick the scope `bot`, then the permissions
   **View Channels** and **Read Message History**.
5. Open the generated link, choose your server, and authorise.

### 3. Connect it in n8n

1. Open **Radar - 3 hourly** and double-click **Discord fetch** (bottom-left branch).
2. Under Credential choose **Create new credential** (type **Discord Bot API**), paste
   the token and save.
3. Pick your server under **Server** and `#radar-feed` under **Channel**.
4. Click **Execute step**. You should see the channel's recent messages.
5. Close the panel. Hover over **Discord fetch** and click the power icon (or select the
   node and press `D`) so it is no longer greyed out.
6. Click **Execute workflow** once to check everything is green, then **Publish**.

Discord items skip the keyword filter, since you chose those channels yourself. Claude
still rates each one against your resume.
