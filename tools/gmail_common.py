"""Shared by gmail_fetch.py and gmail_send.py: where the Gmail login lives."""
import os, sys

PASSWORD_FILE = os.path.expanduser('~/.config/radar/gmail_app_password')


def password():
    """The 16-letter Google app password, read from a file only this user can read."""
    try:
        if os.stat(PASSWORD_FILE).st_mode & 0o077:
            sys.exit('%s is readable by other users; run: chmod 600 %s' % (PASSWORD_FILE, PASSWORD_FILE))
        value = ''.join(open(PASSWORD_FILE).read().split())   # Google shows it with spaces
    except FileNotFoundError:
        sys.exit('no app password yet: put it in ' + PASSWORD_FILE)
    if len(value) != 16:
        sys.exit('%s should hold the 16-letter app password and nothing else' % PASSWORD_FILE)
    return value
