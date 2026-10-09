# 7. The Gmail login

**Current setup (since 2026-10-09): a Gmail app password.** Nothing is published
anywhere, and the login does not expire.

- The password is in `~/.config/radar/gmail_app_password`, readable only by you.
- `tools/gmail_fetch.py` reads mail with it (IMAP, read-only) and `tools/gmail_send.py`
  sends with it (SMTP). n8n's own Gmail nodes and the Google Cloud app are no longer used.
- To replace the password: delete the `Internship Radar` entry at
  <https://myaccount.google.com/apppasswords>, create a new one, and put the new 16
  letters in that file. Nothing needs restarting.
- If you change your Google account password, Google removes all app passwords. The runs
  then fail with "could not sign in"; create a new app password as above.
- The app password can read and send all mail in the account, so keep that file private.

Once you are happy with this setup you can remove what the old login used: the app's
access at <https://myaccount.google.com/permissions>, the `n8ninternship` project in
Google Cloud, and the "Gmail account" credential in n8n. Going back to the old login
means re-importing `workflows/live_backup_2026-10-09_2345_oauth_*.json`.

---

## The other route, not used: publishing the Google app

Kept for reference. It needs two public pages, which is why the app password was chosen.


The Google app behind the Gmail connection is in **Testing** mode, and Google expires
Testing logins after 7 days. Moving it to **In production** stops that. Google asks for a
home page and a privacy-policy page before it lets you publish; both are ready in
`oauth_pages/`. These steps need your GitHub and Google logins, so they are yours to do.
About 10 minutes.

## A. Put the two pages online (GitHub Pages, free)

1. On <https://github.com/new> create a **public** repository, for example
   `internship-radar`. Tick **Add a README file**.
2. In the repository: **Add file → Upload files**, drag in `oauth_pages/index.html` and
   `oauth_pages/privacy.html`, **Commit changes**.
3. **Settings → Pages**: under **Branch** pick `main` and `/ (root)`, **Save**.
4. After a minute the pages are at
   `https://<your-github-name>.github.io/internship-radar/` and
   `https://<your-github-name>.github.io/internship-radar/privacy.html`. Open both once.

## B. Publish the Google app

1. Open <https://console.cloud.google.com/auth/branding> with project `n8ninternship`
   selected.
2. **Application home page**: the first address. **Application privacy policy link**: the
   second. **Authorized domains**: add `<your-github-name>.github.io`. **Save**.
3. Open **Audience** in the left menu and press **Publish app**, then **Confirm**.
4. Google may offer to start "verification". You can skip it: an unverified app in
   production works for your own account. It only means you see a "Google hasn't
   verified this app" screen when signing in (**Advanced → Go to ...** gets past it).

## C. Sign in once more

In n8n open **Credentials → Gmail account → Sign in with Google** and approve. Logins made
while the app was in Testing still expire, so this last sign-in is the one that lasts.

Not tested: these steps follow Google's rules as I know them, but I could not run them
for you. If step B refuses to save, the message on that page says which field it wants.
